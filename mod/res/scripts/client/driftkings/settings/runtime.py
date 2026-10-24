# -*- coding: utf-8 -*-
"""Validate the selected profile before importing feature consumers."""
class SettingsRuntime(object):
    def start(self):
        from driftkings.settings.loader import settings_loader
        settings_loader.directory(settings_loader.active)

    def stop(self):
        pass

    def disableOwner(self, owner):
        from driftkings.settings.service import settings_service
        from driftkings.settings.registry import registry
        for name, section in list(settings_service.settings.configs.items()):
            if getattr(section, 'runtime_owner', None) != owner:
                continue
            registry.entries.pop(name, None)
            settings_service.settings.configs.pop(name, None)
            handler = settings_service._handlers.pop(name, None)
            if handler is not None:
                settings_service.onModSettingsChanged.disconnect(handler)
