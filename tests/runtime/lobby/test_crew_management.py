# -*- coding: utf-8 -*-
"""Crew management: automatic crew return, its exceptions and the per-vehicle ignore list."""
import json
import os
import shutil
import tempfile

from support import RuntimeTest, Settings, game_source, module


class Vehicle(object):
    def __init__(self, invID=10, intCD=100, premium=False, crewFull=False, inBattle=False, locked=False, lastCrew=(1,)):
        self.invID, self.intCD, self.isPremium = invID, intCD, premium
        self.isCrewFull, self.isInBattle, self.isLocked, self.lastCrew = crewFull, inBattle, locked, list(lastCrew)
        self.isInInventory = True


class CrewManagementTests(RuntimeTest):
    def setUp(self):
        super(CrewManagementTests, self).setUp()
        self.folder = tempfile.mkdtemp(prefix='dk-crew-test-')
        self.addCleanup(shutil.rmtree, self.folder)
        self.data = {'enabled': True, 'crewAutoReturn': True, 'crewReturnByDefault': True, 'autoReturnDelay': 0.5,
                     'excludePremiumVehicles': True, 'showNotifications': True}
        self.scheduled, self.messages = [], []
        self.vehicle = Vehicle()
        self.tankmen = {1: module(isInTank=True, vehicleInvID=20)}
        self.vehicles = {20: Vehicle(invID=20)}
        current = module(isPresent=lambda: self.vehicle is not None, item=None, isInHangar=lambda: True,
                         isInBattle=lambda: self.vehicle.isInBattle, isLocked=lambda: self.vehicle.isLocked,
                         isCrewFull=lambda: self.vehicle.isCrewFull)
        self.current = current
        items = module(getTankman=lambda invID: self.tankmen.get(invID), getVehicle=lambda invID: self.vehicles.get(invID),
                       getItemByCD=lambda cd: self.vehicle if cd == self.vehicle.intCD else None)
        self.api, self.hooks = game_source('lobby/crew_management.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'BigWorld': module(wg_getPreferencesFilePath=lambda: os.path.join(self.folder, 'preferences.xml')),
            'external_strings_utils': module(unicode_from_utf8=lambda path: (path, path)),
            'CurrentVehicle': module(g_currentVehicle=current),
            'driftkings.core.callbacks': module(callback=lambda delay, function: self.scheduled.append(delay) or len(self.scheduled),
                                                cancelCallback=lambda handle: None),
            'driftkings.common.utils.exceptions': module(log_exceptions=lambda function: function),
            'gui': module(SystemMessages=module(pushMessage=lambda text, type=None: self.messages.append(text),
                                                pushI18nMessage=lambda text, type=None: self.messages.append(text),
                                                SM_TYPE=module(Warning='warning', Information='info'))),
            'driftkings.settings.definitions.lobby.crew_management': module(
                CrewManagementSettings=lambda: module(i18n={'UI_message_crewNotAvailable': 'not available'})),
        }, real=('driftkings._constants', 'driftkings.common.utils.filesystem'), extra_builtins={'unicode': str})
        self.crew = self.api['g_crew']
        self.crew.itemsCache = module(items=items)
        self.returned = []
        self.crew.processReturnCrew = lambda print_message=True: self.returned.append('current')
        self.crew.processReturnCrewForVehicleSelectorPopup = lambda vehicle: self.returned.append(vehicle.invID)

    def select(self, vehicle):
        self.vehicle = vehicle
        self.current.item = vehicle
        self.crew.handleVehicleChange()

    def stored(self):
        with open(os.path.join(self.folder, 'driftkings', 'auto_prev_crew.json'), 'rb') as stream:
            return json.loads(stream.read().decode('utf-8'))['vehicles']

    def test_ignore_list_is_created_empty(self):
        self.assertEqual(self.stored(), [])
        self.assertEqual(self.api['ignored_vehicles'], set())

    def test_changing_vehicle_schedules_one_return(self):
        self.select(Vehicle(intCD=100))
        self.select(Vehicle(intCD=100))
        self.select(Vehicle(invID=11, intCD=101))
        self.assertEqual(self.scheduled, [0.5, 0.5])

    def test_premium_ignored_and_disabled_vehicles_are_skipped(self):
        self.select(Vehicle(intCD=1, premium=True))
        self.crew.toggleAutoReturnForCurrentVehicle()
        self.select(Vehicle(invID=10, intCD=2))
        self.data['crewReturnByDefault'] = False
        self.select(Vehicle(invID=12, intCD=3))
        self.data.update(crewReturnByDefault=True, enabled=False)
        self.select(Vehicle(invID=13, intCD=4))
        self.assertEqual(self.scheduled, [])

    def test_toggle_updates_the_stored_ignore_list(self):
        self.current.item = self.vehicle
        self.assertFalse(self.crew.toggleAutoReturnForCurrentVehicle())
        self.assertEqual(self.stored(), ['10'])
        self.assertTrue(self.crew.toggleAutoReturnForCurrentVehicle())
        self.assertEqual(self.stored(), [])
        self.assertEqual(self.messages, ['Auto-return disabled for this vehicle', 'Auto-return enabled for this vehicle'])

    def test_return_only_when_the_last_crew_is_free(self):
        self.current.item = self.vehicle
        self.crew.returnCrew()
        self.assertEqual(self.returned, ['current'])
        self.vehicles[20].isLocked = True
        self.crew.returnCrew()
        self.assertEqual((self.returned, self.messages), (['current'], ['not available']))
        self.vehicle.isCrewFull = True
        self.vehicles[20].isLocked = False
        self.crew.returnCrew()
        self.assertEqual(self.returned, ['current'])

    def test_popup_selection_returns_the_crew_once(self):
        self.current.item = self.vehicle
        self.crew.handlePopupSelect([str(self.vehicle.intCD)])
        self.assertEqual(self.returned, [10])
        # The following vehicle change for that vehicle does not schedule a second return.
        self.select(self.vehicle)
        self.assertEqual(self.scheduled, [])
        self.crew.handlePopupSelect(['1', '2'])
        self.vehicle.isPremium = True
        self.crew.handlePopupSelect([str(self.vehicle.intCD)])
        self.assertEqual(self.returned, [10])
