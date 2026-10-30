# -*- coding: utf-8 -*-
"""Own health bar: Gameface wherever the native Gameface HUD loads, Flash elsewhere."""
import re

from support import RuntimeTest, Settings, game_source, module

HUD = 'randomBattleHud'
# EU 2.4.1.1: VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE plus the Halloween extension page.
PAGES = {1: ('classicBattlePage', HUD), 21: ('rankedBattlePage', HUD), 100: ('halloweenBattlePage',)}


class GamefaceHudTests(RuntimeTest):
    def setUp(self):
        super(GamefaceHudTests, self).setUp()
        self.capabilities = self.load('core.battle_capabilities')

    def context(self, gui_type, arena=True, views=True):
        modules = {}
        if views:
            modules['gui.Scaleform.daapi.settings.views'] = module(
                VIEW_ALIAS=module(RANDOM_BATTLE_HUD=HUD), VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE=PAGES,
                RANDOM_BATTLE_PAGE_CONFIG=('classicBattlePage', HUD))
        visitor = module(getArenaGuiType=lambda: gui_type)
        return self.capabilities.BattleCapabilities(
            player=lambda: module(arena=module(bonusType=1) if arena else None),
            session=lambda: module(arenaVisitor=visitor), modules=modules)

    def test_pages_that_load_the_native_hud_use_gameface(self):
        self.assertTrue(self.context(1).has_gameface_hud())
        self.assertTrue(self.context(21).has_gameface_hud())
        # Unlisted modes fall back to the random page configuration, which includes the HUD.
        self.assertTrue(self.context(55).has_gameface_hud())

    def test_event_pages_without_the_native_hud_keep_flash(self):
        self.assertFalse(self.context(100).has_gameface_hud())
        self.assertFalse(self.context(1, arena=False).has_gameface_hud())
        self.assertFalse(self.context(1, views=False).has_gameface_hud())


class OwnHealthGamefaceTests(RuntimeTest):
    def setUp(self):
        super(OwnHealthGamefaceTests, self).setUp()
        self.settings = {'enabled': True, 'x': 0, 'y': -80, 'alignX': 'center', 'alignY': 'bottom',
                         'avgColor': {'brightness': 0.9, 'saturation': 0.7}}
        self.tracker = module(state={'current': 1860, 'maximum': 2400, 'alive': True, 'battle': True})
        component = module(config='vehicle_health', tracker=self.tracker)
        service = Settings(self.settings)
        self.applied = []
        service.apply = lambda config, values: self.applied.append((config, values))
        self.api, _ = game_source('gameface/battle/vehicle_health.py', {
            'importlib': module(import_module=lambda name: component),
            'driftkings.settings.service': service.service(),
            'driftkings.views.marks_model': self.load('views.marks_model'),
            'driftkings.common.utils.formatting': self.load('common.utils.formatting'),
            'driftkings.core.hud_visibility': module(hudVisibility=module(attach=lambda view: None, detach=lambda view: None)),
            'driftkings.gameface.battle.common': module(BattleCardAdapter=self.load('gameface.battle.common').BattleCardAdapter),
        }, real=('driftkings._constants',))
        self.adapter = self.api['OwnHealthAdapter']()
        self.published = []
        self.adapter.publish = lambda payload, config, enabled: self.published.append((payload, config, enabled))

    def test_payload_matches_the_bar_artwork_and_settings_position(self):
        self.adapter.startBattle()
        payload, config, enabled = self.published[-1]
        self.assertTrue(enabled)
        self.assertEqual(payload['text'], '1860 / 2400')
        self.assertAlmostEqual(payload['percent'], 0.775)
        self.assertTrue(re.match(r'^#[0-9A-F]{6}$', payload['color']), payload['color'])
        # Unlocked: the shared kit allows dragging only while the battle cursor is visible.
        self.assertEqual(config, {'x': 0, 'y': -80, 'alignX': 'center', 'alignY': 'bottom', 'locked': False})

    def test_bar_hides_outside_the_battle_period_after_death_and_when_disabled(self):
        self.adapter.refresh()
        self.assertFalse(self.published[-1][2])
        self.adapter.startBattle()
        for key, value in (('battle', False), ('alive', False), ('maximum', 0)):
            original = self.tracker.state[key]
            self.tracker.state[key] = value
            self.adapter.refresh()
            self.assertFalse(self.published[-1][2], key)
            self.tracker.state[key] = original
        self.settings['enabled'] = False
        self.adapter.refresh()
        self.assertFalse(self.published[-1][2])
        self.settings['enabled'] = True
        self.adapter.stopBattle()
        self.assertFalse(self.published[-1][2])


    def child(self, cursor=True, gui=True):
        return module(_cursorVisible=cursor, _guiVisible=gui)

    def test_dragged_position_is_saved_to_the_slider_settings(self):
        self.adapter.startBattle()
        self.adapter.savePosition(self.child(), {'x': 312.4, 'y': -2600, 'alignX': 'right', 'alignY': 'bottom'})
        self.assertEqual(self.applied, [('vehicle_health', {'x': 312, 'y': -2000, 'alignX': 'right', 'alignY': 'bottom'})])

    def test_position_is_not_saved_without_the_battle_cursor_or_outside_battle(self):
        args = {'x': 10, 'y': 10, 'alignX': 'left', 'alignY': 'top'}
        self.adapter.savePosition(self.child(), args)
        self.adapter.startBattle()
        self.adapter.savePosition(self.child(cursor=False), args)
        self.adapter.savePosition(self.child(gui=False), args)
        self.adapter.savePosition(self.child(), {'x': 'bad', 'y': 1})
        self.assertEqual(self.applied, [])

class HealthTrackerTests(RuntimeTest):
    def setUp(self):
        super(HealthTrackerTests, self).setUp()
        self.api, _ = game_source('battle/vehicle_health.py', real=('driftkings._constants',),
                                  extra_builtins={'long': int})
        self.tracker = self.api['HealthTracker']()
        self.refreshed = []
        self.tracker.listener = module(refresh=lambda: self.refreshed.append(dict(self.tracker.state)))

    def test_controlled_vehicle_and_damage_update_the_state(self):
        self.tracker.onVehicleControlling(module(maxHealth=2400, health=2400))
        self.assertEqual(self.refreshed[-1], {'current': 2400, 'maximum': 2400, 'alive': True, 'battle': False})
        self.tracker.setHealth(1860)
        self.assertEqual((self.refreshed[-1]['current'], self.refreshed[-1]['maximum']), (1860, 2400))
        self.tracker.setHealth(-50)
        self.assertEqual((self.refreshed[-1]['current'], self.refreshed[-1]['alive']), (0, False))
        self.tracker.setHealth('broken')
        self.assertEqual(self.refreshed[-1]['current'], 0)
