# -*- coding: utf-8 -*-
"""The framework's own page, declared through the public API like any other mod."""
from Driftkings.settings.panel import locales, logger
from Driftkings.settings.panel.presenter import CORE_ID

_listeners = []


def T(key):
    return locales.translations(key)


def install(api):
    if api.is_registered(CORE_ID):
        return api.mod(CORE_ID)
    from Driftkings.settings.panel import VERSION
    mod = api.register_mod(CORE_ID, name=T('core.name'), version=VERSION, author=u'DriftKingsMods',
                           description=T('core.description'), icon='gear', order=-1000, config_file='dk_settings', category='system')
    languages = [('auto', T('core.language.auto'))] + list(locales.LANGUAGES)
    mod.add_section(T('core.general'))
    mod.add_dropdown('language', T('core.language'), values=languages, default='auto')
    mod.add_hotkey('openKey', T('core.hotkey'), default=[[68]])
    mod.add_section(T('core.appearance'))
    mod.add_color('accent', T('core.accent'), default='#D98219', description=T('core.accent.tip'))
    mod.add_dropdown('theme', T('core.theme'), values=[(key, T('theme.' + key)) for key in ('wot', 'dark', 'black', 'transparent', 'custom')], default='wot')
    from Driftkings.settings.panel.themes import THEMES
    for key in ('background', 'textColor', 'secondary', 'border', 'hover'):
        mod.add_color(key, T('core.' + key), default=THEMES['wot'][key], depends_on={'theme': 'custom'})
    mod.add_slider('opacity', T('core.opacity'), min_value=20, max_value=100, default=96, unit='%')
    mod.add_slider('sidebarOpacity', T('core.sidebarOpacity'), min_value=0, max_value=100, default=35, unit='%')
    mod.add_slider('uiScale', T('core.uiScale'), min_value=80, max_value=140, default=100, step=10, unit='%')
    mod.add_slider('fontSize', T('core.fontSize'), min_value=12, max_value=20, default=15)
    mod.add_slider('sectionFontSize', T('core.sectionFontSize'), min_value=14, max_value=26, default=18)
    mod.add_section(T('core.diagnostics'))
    mod.add_switch('debug', T('core.debug'), default=False, description=T('core.debug.tip'))
    mod.add_section(T('updates.title'))
    mod.add_switch('autoCheckUpdates', T('updates.autoCheck'), default=True)
    mod.add_dropdown('updateChannel', T('updates.channel'),
                     values=[('stable', T('updates.stable')), ('beta', T('updates.beta'))], default='stable')

    tab = None
    for control in mod._mod.controls:
        if control.type == 'section':
            tab = control.label
        control.tab = tab

    def changed(changes):
        if 'debug' in changes:
            logger.set_debug(changes['debug'])
        if 'language' in changes:
            api.set_language(changes['language'])
        for callback in tuple(_listeners):
            try:
                callback(changes)
            except Exception:
                logger.exception('Core settings listener failed')

    mod.on_change(changed)
    logger.set_debug(mod.get('debug'))
    api.set_language(mod.get('language'))
    return mod


def subscribe(callback):
    """Game layer listener for core changes (hangar button visibility/position)."""
    if callback not in _listeners:
        _listeners.append(callback)


def unsubscribe(callback):
    if callback in _listeners:
        _listeners.remove(callback)
