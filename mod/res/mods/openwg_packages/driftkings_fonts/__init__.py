# -*- coding: utf-8 -*-
"""Register packaged fonts after OpenWG's native font provider is ready.

Registration and aliases follow xvm_fonts (XVM Contributors, GPL-3.0-or-later).
The font resources and their original names and credits are preserved.
"""
import openwg_fonts

FONTS = (u'DynamicDefault', u'DynamicOutline', u'VehicleType', u'DriftkingsFont', u'ZurichCondMono')
ALIASES = ((u'dkm', u'DriftkingsFont'), (u'dynamic', u'DynamicDefault'), (u'dynamic2', u'DynamicOutline'),
           (u'vtype', u'VehicleType'), (u'xvm', u'DriftkingsFont'),
           (u'XVMSymbol', u'DriftkingsFont'), (u'mono', u'ZurichCondMono'))
_initialized = False


def owg_module_init():
    global _initialized
    if _initialized:
        return
    # Paths are relative to the resource VFS, not to the working directory.
    # OpenWG extracts archived TTFs to its cache before registering them.
    for name in FONTS:
        openwg_fonts.register_font(u'gui/fonts/driftkings/' + name + u'.ttf')
    for alias, name in ALIASES:
        openwg_fonts.add_alias(alias, name)
    _initialized = True


def owg_module_fini():
    global _initialized
    # The provider owns process-wide fonts; do not remove aliases used by other mods.
    _initialized = False


def owg_module_loaded():
    return _initialized


def owg_module_event(event_name, *args, **kwargs):
    pass
