# -*- coding: utf-8 -*-
import re
import traceback
from math import degrees
from xml.sax.saxutils import escape

import BigWorld
from Avatar import PlayerAvatar
from nations import NAMES

from Driftkings._constants import GLOBAL, INFO_PANEL
from Driftkings.common import getPlayer, getTarget, checkKeys
from Driftkings.core.battle_events import battleEvents
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service, affects
from Driftkings.settings.templates.battle.info_panel import InfoPanelSettings as ConfigInterface
from Driftkings.views.battle.info_panel import Flash

COMPARE_MACROS = ['compareDelim', 'compareColor']
ROMAN_LEVELS = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII')
# Keep the seven preset IDs stable for existing user configurations.
# Reload and DPM are descriptor/base values, not inferred enemy equipment.
def _field(label, value):
    return "<font color='#96A1AB'>%s</font>  <font color='#E6EBEF'>%s</font>" % (label, value)


def _row(*fields):
    return "  <font color='#4A535C'> / </font>  ".join(_field(*field) for field in fields)


def _card(rows, accent='#B9CAD6'):
    header = "<font face='$TitleFont' size='18' color='%s'><b>{{vehicle_name}}</b></font>  <font size='12' color='#96A1AB'>{{vehicle_type}} / {{rlevel}}</font>" % accent
    return "<font face='$FieldFont' size='13'><textformat leading='6'>" + header + '\n' + '\n'.join(rows) + '</textformat></font>'


_FIREPOWER = _row(('Reload (base)', '{{gun_reload}} s'), ('DPM (base)', '{{gun_dpm}}'))
_MOBILITY = _row(('View', '{{vision_radius}} m'), ('Speed', '{{speed_forward}} km/h'), ('HP', '{{vehicle_max_health}}'))
_ARMOR = _row(('Hull', '{{armor_hull_front}} / {{armor_hull_side}} / {{armor_hull_back}}'), ('Turret', '{{armor_turret_front}} / {{armor_turret_side}} / {{armor_turret_back}}'))
_GUN = _row(('Aim', '{{gun_aiming_time}} s'), ('Dispersion', '{{gun_accuracy}}'), ('Clip', '{{gun_clip}}'))
_SHELL = _row(('{{shell_type_1}}', '{{shell_damage_1}} HP'), ('Penetration', '{{shell_power_1}} mm'))
PRESET_TEMPLATES = {
    'default': _card([_FIREPOWER, _MOBILITY, _SHELL]),
    'minimal': _card([_FIREPOWER, _row(('HP', '{{vehicle_max_health}}'), ('View', '{{vision_radius}} m'))]),
    'detailed': _card([_FIREPOWER, _GUN, _MOBILITY, _ARMOR, _SHELL]),
    'full': _card([_FIREPOWER, _GUN, _MOBILITY, _ARMOR, _row(('Power', '{{engine_power_density}} hp/t'), ('Weight', '{{vehicle_weight}} t')), _SHELL, _row(('{{shell_type_2}}', '{{shell_damage_2}} HP'), ('Penetration', '{{shell_power_2}} mm')), _row(('{{shell_type_3}}', '{{shell_damage_3}} HP'), ('Penetration', '{{shell_power_3}} mm'))]),
    'kmp': _card([_FIREPOWER, _SHELL, _row(('View', '{{vision_radius}} m'), ('Weight', "<font color='{{compareColor({{vehicle_weight}}, {{pl_vehicle_weight}})}}'>{{vehicle_weight}} t {{compareDelim({{vehicle_weight}}, {{pl_vehicle_weight}})}} {{pl_vehicle_weight}} t</font>"))]),
    'ndo': _card([_FIREPOWER, _ARMOR, _SHELL, _row(('{{shell_type_2}}', '{{shell_damage_2}} HP'), ('Penetration', '{{shell_power_2}} mm')), _row(('{{shell_type_3}}', '{{shell_damage_3}} HP'), ('Penetration', '{{shell_power_3}} mm'))]),
    'driftkings': _card([_FIREPOWER, _GUN, _MOBILITY, _ARMOR, _SHELL], '#D6BE91')
}
TEMPLATE_INDEX_TO_KEY = {0: 'default', 1: 'minimal', 2: 'detailed', 3: 'full', 4: 'kmp', 5: 'ndo', 6: 'driftkings'}
config = ConfigInterface()
g_flash = Flash()


class DataConstants(object):
    __slots__ = ('_playerVehicle', '_vehicle', '_typeDescriptor', '_gunShots', '_macroHandlers', '_cachedResults',)

    def __init__(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None
        self._cachedResults = {}
        self._macroHandlers = self._buildMacroHandlers()

    def init(self, vehicle, playerVehicle=None):
        if not vehicle and not playerVehicle:
            return
        self._playerVehicle = playerVehicle
        self._vehicle = vehicle
        self._typeDescriptor = vehicle.typeDescriptor if vehicle is not None else self._playerVehicle.typeDescriptor
        self._gunShots = self._typeDescriptor.gun.shots if self._typeDescriptor else None
        self._cachedResults = {}

    def reset(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None
        self._cachedResults = {}

    @staticmethod
    def _get_shell_damage(shell):
        damage = shell.armorDamage if hasattr(shell, 'armorDamage') else shell.damage
        return damage[0]

    def _getPlayerTypeDescriptor(self):
        return self._playerVehicle.typeDescriptor if self._playerVehicle is not None else None

    def _get_gun_dpm_for_descriptor(self, typeDescriptor, cache_key):
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not typeDescriptor:
            return None
        reload_time = typeDescriptor.gun.reloadTime + (typeDescriptor.gun.clip[0] - 1) * typeDescriptor.gun.clip[1]
        if reload_time <= 0 or not typeDescriptor.gun.shots:
            return None
        shell = typeDescriptor.gun.shots[0].shell
        result = '%d' % round(typeDescriptor.gun.clip[0] / reload_time * 60 * self._get_shell_damage(shell), 0)
        self._cachedResults[cache_key] = result
        return result

    def _get_gun_reload_equip_for_descriptor(self, typeDescriptor, cache_key, eq1=1, eq2=1, eq3=1, eq4=1):
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not typeDescriptor:
            return None
        reload_orig = typeDescriptor.gun.reloadTime
        rammer = 0.9 if typeDescriptor.gun.clip[0] == 1 and eq1 == 1 else 1
        if eq2 == 1 and eq3 == 1 and eq4 == 1:
            crew = 1.32
        elif eq2 == 1 and eq3 == 1 and eq4 == 0:
            crew = 1.27
        elif eq2 == 1 and eq3 == 0 and eq4 == 1:
            crew = 1.21
        elif eq2 == 1 and eq3 == 0 and eq4 == 0:
            crew = 1.16
        elif eq2 == 0 and eq3 == 1 and eq4 == 1:
            crew = 1.27
        elif eq2 == 0 and eq3 == 1 and eq4 == 0:
            crew = 1.21
        elif eq2 == 0 and eq3 == 0 and eq4 == 1:
            crew = 1.16
        else:
            crew = 1.1
        result = '%.2f' % round(reload_orig / (0.57 + 0.43 * crew) * rammer, 2)
        self._cachedResults[cache_key] = result
        return result

    def _get_gun_dpm_equip_for_descriptor(self, typeDescriptor, cache_key, eq1=1, eq2=1, eq3=1, eq4=1):
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not typeDescriptor:
            return None
        reload_equip = float(self._get_gun_reload_equip_for_descriptor(typeDescriptor, cache_key + '_reload', eq1, eq2, eq3, eq4))
        reload_time = reload_equip + (typeDescriptor.gun.clip[0] - 1) * typeDescriptor.gun.clip[1]
        if reload_time <= 0 or not typeDescriptor.gun.shots:
            return None
        shell = typeDescriptor.gun.shots[0].shell
        result = '%d' % round(typeDescriptor.gun.clip[0] / reload_time * 60 * self._get_shell_damage(shell), 0)
        self._cachedResults[cache_key] = result
        return result

    @staticmethod
    def l10n(text):
        if text is None:
            return None
        if text in config.i18n:
            text = config.i18n[text]
            if text is None:
                return None
        while True:
            localizedMacroStart = text.find('{{l10n:')
            if localizedMacroStart == -1:
                break
            localizedMacroEnd = text.find('}}', localizedMacroStart)
            if localizedMacroEnd == -1:
                break
            macro = text[localizedMacroStart + 7:localizedMacroEnd]
            parts = macro.split(':')
            macro = config.i18n.get(parts[0], parts[0])
            parts = parts[1:]
            if parts:
                try:
                    macro = macro.format(*parts)
                except StandardError:
                    print('macro:  {}'.format(macro))
                    print('params: {}'.format(parts))
                    traceback.print_exc()
            text = text[:localizedMacroStart] + macro + text[localizedMacroEnd + 2:]
        return config.i18n.get(text, text)

    def _buildMacroHandlers(self):
        handlers = {
            'nick_name': lambda: self._vehicle.publicInfo.name if self._vehicle else None,
            'marks_on_gun': lambda: self._vehicle.publicInfo.marksOnGun if self._vehicle else None,
            'vehicle_type': self._get_vehicle_type,
            'vehicle_name': lambda: self._typeDescriptor.type.userString if self._typeDescriptor else None,
            'vehicle_system_name': lambda: self._typeDescriptor.name if self._typeDescriptor else None,
            'icon_system_name': lambda: self._typeDescriptor.name.replace(':', '-') if self._typeDescriptor else None,
            'gun_name': lambda: self._typeDescriptor.gun.shortUserString if self._typeDescriptor else None,
            'max_ammo': lambda: self._typeDescriptor.gun.maxAmmo if self._typeDescriptor else None,
            'gun_reload': lambda: '%.2f' % self._typeDescriptor.gun.reloadTime if self._typeDescriptor else None,
            'gun_reload_with_crew': lambda: '%.2f' % round(self._typeDescriptor.gun.reloadTime * self._typeDescriptor.miscAttrs.get('gunReloadTimeFactor', 1) / 1.0695 + 0.0043 * self._typeDescriptor.miscAttrs.get('crewLevelIncrease', 0), 1) if self._typeDescriptor else None,
            'gun_dpm': self._get_gun_dpm,
            'gun_reload_equip': self._get_gun_reload_equip,
            'gun_dpm_equip': self._get_gun_dpm_equip,
            'gun_clip': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.gun.clip[0],
            'gun_clip_reload': lambda: None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.clip[1],
            'gun_burst': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.gun.burst[0],
            'gun_burst_reload': lambda: None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.burst[1],
            'gun_aiming_time': lambda: None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.aimingTime,
            'gun_accuracy': lambda: None if not self._typeDescriptor else '%.2f' % round(self._typeDescriptor.gun.shotDispersionAngle * 100, 2),
            'angle_pitch_up': lambda: None if not self._typeDescriptor else '%d' % degrees(-self._typeDescriptor.gun.pitchLimits['absolute'][0]),
            'angle_pitch_down': lambda: None if not self._typeDescriptor else '%d' % degrees(-self._typeDescriptor.gun.pitchLimits['absolute'][1]),
            'angle_pitch_left': lambda: None if not self._typeDescriptor or not self._typeDescriptor.gun.turretYawLimits else '%d' % degrees(-self._typeDescriptor.gun.turretYawLimits[0]),
            'angle_pitch_right': lambda: None if not self._typeDescriptor or not self._typeDescriptor.gun.turretYawLimits else '%d' % degrees(self._typeDescriptor.gun.turretYawLimits[1]),
            'vehicle_max_health': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.maxHealth,
            'armor_hull_front': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.hull.primaryArmor[0],
            'armor_hull_side': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.hull.primaryArmor[1],
            'armor_hull_back': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.hull.primaryArmor[2],
            'turret_name': lambda: None if not self._typeDescriptor else '%s' % self._typeDescriptor.turret.shortUserString,
            'armor_turret_front': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.primaryArmor[0],
            'armor_turret_side': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.primaryArmor[1],
            'armor_turret_back': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.primaryArmor[2],
            'vehicle_weight': lambda: '%.1f' % round(self._typeDescriptor.physics['weight'] / 1000, 1) if self._typeDescriptor else None,
            'chassis_max_weight': lambda: None if not self._typeDescriptor else '%.1f' % round(self._typeDescriptor.chassis.maxLoad / 1000, 1),
            'engine_name': lambda: None if not self._typeDescriptor else '%s' % self._typeDescriptor.engine.shortUserString,
            'engine_power': lambda: None if not self._typeDescriptor else '%d' % round(self._typeDescriptor.engine.power / 735.49875, 0),
            'engine_power_density': self._get_engine_power_density,
            'speed_forward': lambda: None if not self._typeDescriptor else '%d' % (self._typeDescriptor.physics['speedLimits'][0] * 3.6),
            'speed_backward': lambda: None if not self._typeDescriptor else '%d' % (self._typeDescriptor.physics['speedLimits'][1] * 3.6),
            'hull_speed_turn': lambda: None if not self._typeDescriptor else '%.2f' % degrees(self._typeDescriptor.chassis.rotationSpeed),
            'turret_speed_turn': lambda: None if not self._typeDescriptor else '%.2f' % degrees(self._typeDescriptor.turret.rotationSpeed),
            'chassis_rotation_speed': lambda: None if not self._typeDescriptor else '%d' % degrees(self._typeDescriptor.chassis.rotationSpeed),
            'invis_stand': lambda: None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.type.invisibility[1] * 57),
            'invis_stand_shot': lambda: None if not self._typeDescriptor else '%.2f' % (self._typeDescriptor.type.invisibility[1] * self._typeDescriptor.gun.invisibilityFactorAtShot * 57),
            'invis_move': lambda: None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.type.invisibility[0] * 57),
            'invis_move_shot': lambda: None if not self._typeDescriptor else '%.2f' % (self._typeDescriptor.type.invisibility[0] * self._typeDescriptor.gun.invisibilityFactorAtShot * 57),
            'vision_radius': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.circularVisionRadius,
            'radio_name': lambda: None if not self._typeDescriptor else '%s' % self._typeDescriptor.radio.shortUserString,
            'radio_radius': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.radio.distance,
            'nation': lambda: None if not self._typeDescriptor else NAMES[self._typeDescriptor.type.customizationNationID],
            'level': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.type.level,
            'rlevel': self._get_roman_level,
            'pl_vehicle_weight': self._get_pl_vehicle_weight,
            'pl_gun_reload': self._get_pl_gun_reload,
            'pl_gun_reload_equip': self._get_pl_gun_reload_equip,
            'pl_gun_dpm': self._get_pl_gun_dpm,
            'pl_gun_dpm_equip': self._get_pl_gun_dpm_equip,
            'pl_vision_radius': self._get_pl_vision_radius,
            'pl_gun_aiming_time': self._get_pl_gun_aiming_time,
        }
        handlers.update(self._generateShellHandlers())
        handlers.update({'stun_radius': self._get_stun_radius, 'stun_duration_min': self._get_stun_duration_min, 'stun_duration_max': self._get_stun_duration_max, })
        return handlers

    def _generateShellHandlers(self):
        handlers = {}
        handlers.update({
            'shell_name_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%s" % self._gunShots[0].shell.userString,
            'shell_name_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%s" % self._gunShots[1].shell.userString,
            'shell_name_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%s" % self._gunShots[2].shell.userString,
            'shell_damage_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % self._get_shell_damage(self._gunShots[0].shell),
            'shell_damage_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % self._get_shell_damage(self._gunShots[1].shell),
            'shell_damage_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % self._get_shell_damage(self._gunShots[2].shell),
            'shell_power_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % (self._gunShots[0].piercingPower[0]),
            'shell_power_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % (self._gunShots[1].piercingPower[0]),
            'shell_power_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % (self._gunShots[2].piercingPower[0]),
            'shell_type_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else self.l10n(self._gunShots[0].shell.kind.lower()),
            'shell_type_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else self.l10n(self._gunShots[1].shell.kind.lower()),
            'shell_type_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else self.l10n(self._gunShots[2].shell.kind.lower()),
            'shell_speed_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % round(self._gunShots[0].speed * 1.25),
            'shell_speed_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % round(self._gunShots[1].speed * 1.25),
            'shell_speed_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % round(self._gunShots[2].speed * 1.25),
            'shell_distance_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % self._gunShots[0].maxDistance,
            'shell_distance_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % self._gunShots[1].maxDistance,
            'shell_distance_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % self._gunShots[2].maxDistance
        })
        return handlers

    def _get_vehicle_type(self):
        if 'vehicle_type' in self._cachedResults:
            return self._cachedResults['vehicle_type']
        if self._typeDescriptor:
            tags = self._typeDescriptor.type.tags
            result = None
            if 'lightTank' in tags:
                result = 'LT'
            elif 'mediumTank' in tags:
                result = 'MT'
            elif 'heavyTank' in tags:
                result = 'HT'
            elif 'AT-SPG' in tags:
                result = 'TD'
            elif 'SPG' in tags:
                result = 'SPG'
            self._cachedResults['vehicle_type'] = result
            return result
        return None

    def _get_gun_dpm(self):
        return self._get_gun_dpm_for_descriptor(self._typeDescriptor, 'gun_dpm')

    def _get_gun_reload_equip(self, eq1=1, eq2=1, eq3=1, eq4=1):
        cache_key = 'gun_reload_equip_%s_%s_%s_%s' % (eq1, eq2, eq3, eq4)
        return self._get_gun_reload_equip_for_descriptor(self._typeDescriptor, cache_key, eq1, eq2, eq3, eq4)

    def _get_gun_dpm_equip(self, eq1=1, eq2=1, eq3=1, eq4=1):
        cache_key = 'gun_dpm_equip_%s_%s_%s_%s' % (eq1, eq2, eq3, eq4)
        return self._get_gun_dpm_equip_for_descriptor(self._typeDescriptor, cache_key, eq1, eq2, eq3, eq4)

    def _get_engine_power_density(self):
        if 'engine_power_density' in self._cachedResults:
            return self._cachedResults['engine_power_density']
        if not self._typeDescriptor:
            return None
        power = self._typeDescriptor.engine.power / 735.49875
        weight = self._typeDescriptor.physics['weight'] / 1000.0
        if weight <= 0:
            return None
        result = '%.2f' % round(power / weight, 2)
        self._cachedResults['engine_power_density'] = result
        return result

    def _get_roman_level(self):
        if 'roman_level' in self._cachedResults:
            return self._cachedResults['roman_level']
        if not self._typeDescriptor:
            return None
        level_idx = self._typeDescriptor.type.level - 1
        if 0 <= level_idx < len(ROMAN_LEVELS):
            result = ROMAN_LEVELS[level_idx]
            self._cachedResults['roman_level'] = result
            return result
        return None

    def _get_stun_radius(self):
        if 'stun_radius' in self._cachedResults:
            return self._cachedResults['stun_radius']
        if self._gunShots is not None and len(self._gunShots) > 0 and hasattr(self._gunShots[0].shell, 'stun') and self._gunShots[0].shell.stun is not None:
            result = '%d' % self._gunShots[0].shell.stun.stunRadius
            self._cachedResults['stun_radius'] = result
            return result
        return None

    def _get_stun_duration_min(self):
        if 'stun_duration_min' in self._cachedResults:
            return self._cachedResults['stun_duration_min']
        if self._gunShots is not None and len(self._gunShots) > 0 and hasattr(self._gunShots[0].shell, 'stun') and self._gunShots[0].shell.stun is not None:
            time = round(self._gunShots[0].shell.stun.stunDuration * self._gunShots[0].shell.stun.guaranteedStunDuration, 1)
            result = '%.1f' % time
            self._cachedResults['stun_duration_min'] = result
            return result
        return None

    def _get_stun_duration_max(self):
        if 'stun_duration_max' in self._cachedResults:
            return self._cachedResults['stun_duration_max']
        if self._gunShots is not None and len(self._gunShots) > 0 and hasattr(self._gunShots[0].shell, 'stun') and self._gunShots[0].shell.stun is not None:
            result = '%d' % self._gunShots[0].shell.stun.stunDuration
            self._cachedResults['stun_duration_max'] = result
            return result
        return None

    def _get_pl_vehicle_weight(self):
        typeDescriptor = self._getPlayerTypeDescriptor()
        if not typeDescriptor:
            return None
        return '%.1f' % round(typeDescriptor.physics['weight'] / 1000, 1)

    def _get_pl_gun_reload(self):
        typeDescriptor = self._getPlayerTypeDescriptor()
        if not typeDescriptor:
            return None
        return '%.2f' % typeDescriptor.gun.reloadTime

    def _get_pl_gun_reload_equip(self):
        return self._get_gun_reload_equip_for_descriptor(self._getPlayerTypeDescriptor(), 'pl_gun_reload_equip')

    def _get_pl_gun_dpm(self):
        return self._get_gun_dpm_for_descriptor(self._getPlayerTypeDescriptor(), 'pl_gun_dpm')

    def _get_pl_gun_dpm_equip(self):
        return self._get_gun_dpm_equip_for_descriptor(self._getPlayerTypeDescriptor(), 'pl_gun_dpm_equip')

    def _get_pl_vision_radius(self):
        typeDescriptor = self._getPlayerTypeDescriptor()
        if not typeDescriptor:
            return None
        return '%d' % typeDescriptor.turret.circularVisionRadius

    def _get_pl_gun_aiming_time(self):
        typeDescriptor = self._getPlayerTypeDescriptor()
        if not typeDescriptor:
            return None
        return '%.1f' % typeDescriptor.gun.aimingTime

    def __getattr__(self, name):
        if name in self._macroHandlers:
            return self._macroHandlers[name]
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))


class CompareMacros(object):
    __slots__ = ('value1', 'value2')

    def __init__(self):
        self.value1 = None
        self.value2 = None

    def reset(self):
        self.value1 = None
        self.value2 = None

    def setData(self, value1, value2):
        self.value1 = float(value1)
        self.value2 = float(value2)

    @property
    def compareDelim(self):
        return self._getCompareAttribute('delim')

    @property
    def compareColor(self):
        return self._getCompareAttribute('color')

    def _getCompareAttribute(self, attribute):
        if self.value1 is None or self.value2 is None:
            raise ValueError('Values must be defined before comparison.')
        if self.value1 > self.value2:
            return settings_service.getComponentDict(config)[INFO_PANEL.COMPARE_VALUES]['moreThan'][attribute]
        elif self.value1 == self.value2:
            return settings_service.getComponentDict(config)[INFO_PANEL.COMPARE_VALUES]['equal'][attribute]
        else:
            return settings_service.getComponentDict(config)[INFO_PANEL.COMPARE_VALUES]['lessThan'][attribute]


class InfoPanel(DataConstants):
    def __init__(self):
        self._active = False
        self._inBattle = False
        self.textFormats = self.getText() if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else None
        self.hotKeyDown = False
        self.visible = False
        self.timer = None
        DataConstants.__init__(self)

    def reset(self):
        self.cancelHide()
        DataConstants.reset(self)
        self.textFormats = self.getText() if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else None
        self.hotKeyDown = False
        self.visible = False
        self.timer = None

    def start(self):
        if self._active:
            return
        self._active = True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, INFO_PANEL)
        battleEvents.started.connect(self.onBattleStarted)
        battleEvents.ended.connect(self.onBattleEnded)
        battleEvents.key.connect(self.onBattleKey)
        battleEvents.acquire(self)

    def stop(self):
        if not self._active:
            return
        self._active = False
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        battleEvents.started.disconnect(self.onBattleStarted)
        battleEvents.ended.disconnect(self.onBattleEnded)
        battleEvents.key.disconnect(self.onBattleKey)
        try:
            self.onBattleEnded()
        finally:
            battleEvents.release(self)

    def onSettingsChanged(self, component, changes):
        if not affects(changes, GLOBAL.ENABLED, INFO_PANEL.TEMPLATE_PRESET,
                       INFO_PANEL.FORMATS, INFO_PANEL.COMPARE_VALUES):
            return
        enabled = settings_service.getSetting(config, GLOBAL.ENABLED)
        self.textFormats = self.getText() if enabled else None
        if not enabled:
            self.hide()
            self.hotKeyDown = False
        elif self._inBattle and self.visible:
            g_flash.addText(self.setTextsFormatted())

    def onBattleStarted(self):
        if self._inBattle:
            return
        self._inBattle = True
        g_flash.startBattle()

    def onBattleEnded(self):
        self._inBattle = False
        try:
            self.reset()
        finally:
            g_flash.stopBattle()

    def onBattleKey(self, event):
        if self._inBattle:
            self.keyPressed(event)

    @staticmethod
    def getText():
        template_index = settings_service.getComponentDict(config)[INFO_PANEL.TEMPLATE_PRESET]
        # The full preset is editable in JSON; retain the existing preset IDs.
        if template_index == 3 and settings_service.getComponentDict(config).get(INFO_PANEL.FORMATS):
            return u'\n'.join(value if isinstance(value,type(u'')) else value.decode('utf-8')
                              for value in settings_service.getComponentDict(config)[INFO_PANEL.FORMATS])
        template_key = TEMPLATE_INDEX_TO_KEY.get(template_index, 'default')
        return PRESET_TEMPLATES.get(template_key, PRESET_TEMPLATES['default'])

    @staticmethod
    def isConditions(entity):
        player = getPlayer()
        if player is None or entity is None or not hasattr(entity, 'publicInfo'):
            return False
        playerTeam = player.team
        team = getattr(entity.publicInfo, 'team', 0)
        isAlly = team > 0 and team == playerTeam
        if settings_service.getComponentDict(config)[INFO_PANEL.SHOW_FOR] == 0:
            showFor = True
        elif settings_service.getComponentDict(config)[INFO_PANEL.SHOW_FOR] == 1:
            showFor = isAlly
        elif settings_service.getComponentDict(config)[INFO_PANEL.SHOW_FOR] == 2:
            showFor = not isAlly
        else:
            showFor = False
        isAlive = entity.isAlive() if settings_service.getComponentDict(config)[INFO_PANEL.ALIVE_ONLY] else True
        return showFor and isAlive

    def getFuncResponse(self, funcName):
        if not hasattr(self, funcName):
            return ''
        func = getattr(self, funcName, None)
        if callable(func):
            result = func()
            if result is not None:
                value = result if isinstance(result,type(u'')) else result.decode('utf-8', 'replace') if isinstance(result,str) else type(u'')(result)
                return escape(value, {chr(34): '&quot;', chr(39): '&apos;'})
            return ''
        return ''

    def setTextsFormatted(self):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return ''
        textFormat = self.textFormats or self.getText()
        textFormat = self.replaceMacros(textFormat, self._macroHandlers.keys())
        textFormat = self.replaceCompareMacros(textFormat, COMPARE_MACROS)
        return textFormat

    def replaceMacros(self, textFormat, macros):
        for macro in macros:
            macroPattern = '{{' + macro + '}}'
            if macroPattern in textFormat:
                funcName = macro
                funcResponse = self.getFuncResponse(funcName)
                textFormat = textFormat.replace(macroPattern, funcResponse)
        return textFormat

    @staticmethod
    def replaceCompareMacros(textFormat, compareMacros):
        def replace(match):
            args = match.group(2).split(',')
            if len(args) != 2:
                return ''
            try:
                g_comparator.setData(args[0].strip(), args[1].strip())
                return getattr(g_comparator, match.group(1))
            except (TypeError, ValueError):
                return ''
        pattern = r'\{\{(' + '|'.join(re.escape(name) for name in compareMacros) + r')\(([^{}]*)\)\}\}'
        return re.sub(pattern, replace, textFormat)

    def keyPressed(self, event):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        player = getPlayer()
        if not hasattr(player, 'getVehicleAttached'):
            return
        if checkKeys(settings_service.getComponentDict(config)[INFO_PANEL.ALT_KEY]) and event.isKeyDown():
            self.hotKeyDown = True
            self.onUpdateVehicle(player.getVehicleAttached(), ignoreHotKey=True)
        elif self.hotKeyDown and event.isKeyUp() and not checkKeys(settings_service.getComponentDict(config)[INFO_PANEL.ALT_KEY]):
            self.hotKeyDown = False
            target = getTarget()
            if self.isConditions(target):
                self.onUpdateVehicle(target)
            else:
                self.hide()

    def cancelHide(self):
        if self.timer is not None:
            BigWorld.cancelCallback(self.timer)
            self.timer = None

    def onHideTimeout(self):
        # This callback has already fired: do not cancel its consumed ID.
        self.timer = None
        self.hide()

    def hide(self):
        self.cancelHide()
        self.visible = False
        g_flash.setVisible(False)

    def onUpdateBlur(self):
        if not self._inBattle or not self.visible or self.hotKeyDown or self.timer is not None:
            return
        delay=max(0.0,float(settings_service.getComponentDict(config)[INFO_PANEL.DELAY]))
        if delay == 0:
            self.hide()
        else:
            self.timer = BigWorld.callback(delay, self.onHideTimeout)

    def onUpdateVehicle(self, vehicle, ignoreHotKey=False):
        player = getPlayer()
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED] or not g_flash.active or not hasattr(player, 'getVehicleAttached'):
            return
        if self.hotKeyDown and not ignoreHotKey:
            return
        playerVehicle = player.getVehicleAttached()
        if playerVehicle is not None and g_flash:
            self.cancelHide()
            self.visible = True
            g_flash.setVisible(True)
            if hasattr(vehicle, 'typeDescriptor'):
                self.init(vehicle, playerVehicle)
            elif hasattr(playerVehicle, 'typeDescriptor'):
                self.init(None, playerVehicle)
            g_flash.addText(self.setTextsFormatted())


g_comparator = CompareMacros()
g_mod = InfoPanel()


@override(PlayerAvatar, 'targetBlur')
def new__targetBlur(func, self, prevEntity):
    result = func(self, prevEntity)
    # A dead/removed/filtered target must still release an already shown panel.
    if g_mod._inBattle:
        g_mod.onUpdateBlur()
    return result


@override(PlayerAvatar, 'targetFocus')
def new__targetFocus(func, self, entity):
    result = func(self, entity)
    if g_mod._inBattle and settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        if g_mod.isConditions(entity):
            g_mod.onUpdateVehicle(entity)
        else:
            g_mod.onUpdateBlur()
    return result


def init():
    g_mod.start()


def fini():
    g_mod.stop()
