# -*- coding: utf-8 -*-
import weakref
from math import degrees

import BigWorld
from account_helpers.settings_core import settings_constants
from gui.Scaleform.daapi.view.battle.shared.minimap import plugins
from gui.Scaleform.daapi.view.battle.shared.minimap.component import MinimapComponent
from gui.Scaleform.daapi.view.battle.shared.minimap.settings import CIRCLE_TYPE, CIRCLE_STYLE, VIEW_RANGE_CIRCLES_AS3_DESCR
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from Driftkings._constants import BATTLE_ALIASES
from Driftkings._constants import GLOBAL, MINIMAP_PLUGINS
from Driftkings.common import hexToDecimal, logError, xvmInstalled, battle_range
from Driftkings.common.utils.game import checkKeys
from Driftkings.core import minimap as policy
from Driftkings.core.callbacks import callback, cancelCallback
from Driftkings.core.hooks import override
from Driftkings.core.keyboard import keyboard
from Driftkings.settings.service import settings_service
from Driftkings.ui import g_events
from Driftkings.settings.templates.battle.minimap import MinimapPluginsSettings as Settings

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
        settings_service.onModSettingsChanged.connect(self.onModSettingsChanged, MINIMAP_PLUGINS)

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
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] or not settings_service.getComponentDict(self.config)[MINIMAP_PLUGINS.PRESENTATION]['alternativeEnabled']:
            self.setAlternative(False)
        changed = set(settings)
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_PLUGINS.YAW, MINIMAP_PLUGINS.LINES,
                                 MINIMAP_PLUGINS.CIRCLES, MINIMAP_PLUGINS.VIEW_RADIUS,
                                 MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES, MINIMAP_PLUGINS.COLOR_DRAW_CIRCLE,
                                 MINIMAP_PLUGINS.COLOR_MAX_VIEW_CIRCLE, MINIMAP_PLUGINS.COLOR_MIN_SPOTTING_CIRCLE,
                                 MINIMAP_PLUGINS.COLOR_VIEW_CIRCLE)):
            for plugin in list(PERSONAL):
                plugin.refreshPresentation()
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_PLUGINS.LABELS, MINIMAP_PLUGINS.PRESENTATION,
                                 MINIMAP_PLUGINS.SHOW_NAMES, MINIMAP_PLUGINS.SHOW_LAST_POSITIONS,
                                 MINIMAP_PLUGINS.LAST_POSITION_DURATION, MINIMAP_PLUGINS.LOST_MARKER,
                                 MINIMAP_PLUGINS.PERMANENT_MINIMAP_DEATH)):
            for plugin in list(VEHICLES):
                plugin.refreshLabels()
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_PLUGINS.PRESENTATION, MINIMAP_PLUGINS.ZOOM_FACTOR,
                                 MINIMAP_PLUGINS.ZOOM_FACTOR_MAX, MINIMAP_PLUGINS.ICONS, MINIMAP_PLUGINS.HEALTH,
                                 MINIMAP_PLUGINS.LOST_MARKER, MINIMAP_PLUGINS.MAP_SIZE, MINIMAP_PLUGINS.CIRCLES,
                                 MINIMAP_PLUGINS.EXTRA_CIRCLES, MINIMAP_PLUGINS.LABELS, MINIMAP_PLUGINS.LINES,
                                 MINIMAP_PLUGINS.ARTILLERY_AIM, MINIMAP_PLUGINS.SHOW_VEHICLE_TYPES)):
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
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] or not self._active:
            return
        self.setAlternative(bool(settings_service.getComponentDict(self.config)[MINIMAP_PLUGINS.PRESENTATION]['alternativeEnabled'] and checkKeys(settings_service.getComponentDict(self.config)[MINIMAP_PLUGINS.BUTTON])))


config = Settings()
controller = MinimapController(config)


from Driftkings.views.battle.minimap import MinimapCentredView


class PersonalEntriesPlugin(plugins.PersonalEntriesPlugin):

    def _invoke(self, entryID, method, *args):
        result = super(PersonalEntriesPlugin, self)._invoke(entryID, method, *args)
        if method.startswith('as_'):
            if not hasattr(self, '_ranges'):
                self._ranges = {'width': 1000, 'height': 1000, 'circles': {}, 'vehicleClass': getattr(self, '_vehicleClass', None)}
            ranges = self._ranges
            add = {'as_addDrawRange': 'draw', 'as_addDynamicViewRange': 'view', 'as_addMaxViewRage': 'maxView', 'as_addMinSpottingRange': 'proximity'}
            remove = {'as_delDrawRange': 'draw', 'as_delDynRange': 'view', 'as_delMaxViewRage': 'maxView', 'as_delMinSpottingRange': 'proximity'}
            if method == 'as_initArenaSize':
                ranges.update(width=args[0], height=args[1])
            elif method in add:
                ranges['circles'][add[method]] = dict(color=args[0], alpha=args[1], radius=args[2])
            elif method in remove:
                ranges['circles'].pop(remove[method], None)
            elif method == 'as_removeAllCircles':
                ranges['circles'].clear()
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

    def _refreshYawLimits(self):
        info = self._arenaDP.getVehicleInfo()
        if getattr(self, '_vehicleClass', None) != info.vehicleType.classTag:
            self._vehicleClass = info.vehicleType.classTag
            if hasattr(self, '_ranges'):
                self._ranges['vehicleClass'] = self._vehicleClass
                for view in list(VIEWS):
                    view.onRanges(self._ranges)
        limits = info.vehicleType.turretYawLimits
        extended = settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.YAW]
        updated = (degrees(limits[0]), degrees(limits[1])) if limits is not None and (extended or info.isSPG()) else None
        if updated != self.__yawLimits:
            self.__clearYawLimit()
            self.__yawLimits = updated

    def stop(self):
        PERSONAL.discard(self)
        super(PersonalEntriesPlugin, self).stop()

    def refreshPresentation(self):
        self._refreshYawLimits()
        self.__removeAllCircles()
        self.setSettings()

    def _invalidateMarkup(self, *args, **kwargs):
        self._refreshYawLimits()
        return super(PersonalEntriesPlugin, self)._invalidateMarkup(*args, **kwargs)

    def updateSettings(self, diff):
        super(PersonalEntriesPlugin, self).updateSettings(diff)
        self.refreshPresentation()

    def setSettings(self):
        super(PersonalEntriesPlugin, self).setSettings()
        if self.__isAlive and not self.__isObserver:
            direction = self.settingsCore.getSetting(settings_constants.GAME.SHOW_VECTOR_ON_MAP)
            sector = self.settingsCore.getSetting(settings_constants.GAME.SHOW_SECTOR_ON_MAP)
            if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
                direction = policy.visible(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LINES]['direction'], direction)
                sector = policy.visible(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LINES]['sector'], sector)
            self._updateDirectionLine(direction)
            self._updateYawLimits(sector)

    def __showDirectionLine(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LINES]['direction'] == 'off':
            return super(PersonalEntriesPlugin, self).__hideDirectionLine()
        return super(PersonalEntriesPlugin, self).__showDirectionLine()

    def __setupYawLimit(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LINES]['sector'] == 'off':
            return super(PersonalEntriesPlugin, self).__clearYawLimit()
        return super(PersonalEntriesPlugin, self).__setupYawLimit()

    def _circleVisible(self, key, native):
        return policy.visible(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CIRCLES][key]['mode'], native) if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else native

    def _canShowDrawRangeCircle(self):
        return self._circleVisible('draw', super(PersonalEntriesPlugin, self)._canShowDrawRangeCircle())

    def _canShowMaxViewRangeCircle(self):
        return self._circleVisible('maxView', super(PersonalEntriesPlugin, self)._canShowMaxViewRangeCircle())

    def _canShowMinSpottingRangeCircle(self):
        return self._circleVisible('proximity', super(PersonalEntriesPlugin, self)._canShowMinSpottingRangeCircle())

    def _canShowViewRangeCircle(self):
        return self._circleVisible('view', super(PersonalEntriesPlugin, self)._canShowViewRangeCircle())

    def _calcCircularVisionRadius(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.VIEW_RADIUS]:
            vehAttrs = self.sessionProvider.shared.feedback.getVehicleAttrs()
            return vehAttrs.get('circularVisionRadius', self._arenaVisitor.getVisibilityMinRadius())
        # noinspection PyProtectedMember
        return super(PersonalEntriesPlugin, self)._calcCircularVisionRadius()

    def __addDrawRangeCircle(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.DRAW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.DRAW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_DRAW_CIRCLE,(hexToDecimal(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.COLOR_DRAW_CIRCLE]) if settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.DRAW_RANGE), settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CIRCLES]['draw']['alpha'], self._arenaVisitor.getVehicleCircularAoiRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addDrawRangeCircle()

    def __addMaxViewRangeCircle(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MAX_VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MAX_VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_VIEW_CIRCLE,(hexToDecimal(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.COLOR_MAX_VIEW_CIRCLE]) if settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.MAX_VIEW_RANGE), settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CIRCLES]['maxView']['alpha'], self._arenaVisitor.getVisibilityMaxRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addMaxViewRangeCircle()

    def __addMinSpottingRangeCircle(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MIN_SPOTTING_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MIN_SPOTTING_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MIN_SPOTTING_CIRCLE,(hexToDecimal(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.COLOR_MIN_SPOTTING_CIRCLE]) if settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.MIN_SPOTTING_RANGE), settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CIRCLES]['proximity']['alpha'], self._arenaVisitor.getVisibilityMinRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addMinSpottingRangeCircle()

    def __addViewRangeCircle(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            if self.__circlesVisibilityState & CIRCLE_TYPE.VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_DYN_CIRCLE,(hexToDecimal(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.COLOR_VIEW_CIRCLE]) if settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES] else CIRCLE_STYLE.COLOR.VIEW_RANGE), settings_service.getComponentDict(config)[MINIMAP_PLUGINS.CIRCLES]['view']['alpha'], self._getViewRangeRadius())
        else:
            return super(PersonalEntriesPlugin, self).__addViewRangeCircle()


class ArenaVehiclesPlugin(plugins.ArenaVehiclesPlugin):
    def __init__(self, *args, **kwargs):
        self._health = {}
        self._presentations = {}
        self._identities = {}
        super(ArenaVehiclesPlugin, self).__init__(*args, **kwargs)
        self._nativeDestroyed = (self.__showDestroyEntries, self.__isDestroyImmediately)
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.PERMANENT_MINIMAP_DEATH]:
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

    def _hideVehicle(self, entry):
        self._expiredPositions.discard(entry.getID())
        result = super(ArenaVehiclesPlugin, self)._hideVehicle(entry)
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.SHOW_LAST_POSITIONS] and entry.isAlive() and entry.isEnemy() and entry.getMatrix() is not None:
            # The base plugin freezes the matrix at the last observed position.
            # Use its existing Flash entry, rather than a nonexistent setLastPosition API.
            wasActive = entry.isActive()
            if entry.setActive(True):
                self._setActive(entry.getID(), True)
            duration = max(0.0, float(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LAST_POSITION_DURATION]))
            self._lastPositions[entry.getID()] = (entry, BigWorld.time() + duration, wasActive)
            if self._running and self._lastPositionCallback is None:
                self._lastPositionCallback = callback(0.25, self.updateLastPositions)
        for vehicleID, saved in self._entries.items():
            if saved is entry:
                self.refreshLabel(vehicleID, entry)
                break
        return result

    def __setDestroyed(self, vehicleID, entry):
        self._lastPositions.pop(entry.getID(), None)
        self._expiredPositions.discard(entry.getID())
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.PERMANENT_MINIMAP_DEATH] and self.__isDestroyImmediately:
            self._setInAoI(entry, True)
        super(ArenaVehiclesPlugin, self).__setDestroyed(vehicleID, entry)
        self.refreshLabel(vehicleID, entry)

    def __setActive(self, entry, active):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.SHOW_LAST_POSITIONS] and entry.getID() in self._expiredPositions and not entry.isInAoI():
            active = False
        return super(ArenaVehiclesPlugin, self).__setActive(entry, active)

    def _getDisplayedName(self, vInfo):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return super(ArenaVehiclesPlugin, self)._getDisplayedName(vInfo)
        if not vInfo.isAlive() and not settings_service.getComponentDict(config)[MINIMAP_PLUGINS.SHOW_NAMES]:
            return ''
        entry = self._entries.get(vInfo.vehicleID)
        state = 'dead' if not vInfo.isAlive() else 'lost' if entry and entry.getID() in self._lastPositions else 'alive'
        values = {'vehicle': vInfo.getDisplayedName(), 'name': vInfo.player.name,
                  'level': vInfo.vehicleType.level, 'type': vInfo.vehicleType.classTag, 'state': state}
        return policy.label(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LABELS], values, controller.minimapZoom)

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
        group = 'squad' if 'squad' in gui.lower() else 'enemy' if entry.isEnemy() else 'ally'
        lost = self._lastPositions.get(entry.getID())
        state = 'dead' if not info.isAlive() else 'lost' if lost else 'alive'
        age = max(0, int(BigWorld.time() - (lost[1] - settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LAST_POSITION_DURATION]))) if lost else 0
        current, maximum = self._health.get(vehicleID, (None, info.vehicleType.maxHealth))
        if state == 'dead':
            current = 0
        values = dict(vehicle=info.getDisplayedName(), name=info.player.name, level=info.vehicleType.level,
                      type=info.vehicleType.classTag, state=state, group=group, lostSeconds=age)
        values.update(policy.health_values(current, maximum))
        text = policy.label(settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LABELS], values, controller.minimapZoom)
        if state == 'dead' and not settings_service.getComponentDict(config)[MINIMAP_PLUGINS.SHOW_NAMES]:
            text = ''
        if state == 'lost' and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LOST_MARKER]['showSeconds']:
            text += ' [%ss]' % age
        opacity = 100
        if state == 'lost' and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LOST_MARKER]['fade']:
            minimum = settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LOST_MARKER]['minimumAlpha']
            opacity = max(minimum, 100 - (100 - minimum) * age / float(max(1, settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LAST_POSITION_DURATION])))
        payload = dict(id=vehicleID, text=text, group=group, guiLabel=gui, state=state, hp=values['hp'],
                       percent=values['hpPercent'], alpha=opacity)
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
        self.__showDestroyEntries, self.__isDestroyImmediately = self._nativeDestroyed
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.PERMANENT_MINIMAP_DEATH]:
            self.__showDestroyEntries = self.__isDestroyImmediately = True
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED] or not settings_service.getComponentDict(config)[MINIMAP_PLUGINS.SHOW_LAST_POSITIONS]:
            for entry, expires, wasActive in self._lastPositions.values():
                if entry.isAlive() and not entry.isInAoI() and entry.setActive(wasActive):
                    self._setActive(entry.getID(), wasActive)
            self._lastPositions.clear()
            self._expiredPositions.clear()
        for vehicleID, entry in list(self._entries.items()):
            self.refreshLabel(vehicleID, entry)

    def updateLastPositions(self):
        self._lastPositionCallback = None
        if not self._running:
            return
        now = BigWorld.time()
        updateLabels = self._lastLostSecond != int(now)
        self._lastLostSecond = int(now)
        enabled = settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MINIMAP_PLUGINS.SHOW_LAST_POSITIONS]
        for entryID, (entry, expires, wasActive) in list(self._lastPositions.items()):
            if not entry.isAlive() or entry.isInAoI() or not entry.getID():
                self._lastPositions.pop(entryID, None)
            elif not enabled or now >= expires:
                if enabled:
                    self._expiredPositions.add(entryID)
                active = wasActive if not enabled else False
                if entry.setActive(active):
                    self._setActive(entryID, active)
                self._lastPositions.pop(entryID, None)
            elif updateLabels and (settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LOST_MARKER]['showSeconds'] or settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LOST_MARKER]['fade'] or '{{lostSeconds' in settings_service.getComponentDict(config)[MINIMAP_PLUGINS.LABELS]['lost']):
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
        allowedMode = arenaVisitor.gui.guiType in battle_range
        if not xvmInstalled and allowedMode:
            # Preserve mode-specific subclasses rather than replacing event logic.
            for key, custom, base in (('vehicles', ArenaVehiclesPlugin, plugins.ArenaVehiclesPlugin),
                                      ('personal', PersonalEntriesPlugin, plugins.PersonalEntriesPlugin)):
                native = args.get(key)
                if native is base:
                    args[key] = custom
                elif isinstance(native, type) and issubclass(native, base) and not issubclass(native, custom):
                    args[key] = type('Driftkings' + native.__name__, (custom, native), {})
    except Exception as err:
        logError(config.ID, repr(err))
    finally:
        return args


def getBattleViews():
    return ((AS_BATTLE, MinimapCentredView, config),)


def fini():
    controller.dispose()
