# -*- coding: utf-8 -*-
import random
from functools import partial

import BattleReplay
import SoundGroups
from gui import TANKMEN_ROLES_ORDER_DICT
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.battle_control.battle_constants import DEVICE_STATE_AS_DAMAGE
from gui.battle_control.battle_constants import DEVICE_STATE_DESTROYED, VEHICLE_VIEW_STATE, DEVICE_STATE_NORMAL
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.shared.gui_items import Vehicle
from gui.shared.personality import ServicesLocator

from Driftkings._constants import GLOBAL, REPAIR_EXTENDED
from Driftkings.common import checkKeys, getPlayer
from Driftkings.core.callbacks import callback, cancelCallback
from Driftkings.core.keyboard import keyboard
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.repair import RepairExtendedSettings as ConfigInterface

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


config = ConfigInterface()


class Repair(object):

    def __init__(self):
        self.player = None
        self.ctrl = None
        self.consumablesPanel = None
        self.battleStarted = False
        self._battleCheckCallback = None
        self._inputBound = False
        self.pendingAutoCallbacks = {}
        self.items = {
            'extinguisher': [251, 251, None, None],
            'medkit': [763, 1019, None, None],
            'repairkit': [1275, 1531, None, None]
        }
        self.base_markers = {
            'extinguisher': set(['handExtinguishers']),
            'medkit': set(['smallMedkit']),
            'repairkit': set(['smallRepairkit'])
        }
        self.gold_markers = {
            'extinguisher': set(['autoExtinguishers']),
            'medkit': set(['largeMedkit']),
            'repairkit': set(['largeRepairkit'])
        }
        self.complex_item = {
            'leftTrack0': 'chassis',
            'rightTrack0': 'chassis',
            'leftTrack1': 'chassis',
            'rightTrack1': 'chassis',
            'gunner1': 'gunner',
            'gunner2': 'gunner',
            'radioman1': 'radioman',
            'radioman2': 'radioman',
            'loader1': 'loader',
            'loader2': 'loader',
            'wheel0': 'wheel',
            'wheel1': 'wheel',
            'wheel2': 'wheel',
            'wheel3': 'wheel',
            'wheel4': 'wheel',
            'wheel5': 'wheel',
            'wheel6': 'wheel',
            'wheel7': 'wheel'
        }
        self.chassis = ['chassis', 'leftTrack', 'rightTrack', 'leftTrack0', 'rightTrack0', 'leftTrack1', 'rightTrack1', 'wheel', 'wheel0', 'wheel1', 'wheel2', 'wheel3', 'wheel4', 'wheel5', 'wheel6', 'wheel7']
        self._active = False

    def start(self):
        if self._active:
            return
        self._active = True
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_UNREGISTERED, self.__onComponentUnregistered, EVENT_BUS_SCOPE.GLOBAL)

    def stop(self):
        if not self._active:
            return
        self._active = False
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_UNREGISTERED, self.__onComponentUnregistered, EVENT_BUS_SCOPE.GLOBAL)
        self.stopBattle()

    def startBattle(self):
        self.player = getPlayer()
        if self.player is None or not hasattr(self.player, 'guiSessionProvider'):
            return
        self.ctrl = self.player.guiSessionProvider.shared
        if self.ctrl is None or self.battleStarted:
            return
        self.battleStarted = True
        self._bindInputHandlers()
        # auto use
        if self.ctrl.vehicleState is not None:
            self.ctrl.vehicleState.onVehicleStateUpdated += self.autoUse
        # update equipments
        if self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated += self.onEquipmentUpdated
        self.checkBattleStarted()

    def stopBattle(self):
        if self._battleCheckCallback is not None:
            cancelCallback(self._battleCheckCallback)
            self._battleCheckCallback = None
        self._unbindInputHandlers()
        # auto use
        if self.ctrl is not None and self.ctrl.vehicleState is not None:
            self.ctrl.vehicleState.onVehicleStateUpdated -= self.autoUse
        # update equipments
        if self.ctrl is not None and self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated -= self.onEquipmentUpdated
        #
        self.battleStarted = False
        self._clearPendingAutoCallbacks()
        for equipment_tag in self.items:
            self.items[equipment_tag][2] = None
            self.items[equipment_tag][3] = None
        self.items['repairkit'][1] = 1531
        self.player = None
        self.ctrl = None
        self.consumablesPanel = None

    def checkBattleStarted(self):
        self._battleCheckCallback = None
        if self.ctrl is None or self.player is None:
            return
        if hasattr(self.player, 'arena') and self.player.arena and self.player.arena.period == 3:
            self._refreshEquipmentCache()
        else:
            self._battleCheckCallback = callback(0.1, self.checkBattleStarted)

    def useItem(self, equipment_tag, item=None):
        if not self._canUseConsumable():
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            self._activateEquipment(self.items[equipment_tag][0], item)
        else:
            if settings_service.getComponentDict(config)[REPAIR_EXTENDED.USE_GOLD_KITS]:
                equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
                if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
                    self._activateEquipment(self.items[equipment_tag][1], item)

    def useItemManual(self, equipment_tag, item=None):
        if not self._canUseConsumable(requireControl=True):
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            self._activateEquipment(self.items[equipment_tag][0], item)

    def useItemGold(self, equipment_tag, item=None):
        if not self._canUseConsumable(requireControl=True):
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            self._activateEquipment(self.items[equipment_tag][1], item)

    def extinguishFire(self):
        if self.ctrl is None:
            return
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.FIRE):
            equipment_tag = 'extinguisher'
            if self.items[equipment_tag][2]:
                self.useItemManual(equipment_tag)

    def removeStun(self):
        if self.ctrl is None:
            return
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.STUN):
            equipment_tag = 'medkit'
            if self.items[equipment_tag][2]:
                self.useItemManual(equipment_tag)
            elif settings_service.getComponentDict(config)[REPAIR_EXTENDED.USE_GOLD_KITS] and self.items[equipment_tag][3]:
                self.useItemGold(equipment_tag)

    def repair(self, equipment_tag):
        if self.ctrl is None or self.player is None:
            return
        specific = self._getRepairPriority(equipment_tag)
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.USE_GOLD_KITS] and self.items[equipment_tag][3]:
            equipment = self.items[equipment_tag][3]
            if equipment is not None:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in devices:
                    if device in self.complex_item:
                        itemName = self.complex_item[device]
                    else:
                        itemName = device
                    if itemName in specific:
                        result.append(device)
                if len(result) > 1:
                    self.useItemGold(equipment_tag)
                elif result:
                    self.useItemGold(equipment_tag, result[0])
        elif self.items[equipment_tag][2]:
            equipment = self.items[equipment_tag][2]
            if equipment is not None:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in devices:
                    if device in self.complex_item:
                        itemName = self.complex_item[device]
                    else:
                        itemName = device
                    if itemName in specific:
                        result.append(device)
                if result:
                    self.useItemManual(equipment_tag, result[0])

    def repairAll(self):
        if self.ctrl is None:
            return
        self_vehicle = self.player.getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.EXTINGUISH_FIRE]:
            self.extinguishFire()
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.REPAIR_DEVICES]:
            self.repair('repairkit')
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.HEAL_CREW]:
            self.repair('medkit')
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.REMOVE_STUN]:
            self.removeStun()
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.RESTORE_CHASSIS]:
            self.repairChassis()

    def onEquipmentUpdated(self, *_):
        self._refreshEquipmentCache()

    def repairChassis(self):
        if self.ctrl is None:
            return
        self_vehicle = self.player.getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        equipment_tag = 'repairkit'
        for intCD, equipment in self.ctrl.equipments.iterEquipmentsByTag(equipment_tag):
            if equipment.isReady and equipment.isAvailableToUse:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state == DEVICE_STATE_DESTROYED]
                for name in devices:
                    if name in self.chassis:
                        self.useItem(equipment_tag, name)
                        return

    def onHotkeyPressed(self, event):
        if ServicesLocator.appLoader.getDefBattleApp():
            if checkKeys(settings_service.getComponentDict(config)[REPAIR_EXTENDED.BUTTON_CHASSIS]) and event.isKeyDown():
                self.repairChassis()
            if checkKeys(settings_service.getComponentDict(config)[REPAIR_EXTENDED.BUTTON_REPAIR]) and event.isKeyDown():
                self.repairAll()

    def autoUse(self, state, value):
        if not settings_service.getComponentDict(config)[REPAIR_EXTENDED.AUTO_REPAIR]:
            return
        if not self._canUseConsumable(requireControl=True):
            return
        time = self._getAutoDelay()
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.EXTINGUISH_FIRE] and state == VEHICLE_VIEW_STATE.FIRE and bool(value):
            self._scheduleAutoUse('extinguisher', time)
            time += 0.1

        if state == VEHICLE_VIEW_STATE.DEVICES:
            for deviceName, deviceState in self._extractDeviceUpdates(value):
                if deviceState in DEVICE_STATE_AS_DAMAGE:
                    itemName = self.complex_item.get(deviceName, deviceName)
                    equipmentTag = 'medkit' if itemName in TANKMEN_ROLES_ORDER_DICT['enum'] else 'repairkit'
                    # noinspection PyTypeChecker
                    specific = self._getRepairPriority(equipmentTag)
                    if itemName in specific:
                        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.HEAL_CREW] and equipmentTag == 'medkit':
                            self._scheduleAutoUse('medkit', time, deviceName)
                        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.REPAIR_DEVICES] and equipmentTag == 'repairkit':
                            self._scheduleAutoUse('repairkit', time, deviceName)
                            time += 0.1

        stunDuration = getattr(value, 'duration', None)
        hasStun = stunDuration > 0 if stunDuration is not None else bool(value)
        if settings_service.getComponentDict(config)[REPAIR_EXTENDED.REMOVE_STUN] and state == VEHICLE_VIEW_STATE.STUN and hasStun:
            self._scheduleAutoUse('medkit', time)

    def _canUseConsumable(self, requireControl=False):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return False
        replayCtrl = getattr(BattleReplay, 'g_replayCtrl', None)
        if replayCtrl is not None and replayCtrl.isPlaying:
            return False
        if self.ctrl is None or self.player is None:
            return False
        self_vehicle = self.player.getVehicleAttached()
        if self_vehicle is None:
            return False
        if requireControl and (self.ctrl.vehicleState is None or self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id):
            return False
        return True

    def _activateEquipment(self, intCD, item=None):
        if self.ctrl is None or self.player is None:
            return False
        changeResult = self.ctrl.equipments.changeSetting(intCD, entityName=item, avatar=self.player)
        if isinstance(changeResult, tuple):
            result = bool(changeResult[0])
        else:
            result = bool(changeResult)
        if result:
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)
        return result

    def _scheduleAutoUse(self, equipment_tag, delay, item=None):
        if equipment_tag in self.pendingAutoCallbacks:
            cancelCallback(self.pendingAutoCallbacks.pop(equipment_tag))
        self.pendingAutoCallbacks[equipment_tag] = callback(delay, partial(self._processAutoUse, equipment_tag, item))

    def _processAutoUse(self, equipment_tag, item=None):
        self.pendingAutoCallbacks.pop(equipment_tag, None)
        if not settings_service.getComponentDict(config)[REPAIR_EXTENDED.AUTO_REPAIR] or not self._canUseConsumable(requireControl=True):
            return
        if self.items[equipment_tag][2] is None and self.items[equipment_tag][3] is None:
            self._refreshEquipmentCache()
        self.useItem(equipment_tag, item)

    def _clearPendingAutoCallbacks(self):
        for callbackID in self.pendingAutoCallbacks.values():
            cancelCallback(callbackID)
        self.pendingAutoCallbacks.clear()

    def _bindInputHandlers(self):
        if not self._inputBound:
            keyboard.subscribe(self.onHotkeyPressed)
            self._inputBound = True

    def _unbindInputHandlers(self):
        keyboard.unsubscribe(self.onHotkeyPressed)
        self._inputBound = False

    def _getRepairPriority(self, equipment_tag):
        vehicle_class = Vehicle.getVehicleClassTag(self.player.vehicleTypeDescriptor.type.tags)
        priorities = settings_service.getComponentDict(config)[REPAIR_EXTENDED.REPAIR_PRIORITY]
        class_priorities = priorities.get(vehicle_class, priorities['AllAvailableVariables'])
        return class_priorities[equipment_tag]

    def _refreshEquipmentCache(self):
        if self.ctrl is None or self.ctrl.equipments is None:
            return
        for equipment_tag in self.items:
            self.items[equipment_tag][2] = None
            self.items[equipment_tag][3] = None
            for intCD, equipment in self.ctrl.equipments.iterEquipmentsByTag(equipment_tag):
                marker = self._getEquipmentMarker(equipment)
                if marker in self.base_markers[equipment_tag] and self.items[equipment_tag][2] is None:
                    self.items[equipment_tag][0] = intCD
                    self.items[equipment_tag][2] = equipment
                    continue
                if marker in self.gold_markers[equipment_tag] and self.items[equipment_tag][3] is None:
                    self.items[equipment_tag][1] = intCD
                    self.items[equipment_tag][3] = equipment
                    continue
                if self.items[equipment_tag][2] is None:
                    self.items[equipment_tag][0] = intCD
                    self.items[equipment_tag][2] = equipment
                elif self.items[equipment_tag][3] is None:
                    self.items[equipment_tag][1] = intCD
                    self.items[equipment_tag][3] = equipment

    @staticmethod
    def _extractDeviceUpdates(value):
        updates = []
        if isinstance(value, dict):
            iterable = value.itervalues() if hasattr(value, 'itervalues') else value.values()
        elif isinstance(value, (list, tuple)):
            if len(value) >= 2 and isinstance(value[0], string_types):
                iterable = (value,)
            else:
                iterable = value
        else:
            iterable = ()

        for entry in iterable:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2 and isinstance(entry[0], string_types):
                updates.append((entry[0], entry[1]))
        return updates

    @staticmethod
    def _getAutoDelay():
        min_delay = settings_service.getComponentDict(config).get(REPAIR_EXTENDED.TIMER_MIN, 0.3)
        max_delay = settings_service.getComponentDict(config).get(REPAIR_EXTENDED.TIMER_MAX, 0.8)
        try:
            min_delay = float(min_delay)
        except (TypeError, ValueError):
            min_delay = 0.3
        try:
            max_delay = float(max_delay)
        except (TypeError, ValueError):
            max_delay = 0.8
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay
        return random.uniform(min_delay, max_delay)

    @staticmethod
    def _getEquipmentMarker(equipment):
        getter = getattr(equipment, 'getMarker', None)
        if callable(getter):
            return getter()
        return None

    def __onComponentRegistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.consumablesPanel = event.componentPy
            self.startBattle()

    def __onComponentUnregistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.stopBattle()


g_repairExtended = Repair()


def init():
    g_repairExtended.start()


def fini():
    g_repairExtended.stop()
