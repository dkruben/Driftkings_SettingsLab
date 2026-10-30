# -*- coding: utf-8 -*-
"""Native minimap plugin integration and lifecycle."""
from support.minimap import MinimapFixture, Entry
from support import module

class MinimapVehiclesTests(MinimapFixture):
    def test_view_radius_handles_missing_feedback_and_recovers(self):
        plugin = self.api['PersonalEntriesPlugin']()
        shared = module(feedback=None)
        plugin.sessionProvider = module(shared=shared)
        plugin._arenaVisitor = module(getVisibilityMinRadius=lambda: 50)
        self.data['viewRadius'] = True
        self.assertEqual(plugin._calcCircularVisionRadius(), 50)
        shared.feedback = module(getVehicleAttrs=lambda: None)
        self.assertEqual(plugin._calcCircularVisionRadius(), 50)
        shared.feedback = module(getVehicleAttrs=lambda: {})
        self.assertEqual(plugin._calcCircularVisionRadius(), 50)
        shared.feedback = module(getVehicleAttrs=lambda: {'circularVisionRadius': 470})
        self.assertEqual(plugin._calcCircularVisionRadius(), 470)
        self.data['viewRadius'] = False
        self.assertEqual(plugin._calcCircularVisionRadius(), 445)
        self.data.update(enabled=False, viewRadius=True)
        self.assertEqual(plugin._calcCircularVisionRadius(), 445)

    def test_lost_enemy_keeps_its_icon_and_label_until_spotted_again(self):
        self.plugin._hideVehicle(self.entry)
        self.assertIn(7, self.plugin._lastPositions)
        self.assertTrue(self.entry.isActive())
        self.assertIn((7, 'setInAoI', True), self.plugin.invoked)
        self.assertEqual(self.published[-1]['state'], 'lost')
        self.assertEqual(self.published[-1]['color'], self.data['lostMarker']['enemyColor'])
        # Duration 0: still kept after a long time, until the vehicle is seen again.
        self.tick(600)
        self.assertIn(7, self.plugin._lastPositions)
        self.plugin._setInAoI(self.entry, True)
        self.assertNotIn(7, self.plugin._lastPositions)
        self.assertEqual(self.published[-1]['state'], 'alive')

    def test_timed_last_position_expires_and_hides_the_entry(self):
        self.data['lastPositionDuration'] = 10
        self.plugin._hideVehicle(self.entry)
        self.tick(5)
        self.assertIn(7, self.plugin._lastPositions)
        self.tick(6)
        self.assertNotIn(7, self.plugin._lastPositions)
        self.assertIn(7, self.plugin._expiredPositions)
        self.assertFalse(self.entry.isActive())
        self.assertEqual(self.plugin.activated[-1], (7, False))
        self.assertEqual(self.callbacks, [])

    def test_allies_destroyed_and_disabled_option_leave_no_last_position(self):
        ally = Entry(8, enemy=False)
        self.plugin._entries[6] = ally
        self.plugin._hideVehicle(ally)
        self.assertNotIn(8, self.plugin._lastPositions)
        self.data['showLastPositions'] = False
        self.plugin._hideVehicle(self.entry)
        self.assertNotIn(7, self.plugin._lastPositions)
        self.data['showLastPositions'] = True
        self.entry.inAoI = True
        self.plugin._hideVehicle(self.entry)
        self.entry.alive = False
        self.tick(1)
        self.assertNotIn(7, self.plugin._lastPositions)

    def test_lost_seconds_fade_and_disable_restore_the_native_state(self):
        self.data['lostMarker'].update(showSeconds=True, fade=True)
        self.plugin._hideVehicle(self.entry)
        self.tick(30)
        payload = self.published[-1]
        self.assertTrue(payload['text'].endswith(' [30s]'))
        self.assertLess(payload['alpha'], 100)
        self.assertGreaterEqual(payload['alpha'], self.data['lostMarker']['minimumAlpha'])
        self.data['showLastPositions'] = False
        self.plugin.refreshLabels()
        self.assertEqual(self.plugin._lastPositions, {})
        self.assertIn((7, 'setInAoI', False), self.plugin.invoked)
        self.assertEqual(self.published[-1]['state'], 'alive')

    def test_stop_clears_every_tracked_position(self):
        self.plugin._hideVehicle(self.entry)
        self.plugin.stop()
        self.assertEqual((self.plugin._lastPositions, self.plugin._expiredPositions), ({}, set()))
        self.assertNotIn(self.plugin, self.api['VEHICLES'])
