# -*- coding: utf-8 -*-
"""Schedule the optional map package; the native worker applies it after exit."""
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from driftkings._constants import BATTLE_PREFERENCES, GLOBAL
from driftkings.core.updater.installer import read_resource
from driftkings.core.updater.versioning import normalize_game_version
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.Fog')
RESOURCE = 'gui/driftkings/fog/Driftkings.FogPackage.exe'
INFO = 'gui/driftkings/fog/helper.json'
PACKAGE = 'Driftkings.RemoveFog.wotmod'
REMOVE_FOG_MOD_ID = 'driftkings.removefog'
# Legacy resolution of the persisted preference; EXPLICIT and DEFAULT_OFF never write.
DEFAULT_OFF = 'default_off'
EXPLICIT = 'explicit'
LEGACY_MIGRATE = 'legacy_migrate'
AMBIGUOUS = 'ambiguous'
_controller = None


def package_evidence(path):
    """'absent', 'owned' (a readable Driftkings Remove Fog package) or 'foreign' (anything else)."""
    if not os.path.lexists(path):
        return 'absent'
    try:
        if not os.path.isfile(path):
            return 'foreign'
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo('meta.xml')
            if info.file_size > 8192:
                return 'foreign'
            meta = ET.fromstring(archive.read(info))
            return 'owned' if meta.findtext('id') == REMOVE_FOG_MOD_ID else 'foreign'
    except (IOError, OSError, KeyError, ValueError, zipfile.BadZipfile, ET.ParseError):
        return 'foreign'


def classify_preference(profile_file, package):
    """Resolve the legacy state from the active profile and the package of the matching client folder only.

    The key's presence is read from the file, never inferred from its value. The loader writes defaults into a
    missing file before this runs, so a file that exists with an explicit false is indistinguishable from a
    materialized default; that is why automatic code never removes a package (see startup()).
    """
    from driftkings.settings.store import read_object
    if not os.path.isfile(profile_file):
        # A profile with no stored preference is a new profile: never migrated, never written here.
        return DEFAULT_OFF
    try:
        values = read_object(profile_file)
    except (IOError, OSError, ValueError):
        return AMBIGUOUS
    if BATTLE_PREFERENCES.REMOVE_FOG in values:
        return EXPLICIT if type(values[BATTLE_PREFERENCES.REMOVE_FOG]) is bool else AMBIGUOUS
    evidence = package_evidence(package)
    if evidence == 'absent':
        return DEFAULT_OFF
    if evidence == 'owned':
        return LEGACY_MIGRATE
    return AMBIGUOUS


def migrate_preference(profile_file, package):
    """Persist removeFog=true for a legacy profile with no key and an owned package; idempotent, no marker file."""
    state = classify_preference(profile_file, package)
    if state == LEGACY_MIGRATE:
        from driftkings.settings.store import read_object, SettingsStore
        values = read_object(profile_file) if os.path.isfile(profile_file) else {}
        values[BATTLE_PREFERENCES.REMOVE_FOG] = True
        SettingsStore(profile_file).write(values)
        LOG.info('Legacy Remove Fog preference migrated to true (owned package present)')
    return state


def mentions_remove_fog(changes):
    try:
        return BATTLE_PREFERENCES.REMOVE_FOG in changes
    except TypeError:
        return False


def coordinated_restart():
    """None means no fog work; True means its worker now owns the restart."""
    if _controller is None or _controller.process is None:
        return None
    return _controller.request_restart()


def mod_directory(root, version):
    """Resolve only the client's declared version folder, including the CT suffix."""
    if normalize_game_version(version) != version:
        raise ValueError('Invalid fog client version')
    names = (version, version + ' Common Test')
    paths = os.path.join(root, 'paths.xml')
    if os.path.isfile(paths):
        matches = []
        for node in ET.parse(paths).findall('./Paths/Path'):
            value = (node.text or '').strip().replace('\\', '/')
            for name in names:
                if value in ('./mods/' + name, 'mods/' + name) and name not in matches:
                    matches.append(name)
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous client mod path')
        folder = matches[0]
    else:
        folder = version
    directory = os.path.join(root, 'mods', folder)
    if not os.path.isdir(directory):
        raise ValueError('Client mod version directory missing')
    return directory


def source_stamp(root):
    """Match the native generator's inventory stamp without reading map content."""
    import re
    folder = os.path.join(root, 'res', 'packages')
    lines = []
    for name in sorted(os.listdir(folder)):
        if not re.match(r'^\d+_.+\.pkg\Z', name) or name.endswith('_hd.pkg'):
            continue
        stat = os.stat(os.path.join(folder, name))
        lines.append('%s:%d:%d\n' % (name, stat.st_size, int(stat.st_mtime)))
    return hashlib.sha256(''.join(lines).encode('utf-8')).hexdigest()


def package_current(path, stamp):
    if not os.path.isfile(path):
        return False
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo('meta.xml')
        if info.file_size > 8192:
            raise ValueError('Fog metadata exceeds limit')
        meta = ET.fromstring(archive.read(info))
        if meta.findtext('id') != 'driftkings.removefog':
            raise ValueError('Optional package belongs to another mod')
        return meta.findtext('sources') == stamp


class FogPackageController(object):
    def __init__(self, config):
        self.config = config
        self.process = None
        self.token = None
        self.notice = None
        self.previous_error = False
        self.active = False
        self.desired = None
        self.revision = 0
        self.restart_requested = False
        self.hold = False
        # The preference the fog package should follow. Set by prepare() and by explicit user changes only;
        # a reload, a profile load or a materialized default never sets it.
        self.intent_value = None

    def current_intent(self):
        if self.intent_value is not None:
            return self.intent_value
        value = self.config.data.get(BATTLE_PREFERENCES.REMOVE_FOG)
        return value if type(value) is bool else None

    def start(self):
        global _controller
        from helpers import getClientVersion

        from driftkings.common.utils import events
        from driftkings.core.callbacks import callbacks
        self.callbacks = callbacks
        self.root = os.path.abspath(os.getcwd())
        self.version = normalize_game_version(getClientVersion())
        if self.version is None:
            raise ValueError('Unknown client version for fog package')
        self.cache = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'cache', 'fog')
        self.stage = os.path.join(self.cache, 'session-' + str(os.getpid()))
        self.target = os.path.join(mod_directory(self.root, self.version), PACKAGE)
        self.active = True
        _controller = self
        # Resolve the stored preference before any signal can call changed(): the connection comes after.
        from driftkings.settings.loader import settings_loader
        self.prepare(settings_loader.path(BATTLE_PREFERENCES.NAME))
        self.event = events.LobbyView.populate.after.event
        self.event += self.lobby
        settings_service.onModSettingsChanged.connect(self.changed, BATTLE_PREFERENCES.NAME,
            (GLOBAL.ENABLED, BATTLE_PREFERENCES.REMOVE_FOG))
        self.previous_result()
        self.startup()

    def startup(self):
        """Automatic work at launch: install or refresh only for an on preference; never remove."""
        if self.hold:
            return
        if self.current_intent() is not True:
            return
        self.changed(None, {})

    def prepare(self, profile_file):
        """Resolve the persisted preference before any automatic decision; ambiguity schedules nothing."""
        from driftkings.settings.store import read_object
        try:
            state = migrate_preference(profile_file, self.target)
            if state == DEFAULT_OFF:
                self.intent_value = False
            elif state in (EXPLICIT, LEGACY_MIGRATE):
                value = bool(read_object(profile_file)[BATTLE_PREFERENCES.REMOVE_FOG])
                self.config.data[BATTLE_PREFERENCES.REMOVE_FOG] = value
                self.intent_value = value
        except Exception:
            state = AMBIGUOUS
            LOG.exception('Remove Fog preference could not be resolved safely')
        if state == AMBIGUOUS:
            self.intent_value = None
            self.hold = True
            LOG.warning('Remove Fog preference ambiguous; no automatic fog operation is scheduled')
        return state

    def previous_result(self):
        if not os.path.isdir(self.cache):
            return
        results = []
        for name in os.listdir(self.cache):
            if not name.startswith('session-'):
                continue
            path = os.path.join(self.cache, name, 'result')
            if os.path.isfile(path):
                results.append((os.path.getmtime(path), path))
        if not results:
            return
        path = max(results)[1]
        if os.path.exists(path + '.reported'):
            return
        with open(path, 'rb') as stream:
            value = stream.read(4096).decode('utf-8-sig', 'replace')
        if value.startswith(self.version + ':error:'):
            LOG.error('Previous fog operation failed: %s', value)
            self.previous_error = True
        else:
            LOG.info('Previous fog operation: %s', value)
        with open(path + '.reported', 'wb') as stream:
            stream.write(b'1')

    def remove_stale_sessions(self, age=86400, limit=20):
        """Keep this session and the latest result; a helper still running keeps its files locked."""
        import time

        from driftkings.core.updater.results import remove_flat_directory
        sessions = []
        for name in os.listdir(self.cache):
            folder = os.path.join(self.cache, name)
            if name.startswith('session-') and os.path.isdir(folder):
                result = os.path.join(folder, 'result')
                sessions.append((os.path.getmtime(result) if os.path.isfile(result) else 0, folder))
        latest = max(sessions)[1] if sessions else None
        threshold = time.time() - age
        removed = 0
        for _, folder in sorted(sessions):
            if removed >= limit:
                break
            if folder in (self.stage, latest) or os.path.getmtime(folder) > threshold:
                continue
            try:
                remove_flat_directory(folder)
                removed += 1
            except Exception:
                LOG.debug('Kept fog session folder %s', folder, exc_info=True)

    def present_intent(self, changes):
        """After a reload, show the preference the package follows; no write, no event, no scheduled work.

        The panel describes the live dictionary, so the in-memory option is set to the known intent when a reload
        replaced it with a default. Unknown or held states keep what was read.
        """
        if not mentions_remove_fog(changes) or self.hold or self.intent_value is None:
            return
        if self.config.data.get(BATTLE_PREFERENCES.REMOVE_FOG) != self.intent_value:
            self.config.data[BATTLE_PREFERENCES.REMOVE_FOG] = self.intent_value

    def changed(self, component, changes):
        if not self.active:
            return
        if getattr(changes, 'origin', None) == 'reload':
            # Reading storage (panel open, missing file, missing key, external edit) never schedules work.
            self.present_intent(changes)
            return
        mentions = mentions_remove_fog(changes)
        if self.hold and not mentions:
            # Ambiguous legacy state: only an explicit user change to the option may act.
            return
        if mentions and component is not None:
            value = self.config.data.get(BATTLE_PREFERENCES.REMOVE_FOG)
            if type(value) is not bool:
                LOG.warning('Remove Fog preference missing or invalid; no fog operation is scheduled')
                return
            self.intent_value = value
            self.hold = False
        intent = self.current_intent()
        if intent is None:
            LOG.warning('Remove Fog preference unknown; no fog operation is scheduled')
            return
        desired = bool(self.config.data[GLOBAL.ENABLED] and intent)
        if (component is None or not mentions) and not desired:
            # Automatic calls, and the master switch alone, never remove the package: only an explicit change of
            # the Remove Fog option may order a removal.
            return
        try:
            if self.process is None:
                if desired and package_current(self.target, source_stamp(self.root)):
                    self.desired = desired
                    return
                if not desired and not os.path.exists(self.target):
                    self.desired = desired
                    return
            if self.desired == desired and self.process is not None and self.process.poll() is None:
                return
            self.schedule(desired)
        except Exception:
            LOG.exception('Could not schedule optional fog package')
            self.notice = 'UI_fog_error'
            self.notify()

    def schedule(self, desired):
        # ResMgr reads stay on the client thread. No Python installation is needed.
        if self.process is not None and self.process.poll() is not None:
            raise RuntimeError('Fog installer exited before the client')
        if self.process is None:
            binary = read_resource(RESOURCE)
            metadata = json.loads(read_resource(INFO).decode('utf-8'))
            if (metadata.get('schema') != 1 or metadata.get('size') != len(binary) or
                    not 0 < len(binary) <= 256 * 1024 or
                    hashlib.sha256(binary).hexdigest() != metadata.get('sha256')):
                raise ValueError('Fog helper identity mismatch')
            if not os.path.isdir(self.stage):
                os.makedirs(self.stage)
            from driftkings.core.updater import windows_files
            windows_files.initialize(read_resource, self.root)
            windows_files.safe_path(self.stage)
            try:
                self.remove_stale_sessions()
            except Exception:
                LOG.debug('Fog session cleanup skipped', exc_info=True)
            helper = os.path.join(self.stage, 'Driftkings.FogPackage.exe')
            descriptor = os.open(helper, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
            with os.fdopen(descriptor, 'wb') as output:
                output.write(binary)
                output.flush()
                os.fsync(output.fileno())
        # Persist the last applied selection, including toggles/profile changes.
        self.revision += 1
        if self.revision > 99999999:
            raise ValueError('Fog request revision limit')
        request = os.path.join(self.stage, 'request-%08d.%s' % (self.revision, 'on' if desired else 'off'))
        descriptor = os.open(request, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
        with os.fdopen(descriptor, 'wb') as output:
            output.flush()
            os.fsync(output.fileno())
        self.desired = desired
        if self.process is None:
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            self.process = subprocess.Popen([helper, str(os.getpid()), self.version, self.stage],
                shell=False, startupinfo=startup, creationflags=0x08000000)
        self.notice = 'UI_fog_restart_on' if desired else 'UI_fog_restart_off'
        LOG.info('Fog selection scheduled: enabled=%s client=%s stage=%s', desired, self.version, self.stage)
        if self.token is None:
            self.wait_ready(0)

    def wait_ready(self, attempt):
        self.token = None
        if not self.active:
            return
        if self.process.poll() is not None or attempt >= 600:
            LOG.error('Fog helper did not acknowledge scheduling: %s', self.stage)
            self.notice = 'UI_fog_error'
            self.restart_requested = False
            self.notify()
        elif os.path.isfile(os.path.join(self.stage, 'prepared')):
            self.notify()
            if self.restart_requested:
                self.finish_restart()
        else:
            self.token = self.callbacks.schedule(0.1, lambda: self.wait_ready(attempt + 1))

    def request_restart(self):
        if not self.active or self.process is None or self.process.poll() is not None:
            self.notice = 'UI_fog_error'
            self.notify()
            return False
        self.restart_requested = True
        if self.token is None:
            self.wait_ready(0)
        return True

    def finish_restart(self):
        import BigWorld
        path = os.path.join(self.stage, 'restart')
        try:
            BigWorld.savePreferences()
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(str(os.getpid()).encode('ascii'))
                stream.flush()
                os.fsync(stream.fileno())
            if self.process.poll() is not None:
                raise RuntimeError('Fog installer exited before coordinated restart')
            LOG.info('Coordinated fog restart confirmed; worker will reopen the client after installation')
            BigWorld.quit()
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            LOG.exception('Could not request coordinated fog restart')
            self.notice = 'UI_fog_error'
            self.notify()
        finally:
            self.restart_requested = False

    def lobby(self, *args, **kwargs):
        self.notify()

    def notify(self):
        if not self.notice and not self.previous_error:
            return
        from driftkings.settings.panel import settings
        if not settings.started or settings.in_battle:
            return
        from gui.shared.personality import ServicesLocator
        from skeletons.gui.app_loader import GuiGlobalSpaceID
        if ServicesLocator.appLoader.getSpaceID() != GuiGlobalSpaceID.LOBBY:
            return
        from gui import SystemMessages
        if self.previous_error:
            SystemMessages.pushMessage(self.config.i18n['UI_fog_error'], type=SystemMessages.SM_TYPE.Information)
            self.previous_error = False
        if self.notice:
            SystemMessages.pushMessage(self.config.i18n[self.notice], type=SystemMessages.SM_TYPE.Information)
        self.notice = None

    def stop(self):
        global _controller
        if _controller is self:
            _controller = None
        self.active = False
        settings_service.onModSettingsChanged.disconnect(self.changed)
        if hasattr(self, 'event'):
            self.event -= self.lobby
        if self.token is not None:
            self.callbacks.cancel(self.token)
            self.token = None
        # The worker deliberately survives shutdown to apply the saved request.
