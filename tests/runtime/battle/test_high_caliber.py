# -*- coding: utf-8 -*-
"""Exercise the real damage handlers and projection without the WoT client."""
import json
import os
import ast

from support import ROOT, RuntimeTest, gameface_core, module, source


class Signal(object):
    def __init__(self):
        self.handlers = []

    def connect(self, handler, *args):
        if handler not in self.handlers:
            self.handlers.append(handler)

    def disconnect(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    def __iadd__(self, handler):
        self.connect(handler)
        return self

    def __isub__(self, handler):
        self.disconnect(handler)
        return self


class HighCaliberTests(RuntimeTest):
    def setUp(self):
        super(HighCaliberTests, self).setUp()
        self.project = self.load('core.high_caliber').project
        with open(os.path.join(ROOT, 'res/configs/driftkings/default/high_caliber_progress.json'), 'rb') as stream:
            self.settings = json.load(stream)
        # Behaviour tests run with the module enabled; the shipped default is off (Phase 11.6).
        self.settings['enabled'] = True
        self.allowed = True
        self.applied = []
        self.player = module(arena=module(guiType=1, onVehicleAdded=Signal(), onVehicleUpdated=Signal()),
                             playerVehicleID=1, team=1, onVehicleEnterWorld=Signal())
        self.player.guiSessionProvider = module(getArenaDP=lambda: module(getEnemyTeams=lambda: [2]))
        names = dict(NAME='high_caliber_progress', HIGH_CALIBER_PROGRESS='mainGun', FORMAT='format',
                     BACK_GROUND_ENABLED='backGroundEnabled', TEXT_LOCK='textLock',
                     TEXT_POSITION='textPosition', BACKGROUND='background', SHADOW='shadow')
        self.constants = module(GLOBAL=module(ENABLED='enabled'), HIGH_CALIBER_PROGRESS=module(**names))
        self.service = module(getComponentDict=lambda cfg: self.settings, onModSettingsChanged=Signal(),
                              apply=lambda cfg, changes: self.applied.append(changes))
        self.events = module(**dict((name, Signal()) for name in ('started', 'loaded', 'ended', 'killed', 'healthDetailed')))
        self.owners = []
        self.events.acquire = lambda owner: self.owners.append(owner)
        self.events.release = lambda owner: self.owners.remove(owner)
        identity = lambda *args: lambda fn: fn
        self.deps = {
            'Vehicle': module(Vehicle=object),
            'constants': module(ARENA_GUI_TYPE=module(RANDOM=1, EPIC_RANDOM=2)),
            'driftkings.core.battle_policy': module(battle_policy=module(decision=lambda name: (self.allowed, ''))),
            'gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator': module(RibbonsAggregator=object),
            'gui.battle_control.arena_info': module(vos_collections=module(
                VehiclesInfoCollection=lambda: module(iterator=lambda dp: []))),
            'gui.battle_control.battle_constants': module(FEEDBACK_EVENT_ID=module(PLAYER_DAMAGED_HP_ENEMY=10)),
            'driftkings._constants': self.constants,
            'BigWorld': module(player=lambda: self.player),
            'driftkings.common.utils.wgutils': module(create_range=source('common/utils/wgutils.py', {'BigWorld': module()})['create_range']),
            'driftkings.core.battle_events': module(battleEvents=self.events),
            'driftkings.core.hooks': module(override=identity, on_event=identity),
            'driftkings.settings.service': module(settings_service=self.service),
            'driftkings.settings.definitions.battle.high_caliber_progress': module(HighCaliberProgressSettings=object),
            'driftkings.gameface.battle.high_caliber_gameface': module(MainGunAdapter=object),
        }
        self.api = source('battle/high_caliber_progress.py', self.deps)
        self.gun, self.scl = self.api['mainGuns'], self.api['scl']
        self.prepare()

    def prepare(self):
        self.scl.inBattle = True
        self.scl.guiType = 1
        self.scl.playerID = 1
        self.scl.enemyTeam = 2
        self.scl.health = {2: [20000, 20000]}
        self.gun.battleLoading()

    def feedback(self, damage):
        event = module(getType=lambda: 10, getExtra=lambda: module(getDamage=lambda: damage))
        self.gun.onPlayerFeedbackReceived([event])

    def test_initial_target_minimum_rounding_and_progress(self):
        self.assertEqual(self.gun.payload['target'], 4000)
        self.assertEqual(self.gun.payload['remaining'], 4000)
        self.assertEqual(self.gun.payload['progress'], 0)
        self.scl.health[2] = [5001, 5001]
        self.gun.battleLoading()
        self.assertEqual(self.gun.payload['target'], 1001)
        self.scl.health[2] = [100, 100]
        self.gun.battleLoading()
        self.assertEqual(self.gun.payload['target'], 1000)

    def test_damage_and_dynamic_competition_can_regress_after_achievement(self):
        self.feedback(4000)
        self.assertEqual(self.gun.payload['state'], 'achieved')
        self.gun.playersDamage(2, 5000, 1, 2)
        self.assertEqual(self.gun.payload['state'], 'progress')
        self.assertEqual(self.gun.payload['remaining'], 1000)
        self.assertEqual(self.gun.payload['progress'], 80)
        self.feedback(1500)
        self.assertEqual(self.gun.payload['state'], 'achieved')
        self.assertEqual(self.gun.payload['progress'], 100)

    def test_static_target_still_refreshes_damage(self):
        self.settings['mainGun']['dynamic'] = False
        self.gun.playersDamage(2, 7000, 1, 2)
        self.feedback(1000)
        self.assertEqual(self.gun.payload['target'], 4000)
        self.assertEqual(self.gun.payload['remaining'], 3000)
        self.assertEqual(self.gun.payload['progress'], 25)

    def test_friendly_damage_is_sticky_and_not_reset_by_more_damage(self):
        self.gun.playersDamage(1, 10, 1, 1)
        self.assertEqual(self.gun.payload['reason'], 'ineligible')
        self.feedback(9000)
        self.assertFalse(self.gun.payload['eligible'])
        self.assertEqual(self.gun.payload['state'], 'unavailable')

    def test_insufficient_enemy_hp_including_zero(self):
        self.feedback(2000)
        self.scl.health[2][0] = 1999
        self.gun.updateMainGun()
        self.assertEqual(self.gun.payload['reason'], 'insufficient')
        self.scl.health[2][0] = 0
        self.gun.updateMainGun()
        self.assertEqual(self.gun.payload['state'], 'unavailable')

    def test_health_before_feedback_does_not_double_count_own_damage(self):
        self.scl.health[2][0] = 3900
        self.gun.playersDamage(1, 100, 2, 1)
        self.assertEqual(self.gun.payload['state'], 'progress')
        self.assertEqual(self.gun.payload['damage'], 0)
        self.feedback(100)
        self.assertEqual(self.gun.payload['remaining'], 3900)
        self.assertEqual(self.gun.payload['damage'], 100)

    def test_death_and_end_reset_and_new_battle(self):
        self.feedback(1000)
        self.scl._onVehicleKilled(1)
        self.assertEqual(self.gun.payload['reason'], 'destroyed')
        self.scl.destroyBattle()
        self.assertFalse(self.gun.payload['visible'])
        self.prepare()
        self.assertEqual(self.gun.payload['damage'], 0)
        self.assertEqual(self.gun.players_damage, {})
        self.assertFalse(self.gun.destroyed)

    def test_disabled_and_disallowed_modes_hide_without_stale_values(self):
        self.settings['enabled'] = False
        self.scl.onSettingsChanged(None, {})
        self.assertFalse(self.gun.payload['visible'])
        self.settings['enabled'] = True
        self.allowed = False
        self.gun.updateMainGun()
        self.assertFalse(self.gun.payload['visible'])
        self.allowed = True
        self.scl.guiType = 99
        self.gun.updateMainGun()
        self.assertFalse(self.gun.payload['visible'])

    def test_subscriptions_are_idempotent_and_cleaned(self):
        self.scl.inBattle = False
        self.scl.start()
        self.scl.start()
        self.assertEqual(len(self.events.started.handlers), 1)
        self.assertEqual(len(self.owners), 1)
        self.scl.stop()
        self.scl.stop()
        self.assertEqual(self.owners, [])
        self.assertEqual(self.events.started.handlers, [])

    def test_projection_limits_and_achieved_after_death(self):
        value = self.project(1000, 0, 1200, True, False, False, 0)
        self.assertEqual(value['state'], 'achieved')
        self.assertEqual(value['progress'], 100)
        self.assertEqual(value['remaining'], 0)
        self.assertEqual(self.project(0, 0, 0, True, False, True, None)['progress'], 0)
