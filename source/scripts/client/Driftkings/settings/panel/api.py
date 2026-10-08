# -*- coding: utf-8 -*-
"""
Public facade used by mods: `from Driftkings.settings.panel import settings`.
Mods may register before or after the framework starts; configuration files are
read at registration, the interface language is resolved when the game starts it.
"""
from Driftkings.settings.panel import locales, logger
from Driftkings.settings.panel.registry import ModRegistry
from Driftkings.settings.panel.storage import ConfigStore, ConfigReadError

CONFIG_ROOT = './mods/configs/Driftkings/.settings'


def migrate_preferences(destination, previous_root):
    """Copy old preferences/snapshots once, preserving originals and newer files."""
    import os
    import re
    for folder in ('', 'profiles', 'locales'):
        previous = ConfigStore(os.path.join(previous_root, folder))
        target = ConfigStore(os.path.join(destination, folder))
        if not os.path.isdir(previous.root):
            continue
        names = ['dk_settings'] if not folder else [
            name[:-5] for name in os.listdir(previous.root)
            if re.match(r'^[A-Za-z0-9_-]{1,64}\.json$', name)]
        for name in names:
            if os.path.exists(target.path(name)):
                continue
            try:
                document = previous.read(name)
                if document:
                    target.write(name, document)
            except (ConfigReadError, IOError, OSError) as error:
                logger.warning('Could not migrate settings %s/%s: %s', folder, name, error)


class SettingsAPI(object):
    def __init__(self, root=CONFIG_ROOT):
        self.root = root
        self.registry = ModRegistry(ConfigStore(root))
        self.client_language = 'en'
        self.language, self.strings = locales.load('en')
        self.window = None
        self.window_open = False
        self.started = False
        self.in_battle = False
        self.restart_required = set()

    # Mod author API --------------------------------------------------------
    def register_mod(self, mod_id=None, name=None, version=u'', author=u'', description=u'', icon=None, order=None, config_file=None, id=None, category=None, dependencies=None):
        handle = self.registry.register_mod(mod_id, name, version, author, description, icon, order, config_file, id)
        handle._mod.category = category
        handle._mod.dependencies = list(dependencies or [])
        return handle

    def register_sound_mod(self, mod_id, bank, events, loaded=None, volume=None, **metadata):
        from Driftkings.settings.panel.sound import sound_manager
        metadata.setdefault('category', locales.translations('sound.name'))
        metadata.setdefault('icon', 'speaker')
        mod = self.register_mod(mod_id, **metadata)
        try:
            sound_manager.register(mod.id, bank, events, loaded=loaded, volume=volume)
        except Exception:
            self.registry.unregister_mod(mod.id)
            raise
        self.registry._notify_structure()
        return mod

    def mod(self, mod_id):
        return self.registry.mod(mod_id)

    def is_registered(self, mod_id):
        return mod_id in self.registry.mods

    def get(self, mod_id, setting_id, default=None):
        return self.registry.get(mod_id, setting_id, default)

    def __getattr__(self, name):
        # settings.add_switch(mod_id=..., setting_id=..., ...) and the other add_* shortcuts.
        if name.startswith('add_'):
            return getattr(self.registry, name)
        raise AttributeError(name)

    def open(self):
        """Open the integrated window in a supported game context."""
        if self.window is not None:
            return self.window.open()
        return False

    # Framework -------------------------------------------------------------
    def start(self, client_language='en'):
        self.client_language = client_language
        # Preserve existing interface preferences; never touch the old files.
        if self.root == CONFIG_ROOT:
            migrate_preferences(self.root, './mods/configs/DriftKingsMods')
        from Driftkings.settings.panel import core_page
        core_page.install(self)
        self.started = True
        logger.info('Loaded (%d mods)', len(self.registry.mods))

    def set_language(self, preference):
        code = self.client_language if preference in (None, 'auto') else preference
        self.language, self.strings = locales.load(code, self.root)
        self.registry.language = self.language
        self.registry._notify_structure()

    def apply_session(self, session):
        session.save()
        return True

    def save_session(self, session):
        session.save()

    def discard_session(self, session):
        session.discard()
