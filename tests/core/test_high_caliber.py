# -*- coding: utf-8 -*-
"""Exercise the real damage handlers and projection without the WoT client."""
import json
import os
import ast

from support import ROOT, RuntimeTest, module, source


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
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player),
            'driftkings.core.battle_events': module(battleEvents=self.events),
            'driftkings.core.hooks': module(override=identity, on_event=identity),
            'driftkings.settings.service': module(settings_service=self.service),
            'driftkings.settings.definitions.battle.high_caliber_progress': module(HighCaliberProgressSettings=object),
            'driftkings.views.battle.high_caliber_gameface': module(MainGunAdapter=object),
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


    def test_gameface_lifecycle_visibility_position_and_localized_payload(self):
        class Model(object):
            def __init__(self, **kwargs):
                self._initialize()

            def _initialize(self):
                pass

            def _addStringProperty(self, *args):
                pass

            def _addCommand(self, name):
                return Signal()

        class View(object):
            def __init__(self, layoutID, model):
                self.model = model()

            def getViewModel(self):
                return self.model

            def _onLoaded(self):
                pass

            def _getEvents(self):
                return ()

            def _getListeners(self):
                return ()

            def _finalize(self):
                pass

            def setEnabled(self, enabled):
                self.enabled = enabled

            def destroy(self):
                self._finalize()

        class Parent(object):
            child = None

            def getChildView(self, resource):
                return self.child

        hooks, published, attached = {}, [], []

        def override(cls, name):
            def decorate(fn):
                hooks[name] = fn
                return fn
            return decorate

        def publish(child, payload):
            # Real publish_card already has deduplication coverage elsewhere.
            if child._lastPayload != payload:
                child._lastPayload = payload
                published.append(payload)

        with open(os.path.join(ROOT, 'mod/res/mods/driftkings/text/pt.yml'), 'rb') as stream:
            catalog = self.load('core.locale_catalog').parse_catalog(stream.read())['TEXT']
        component = module(config=module(lang='pt', i18n=catalog['high_caliber_progress']), mainGuns=self.gun)
        ui = module(attach_assets=lambda *args: None, resource_id=lambda path: 42)
        deps = {
            'importlib': module(import_module=lambda name: component),
            'driftkings._constants': self.constants,
            'driftkings.core.hud_visibility': module(hudVisibility=module(
                attach=lambda obj: attached.append(obj), detach=lambda obj: attached.remove(obj))),
            'driftkings.settings.service': module(settings_service=self.service),
            'driftkings.views.hangar.common': module(publish_card=publish),
            'driftkings.views.marks_model': module(moved_panel=self.load('views.marks_model').moved_panel,
                                                  finite=lambda value: None if value == 'bad' else float(value),
                                                  number_locale=lambda lang: {'groupSeparator': u'\u00a0'}),
            'gui.impl.battle.random.hud': module(RandomHUDView=Parent),
            'frameworks.wulf': module(ViewModel=Model),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.shared': module(events=module(GameEvent=module(GUI_VISIBILITY=1, SHOW_CURSOR=2, HIDE_CURSOR=3)),
                                 EVENT_BUS_SCOPE=module(BATTLE=1, GLOBAL=2)),
            'driftkings.core.hooks': module(override=override),
            'driftkings.ui.gameface': ui,
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {'resource': 'test'}),
            'GUI': module(mcursor=lambda: module(visible=False)),
        }
        base = source('views/battle/common.py', deps)
        base['setattr'] = lambda target, name, value: setattr(target, name, value)
        deps['driftkings.views.battle.common'] = module(BattleCardAdapter=base['BattleCardAdapter'])
        adapter = source('views/battle/high_caliber_gameface.py', deps)['MainGunAdapter']()
        adapter.install()
        adapter.install()
        self.assertEqual(len(attached), 1)
        parent = Parent()
        factories = hooks['_getChildComponents'](lambda parent: {3: 'native'}, parent)
        self.assertEqual(factories[3], 'native')
        child = factories[42]()
        parent.child = child
        child._onLoaded()
        self.assertTrue(published[-1]['config']['visible'])
        self.assertFalse(published[-1]['config']['draggable'])
        self.assertEqual(published[-1]['primaryText'], u'4\u00a0000 HP')
        self.assertEqual(len(child._getEvents()), 1)
        before = len(published)
        adapter.refresh()
        self.assertEqual(len(published), before)
        child._showCursor(None)
        self.assertTrue(published[-1]['config']['draggable'])
        child._savePosition({'x': 99999, 'y': -99999})
        self.assertEqual(self.applied[-1]['textPosition']['x'], 7680)
        self.assertEqual(self.applied[-1]['textPosition']['alignX'], 'left')
        self.settings['textLock'] = True
        child._savePosition({'x': 10, 'y': 10})
        self.assertEqual(len(self.applied), 1)
        adapter.setBattleHudVisible(False)
        self.assertFalse(published[-1]['config']['visible'])
        adapter.setBattleHudVisible(True)
        # A stale renderer key must never switch off the only presentation.
        self.settings['renderer'] = 'legacy'
        adapter.refresh()
        self.assertTrue(published[-1]['config']['visible'])
        self.gun.playersDamage(1, 10, 1, 1)
        adapter.refresh()
        self.assertEqual(published[-1]['primaryText'], catalog['high_caliber_progress']['UI_hc_unavailable'])
        adapter.dispose()
        self.assertEqual(attached, [])
        self.assertEqual(len(adapter.views), 0)
        self.assertFalse(child.enabled)
