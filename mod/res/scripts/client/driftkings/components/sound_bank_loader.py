# -*- coding: utf-8 -*-
import glob
import os
from xml.etree import ElementTree
import zipfile

import BigWorld
from frameworks.wulf import WindowLayer
from gui.impl.dialogs import dialogs
from gui.impl.dialogs.builders import WarningDialogBuilder
from gui.impl.pub.dialog_window import DialogButtons as DButtons
from gui.shared.personality import ServicesLocator as SL
from helpers import getClientVersion
import ResMgr
from wg_async import wg_async, wg_await

from driftkings._constants import SOUND_BANK_LOADER
from driftkings.common.utils import events
from driftkings.common.utils.iter import remDups
from driftkings.logger import get_logger
from driftkings.settings.definitions.components.sound_bank_loader import SoundBankLoaderSettings as Settings
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.SoundBankLoader')
curCV = ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString


class AudioModsSection(object):
    """Read-only DataSection subset for XML stored inside mounted mod archives."""
    def __init__(self, element):
        self.element = element

    @property
    def asString(self):
        return (self.element.text or '').strip()

    def has_key(self, name):
        return self.element.find(name) is not None

    def __getitem__(self, name):
        element = self.element.find(name)
        return AudioModsSection(element) if element is not None else None

    def items(self):
        return [(element.tag, AudioModsSection(element)) for element in self.element]

    def values(self):
        return [AudioModsSection(element) for element in self.element]


class BanksLoaderController(object):
    def __init__(self, config):
        self.config = config
        self.editedBanks = {'create': [], 'delete': [], 'memory': [], 'move': [], 'remap': set(), 'wotmod': [], 'section': []}
        self.version_changed = False
        self.was_declined = False
        self._runtimeActive = False
        self._restartPending = False
        self._generation = 0

    def start(self):
        if self._runtimeActive:
            return
        self.suppress_old_mod()
        self.checkConfigs()
        self._runtimeActive = True
        for event in self.restartEvents():
            event.event += self.tryRestart

    def stop(self):
        if not self._runtimeActive:
            return
        self._runtimeActive = False
        self._generation += 1
        for event in self.restartEvents():
            event.event -= self.tryRestart

    @staticmethod
    def restartEvents():
        return (events.LoginView.populate.after, events.LobbyView.populate.after, events.PlayerAvatar.startGUI.after)

    @wg_async
    def tryRestart(self, *_, **__):
        if not self._runtimeActive or self._restartPending or self.was_declined or not any(self.editedBanks.values()):
            return
        self._restartPending = True
        generation = self._generation
        try:
            LOG.info('requesting client restart...')
            reasons = []
            if settings_service.getComponentDict(self.config)[SOUND_BANK_LOADER.DEBUG]:
                for key in self.editedBanks:
                    if self.editedBanks[key]:
                        if isinstance(self.editedBanks[key], (list, set)):
                            reason_text = self.config.i18n['UI_restart_' + key] + ', '.join(('<b>%s</b>' % x for x in remDups(self.editedBanks[key])))
                            reasons.append(reason_text)
            reasonStr = self.config.i18n['UI_restart_reason'].format(';\n'.join(reasons)) if reasons else ''
            dialogText = self.config.i18n['UI_restart_text'].format(reason=self.config.i18n['UI_restart_reason_' + ('update' if self.version_changed else 'new')], reasons=reasonStr)
            builder = WarningDialogBuilder().setFormattedMessage(dialogText).setFormattedTitle(
                self.config.i18n['UI_restart_header'])
            for ID, key in ((DButtons.PURCHASE, 'restart'), (DButtons.RESEARCH, 'shutdown'), (DButtons.SUBMIT, 'close')):
                builder.addButton(ID, None, ID == DButtons.PURCHASE, rawLabel=self.config.i18n['UI_restart_button_%s' % key])
            try:
                parent = SL.appLoader.getApp().containerManager.getContainer(WindowLayer.VIEW).getView()
            except (AttributeError, TypeError):
                parent = None
            result = yield wg_await(dialogs.show(builder.build(parent)))
            if not self._runtimeActive or generation != self._generation:
                return
            if result.result == DButtons.PURCHASE:
                LOG.info('client restart confirmed.')
                BigWorld.savePreferences()
                from driftkings.core.fog_package import coordinated_restart
                if coordinated_restart() is None:
                    BigWorld.restartGame()
            elif result.result == DButtons.RESEARCH:
                LOG.info('client shut down.')
                BigWorld.savePreferences()
                BigWorld.quit()
            elif result.result == DButtons.SUBMIT:
                LOG.info('client restart declined.')
                self.was_declined = True
            return
        finally:
            self._restartPending = False

    @staticmethod
    def suppress_old_mod():
        oldModName = curCV + '/scripts/client/gui/mods/mod_wg_load_custom_ekspont_banks.pyc'
        if os.path.isfile(oldModName) and os.path.isfile(oldModName + '1'):
            try:
                os.remove(oldModName + '1')
            except StandardError:
                LOG.exception('Sound bank loader error')
        if os.path.isfile(oldModName):
            os.rename(oldModName, oldModName + '1')

    def check_wotmods(self, mediaPath):
        # Read package metadata directly: no masking package or renamed archive
        # is required when the consolidated XML lives in the loose overrides.
        modsRoot = curCV.replace('res_', '') + '/'
        load_order_xml = '.' + modsRoot + 'load_order.xml'
        legacy = '_aaa_BanksLoader_audioMods.wotmod'
        orderSect = ResMgr.openSection(load_order_xml)
        collection = orderSect['Collection'] if orderSect is not None else None
        order = [item.asString for item in collection.values()] if collection is not None else []
        packages = {}
        legacy_present = False
        for folder, directories, files in os.walk(modsRoot):
            directories.sort()
            for name in sorted(files):
                if name == legacy:
                    legacy_present = True
                    continue
                if not name.endswith('.wotmod') or '_BanksLoaded' in name:
                    continue
                path = os.path.join(folder, name)
                relative = os.path.relpath(path, modsRoot).replace(os.sep, '/')
                packages[relative] = path
        sequence = []
        for name in order:
            name = name.replace('\\', '/')
            if name in packages and name not in sequence:
                sequence.append(name)
        sequence.extend(name for name in sorted(packages) if name not in sequence)
        sections, bank_sections = [], {}
        resource = 'res/%s/audio_mods.xml' % mediaPath
        for name in sequence:
            with zipfile.ZipFile(packages[name]) as archive:
                if resource not in archive.namelist():
                    continue
                # Parse every input before changing load_order or publishing XML.
                # Invalid input must leave the previous override untouched.
                try:
                    element = ElementTree.fromstring(archive.read(resource))
                except (ElementTree.ParseError, ValueError) as error:
                    raise ValueError('Invalid audio_mods.xml in %s: %s' % (name, error))
                sections.append(AudioModsSection(element))
                target = element.find('engine_config_section')
                banks = [path for path in archive.namelist()
                         if path.startswith('res/' + mediaPath + '/') and path.endswith('.bnk')]
                if target is not None and target.text and banks:
                    bank_sections[os.path.basename(banks[0])] = target.text.strip()
        self._packageAudioMods = sections
        self._packageBankSections = bank_sections
        if legacy_present and not os.path.isfile(curCV + '/' + mediaPath + '/audio_mods.xml'):
            self.editedBanks['remap'].add('audio_mods.xml')
        # Migrate only the obsolete helper reference. Do not rewrite other mods'
        # archives, remove their files or create load_order.xml unnecessarily.
        if collection is not None:
            changed = False
            for item in list(collection.values()):
                if os.path.basename(item.asString.replace('\\', '/')) == legacy:
                    collection.deleteSection(item)
                    changed = True
            if changed:
                orderSect.save()
                self.editedBanks['wotmod'].append('load_order.xml')
        ResMgr.purge(load_order_xml, True)

    def checkConfigs(self):
        while True:
            orig_engine = ResMgr.openSection('engine_config.xml')
            if orig_engine is None:
                LOG.error('ERROR: engine_config.xml not found')
                return
            path = curCV + '/' + 'engine_config.xml'
            if not os.path.isfile(path):
                break
            if orig_engine.has_key('BanksLoader_gameVersion') and orig_engine[
                'BanksLoader_gameVersion'].asString == getClientVersion():
                break
            LOG.info('client version change detected')
            self.version_changed = True
            try:
                os.remove(path)
            except StandardError:
                LOG.exception('Sound bank loader error')
            del orig_engine
            ResMgr.purge('engine_config.xml')
        new_engine = ResMgr.openSection('./engine_config_edited.xml', True)
        new_engine.copy(orig_engine)
        if not new_engine.has_key('BanksLoader_gameVersion'):
            new_engine.writeString('BanksLoader_gameVersion', getClientVersion())
        ResMgr.purge('engine_config.xml')
        soundMgr = new_engine['soundMgr']
        mediaPath = soundMgr['wwmediaPath'].asString
        self.check_wotmods(mediaPath)
        bankFiles = self.collectBankFiles(mediaPath)
        audio_mods_new = self.merge_audio_mods(mediaPath, bankFiles)
        self.manageMemorySettings(soundMgr)
        for profile_name in ('WWISE_active_profile', 'WWISE_emergency_profile'):
            profile_type = profile_name.split('_')[1]
            profile = soundMgr[soundMgr[profile_name].asString]
            self.manageProfileMemorySettings(profile_type, profile)
            self.manageProfileBanks(profile_type, profile, bankFiles)
        self.saveNewFile(audio_mods_new, mediaPath + '/', 'audio_mods_edited.xml', mediaPath + '/audio_mods.xml',('delete', 'move', 'remap'))
        self.saveNewFile(new_engine, '', 'engine_config_edited.xml', 'engine_config.xml', ('delete', 'move', 'create', 'memory'))

    def collectBankFiles(self, mediaPath):
        bankFiles = {
            'mods': set(), 'pkg': set(), 'ignore': set(), 'section': {},
            'audio_mods_allowed': ('protanki.bnk',),
            'res': {os.path.basename(path) for path in glob.iglob('./res/' + mediaPath + '/*') if os.path.splitext(path)[1] in ('.bnk', '.pck')}
        }
        for pkgPath in glob.iglob('res/packages/audioww*.pkg'):
            with zipfile.ZipFile(pkgPath) as pkg:
                bankFiles['pkg'].update({os.path.basename(name) for name in pkg.namelist()})
        bankFiles['orig'] = bankFiles['res'] | bankFiles['pkg']
        bankFiles['mods'] = set((x for x in ResMgr.openSection(mediaPath).keys() if os.path.splitext(x)[1] in ('.bnk', '.pck') and not any((y in bankFiles['orig'] for y in (x, x.lower())))))
        bankFiles['all'] = bankFiles['orig'] | bankFiles['mods']
        return bankFiles

    def recollectExtensionBankFiles(self, extensionName, bankFiles):
        extensionPath = 'res/packages/%s.pkg' % extensionName
        if not os.path.exists(extensionPath):
            LOG.info('found extension field in bank define but it is missing')
            return
        with zipfile.ZipFile(extensionPath) as extension:
            extensionBanks = {os.path.basename(name) for name in extension.namelist() if name.endswith(('.bnk', 'pck'))}
            LOG.info('found extension banks %s for extension %s', list(extensionBanks), extensionName)
            bankFiles['pkg'].update(extensionBanks)
            bankFiles['orig'] = bankFiles['res'] | bankFiles['pkg']
            bankFiles['all'] = bankFiles['orig'] | bankFiles['mods']

    def check_and_collect_data(self, key, section, struct, is_orig):
        result = []
        for name, sect in section.items() if section is not None else ():
            if name != struct['key'] or not all((sect.has_key(x) for x in struct['keys'])):
                if is_orig:
                    self.editedBanks['remap'].add(key)
                    LOG.info('cleaned wrong section for setting %s', key)
                continue
            data = {x: sect[x].asString for x in struct['keys']}
            if struct['data']:
                sub_name = struct['data']['name']
                if sect.has_key(sub_name):
                    data[sub_name] = self.check_and_collect_data(key, sect[sub_name], struct['data'], is_orig)
                else:
                    data[sub_name] = []
            result.append(data)
        return result

    def create_sect_from_data(self, sect, data, struct):
        for data in data:
            new_sect = sect.createSection(struct['key'])
            for key in struct['keys']:
                new_sect.writeString(key, data[key])
            if struct['data']:
                sub_name = struct['data']['name']
                self.create_sect_from_data(new_sect.createSection(sub_name), data[sub_name], struct['data'])

    @staticmethod
    def merge_records(previous, incoming, struct):
        # Overlay updated mappings by identity, while retaining unrelated entries
        # and nested switch/state mappings contributed by other mods.
        result = [dict(item) for item in previous]
        for item in incoming:
            identity = item[struct['keys'][0]]
            existing = next((index for index, value in enumerate(result)
                             if value[struct['keys'][0]] == identity), None)
            if existing is None:
                result.append(dict(item))
                continue
            merged = dict(result[existing])
            merged.update(item)
            nested = struct['data']
            if nested:
                key = nested['name']
                merged[key] = BanksLoaderController.merge_records(
                    result[existing].get(key, []), item.get(key, []), nested)
            result[existing] = merged
        return result

    def merge_audio_mods(self, mediaPath, bankFiles):
        audio_mods = ResMgr.openSection(mediaPath + '/audio_mods.xml')
        edited_path = mediaPath + '/audio_mods_edited.xml'
        ResMgr.purge(edited_path, True)
        audio_mods_new = ResMgr.openSection(edited_path, True)
        for name, section in list(audio_mods_new.items()):
            audio_mods_new.deleteSection(section)
        if audio_mods is not None:
            # Preserve sections outside the known remapping schema as well.
            audio_mods_new.copy(audio_mods)
        else:
            self.editedBanks['remap'].add('audio_mods.xml')
        data_structure = [
            {'name': 'events', 'key': 'event', 'keys': ('name', 'mod'), 'data': ()},
            {'name': 'switches', 'key': 'switch', 'keys': ('name', 'mod'), 'data': {'name': 'states', 'key': 'state', 'keys': ('name', 'mod'), 'data': ()}},
            {'name': 'RTPCs', 'key': 'RTPC', 'keys': ('name', 'mod'), 'data': ()},
            {'name': 'states', 'key': 'stateGroup', 'keys': ('name', 'mod'), 'data': {'name': 'stateNames', 'key': 'state', 'keys': ('name', 'mod'), 'data': ()}}
        ]
        sources = []
        folder = ResMgr.openSection(mediaPath)
        for path in sorted(folder.keys() if folder is not None else ()):
            if not path.endswith('.xml') or path.replace('.xml', '.bnk') not in bankFiles['all']:
                continue
            section = ResMgr.openSection(mediaPath + '/' + path)
            bankName = path.replace('.xml', '.bnk')
            if section is None:
                bankFiles['ignore'].add(bankName)
                LOG.error('error while reading %s', path)
                continue
            sources.append(section)
            if section.has_key('engine_config_section'):
                bankFiles['section'][bankName] = section['engine_config_section'].asString
        bankFiles['section'].update(getattr(self, '_packageBankSections', {}))
        sources.extend(getattr(self, '_packageAudioMods', ()))
        for struct in data_structure:
            key = struct['name']
            old = self.check_and_collect_data(key, audio_mods[key], struct, True) if audio_mods is not None and audio_mods.has_key(key) else []
            merged = self.merge_records([], old, struct)
            for section in sources:
                incoming = self.check_and_collect_data(key, section[key], struct, False) if section.has_key(key) else []
                merged = self.merge_records(merged, incoming, struct)
            if old != merged:
                self.editedBanks['remap'].add(key)
            if audio_mods_new.has_key(key):
                audio_mods_new.deleteSection(key)
            self.create_sect_from_data(audio_mods_new.createSection(key), merged, struct)
        # Preserve explicit loadBanks registrations, including XML-only packages.
        banks, old_banks = [], []
        for section in ([audio_mods] if audio_mods is not None else []) + sources:
            if not section.has_key('loadBanks'):
                continue
            for bank in section['loadBanks'].values():
                child = bank['name']
                name = bank.asString or (child.asString if child is not None else '')
                if name and name not in banks:
                    banks.append(name)
            if section is audio_mods:
                old_banks = list(banks)
        if old_banks != banks:
            self.editedBanks['remap'].add('loadBanks')
        if audio_mods_new.has_key('loadBanks'):
            audio_mods_new.deleteSection('loadBanks')
        loadBanks = audio_mods_new.createSection('loadBanks')
        for name in banks:
            loadBanks.createSection('bank').writeString('name', name)
        # Explicit audio_mods loading owns these banks. Do not also register
        # them in engine_config profiles, and remove stale profile entries.
        bankFiles['audio_mods_allowed'] = set(bankFiles['audio_mods_allowed']) | set(banks)
        return audio_mods_new

    def manageMemorySettings(self, soundMgr):
        settings = settings_service.getComponentDict(self.config)
        for mgrKey in ('memoryLimit',):
            value = soundMgr[mgrKey]
            if value is not None and value.asInt != int(settings[mgrKey]):
                self.editedBanks['memory'].append(mgrKey)
                soundMgr.writeInt(mgrKey, settings[mgrKey])
                LOG.info('changing value for memory setting: %s', mgrKey)

    def manageProfileMemorySettings(self, profile_type, profile):
        settings = settings_service.getComponentDict(self.config)
        poolKeys = {
            'memoryManager': ('defaultPool', 'lowEnginePool', 'streamingPool', 'IOPoolSize'),
            'memoryManager_64bit': ('defaultPool', 'lowEnginePool', 'streamingPool', 'IOPoolSize'),
            'soundRender': ('max_voices',)
        }
        for poolKey, poolValuesList in poolKeys.iteritems():
            for poolValue in poolValuesList:
                value = profile[poolKey][poolValue]
                if value is not None and value.asInt != int(settings[poolValue]):
                    self.editedBanks['memory'].append(poolValue)
                    profile[poolKey].writeInt(poolValue, settings[poolValue])
                    LOG.info('changing value for %s memory setting: %s', profile_type, poolValue)
        return

    def manageProfileBanks(self, profile_type, profile, bankFiles):
        exist = set()
        for name, section in profile.items():
            if 'soundbanks' not in name:
                continue
            for sectName, bank in section.items():
                if sectName != 'bank':
                    continue
                bankName = bank['name'].asString
                bankExtension = bank.readString('extension', '')
                if bankExtension and bankName not in bankFiles['all']:
                    LOG.info('found section for missing bank %s with existing extension %s', bankName, bankExtension)
                    self.recollectExtensionBankFiles(bankExtension, bankFiles)
                if bankName not in bankFiles['all'] or bankName in bankFiles['audio_mods_allowed']:
                    LOG.info('clearing %s section for missing bank %s', profile_type, bankName)
                    self.editedBanks['delete'].append(bankName)
                    section.deleteSection(bank)
                if bankFiles['section'].get(bankName, name) != name:
                    LOG.info('deleting %s section from %s for bank %s', profile_type, name, bankName)
                    self.editedBanks['section'].append(bankName)
                    section.deleteSection(bank)
                if bankName in bankFiles['mods'] and bankName in exist:
                    LOG.info('clearing %s section duplicate for bank %s', profile_type, bankName)
                    self.editedBanks['delete'].append(bankName)
                    section.deleteSection(bank)
                exist.add(bankName)
        bankFiles['orig'] = {x.lower() for x in bankFiles['orig']}
        for bankName in sorted(bankFiles['mods']):
            if not any((bankName in bankFiles[x] for x in ('orig', 'ignore', 'audio_mods_allowed'))) and bankName not in exist:
                sectName = bankFiles['section'].get(bankName, 'SFX_soundbanks_loadonce')
                LOG.info('creating %s section in %s for bank %s', profile_type, sectName, bankName)
                if bankName in self.editedBanks['delete']:
                    self.editedBanks['delete'].remove(bankName)
                    self.editedBanks['move'].append(bankName)
                elif bankName not in self.editedBanks['section']:
                    self.editedBanks['create'].append(bankName)
                profile.createSection(sectName + '/bank').writeString('name', bankName)

    def saveNewFile(self, new_file, new_dir, new_name, orig_path, keys):
        if not any((self.editedBanks[key] for key in keys)):
            ResMgr.purge(new_dir + new_name)
            return
        orig_path = curCV + '/' + orig_path
        new_path = new_dir + new_name
        new_dir = curCV + '/' + new_dir
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        new_file.save()
        candidates = (new_dir + new_name, './res/' + new_path, './' + new_path)
        staged = next((path for path in candidates if os.path.isfile(path)), None)
        if staged is None:
            raise IOError('BanksLoader staged XML not found: ' + new_name)
        backup = orig_path + '.BanksLoader.bak'
        if os.path.exists(backup):
            raise IOError('BanksLoader XML backup requires recovery: ' + backup)
        previous = os.path.isfile(orig_path)
        if previous:
            os.rename(orig_path, backup)
        try:
            os.rename(staged, orig_path)
        except StandardError:
            if previous:
                os.rename(backup, orig_path)
            raise
        if previous:
            os.remove(backup)


_config = Settings()
controller = BanksLoaderController(_config)


def init():
    controller.start()


def fini():
    controller.stop()
