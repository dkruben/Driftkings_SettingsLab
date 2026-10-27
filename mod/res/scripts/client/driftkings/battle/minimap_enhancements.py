# -*- coding: utf-8 -*-
from math import degrees
import weakref

from account_helpers.settings_core import settings_constants
import BigWorld
from gui.Scaleform.daapi.view.battle.shared.minimap import plugins
from gui.Scaleform.daapi.view.battle.shared.minimap.component import MinimapComponent
from gui.Scaleform.daapi.view.battle.shared.minimap.settings import (CIRCLE_STYLE, CIRCLE_TYPE,
                                                                     VIEW_RANGE_CIRCLES_AS3_DESCR)
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from driftkings._constants import BATTLE_ALIASES, GLOBAL, MINIMAP_ENHANCEMENTS
from driftkings.common.utils.formatting import hexToDecimal
from driftkings.common.utils.game import checkKeys
from driftkings.common.utils.wgutils import getBattleTypes, hasCompetingMarkers
from driftkings.core import minimap as policy
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.core.hooks import override
from driftkings.core.keyboard import keyboard
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.minimap_enhancements import MinimapEnhancementsSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.ui import g_events

LOG = get_logger('driftkings.battle.minimap_enhancements')

PERSONAL = weakref.WeakSet()
VEHICLES = weakref.WeakSet()
VIEWS = weakref.WeakSet()
AS_BATTLE = BATTLE_ALIASES.MINIMAP


class MinimapController(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self, config):
        self.config = config
        self._active = False
        self.minimapZoom = False
        settings_service.onModSettingsChanged.connect(self.onModSettingsChanged, MINIMAP_ENHANCEMENTS)

    def activate(self):
        if self._active:
            return
        self._active = True
        keyboard.subscribe(self.onHotkeyPressed)

    def deactivate(self):
        keyboard.unsubscribe(self.onHotkeyPressed)
        self._active = False
        # Flash disposal restores zoom; do not access an arena being destroyed.
        self.minimapZoom = False

    def dispose(self):
        self.deactivate()
        settings_service.onModSettingsChanged.disconnect(self.onModSettingsChanged)

    def onModSettingsChanged(self, component, settings):
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] or not settings_service.getComponentDict(self.config)[MINIMAP_ENHANCEMENTS.PRESENTATION]['alternativeEnabled']:
            self.setAlternative(False)
        changed = set(settings)
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_ENHANCEMENTS.YAW, MINIMAP_ENHANCEMENTS.LINES,
                                 MINIMAP_ENHANCEMENTS.CIRCLES, MINIMAP_ENHANCEMENTS.VIEW_RADIUS,
                                 MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES, MINIMAP_ENHANCEMENTS.COLOR_DRAW_CIRCLE,
                                 MINIMAP_ENHANCEMENTS.COLOR_MAX_VIEW_CIRCLE, MINIMAP_ENHANCEMENTS.COLOR_MIN_SPOTTING_CIRCLE,
                                 MINIMAP_ENHANCEMENTS.COLOR_VIEW_CIRCLE)):
            for plugin in list(PERSONAL):
                plugin.refreshPresentation()
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_ENHANCEMENTS.LABELS, MINIMAP_ENHANCEMENTS.PRESENTATION,
                                 MINIMAP_ENHANCEMENTS.SHOW_NAMES, MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS,
                                 MINIMAP_ENHANCEMENTS.LAST_POSITION_DURATION, MINIMAP_ENHANCEMENTS.LOST_MARKER,
                                 MINIMAP_ENHANCEMENTS.PERMANENT_MINIMAP_DEATH)):
            for plugin in list(VEHICLES):
                plugin.refreshLabels()
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_ENHANCEMENTS.PRESENTATION, MINIMAP_ENHANCEMENTS.ZOOM_FACTOR,
                                 MINIMAP_ENHANCEMENTS.ZOOM_FACTOR_MAX, MINIMAP_ENHANCEMENTS.ICONS, MINIMAP_ENHANCEMENTS.HEALTH,
                                 MINIMAP_ENHANCEMENTS.LOST_MARKER, MINIMAP_ENHANCEMENTS.MAP_SIZE, MINIMAP_ENHANCEMENTS.CIRCLES,
                                 MINIMAP_ENHANCEMENTS.EXTRA_CIRCLES, MINIMAP_ENHANCEMENTS.LABELS, MINIMAP_ENHANCEMENTS.LINES,
                                 MINIMAP_ENHANCEMENTS.ARTILLERY_AIM, MINIMAP_ENHANCEMENTS.SHOW_VEHICLE_TYPES,
                                 MINIMAP_ENHANCEMENTS.NEARBY)):
            for view in list(VIEWS):
                view.onAltKey(self.minimapZoom)

    def setAlternative(self, pressed):
        if self.minimapZoom == pressed:
            return
        self.minimapZoom = pressed
        g_events.onAltKey(pressed)
        for plugin in list(VEHICLES):
            plugin.refreshLabels()

    @property
    def notEpicBattle(self):
        return not self.sessionProvider.arenaVisitor.gui.isInEpicRange()

    def onHotkeyPressed(self, event):
        settings = settings_service.getComponentDict(self.config)
        if not settings[GLOBAL.ENABLED] or not self._active:
            return
        self.setAlternative(bool(settings[MINIMAP_ENHANCEMENTS.PRESENTATION]['alternativeEnabled'] and checkKeys(settings[MINIMAP_ENHANCEMENTS.BUTTON])))


config = Settings()
controller = MinimapController(config)


from driftkings.flash.batalha.minimap_enhancements import MinimapEnhancementsView


class PersonalEntriesPlugin(plugins.PersonalEntriesPlugin):

    def _rangeState(self):
        if not hasattr(self, '_ranges'):
            # Width 0 until as_initArenaSize: Flash then uses the arena bounding box instead.
            self._ranges = {'width': 0, 'height': 0, 'circles': {}, 'vehicleClass': getattr(self, '_vehicleClass', None)}
        return self._ranges

    def _publishRanges(self):
        for view in list(VIEWS):
            view.onRanges(self._rangeState())

    def _updateShellRange(self, *args):
        circles = self._rangeState()['circles']
        settings = settings_service.getComponentDict(config)
        style = settings[MINIMAP_ENHANCEMENTS.CIRCLES]['shell']
        radius = None
        if settings[GLOBAL.ENABLED] and style['mode'] == 'on' and self.__isAlive and not self.__isObserver:
            ammo = self.sessionProvider.shared.ammo
            descriptor = getattr(BigWorld.player(), 'vehicleTypeDescriptor', None)
            radius = policy.shell_range(descriptor, ammo.getCurrentShellCD() if ammo is not None else None)
        shell = dict(color=hexToDecimal(style['color']), alpha=style['alpha'], radius=radius) if radius else None
        if circles.get('shell') != shell:
            if shell:
                circles['shell'] = shell
            else:
                circles.pop('shell', None)
            self._publishRanges()

    def _invoke(self, entryID, method, *args):
        result = super(PersonalEntriesPlugin, self)._invoke(entryID, method, *args)
        if method.startswith('as_'):
            ranges = self._rangeState()
            add = {'as_addDrawRange': 'draw', 'as_addDynamicViewRange': 'view', 'as_addMaxViewRage': 'maxView', 'as_addMinSpottingRange': 'proximity'}
            remove = {'as_delDrawRange': 'draw', 'as_delDynRange': 'view', 'as_delMaxViewRage': 'maxView', 'as_delMinSpottingRange': 'proximity'}
            if method == 'as_initArenaSize':
                ranges.update(width=args[0], height=args[1])
            elif method in add:
                ranges['circles'][add[method]] = dict(color=args[0], alpha=args[1], radius=args[2])
            elif method in remove:
                ranges['circles'].pop(remove[method], None)
            elif method == 'as_removeAllCircles':
                # Only native circles are removed; the shell range is ours.
                for key in [key for key in ranges['circles'] if key != 'shell']:
                    ranges['circles'].pop(key)
            elif method == 'as_updateDynRange' and 'view' in ranges['circles']:
                ranges['circles']['view']['radius'] = args[0]
            else:
                return result
            for view in list(VIEWS):
                view.onRanges(ranges)
        return result

    def start(self):
        PERSONAL.add(self)
        super(PersonalEntriesPlugin, self).start()
        self._refreshYawLimits()
        ammo = self.sessionProvider.shared.ammo
        if ammo is not None:
            ammo.onCurrentShellChanged += self._updateShellRange
        self._updateShellRange()

    def _refreshYawLimits(self):
        info = self._arenaDP.getVehicleInfo()
        names = policy.vehicle_names(getattr(info.vehicleType, 'iconName', ''), getattr(info.vehicleType, 'shortName', ''))
        ranges = self._rangeState()
        if getattr(self, '_vehicleClass', None) != info.vehicleType.classTag or ranges.get('vehicleNames') != names:
            self._vehicleClass = info.vehicleType.classTag
            ranges.update(vehicleClass=self._vehicleClass, vehicleNames=names)
            self._publishRanges()
        limits = info.vehicleType.turretYawLimits
        extended = settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.YAW]
        updated = (degrees(limits[0]), degrees(limits[1])) if limits is not None and (extended or info.isSPG()) else None
        if updated != self.__yawLimits:
            self.__clearYawLimit()
            self.__yawLimits = updated

    def stop(self):
        PERSONAL.discard(self)
        ammo = self.sessionProvider.shared.ammo
        if ammo is not None:
            ammo.onCurrentShellChanged -= self._updateShellRange
        super(PersonalEntriesPlugin, self).stop()

    def refreshPresentation(self):
        self._refreshYawLimits()
        self.__removeAllCircles()
        self.setSettings()
        self._updateShellRange()

    def _invalidateMarkup(self, *args, **kwargs):
        self._refreshYawLimits()
        return super(PersonalEntriesPlugin, self)._invalidateMarkup(*args, **kwargs)

    def updateSettings(self, diff):
        super(PersonalEntriesPlugin, self).updateSettings(diff)
        self.refreshPresentation()

    def setSettings(self):
        settings = settings_service.getComponentDict(config)
        super(PersonalEntriesPlugin, self).setSettings()
        if self.__isAlive and not self.__isObserver:
            direction = self.settingsCore.getSetting(settings_constants.GAME.SHOW_VECTOR_ON_MAP)
            sector = self.settingsCore.getSetting(settings_constants.GAME.SHOW_SECTOR_ON_MAP)
            if settings[GLOBAL.ENABLED]:
                direction = policy.visible(settings[MINIMAP_ENHANCEMENTS.LINES]['direction'], direction)
                sector = policy.visible(settings[MINIMAP_ENHANCEMENTS.LINES]['sector'], sector)
            self._updateDirectionLine(direction)
            self._updateYawLimits(sector)

    def __showDirectionLine(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.LINES]['direction'] == 'off':
            return super(PersonalEntriesPlugin, self).__hideDirectionLine()
        return super(PersonalEntriesPlugin, self).__showDirectionLine()

    def __setupYawLimit(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.LINES]['sector'] == 'off':
            return super(PersonalEntriesPlugin, self).__clearYawLimit()
        return super(PersonalEntriesPlugin, self).__setupYawLimit()

    def _circleVisible(self, key, native):
        settings = settings_service.getComponentDict(config)
        return policy.visible(settings[MINIMAP_ENHANCEMENTS.CIRCLES][key]['mode'], native) if settings[GLOBAL.ENABLED] else native

    def _canShowDrawRangeCircle(self):
        return self._circleVisible('draw', super(PersonalEntriesPlugin, self)._canShowDrawRangeCircle())

    def _canShowMaxViewRangeCircle(self):
        return self._circleVisible('maxView', super(PersonalEntriesPlugin, self)._canShowMaxViewRangeCircle())

    def _canShowMinSpottingRangeCircle(self):
        return self._circleVisible('proximity', super(PersonalEntriesPlugin, self)._canShowMinSpottingRangeCircle())

    def _canShowViewRangeCircle(self):
        return self._circleVisible('view', super(PersonalEntriesPlugin, self)._canShowViewRangeCircle())

    def _calcCircularVisionRadius(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.VIEW_RADIUS]:
            # Feedback can be absent while battle services start or stop.
            feedback = self.sessionProvider.shared.feedback
            vehAttrs = feedback.getVehicleAttrs() if feedback is not None else None
            if vehAttrs is None:
                return self._arenaVisitor.getVisibilityMinRadius()
            return vehAttrs.get('circularVisionRadius', self._arenaVisitor.getVisibilityMinRadius())
        # noinspection PyProtectedMember
        return super(PersonalEntriesPlugin, self)._calcCircularVisionRadius()

    def __addDrawRangeCircle(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.DRAW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.DRAW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_DRAW_CIRCLE,(hexToDecimal(settings[MINIMAP_ENHANCEMENTS.COLOR_DRAW_CIRCLE]) if settings[MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.DRAW_RANGE), settings[MINIMAP_ENHANCEMENTS.CIRCLES]['draw']['alpha'], self._arenaVisitor.getVehicleCircularAoiRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addDrawRangeCircle()

    def __addMaxViewRangeCircle(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MAX_VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MAX_VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_VIEW_CIRCLE,(hexToDecimal(settings[MINIMAP_ENHANCEMENTS.COLOR_MAX_VIEW_CIRCLE]) if settings[MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.MAX_VIEW_RANGE), settings[MINIMAP_ENHANCEMENTS.CIRCLES]['maxView']['alpha'], self._arenaVisitor.getVisibilityMaxRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addMaxViewRangeCircle()

    def __addMinSpottingRangeCircle(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MIN_SPOTTING_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MIN_SPOTTING_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MIN_SPOTTING_CIRCLE,(hexToDecimal(settings[MINIMAP_ENHANCEMENTS.COLOR_MIN_SPOTTING_CIRCLE]) if settings[MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.MIN_SPOTTING_RANGE), settings[MINIMAP_ENHANCEMENTS.CIRCLES]['proximity']['alpha'], self._arenaVisitor.getVisibilityMinRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addMinSpottingRangeCircle()

    def __addViewRangeCircle(self):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_DYN_CIRCLE,(hexToDecimal(settings[MINIMAP_ENHANCEMENTS.COLOR_VIEW_CIRCLE]) if settings[MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.VIEW_RANGE), settings[MINIMAP_ENHANCEMENTS.CIRCLES]['view']['alpha'], self._getViewRangeRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addViewRangeCircle()


class ArenaVehiclesPlugin(plugins.ArenaVehiclesPlugin):
    def __init__(self, *args, **kwargs):
        settings = settings_service.getComponentDict(config)
        self._health = {}
        self._presentations = {}
        self._identities = {}
        super(ArenaVehiclesPlugin, self).__init__(*args, **kwargs)
        self._nativeDestroyed = (self.__showDestroyEntries, self.__isDestroyImmediately)
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.PERMANENT_MINIMAP_DEATH]:
            self.__showDestroyEntries = True
            self.__isDestroyImmediately = True
        self._lastPositions = {}
        self._expiredPositions = set()
        self._lastPositionCallback = None
        self._lastLostSecond = None
        self._running = False

    def start(self):
        self._running = True
        VEHICLES.add(self)
        super(ArenaVehiclesPlugin, self).start()

    def stop(self):
        self._running = False
        VEHICLES.discard(self)
        if self._lastPositionCallback is not None:
            cancelCallback(self._lastPositionCallback)
            self._lastPositionCallback = None
        self._lastPositions.clear()
        self._expiredPositions.clear()
        self._health.clear()
        self._presentations.clear()
        self._identities.clear()
        super(ArenaVehiclesPlugin, self).stop()

    def _showVehicle(self, vehicleID, location):
        entry = self._entries[vehicleID]
        self._lastPositions.pop(entry.getID(), None)
        self._expiredPositions.discard(entry.getID())
        result = super(ArenaVehiclesPlugin, self)._showVehicle(vehicleID, location)
        self.refreshLabel(vehicleID, entry)
        return result

    def _vehicleOf(self, entry):
        for vehicleID, saved in self._entries.items():
            if saved is entry:
                return vehicleID
        return None

    def _lostIcon(self, entry, lost):
        # The client draws a 'last seen' dot for vehicles outside the area of interest.
        # Tell only the Flash entry it is still in AoI so it keeps the vehicle icon;
        # the model stays out of AoI, so the next spotting is handled natively.
        icon = settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LOST_MARKER]['icon']
        if not entry.isInAoI() and (icon or not lost):
            self._invoke(entry.getID(), 'setInAoI', bool(lost and icon))

    def _clearLost(self, entry):
        if entry.getID() not in self._lastPositions and entry.getID() not in self._expiredPositions:
            return
        self._lastPositions.pop(entry.getID(), None)
        self._expiredPositions.discard(entry.getID())
        vehicleID = self._vehicleOf(entry)
        if vehicleID is not None:
            self.refreshLabel(vehicleID, entry)

    def _setInAoI(self, entry, isInAoI):
        result = super(ArenaVehiclesPlugin, self)._setInAoI(entry, isInAoI)
        # Spotted again. Vehicles spotted by allies outside our area of interest come
        # back through updatePositions (FAR), which never calls _showVehicle.
        if isInAoI:
            self._clearLost(entry)
        return result

    def _hideVehicle(self, entry):
        settings = settings_service.getComponentDict(config)
        self._expiredPositions.discard(entry.getID())
        result = super(ArenaVehiclesPlugin, self)._hideVehicle(entry)
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS] and entry.isAlive() and entry.isEnemy() and entry.getMatrix() is not None:
            # The base plugin freezes the matrix at the last observed position.
            # Use its existing Flash entry, rather than a nonexistent setLastPosition API.
            wasActive = entry.isActive()
            if entry.setActive(True):
                self._setActive(entry.getID(), True)
            # A duration of 0 keeps the last position until the vehicle is seen again or dies.
            duration = max(0.0, float(settings[MINIMAP_ENHANCEMENTS.LAST_POSITION_DURATION]))
            now = BigWorld.time()
            self._lastPositions[entry.getID()] = (entry, now + duration if duration > 0 else None, wasActive, now)
            self._lostIcon(entry, True)
            if self._running and self._lastPositionCallback is None:
                self._lastPositionCallback = callback(0.25, self.updateLastPositions)
        for vehicleID, saved in self._entries.items():
            if saved is entry:
                self.refreshLabel(vehicleID, entry)
                break
        return result

    def __setDestroyed(self, vehicleID, entry):
        settings = settings_service.getComponentDict(config)
        self._lastPositions.pop(entry.getID(), None)
        self._expiredPositions.discard(entry.getID())
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.PERMANENT_MINIMAP_DEATH] and self.__isDestroyImmediately:
            self._setInAoI(entry, True)
        super(ArenaVehiclesPlugin, self).__setDestroyed(vehicleID, entry)
        self.refreshLabel(vehicleID, entry)

    def __setActive(self, entry, active):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS] and entry.getID() in self._expiredPositions and not entry.isInAoI():
            active = False
        return super(ArenaVehiclesPlugin, self).__setActive(entry, active)

    def _getDisplayedName(self, vInfo):
        settings = settings_service.getComponentDict(config)
        if not settings[GLOBAL.ENABLED]:
            return super(ArenaVehiclesPlugin, self)._getDisplayedName(vInfo)
        if not vInfo.isAlive() and not settings[MINIMAP_ENHANCEMENTS.SHOW_NAMES]:
            return ''
        entry = self._entries.get(vInfo.vehicleID)
        state = 'dead' if not vInfo.isAlive() else 'lost' if entry and entry.getID() in self._lastPositions else 'alive'
        values = {'vehicle': vInfo.getDisplayedName(), 'name': vInfo.player.name,
                  'level': vInfo.vehicleType.level, 'type': vInfo.vehicleType.classTag, 'state': state}
        return policy.label(settings[MINIMAP_ENHANCEMENTS.LABELS], values, controller.minimapZoom)

    def _setVehicleInfo(self, vehicleID, entry, vInfo, guiProps, isSpotted=False):
        self._trackVehicle(vehicleID, vInfo)
        result = super(ArenaVehiclesPlugin, self)._setVehicleInfo(vehicleID, entry, vInfo, guiProps, isSpotted)
        self._publishVehicle(vehicleID, entry, vInfo, guiProps)
        return result

    def _trackVehicle(self, vehicleID, vInfo):
        identity = (vInfo.vehicleType.compactDescr, vInfo.isAlive())
        previous = self._identities.get(vehicleID)
        if previous and (identity[0] != previous[0] or identity[1] and not previous[1]):
            self._health.pop(vehicleID, None)
        self._identities[vehicleID] = identity

    def _onVehicleHealthChanged(self, vehicleID, currH, maxH):
        result = super(ArenaVehiclesPlugin, self)._onVehicleHealthChanged(vehicleID, currH, maxH)
        if vehicleID in self._entries and maxH and maxH > 0 and currH <= maxH:
            info = self._arenaDP.getVehicleInfo(vehicleID)
            if info is None:
                return result
            self._trackVehicle(vehicleID, info)
            currH = max(0, currH)
            self._health[vehicleID] = (currH, maxH)
            self._publishVehicle(vehicleID, self._entries[vehicleID])
        return result

    def _publishVehicle(self, vehicleID, entry, info=None, props=None):
        if info is None:
            info = self._arenaDP.getVehicleInfo(vehicleID)
        if info is None:
            return
        if props is None:
            props = self._arenaDP.getPlayerGuiProps(vehicleID, info.team)
        gui = self._getGuiPropsName(props)
        group = policy.vehicle_group(gui, entry.isEnemy())
        lost = self._lastPositions.get(entry.getID())
        state = 'dead' if not info.isAlive() else 'lost' if lost else 'alive'
        age = max(0, int(BigWorld.time() - lost[3])) if lost else 0
        current, maximum = self._health.get(vehicleID, (None, info.vehicleType.maxHealth))
        if state == 'dead':
            current = 0
        values = dict(vehicle=info.getDisplayedName(), name=info.player.name, level=info.vehicleType.level,
                      type=info.vehicleType.classTag, state=state, group=group, lostSeconds=age)
        values.update(policy.health_values(current, maximum))
        text = policy.label(settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LABELS], values, controller.minimapZoom)
        if state == 'dead' and not settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.SHOW_NAMES]:
            text = ''
        if state == 'lost' and settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LOST_MARKER]['showSeconds']:
            text += ' [%ss]' % age
        opacity = 100
        if state == 'lost' and settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LOST_MARKER]['fade']:
            minimum = settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LOST_MARKER]['minimumAlpha']
            # Permanent markers fade over a minute, then stay at the minimum opacity.
            window = settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LAST_POSITION_DURATION] or 60
            opacity = max(minimum, 100 - (100 - minimum) * age / float(max(1, window)))
        payload = dict(id=vehicleID, text=text, group=group, guiLabel=gui, state=state, hp=values['hp'],
                       percent=values['hpPercent'], alpha=opacity,
                       color=policy.marker_color(group, state, settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LOST_MARKER]),
                       lostColor=policy.lost_color(group, settings_service.getComponentDict(config)[MINIMAP_ENHANCEMENTS.LOST_MARKER]))
        if self._presentations.get(vehicleID) == payload:
            return
        self._presentations[vehicleID] = payload
        for view in list(VIEWS):
            view.onVehicleData(payload)

    def refreshLabel(self, vehicleID, entry):
        info = self._arenaDP.getVehicleInfo(vehicleID)
        if info is not None:
            props = self._arenaDP.getPlayerGuiProps(vehicleID, info.team)
            self._setVehicleInfo(vehicleID, entry, info, props)

    def refreshLabels(self):
        settings = settings_service.getComponentDict(config)
        self.__showDestroyEntries, self.__isDestroyImmediately = self._nativeDestroyed
        if settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.PERMANENT_MINIMAP_DEATH]:
            self.__showDestroyEntries = self.__isDestroyImmediately = True
        keep = settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS]
        for entry, expires, wasActive, since in self._lastPositions.values():
            self._lostIcon(entry, keep)
        if not keep:
            for entry, expires, wasActive, since in self._lastPositions.values():
                if entry.isAlive() and not entry.isInAoI() and entry.setActive(wasActive):
                    self._setActive(entry.getID(), wasActive)
            self._lastPositions.clear()
            self._expiredPositions.clear()
        for vehicleID, entry in list(self._entries.items()):
            self.refreshLabel(vehicleID, entry)

    def updateLastPositions(self):
        settings = settings_service.getComponentDict(config)
        self._lastPositionCallback = None
        if not self._running:
            return
        now = BigWorld.time()
        updateLabels = self._lastLostSecond != int(now)
        self._lastLostSecond = int(now)
        enabled = settings[GLOBAL.ENABLED] and settings[MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS]
        for entryID, (entry, expires, wasActive, since) in list(self._lastPositions.items()):
            if not entry.isAlive() or entry.isInAoI() or not entry.getID():
                # Seen again or destroyed: drop the 'lost' label and colours too.
                self._clearLost(entry)
                self._lastPositions.pop(entryID, None)
            elif not enabled or expires is not None and now >= expires:
                if enabled:
                    self._expiredPositions.add(entryID)
                active = wasActive if not enabled else False
                if entry.setActive(active):
                    self._setActive(entryID, active)
                self._lastPositions.pop(entryID, None)
            elif updateLabels and (settings[MINIMAP_ENHANCEMENTS.LOST_MARKER]['showSeconds'] or settings[MINIMAP_ENHANCEMENTS.LOST_MARKER]['fade'] or '{{lostSeconds' in settings[MINIMAP_ENHANCEMENTS.LABELS]['lost']):
                for vehicleID, model in self._entries.items():
                    if model is entry:
                        self._publishVehicle(vehicleID, entry)
                        break
        if self._lastPositions:
            self._lastPositionCallback = callback(0.25, self.updateLastPositions)


@override(MinimapComponent, '_setupPlugins')
def new_setupPlugins(func, self, arenaVisitor):
    args = func(self, arenaVisitor)
    try:
        allowedMode = arenaVisitor.gui.guiType in getBattleTypes()
        if not hasCompetingMarkers() and allowedMode:
            # Preserve mode-specific subclasses rather than replacing event logic.
            for key, custom, base in (('vehicles', ArenaVehiclesPlugin, plugins.ArenaVehiclesPlugin),
                                      ('personal', PersonalEntriesPlugin, plugins.PersonalEntriesPlugin)):
                native = args.get(key)
                if native is base:
                    args[key] = custom
                elif isinstance(native, type) and issubclass(native, base) and not issubclass(native, custom):
                    args[key] = type('driftkings' + native.__name__, (custom, native), {})
    except Exception as err:
        LOG.error(repr(err))
    return args


def getBattleViews():
    return ((AS_BATTLE, MinimapEnhancementsView, config),)


def fini():
    controller.dispose()
