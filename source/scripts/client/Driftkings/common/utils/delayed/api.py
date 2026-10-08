# -*- coding: utf-8 -*-
"""Registration of existing templates in the owned registry."""
__all__ = ('registerSettings',)

def registerSettings(config):
    from helpers import getClientLanguage
    from Driftkings.settings.registry import registry
    config.lang = str(getClientLanguage()).lower()
    config.loadLang()
    registry.register(config)
