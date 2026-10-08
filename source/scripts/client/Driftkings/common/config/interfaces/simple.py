# -*- coding: utf-8 -*-
import os
import traceback

import ResMgr

from Driftkings import VERSION
from Driftkings.settings.lifecycle import SettingsLifecycle
from ..json_reader import loadJson, loadJsonOrdered
from ..template_builders import TemplateBuilder
from ..utils import smart_update, processHotKeys

__all__ = ('ConfigNoInterface', 'ConfigInterface',)


class ConfigBase(object):
    def __init__(self):
        self.ID = ''
        self.defaultKeys = {}
        self.i18n = {}
        self.data = {}
        self.author = ''
        self.version = VERSION
        self.modsGroup = ''
        self.configPath = ''
        self.langPath = ''

    LOG = property(lambda self: self.ID + ':')
    def loadDataJson(self, *args, **kwargs):
        if self.modsGroup == 'Driftkings':
            from Driftkings.settings.store import load_config
            return load_config(self)
        return loadJson(self.ID, self.ID, self.data, self.configPath, *args, **kwargs)

    def writeDataJson(self, *args, **kwargs):
        if self.modsGroup == 'Driftkings':
            from Driftkings.settings.loader import settings_loader
            return settings_loader.save(self.ID, self.data)
        return loadJson(self.ID, self.ID, self.data, self.configPath, True, False, *args, **kwargs)

    def loadLangJson(self, *args, **kwargs):
        if self.modsGroup == 'Driftkings':
            from Driftkings.i18n import catalog
            return catalog.section(self.ID, self.lang)
        return loadJson(self.ID, self.lang, self.i18n, self.langPath, *args, **kwargs)

    def init(self):
        self.configPath = './mods/configs/%s/%s/' % (self.modsGroup, self.ID)
        self.langPath = './mods/configs/Driftkings/i18n/' if self.modsGroup == 'Driftkings' else '%si18n/' % self.configPath
        self.registerHotkeys()
        if self.modsGroup == 'Driftkings':
            from Driftkings.settings.service import settings_service
            settings_service.register(self)

    def loadLang(self):
        labels = self.loadLangJson()
        self.i18n.clear()
        self.i18n.update(labels)

    def createTB(self):
        return TemplateBuilder(self.data, self.i18n)

    def readConfigDir(self, quiet, recursive=False, dir_name='configs', error_not_exist=True, make_dir=True, ordered=False, encrypted=False, migrate=False, ext='.json'):
        configs_dir = self.configPath + dir_name + '/'
        if not os.path.isdir(configs_dir):
            if error_not_exist and not quiet:
                print('=' * 30)
                print(self.LOG, 'config directory not found:', configs_dir)
                print('=' * 30)
            if make_dir:
                os.makedirs(configs_dir)
        for dir_path, sub_dirs, names in os.walk(configs_dir):
            dir_path = dir_path.replace('\\', '/').decode('windows-1251').encode('utf-8')
            local_path = dir_path.replace(configs_dir, '')
            names = sorted([x for x in names if x.endswith(ext)], key=str.lower)
            if not recursive:
                sub_dirs[:] = []
            for name in names:
                name = os.path.splitext(name)[0].decode('windows-1251').encode('utf-8')
                json_data = {}
                try:
                    if ext == '.json':
                        if ordered:
                            json_data = loadJsonOrdered(self.ID, dir_path, name)
                        else:
                            json_data = loadJson(self.ID, name, json_data, dir_path, encrypted=encrypted)
                    elif ext == '.xml':
                        json_data = ResMgr.openSection('.' + dir_path + '/' + name + ext)
                except Exception:
                    traceback.print_exc()
                if not json_data:
                    print(self.LOG, (dir_path and (dir_path + '/')) + name + ext, 'is invalid')
                    continue
                try:
                    if ext == '.json':
                        if migrate:
                            self.onMigrateConfig(quiet, dir_path, local_path, name, json_data, sub_dirs, names)
                        else:
                            self.onReadConfig(quiet, local_path, name, json_data, sub_dirs, names)
                    elif ext == '.xml':
                        self.onReadDataSection(quiet, dir_path, local_path, name, json_data, sub_dirs, names)
                        ResMgr.purge('.' + dir_path + '/' + name + ext)
                except Exception:
                    traceback.print_exc()

    def onMigrateConfig(self, quiet, path, dir_path, name, json_data, sub_dirs, names):
        """clearing sub_dirs and/or names using slice assignment breaks the corresponding loop"""
        pass

    def onReadConfig(self, quiet, dir_path, name, json_data, sub_dirs, names):
        """clearing sub_dirs and/or names using slice assignment breaks the corresponding loop"""
        pass

    def onReadDataSection(self, quiet, path, dir_path, name, data_section, sub_dirs, names):
        """clearing sub_dirs and/or names using slice assignment breaks the corresponding loop"""
        pass


    def onHotkeyPressed(self, event):
        pass

    def registerHotkeys(self):
        from Driftkings.core.keyboard import keyboard
        keyboard.subscribe(self.onHotkeyPressed)



class ConfigNoInterface(object):
    def createTemplate(self):
        pass


class ConfigInterface(ConfigBase, SettingsLifecycle):
    def __init__(self):
        ConfigBase.__init__(self)
        SettingsLifecycle.__init__(self)

    def getData(self):
        return self.data

    def createTemplate(self):
        raise NotImplementedError

    def readData(self, quiet=True):
        processHotKeys(self.data, self.defaultKeys, 'write')
        try:
            smart_update(self.data, self.loadDataJson(quiet=quiet))
        finally:
            processHotKeys(self.data, self.defaultKeys, 'read')

    def onApplySettings(self, settings):
        smart_update(self.data, settings)
        processHotKeys(self.data, self.defaultKeys, 'write')
        try:
            self.writeDataJson()
        finally:
            processHotKeys(self.data, self.defaultKeys, 'read')
