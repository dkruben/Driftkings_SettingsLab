# -*- coding: utf-8 -*-
"""Passive integration observations. Never imports or initializes external mods."""
import logging
import sys

LOG = logging.getLogger('Driftkings.Compatibility')
ABSENT = 'ABSENT'
PRESENT = 'PRESENT'
POSSIBLE_CONFLICT = 'POSSIBLE_CONFLICT'
CONFIRMED_CONFLICT = 'CONFIRMED_CONFLICT'
UNKNOWN = 'UNKNOWN'

MODULES = {
    'XVM': ('xvm_main', 'xvm_battle', 'xvm_battle_minimap'),
    'BattleObserver': ('gui.mods.mod_armagomen_battle_observer', 'armagomen.battle_observer'),
    'ModsListAPI': ('gui.modsListApi',),
    'OpenWGGameface': ('openwg_gameface',),
}
FEATURES = {
    'PlayerPanelPro': ('XVM', 'BattleObserver'),
    'MinimapPlugins': ('XVM', 'BattleObserver'),
    'MarksOnGunBattle': ('XVM', 'BattleObserver'),
}


def read(obj, name, default=None):
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


class CompatibilityManager(object):
    def __init__(self, modules=None):
        self.modules = sys.modules if modules is None else modules
        self._logged = {}

    def module(self, name):
        try:
            return self.modules.get(name)
        except Exception:
            return None

    def status(self, name):
        if name not in MODULES:
            return UNKNOWN
        try:
            available = [self.modules.get(key) for key in MODULES[name]]
            loaded = any(module is not None for module in available)
            state = PRESENT if loaded else UNKNOWN if any(key in self.modules for key in MODULES[name]) else ABSENT
        except Exception:
            state = UNKNOWN
        if state == PRESENT and name == 'ModsListAPI' and read(self.module('gui.modsListApi'), 'g_modsListApi') is None:
            state = UNKNOWN
        if state == PRESENT and name == 'OpenWGGameface':
            module = self.module('openwg_gameface')
            if not callable(read(module, 'gf_mod_inject')) or not callable(read(module, 'res_id_by_key')):
                state = UNKNOWN
        self._log('presence:' + name, state, '%s %s', name, state)
        return state

    def is_installed(self, name):
        # ABSENT means not observed in the loaded runtime, not a disk inventory.
        return self.status(name) == PRESENT

    def _xvm_active(self, feature):
        module_name, path = {
            'PlayerPanelPro': ('xvm_battle', 'playersPanel.enabled'),
            'MinimapPlugins': ('xvm_battle_minimap', 'minimap.enabled'),
        }.get(feature, (None, None))
        if module_name is None:
            return None
        module = self.module(module_name)
        config = self.module('xvm_main.config')
        # Some XVM loaders expose config on the already-loaded package.
        if config is None:
            config = read(self.module('xvm_main'), 'config')
        loaded, getter = read(module, 'owg_module_loaded'), read(config, 'get')
        if not callable(loaded) or not callable(getter):
            return None
        try:
            if loaded() is not True:
                return False
            active = getter(path, None)
            return active if type(active) is bool else None
        except Exception:
            return None

    def conflict_status(self, feature, integration):
        if feature not in FEATURES or integration not in FEATURES[feature]:
            return ABSENT
        state = self.status(integration)
        if state != PRESENT:
            return state
        active = self._xvm_active(feature) if integration == 'XVM' else None
        # Battle Observer imports are evidence of potential overlap only. They
        # do not prove that an instance/settings are active in this battle.
        if active is False:
            return PRESENT
        result = CONFIRMED_CONFLICT if active is True else POSSIBLE_CONFLICT
        self._log('conflict:' + feature + ':' + integration, result,
                  '%s: %s/%s', result, feature, integration)
        return result

    def has_possible_conflict(self, feature):
        return any(self.conflict_status(feature, name) == POSSIBLE_CONFLICT for name in FEATURES.get(feature, ()))

    def has_confirmed_conflict(self, feature):
        return any(self.conflict_status(feature, name) == CONFIRMED_CONFLICT for name in FEATURES.get(feature, ()))

    def warnings_for(self, component):
        warnings = []
        for name in FEATURES.get(component, ()):
            state = self.conflict_status(component, name)
            if state in (POSSIBLE_CONFLICT, CONFIRMED_CONFLICT):
                warnings.append({'code': 'external.' + name + '.' + component,
                                 'level': 'warning', 'integration': name,
                                 'component': component, 'status': state,
                                 'text': '%s: %s may overlap with %s.' % (state, name, component)})
        return warnings

    def _log(self, key, value, message, *args):
        if self._logged.get(key) != value:
            self._logged[key] = value
            LOG.info(message, *args)


compatibility = CompatibilityManager()

is_installed = compatibility.is_installed
status = compatibility.status
has_possible_conflict = compatibility.has_possible_conflict
has_confirmed_conflict = compatibility.has_confirmed_conflict
warnings_for = compatibility.warnings_for
