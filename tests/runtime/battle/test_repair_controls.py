# -*- coding: utf-8 -*-
"""Repair controls: kit detection, repair priority, gold kit use and safety guards."""
import copy
import json
import os

from support import Event, RuntimeTest, Settings, game_source, module

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
with open(os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'repair_controls.json'), 'rb') as stream:
    DEFAULTS = json.loads(stream.read().decode('utf-8-sig'))


class Kit(object):
    def __init__(self, marker, entities=(), ready=True):
        self.marker, self.entities = marker, list(entities)
        self.isReady = self.isAvailableToUse = ready

    def getMarker(self):
        return self.marker

    def getEntitiesIterator(self):
        return iter(self.entities)


class Equipments(object):
    def __init__(self, kits):
        self.kits, self.used = kits, []
        self.onEquipmentUpdated = Event()

    def iterEquipmentsByTag(self, tag):
        return [(cd, kit) for cd, (kitTag, kit) in sorted(self.kits.items()) if kitTag == tag]

    def hasEquipment(self, cd):
        return cd in self.kits

    def getEquipment(self, cd):
        return self.kits[cd][1]

    def changeSetting(self, cd, entityName=None, avatar=None):
        self.used.append((cd, entityName))
        return True, None


class RepairControlsTests(RuntimeTest):
    def setUp(self):
        super(RepairControlsTests, self).setUp()
        self.data = copy.deepcopy(DEFAULTS)
        self.states = {'fire': False, 'stun': False}
        self.controlling = 5
        self.replay = module(isPlaying=False)
        self.keys = set()
        self.api, _ = game_source('battle/repair_controls.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'gui.battle_control.battle_constants': module(DEVICE_STATE_DESTROYED='destroyed', DEVICE_STATE_NORMAL='normal',
                                                          VEHICLE_VIEW_STATE=module(FIRE='fire', STUN='stun')),
            'gui.shared.gui_items': module(Vehicle=module(getVehicleClassTag=lambda tags: 'heavyTank')),
            'BattleReplay': module(g_replayCtrl=self.replay),
            'driftkings.core.callbacks': module(callback=lambda delay, function: None, cancelCallback=lambda handle: None),
            'driftkings.common.utils.game': module(checkKeys=lambda keys: str(keys) in self.keys),
            'gui.shared.personality': module(ServicesLocator=module(appLoader=module(getDefBattleApp=lambda: True))),
        }, real=('driftkings._constants',))
        self.repair = self.api['Repair']()

    def battle(self, **kits):
        equipments = Equipments(kits)
        vehicle_state = module(getStateValue=lambda state: self.states[state], getControllingVehicleID=lambda: self.controlling)
        self.repair.player = module(getVehicleAttached=lambda: module(id=5),
                                    vehicleTypeDescriptor=module(type=module(tags=frozenset(('heavyTank',)))))
        self.repair.ctrl = module(equipments=equipments, vehicleState=vehicle_state)
        self.repair._refreshEquipmentCache()
        return equipments

    def test_regular_and_gold_kits_are_found_by_marker(self):
        regular, gold = Kit('smallRepairkit'), Kit('largeRepairkit')
        self.battle(cd9=('repairkit', gold), cd1=('repairkit', regular), cd5=('medkit', Kit('unknown')))
        items = self.repair.items
        self.assertEqual(items['repairkit'][0:4], ['cd1', 'cd9', regular, gold])
        # Without a known marker the first kit is treated as the regular one.
        self.assertEqual(items['medkit'][0], 'cd5')
        self.assertIsNone(items['medkit'][3])

    def test_devices_are_repaired_in_the_configured_priority_order(self):
        self.data['useGoldKits'] = False
        kit = Kit('smallRepairkit', [('engine', 'critical'), ('radio', 'critical'), ('turretRotator', 'critical'), ('gun', 'normal')])
        equipments = self.battle(cd1=('repairkit', kit))
        self.repair.repair('repairkit')
        # Heavy tank priority: turret ring before engine; the radio is not in the list.
        self.assertEqual(equipments.used, [('cd1', 'turretRotator')])

    def test_track_and_crew_slots_map_to_their_priority_names(self):
        self.data['useGoldKits'] = False
        medkit = Kit('smallMedkit', [('radioman1', 'critical'), ('loader2', 'critical')])
        equipments = self.battle(cd2=('medkit', medkit))
        self.repair.repair('medkit')
        self.assertEqual(equipments.used, [('cd2', 'loader2')])

    def test_gold_kit_repairs_everything_when_several_devices_are_damaged(self):
        gold = Kit('largeRepairkit', [('engine', 'critical'), ('gun', 'destroyed')])
        equipments = self.battle(cd1=('repairkit', Kit('smallRepairkit')), cd9=('repairkit', gold))
        self.repair.repair('repairkit')
        self.assertEqual(equipments.used, [('cd9', None)])
        gold.entities = [('gun', 'critical')]
        self.repair.repair('repairkit')
        self.assertEqual(equipments.used[-1], ('cd9', 'gun'))

    def test_regular_kit_falls_back_to_gold_only_when_allowed(self):
        busy = Kit('smallRepairkit', ready=False)
        equipments = self.battle(cd1=('repairkit', busy), cd9=('repairkit', Kit('largeRepairkit')))
        self.repair.useItem('repairkit', 'engine')
        self.assertEqual(equipments.used, [('cd9', 'engine')])
        self.data['useGoldKits'] = False
        self.repair.useItem('repairkit', 'engine')
        self.assertEqual(len(equipments.used), 1)

    def test_fire_stun_and_chassis(self):
        self.data['useGoldKits'] = False
        tracks = Kit('smallRepairkit', [('leftTrack0', 'destroyed'), ('engine', 'destroyed')])
        equipments = self.battle(cd1=('repairkit', tracks), cd3=('extinguisher', Kit('handExtinguishers')),
                                 cd4=('medkit', Kit('smallMedkit')))
        self.states.update(fire=True, stun=True)
        self.repair.extinguishFire()
        self.repair.removeStun()
        self.repair.repairChassis()
        self.assertEqual(equipments.used, [('cd3', None), ('cd4', None), ('cd1', 'leftTrack0')])

    def test_repair_key_runs_only_the_enabled_actions(self):
        self.data.update(extinguishFire=False, healCrew=False, removeStun=False, restoreChassis=False, useGoldKits=False)
        kit = Kit('smallRepairkit', [('engine', 'critical')])
        equipments = self.battle(cd1=('repairkit', kit), cd3=('extinguisher', Kit('handExtinguishers')))
        self.states['fire'] = True
        self.keys.add(str(self.data['buttonRepair']))
        self.repair.onHotkeyPressed(module(isKeyDown=lambda: True))
        self.assertEqual(equipments.used, [('cd1', 'engine')])

    def test_guards_block_disabled_replay_and_foreign_vehicles(self):
        self.data['useGoldKits'] = False
        equipments = self.battle(cd3=('extinguisher', Kit('handExtinguishers')))
        self.states['fire'] = True
        self.controlling = 9
        self.repair.extinguishFire()
        self.controlling = 5
        self.replay.isPlaying = True
        self.repair.extinguishFire()
        self.replay.isPlaying = False
        self.data['enabled'] = False
        self.repair.extinguishFire()
        self.assertEqual(equipments.used, [])
        self.data['enabled'] = True
        self.repair.extinguishFire()
        self.assertEqual(equipments.used, [('cd3', None)])

    def test_stopping_the_battle_forgets_the_kits(self):
        self.battle(cd1=('repairkit', Kit('smallRepairkit')))
        self.repair.stopBattle()
        self.assertEqual([self.repair.items[tag][2:] for tag in sorted(self.repair.items)], [[None, None]] * 3)
        self.assertIsNone(self.repair.ctrl)
