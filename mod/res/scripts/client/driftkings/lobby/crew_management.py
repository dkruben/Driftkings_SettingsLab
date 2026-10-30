# -*- coding: utf-8 -*-
from io import open
import json
import os

import BigWorld
from CurrentVehicle import g_currentVehicle
from external_strings_utils import unicode_from_utf8
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.cyberSport.VehicleSelectorPopup import VehicleSelectorPopup
from gui.shared.gui_items.processors.tankman import TankmanReturn, TankmanUnload
from gui.shared.utils import decorators
from gui.shared.utils.requesters import REQ_CRITERIA
from helpers import dependency
from skeletons.gui.app_loader import GuiGlobalSpaceID
from skeletons.gui.shared import IItemsCache

from driftkings._constants import CREW_MANAGEMENT, GLOBAL
from driftkings.common.utils.exceptions import log_exceptions
from driftkings.common.utils.filesystem import atomicWrite, recoverFile
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.core.hooks import override
from driftkings.settings.definitions.lobby.crew_management import CrewManagementSettings as Settings
from driftkings.settings.service import settings_service


def getCachePath():
    path = os.path.join(os.path.normpath(os.path.dirname(unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1])), 'driftkings')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def encodeData(data):
    if isinstance(data, dict):
        return {encodeData(key): encodeData(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [encodeData(element) for element in data]
    elif isinstance(data, (str, unicode)):
        return data.encode('utf-8')
    else:
        return data


def openJsonFile(path):
    recoverFile(path)
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as dataFile:
        return encodeData(json.load(dataFile, encoding='utf-8'))


def writeJsonFile(path, data):
    encoded = unicode(json.dumps(data, skipkeys=True, ensure_ascii=False, indent=2, sort_keys=True)).encode('utf-8')
    atomicWrite(path, encoded)
    return True


def openIgnoredVehicles():
    path = os.path.join(getCachePath(), 'auto_prev_crew.json')
    if not os.path.exists(path):
        writeJsonFile(path, {'vehicles': []})
        return set()
    data = openJsonFile(path)
    return set(data.get('vehicles', []))


def updateIgnoredVehicles(vehicles):
    global ignored_vehicles
    path = os.path.join(getCachePath(), 'auto_prev_crew.json')
    if isinstance(vehicles, (str, unicode)):
        vehicles_set = ignored_vehicles.copy()
        vehicles_set.add(vehicles)
        vehicles = vehicles_set
    ignored_vehicles = set(str(vehicle_id) for vehicle_id in vehicles)
    return writeJsonFile(path, {'vehicles': sorted(ignored_vehicles)})


def removeIgnoredVehicle(vehicle_id):
    global ignored_vehicles
    vehicles_set = ignored_vehicles.copy()
    if str(vehicle_id) in vehicles_set:
        vehicles_set.remove(str(vehicle_id))
        ignored_vehicles = vehicles_set
        return writeJsonFile(os.path.join(getCachePath(), 'auto_prev_crew.json'), {'vehicles': sorted(vehicles_set)})
    return False


ignored_vehicles = openIgnoredVehicles()
config = Settings()


class Crew(object):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.intCD = None
        self.__callbackID = None
        self.__skipNextAutoReturnInvID = None
        self.last_operation_time = 0

    def init(self):
        if g_currentVehicle.isPresent():
            vehicle = g_currentVehicle.item
            self.intCD = vehicle.intCD

    def invalidate(self):
        self.intCD = None
        self.__skipNextAutoReturnInvID = None
        if self.__callbackID is not None:
            cancelCallback(self.__callbackID)
            self.__callbackID = None

    @decorators.adisp_process('crewReturning')
    def processReturnCrew(self, print_message=True):
        if not g_currentVehicle.isPresent():
            return
        result = yield TankmanReturn(g_currentVehicle.item).request()
        if result and result.userMsg and print_message and settings_service.getComponentDict(config)[CREW_MANAGEMENT.SHOW_NOTIFICATIONS]:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.adisp_process('crewReturning')
    def processReturnCrewForVehicleSelectorPopup(self, vehicle):
        if vehicle and not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
            yield TankmanReturn(vehicle).request()

    @decorators.adisp_process('unloading')
    def processUnloadCrew(self):
        if not g_currentVehicle.isPresent():
            return
        result = yield TankmanUnload(g_currentVehicle.item.invID).request()
        if result and result.userMsg and settings_service.getComponentDict(config)[CREW_MANAGEMENT.SHOW_NOTIFICATIONS]:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def handleVehicleChange(self):
        settings = settings_service.getComponentDict(config)
        if not settings[GLOBAL.ENABLED]:
            return
        if settings[CREW_MANAGEMENT.CREW_AUTO_RETURN] and settings[CREW_MANAGEMENT.CREW_RETURN_BY_DEFAULT]:
            if self.__callbackID is not None:
                cancelCallback(self.__callbackID)
                self.__callbackID = None
            if not g_currentVehicle.isPresent():
                return
            vehicle = g_currentVehicle.item
            intCD = vehicle.intCD
            if settings[CREW_MANAGEMENT.EXCLUDE_PREMIUM_VEHICLES] and vehicle.isPremium:
                return
            if self.__skipNextAutoReturnInvID == vehicle.invID:
                self.__skipNextAutoReturnInvID = None
                self.intCD = intCD
                return
            if str(vehicle.invID) in ignored_vehicles:
                self.intCD = intCD
                return
            if intCD != self.intCD:
                self.__callbackID = callback(settings[CREW_MANAGEMENT.AUTO_RETURN_DELAY], self.returnCrew)
                self.intCD = intCD

    @log_exceptions
    def handlePopupSelect(self, items):
        settings = settings_service.getComponentDict(config)
        if not items or not settings[GLOBAL.ENABLED] or not settings[CREW_MANAGEMENT.CREW_AUTO_RETURN]:
            return
        if len(items) == 1:
            cd = int(items[0])
            vehicle = self.itemsCache.items.getItemByCD(cd)
            if vehicle and vehicle.isInInventory and not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
                if settings[CREW_MANAGEMENT.EXCLUDE_PREMIUM_VEHICLES] and vehicle.isPremium:
                    return
                self.__skipNextAutoReturnInvID = vehicle.invID
                self.processReturnCrewForVehicleSelectorPopup(vehicle)

    def isLastCrewAvailable(self):
        if not g_currentVehicle.isPresent():
            return False
        vehicle = g_currentVehicle.item
        lastCrewIDs = vehicle.lastCrew
        if lastCrewIDs is None:
            return False
        for lastTankmenInvID in lastCrewIDs:
            actualLastTankman = self.itemsCache.items.getTankman(lastTankmenInvID)
            if actualLastTankman is not None and actualLastTankman.isInTank:
                lastTankmanVehicle = self.itemsCache.items.getVehicle(actualLastTankman.vehicleInvID)
                if lastTankmanVehicle and lastTankmanVehicle.isLocked:
                    return False
        return True

    def returnCrew(self):
        self.__callbackID = None
        if not g_currentVehicle.isPresent():
            return
        if not g_currentVehicle.isInHangar() or g_currentVehicle.isInBattle() or g_currentVehicle.isLocked() or g_currentVehicle.isCrewFull():
            return
        if str(g_currentVehicle.item.invID) in ignored_vehicles:
            return
        if not self.isLastCrewAvailable():
            if settings_service.getComponentDict(config)[CREW_MANAGEMENT.SHOW_NOTIFICATIONS]:
                SystemMessages.pushMessage(config.i18n['UI_message_crewNotAvailable'], type=SystemMessages.SM_TYPE.Warning)
            return
        self.processReturnCrew()

    def toggleAutoReturnForCurrentVehicle(self):
        settings = settings_service.getComponentDict(config)
        if not g_currentVehicle.isPresent():
            return False
        vehicle_id = str(g_currentVehicle.item.invID)
        if vehicle_id in ignored_vehicles:
            removeIgnoredVehicle(vehicle_id)
            if settings[CREW_MANAGEMENT.SHOW_NOTIFICATIONS]:
                SystemMessages.pushMessage('Auto-return enabled for this vehicle', type=SystemMessages.SM_TYPE.Information)
            return True
        else:
            updateIgnoredVehicles(vehicle_id)
            if settings[CREW_MANAGEMENT.SHOW_NOTIFICATIONS]:
                SystemMessages.pushMessage("Auto-return disabled for this vehicle", type=SystemMessages.SM_TYPE.Information)
            return False

    def getCrewInfo(self):
        if not g_currentVehicle.isPresent():
            return None
        vehicle = g_currentVehicle.item
        crew_info = {'vehicle_name': vehicle.userName, 'crew_complete': vehicle.isCrewFull, 'crew_members': []}
        for slotIdx, tankman in vehicle.crew:
            if tankman is not None:
                crew_info['crew_members'].append({'name': tankman.fullUserName, 'role': tankman.roleUserName, 'level': tankman.level, 'skills': [skill.userName for skill in tankman.skills]})
            else:
                crew_info['crew_members'].append(None)
        return crew_info

    def returnAllCrews(self):
        vehicles = self.itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY)
        for vehicle in vehicles.values():
            if str(vehicle.invID) in ignored_vehicles:
                continue
            if settings_service.getComponentDict(config)[CREW_MANAGEMENT.EXCLUDE_PREMIUM_VEHICLES] and vehicle.isPremium:
                continue
            if not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
                self.processReturnCrewForVehicleSelectorPopup(vehicle)


g_crew = Crew()

from driftkings.gameface.lobby import crew_progression as progression_view

progression_view.install(config)


@override(VehicleSelectorPopup, 'onSelectVehicles')
@log_exceptions
def new__onSelectVehicles(func, self, items):
    func(self, items)
    g_crew.handlePopupSelect(items)


_lobbyActive = False


def onContextEntered(spaceID):
    global _lobbyActive
    if spaceID == GuiGlobalSpaceID.LOBBY and not _lobbyActive:
        _lobbyActive = True
        g_crew.init()
        progression_view.g_controller.start()
        g_currentVehicle.onChanged += _onChanged


def onContextLeft(spaceID):
    global _lobbyActive
    if spaceID == GuiGlobalSpaceID.LOBBY and _lobbyActive:
        _lobbyActive = False
        g_currentVehicle.onChanged -= _onChanged
        g_crew.invalidate()
        progression_view.g_controller.stop()


@log_exceptions
def _onChanged():
    g_crew.handleVehicleChange()


def fini():
    onContextLeft(GuiGlobalSpaceID.LOBBY)
