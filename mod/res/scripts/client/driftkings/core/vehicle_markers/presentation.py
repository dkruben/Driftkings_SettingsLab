# -*- coding: utf-8 -*-
"""Map standalone JSON options onto WoT 2.4.1 native marker settings."""
import copy

from driftkings.core.vehicle_markers.hooks import Hooks
from driftkings.common.utils.compat import string_types

HP_MODES = {'percent': 0, 'currentAndMax': 1, 'current': 2, 'hidden': 3}
FIELDS = {'vehicleName': 'VehicleName', 'playerName': 'PlayerName',
          'healthBar': 'HpIndicator', 'damage': 'Damage', 'vehicleIcon': 'Icon', 'levelIcon': 'Level'}


def validate(options):
    if not isinstance(options, dict) or type(options.get('enabled')) is not bool:
        raise ValueError('markers.enabled must be boolean')
    allowed = set(('enabled', 'ally', 'enemy', 'dead'))
    if set(options) - allowed:
        raise ValueError('Unknown markers group')
    for group in ('ally', 'enemy', 'dead'):
        modes = options.get(group, {})
        if not isinstance(modes, dict) or set(modes) - set(('normal', 'extended')):
            raise ValueError('Invalid marker modes: ' + group)
        for mode, fields in modes.items():
            if not isinstance(fields, dict) or set(fields) - (set(FIELDS) | set(('hp',))):
                raise ValueError('Invalid marker fields: ' + group + '.' + mode)
            for key, value in fields.items():
                if key == 'hp':
                    if not isinstance(value, string_types) or value not in HP_MODES:
                        raise ValueError('Invalid hp mode')
                elif type(value) is not bool:
                    raise ValueError('Marker visibility must be boolean: ' + key)


def apply(settings, options, custom_fields=None):
    """Copy first; never mutate the account settings dictionary."""
    result = copy.deepcopy(settings)
    if custom_fields is not None and custom_fields.get('profiles') is not None:
        result['__vmTest'] = copy.deepcopy(custom_fields)
        return result
    for group in ('ally', 'enemy', 'dead'):
        if group not in result:
            continue
        for mode, fields in options.get(group, {}).items():
            prefix = 'markerBase' if mode == 'normal' else 'markerAlt'
            for key, value in fields.items():
                suffix = 'Hp' if key == 'hp' else FIELDS[key]
                result[group][prefix + suffix] = HP_MODES[value] if key == 'hp' else value
    if custom_fields is not None:
        result['__vmTest'] = copy.deepcopy(custom_fields)
        if custom_fields.get('enabled'):
            for group in ('ally', 'enemy', 'dead'):
                if group not in result:
                    continue
                for mode in custom_fields.get(group, {}):
                    prefix = 'markerBase' if mode == 'normal' else 'markerAlt'
                    result[group][prefix + 'Hp'] = HP_MODES['hidden']
                    result[group][prefix + 'VehicleName'] = False
                    result[group][prefix + 'PlayerName'] = False
    if custom_fields is not None and custom_fields.get('healthBar', {}).get('enabled'):
        for group in ('ally', 'enemy', 'dead'):
            if group in result:
                result[group]['markerBaseHpIndicator'] = False
                result[group]['markerAltHpIndicator'] = False
    icons = custom_fields.get('icons', {}) if custom_fields is not None else {}
    if icons.get('enabled') and not icons.get('vehicle', {}).get('enabled', True):
        for group in ('ally', 'enemy', 'dead'):
            if group in result:
                result[group]['markerBaseIcon'] = False
                result[group]['markerAltIcon'] = False
    return result


class Presentation(object):
    def __init__(self, logger, options, fields=None, supported=None):
        self.logger = logger
        self.options = options
        self.fields = fields
        self.supported = supported
        self.skipped = set()
        self.hooks = Hooks(logger)
        self.active = False
        self.reported = False

    def install(self, manager):
        if self.active:
            return
        self.active = True
        try:
            self.hooks.around(manager, 'setMarkerSettings', self.configure)
        except Exception:
            self.close()
            raise

    def configure(self, original, manager, settings, *args, **kwargs):
        if not self.active:
            return original(manager, settings, *args, **kwargs)
        allowed = type(manager).__name__ != 'KillCamMarkersManager'
        if self.supported is not None:
            try:
                allowed = allowed and self.supported(manager)
            except Exception:
                allowed = False
                self.logger.exception('[Driftkings.VehicleMarkers] Cannot identify battle mode; keeping native settings')
        if not allowed:
            configured = copy.deepcopy(settings)
            if isinstance(configured, dict):
                # Explicitly clear our Flash payload if a movie/domain is reused.
                configured['__vmTest'] = None
            if type(manager).__name__ not in self.skipped:
                self.skipped.add(type(manager).__name__)
                self.logger.info('[Driftkings.VehicleMarkers] Native presentation retained for unsupported battle/manager: %s', type(manager).__name__)
            return original(manager, configured, *args, **kwargs)
        try:
            configured = apply(settings, self.options, self.fields)
        except Exception:
            self.logger.exception('[Driftkings.VehicleMarkers] Invalid native marker data; retaining original settings')
            configured = settings
        result = original(manager, configured, *args, **kwargs)
        if not self.reported:
            self.reported = True
            self.logger.info('[Driftkings.VehicleMarkers] JSON presentation applied to native markers (normal/Alt)')
        return result

    def close(self):
        self.active = False
        restored, retained = self.hooks.clear()
        self.logger.info('[Driftkings.VehicleMarkers] Presentation closed: hooks restored=%s; retained in other mod chains=%s', restored, retained)
