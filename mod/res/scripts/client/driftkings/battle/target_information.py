# -*- coding: utf-8 -*-
from math import degrees
import re
from xml.sax.saxutils import escape

import BigWorld
from gui.shared.gui_items.Vehicle import getContourIconPath, getIconPath
from nations import NAMES

from driftkings._constants import GLOBAL, ROMAN_NUMERALS, TARGET_INFORMATION
from driftkings.common.utils.game import checkKeys
from driftkings.core.battle_capabilities import battle_capabilities
from driftkings.core.battle_events import battleEvents
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.core.gun_stats import damage_per_minute, reload_with_equipment
from driftkings.core.vehicle_images import resolve_vehicle_images
from driftkings.gameface.battle.screen_texts import TargetInformationAdapter
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.target_information import TargetInformationSettings
from driftkings.settings.service import affects, settings_service

COMPARE_MACROS = ['compareDelim', 'compareColor']
ROMAN_LEVELS = ROMAN_NUMERALS
# Keep the preset IDs stable for existing user configurations; new presets go at the end.
# Reload and DPM are descriptor/base values, not inferred enemy equipment.
def _label(key):
    return '{{i18n:card_' + key + '}}'


def _field(label, value):
    return "<font color='#96A1AB'>%s</font>  <font color='#E6EBEF'>%s</font>" % (label, value)


def _row(*fields):
    return "  <font color='#4A535C'> / </font>  ".join(_field(*field) for field in fields)


def _card(rows, accent='#B9CAD6'):
    header = "<font face='$TitleFont' size='18' color='%s'><b>{{vehicle_name}}</b></font>  <font size='12' color='#96A1AB'>{{vehicle_type}} / {{rlevel}}</font>" % accent
    return "<font face='$FieldFont' size='13'><textformat leading='6'>" + header + '\n' + '\n'.join(rows) + '</textformat></font>'


_FIREPOWER = _row((_label('reload'), '{{gun_reload}} s'), (_label('dpm'), '{{gun_dpm}}'))
_MOBILITY = _row((_label('view'), '{{vision_radius}} m'), (_label('speed'), '{{speed_forward}} km/h'),
                 (_label('hp'), '{{vehicle_max_health}}'))
_ARMOR = _row((_label('hull'), '{{armor_hull_front}} / {{armor_hull_side}} / {{armor_hull_back}}'),
              (_label('turret'), '{{armor_turret_front}} / {{armor_turret_side}} / {{armor_turret_back}}'))
_GUN = _row((_label('aim'), '{{gun_aiming_time}} s'), (_label('dispersion'), '{{gun_accuracy}}'),
            (_label('clip'), '{{gun_clip}}'))
def _table(label, *macros):
    return "<textformat tabstops='[85,125,165]'>" + _label(label) + ':' + ''.join('<tab>{{%s}}' % macro for macro in macros) + '</textformat>'


_SHELL = _row(('{{shell_type_1}}', '{{shell_damage_1}} HP'), (_label('penetration'), '{{shell_power_1}} mm'))
PRESET_TEMPLATES = {
    'default': _card([_FIREPOWER, _MOBILITY, _SHELL]),
    'minimal': _card([_FIREPOWER,
                      _row((_label('hp'), '{{vehicle_max_health}}'), (_label('view'), '{{vision_radius}} m'))]),
    'detailed': _card([_FIREPOWER, _GUN, _MOBILITY, _ARMOR, _SHELL]),
    'full': _card([_FIREPOWER, _GUN, _MOBILITY, _ARMOR,
                   _row((_label('power'), '{{engine_power_density}} hp/t'),
                        (_label('weight'), '{{vehicle_weight}} t')), _SHELL,
                   _row(('{{shell_type_2}}', '{{shell_damage_2}} HP'),
                        (_label('penetration'), '{{shell_power_2}} mm')),
                   _row(('{{shell_type_3}}', '{{shell_damage_3}} HP'),
                        (_label('penetration'), '{{shell_power_3}} mm'))]),
    'kmp': _card([_FIREPOWER, _SHELL,
                  _row((_label('view'), '{{vision_radius}} m'),
                       (_label('weight'),
                        "<font color='{{compareColor({{vehicle_weight}}, {{pl_vehicle_weight}})}}'>{{vehicle_weight}} t {{compareDelim({{vehicle_weight}}, {{pl_vehicle_weight}})}} {{pl_vehicle_weight}} t</font>"))]),
    'ndo': _card([_FIREPOWER, _ARMOR, _SHELL,
                  _row(('{{shell_type_2}}', '{{shell_damage_2}} HP'), (_label('penetration'), '{{shell_power_2}} mm')),
                  _row(('{{shell_type_3}}', '{{shell_damage_3}} HP'),
                       (_label('penetration'), '{{shell_power_3}} mm'))]),
    'driftkings': _card([_FIREPOWER, _GUN, _MOBILITY, _ARMOR, _SHELL], '#D6BE91'),
    # The card formerly shipped as a custom default: picture, reload with equipment and tab-aligned tables.
    'classic': '<br/>'.join([
        '{{vehicle_name}}', '{{gun_reload_equip}} s', "<img src='img://gui/maps/icons/vehicle/{{icon_system_name}}.png'>",
        "<textformat tabstops='[95]'>" + _label('weight') + ': {{vehicle_weight}} t<tab>' + _label('view') +
        ': {{vision_radius}} m</textformat>'] + [_table(*table) for table in (
            ('hull', 'armor_hull_front', 'armor_hull_side', 'armor_hull_back'),
            ('turret', 'armor_turret_front', 'armor_turret_side', 'armor_turret_back'),
            ('type', 'shell_type_1', 'shell_type_2', 'shell_type_3'),
            ('penetration', 'shell_power_1', 'shell_power_2', 'shell_power_3'),
            ('damage', 'shell_damage_1', 'shell_damage_2', 'shell_damage_3'))])
}
TEMPLATE_INDEX_TO_KEY = {0: 'default', 1: 'minimal', 2: 'detailed', 3: 'full', 4: 'kmp', 5: 'ndo', 6: 'driftkings',
                         7: 'classic'}
CLASSIC_PRESET = 7
LOG = get_logger('Driftkings.TargetInformation')
target_information_settings = TargetInformationSettings()
g_gameface = TargetInformationAdapter()
g_flash = None
g_panel = g_gameface


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

    # Calcula e guarda o dano por minuto da arma do descritor indicado.
    def _get_gun_dpm_for_descriptor(self, typeDescriptor, cache_key):
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not typeDescriptor or not typeDescriptor.gun.shots:
            return None
        gun = typeDescriptor.gun
        dpm = damage_per_minute(gun.reloadTime, gun.clip[0], gun.clip[1], self._get_shell_damage(gun.shots[0].shell))
        if dpm is None:
            return None
        result = '%d' % dpm
        self._cachedResults[cache_key] = result
        return result

    def _get_gun_reload_equip_for_descriptor(self, typeDescriptor, cache_key):
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not typeDescriptor:
            return None
        gun = typeDescriptor.gun
        result = '%.2f' % reload_with_equipment(gun.reloadTime, gun.clip[0])
        self._cachedResults[cache_key] = result
        return result

    def _get_gun_dpm_equip_for_descriptor(self, typeDescriptor, cache_key):
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not typeDescriptor or not typeDescriptor.gun.shots:
            return None
        gun = typeDescriptor.gun
        reload_equip = reload_with_equipment(gun.reloadTime, gun.clip[0])
        dpm = damage_per_minute(reload_equip, gun.clip[0], gun.clip[1], self._get_shell_damage(gun.shots[0].shell))
        if dpm is None:
            return None
        result = '%d' % dpm
        self._cachedResults[cache_key] = result
        return result

    @staticmethod
    def i18n(text):
        if text is None:
            return None
        if text in target_information_settings.i18n:
            text = target_information_settings.i18n[text]
            if text is None:
                return None
        text = DataConstants.expandI18n(text)
        return target_information_settings.i18n.get(text, text)

    @staticmethod
    def expandI18n(text):
        position = 0
        while True:
            # {{i18n:KEY}}; legacy {{l10n:KEY}} is read the same way.
            starts = [start for start in (text.find('{{i18n:', position), text.find('{{l10n:', position))
                      if start != -1]
            localizedMacroStart = min(starts) if starts else -1
            if localizedMacroStart == -1:
                break
            localizedMacroEnd = text.find('}}', localizedMacroStart)
            if localizedMacroEnd == -1:
                break
            macro = text[localizedMacroStart + 7:localizedMacroEnd]
            parts = macro.split(':')
            macro = target_information_settings.i18n.get(parts[0]) or parts[0]
            parts = parts[1:]
            if parts:
                try:
                    macro = macro.format(*parts)
                except StandardError:
                    LOG.exception('Could not format macro %r with params %r', macro, parts)
            text = text[:localizedMacroStart] + macro + text[localizedMacroEnd + 2:]
            # Translated text is final: never expand macros inside it again.
            position = localizedMacroStart + len(macro)
        return text

    def _target(self, read):
        """Macro handler reading the target's descriptor; None without a target."""
        return lambda: read(self._typeDescriptor) if self._typeDescriptor else None

    def _player(self, read):
        """Macro handler reading the player's own descriptor; None without one."""
        def handler():
            typeDescriptor = self._getPlayerTypeDescriptor()
            return read(typeDescriptor) if typeDescriptor else None
        return handler

    def _shell(self, index, read):
        """Macro handler reading the target gun's shot at index; None when the gun has fewer shots."""
        def handler():
            shots = self._gunShots
            return read(shots[index]) if shots and len(shots) > index else None
        return handler

    def _stun(self, key, read):
        """Cached macro handler reading the first shell's stun; None for shells without stun."""
        def handler():
            if key in self._cachedResults:
                return self._cachedResults[key]
            shots = self._gunShots
            stun = getattr(shots[0].shell, 'stun', None) if shots else None
            if stun is None:
                return None
            result = self._cachedResults[key] = read(stun)
            return result
        return handler

    def _buildMacroHandlers(self):
        target, player = self._target, self._player
        handlers = {
            'nick_name': lambda: self._vehicle.publicInfo.name if self._vehicle else None,
            'marks_on_gun': lambda: self._vehicle.publicInfo.marksOnGun if self._vehicle else None,
            'vehicle_type': self._get_vehicle_type,
            'vehicle_name': target(lambda d: d.type.userString),
            'vehicle_system_name': target(lambda d: d.name),
            'icon_system_name': target(lambda d: d.name.replace(':', '-')),
            'gun_name': target(lambda d: d.gun.shortUserString),
            'max_ammo': target(lambda d: d.gun.maxAmmo),
            'gun_reload': target(lambda d: '%.2f' % d.gun.reloadTime),
            'gun_reload_with_crew': target(lambda d: '%.2f' % round(
                d.gun.reloadTime * d.miscAttrs.get('gunReloadTimeFactor', 1) / 1.0695
                + 0.0043 * d.miscAttrs.get('crewLevelIncrease', 0), 1)),
            'gun_dpm': self._get_gun_dpm,
            'gun_reload_equip': self._get_gun_reload_equip,
            'gun_dpm_equip': self._get_gun_dpm_equip,
            'gun_clip': target(lambda d: '%d' % d.gun.clip[0]),
            'gun_clip_reload': target(lambda d: '%.1f' % d.gun.clip[1]),
            'gun_burst': target(lambda d: '%d' % d.gun.burst[0]),
            'gun_burst_reload': target(lambda d: '%.1f' % d.gun.burst[1]),
            'gun_aiming_time': target(lambda d: '%.1f' % d.gun.aimingTime),
            'gun_accuracy': target(lambda d: '%.2f' % round(d.gun.shotDispersionAngle * 100, 2)),
            'angle_pitch_up': target(lambda d: '%d' % degrees(-d.gun.pitchLimits['absolute'][0])),
            'angle_pitch_down': target(lambda d: '%d' % degrees(-d.gun.pitchLimits['absolute'][1])),
            'angle_pitch_left': target(lambda d: '%d' % degrees(-d.gun.turretYawLimits[0])
                                       if d.gun.turretYawLimits else None),
            'angle_pitch_right': target(lambda d: '%d' % degrees(d.gun.turretYawLimits[1])
                                        if d.gun.turretYawLimits else None),
            'vehicle_max_health': target(lambda d: '%d' % d.maxHealth),
            'armor_hull_front': target(lambda d: '%d' % d.hull.primaryArmor[0]),
            'armor_hull_side': target(lambda d: '%d' % d.hull.primaryArmor[1]),
            'armor_hull_back': target(lambda d: '%d' % d.hull.primaryArmor[2]),
            'turret_name': target(lambda d: '%s' % d.turret.shortUserString),
            'armor_turret_front': target(lambda d: '%d' % d.turret.primaryArmor[0]),
            'armor_turret_side': target(lambda d: '%d' % d.turret.primaryArmor[1]),
            'armor_turret_back': target(lambda d: '%d' % d.turret.primaryArmor[2]),
            'vehicle_weight': target(lambda d: '%.1f' % round(d.physics['weight'] / 1000.0, 1)),
            'chassis_max_weight': target(lambda d: '%.1f' % round(d.chassis.maxLoad / 1000.0, 1)),
            'engine_name': target(lambda d: '%s' % d.engine.shortUserString),
            'engine_power': target(lambda d: '%d' % round(d.engine.power / 735.49875, 0)),
            'engine_power_density': self._get_engine_power_density,
            'speed_forward': target(lambda d: '%d' % (d.physics['speedLimits'][0] * 3.6)),
            'speed_backward': target(lambda d: '%d' % (d.physics['speedLimits'][1] * 3.6)),
            'hull_speed_turn': target(lambda d: '%.2f' % degrees(d.chassis.rotationSpeed)),
            'turret_speed_turn': target(lambda d: '%.2f' % degrees(d.turret.rotationSpeed)),
            'chassis_rotation_speed': target(lambda d: '%d' % degrees(d.chassis.rotationSpeed)),
            'invis_stand': target(lambda d: '%.1f' % (d.type.invisibility[1] * 57)),
            'invis_stand_shot': target(lambda d: '%.2f' % (d.type.invisibility[1]
                                                           * d.gun.invisibilityFactorAtShot * 57)),
            'invis_move': target(lambda d: '%.1f' % (d.type.invisibility[0] * 57)),
            'invis_move_shot': target(lambda d: '%.2f' % (d.type.invisibility[0]
                                                          * d.gun.invisibilityFactorAtShot * 57)),
            'vision_radius': target(lambda d: '%d' % d.turret.circularVisionRadius),
            'radio_name': target(lambda d: '%s' % d.radio.shortUserString),
            'radio_radius': target(lambda d: '%d' % d.radio.distance),
            'nation': target(lambda d: NAMES[d.type.customizationNationID]),
            'level': target(lambda d: '%d' % d.type.level),
            'rlevel': self._get_roman_level,
            'pl_vehicle_weight': player(lambda d: '%.1f' % round(d.physics['weight'] / 1000.0, 1)),
            'pl_gun_reload': player(lambda d: '%.2f' % d.gun.reloadTime),
            'pl_gun_reload_equip': lambda: self._get_gun_reload_equip_for_descriptor(
                self._getPlayerTypeDescriptor(), 'pl_gun_reload_equip'),
            'pl_gun_dpm': lambda: self._get_gun_dpm_for_descriptor(self._getPlayerTypeDescriptor(), 'pl_gun_dpm'),
            'pl_gun_dpm_equip': lambda: self._get_gun_dpm_equip_for_descriptor(
                self._getPlayerTypeDescriptor(), 'pl_gun_dpm_equip'),
            'pl_vision_radius': player(lambda d: '%d' % d.turret.circularVisionRadius),
            'pl_gun_aiming_time': player(lambda d: '%.1f' % d.gun.aimingTime),
            'stun_radius': self._stun('stun_radius', lambda stun: '%d' % stun.stunRadius),
            'stun_duration_min': self._stun('stun_duration_min', lambda stun: '%.1f' % round(
                stun.stunDuration * stun.guaranteedStunDuration, 1)),
            'stun_duration_max': self._stun('stun_duration_max', lambda stun: '%d' % stun.stunDuration),
        }
        for number in (1, 2, 3):
            index = number - 1
            handlers.update({
                'shell_name_%d' % number: self._shell(index, lambda shot: '%s' % shot.shell.userString),
                'shell_damage_%d' % number: self._shell(index, lambda shot: '%d' % self._get_shell_damage(shot.shell)),
                'shell_power_%d' % number: self._shell(index, lambda shot: '%d' % shot.piercingPower[0]),
                'shell_type_%d' % number: self._shell(index, lambda shot: self.i18n(shot.shell.kind.lower())),
                'shell_speed_%d' % number: self._shell(index, lambda shot: '%d' % round(shot.speed * 1.25)),
                'shell_distance_%d' % number: self._shell(index, lambda shot: '%d' % shot.maxDistance),
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

    def _get_gun_reload_equip(self):
        return self._get_gun_reload_equip_for_descriptor(self._typeDescriptor, 'gun_reload_equip')

    def _get_gun_dpm_equip(self):
        return self._get_gun_dpm_equip_for_descriptor(self._typeDescriptor, 'gun_dpm_equip')

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
        settings = settings_service.getComponentDict(target_information_settings)
        if self.value1 is None or self.value2 is None:
            raise ValueError('Values must be defined before comparison.')
        if self.value1 > self.value2:
            return settings[TARGET_INFORMATION.COMPARE_VALUES]['moreThan'][attribute]
        elif self.value1 == self.value2:
            return settings[TARGET_INFORMATION.COMPARE_VALUES]['equal'][attribute]
        else:
            return settings[TARGET_INFORMATION.COMPARE_VALUES]['lessThan'][attribute]


class InfoPanel(DataConstants):
    def __init__(self):
        self._active = False
        self._inBattle = False
        self.textFormats = (self.getText()
                            if settings_service.getComponentDict(target_information_settings)[GLOBAL.ENABLED] else None)
        self.hotKeyDown = False
        self.visible = False
        self.timer = None
        self._feedback = None
        DataConstants.__init__(self)

    def reset(self):
        self.cancelHide()
        DataConstants.reset(self)
        self.textFormats = (self.getText()
                            if settings_service.getComponentDict(target_information_settings)[GLOBAL.ENABLED] else None)
        self.hotKeyDown = False
        self.visible = False
        self.timer = None

    def start(self):
        if self._active:
            return
        self._active = True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, TARGET_INFORMATION)
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
        if not affects(changes, GLOBAL.ENABLED, TARGET_INFORMATION.TEMPLATE_PRESET,
                       TARGET_INFORMATION.FORMATS, TARGET_INFORMATION.COMPARE_VALUES):
            return
        enabled = settings_service.getSetting(target_information_settings, GLOBAL.ENABLED)
        self.textFormats = self.getText() if enabled else None
        if not enabled:
            self.hide()
            self.hotKeyDown = False
        elif self._inBattle and self.visible:
            g_panel.setText(self.setTextsFormatted())

    def onBattleStarted(self):
        global g_flash, g_panel
        if self._inBattle:
            return
        if battle_capabilities.has_gameface_hud():
            g_panel = g_gameface
        else:
            if g_flash is None:
                from driftkings.flash.battle.target_information import Flash
                g_flash = Flash()
            g_panel = g_flash
        self._inBattle = True
        feedback = BigWorld.player().guiSessionProvider.shared.feedback
        if feedback is not None:
            feedback.onVehicleFeedbackReceived += self.onVehicleFeedback
            self._feedback = feedback
        g_panel.startBattle()

    def onBattleEnded(self):
        self._inBattle = False
        if self._feedback is not None:
            self._feedback.onVehicleFeedbackReceived -= self.onVehicleFeedback
            self._feedback = None
        try:
            self.reset()
        finally:
            g_panel.stopBattle()

    def onVehicleFeedback(self, eventID, vehicleID, value):
        # PlayerAvatar.targetFocus/targetBlur report the aimed entity as ENTITY_IN_FOCUS.
        from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
        if eventID != FEEDBACK_EVENT_ID.ENTITY_IN_FOCUS or not self._inBattle:
            return
        if not getattr(value, 'isInFocus', False):
            # A dead/removed/filtered target must still release an already shown panel.
            self.onUpdateBlur()
            return
        if not settings_service.getComponentDict(target_information_settings)[GLOBAL.ENABLED]:
            return
        entity = BigWorld.entity(vehicleID)
        if entity is not None and self.isConditions(entity):
            self.onUpdateVehicle(entity)
        else:
            self.onUpdateBlur()

    def onBattleKey(self, event):
        if self._inBattle:
            self.keyPressed(event)

    @staticmethod
    def getText():
        settings = settings_service.getComponentDict(target_information_settings)
        template_index = settings[TARGET_INFORMATION.TEMPLATE_PRESET]
        # The full preset is editable in JSON; retain the existing preset IDs.
        if template_index == 3 and settings.get(TARGET_INFORMATION.FORMATS):
            return u'\n'.join(value if isinstance(value,type(u'')) else value.decode('utf-8')
                              for value in settings[TARGET_INFORMATION.FORMATS])
        template_key = TEMPLATE_INDEX_TO_KEY.get(template_index, 'default')
        return PRESET_TEMPLATES.get(template_key, PRESET_TEMPLATES['default'])

    @staticmethod
    def isConditions(entity):
        settings = settings_service.getComponentDict(target_information_settings)
        player = BigWorld.player()
        if player is None or entity is None or not hasattr(entity, 'publicInfo'):
            return False
        playerTeam = player.team
        team = getattr(entity.publicInfo, 'team', 0)
        isAlly = team > 0 and team == playerTeam
        if settings[TARGET_INFORMATION.SHOW_FOR] == 0:
            showFor = True
        elif settings[TARGET_INFORMATION.SHOW_FOR] == 1:
            showFor = isAlly
        elif settings[TARGET_INFORMATION.SHOW_FOR] == 2:
            showFor = not isAlly
        else:
            showFor = False
        isAlive = entity.isAlive() if settings[TARGET_INFORMATION.ALIVE_ONLY] else True
        return showFor and isAlive

    def getFuncResponse(self, funcName):
        if not hasattr(self, funcName):
            return ''
        func = getattr(self, funcName, None)
        if callable(func):
            result = func()
            if result is not None:
                value = (result if isinstance(result,type(u'')) else result.decode('utf-8', 'replace')
                         if isinstance(result,str) else type(u'')(result))
                return escape(value, {chr(34): '&quot;', chr(39): '&apos;'})
            return ''
        return ''

    def setTextsFormatted(self):
        if not settings_service.getComponentDict(target_information_settings)[GLOBAL.ENABLED]:
            return ''
        textFormat = self.expandI18n(self.textFormats or self.getText())
        textFormat = self.replaceMacros(textFormat, self._macroHandlers.keys())
        textFormat = self.replaceCompareMacros(textFormat, COMPARE_MACROS)
        return resolve_vehicle_images(textFormat, getIconPath, getContourIconPath)

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
        settings = settings_service.getComponentDict(target_information_settings)
        if not settings[GLOBAL.ENABLED]:
            return
        player = BigWorld.player()
        if not hasattr(player, 'getVehicleAttached'):
            return
        if checkKeys(settings[TARGET_INFORMATION.ALT_KEY]) and event.isKeyDown():
            self.hotKeyDown = True
            self.onUpdateVehicle(player.getVehicleAttached(), ignoreHotKey=True)
        elif self.hotKeyDown and event.isKeyUp() and not checkKeys(settings[TARGET_INFORMATION.ALT_KEY]):
            self.hotKeyDown = False
            target = BigWorld.target()
            if self.isConditions(target):
                self.onUpdateVehicle(target)
            else:
                self.hide()

    def cancelHide(self):
        if self.timer is not None:
            cancelCallback(self.timer)
            self.timer = None

    def onHideTimeout(self):
        # This callback has already fired: do not cancel its consumed ID.
        self.timer = None
        self.hide()

    def hide(self):
        self.cancelHide()
        self.visible = False
        g_panel.show(False)

    def onUpdateBlur(self):
        if not self._inBattle or not self.visible or self.hotKeyDown or self.timer is not None:
            return
        delay=max(0.0,float(settings_service.getComponentDict(target_information_settings)[TARGET_INFORMATION.DELAY]))
        if delay == 0:
            self.hide()
        else:
            self.timer = callback(delay, self.onHideTimeout)

    def onUpdateVehicle(self, vehicle, ignoreHotKey=False):
        player = BigWorld.player()
        if (not settings_service.getComponentDict(target_information_settings)[GLOBAL.ENABLED] or not g_panel.active
            or not hasattr(player, 'getVehicleAttached')):
            return
        if self.hotKeyDown and not ignoreHotKey:
            return
        playerVehicle = player.getVehicleAttached()
        if playerVehicle is not None:
            self.cancelHide()
            self.visible = True
            g_panel.show(True)
            if hasattr(vehicle, 'typeDescriptor'):
                self.init(vehicle, playerVehicle)
            elif hasattr(playerVehicle, 'typeDescriptor'):
                self.init(None, playerVehicle)
            g_panel.setText(self.setTextsFormatted())


g_comparator = CompareMacros()
g_mod = InfoPanel()


def init():
    g_gameface.install()
    g_mod.start()


def fini():
    try:
        g_mod.stop()
    finally:
        g_gameface.dispose()
