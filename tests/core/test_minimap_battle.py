# -*- coding: utf-8 -*-
"""Minimap vehicles plugin: last positions, expiry, spotting again and labels, on a stub of the native plugin."""
import copy

from support import RuntimeTest, module, source
from test_minimap import defaults


class Entry(object):
    def __init__(self, entryID, enemy=True):
        self.entryID = entryID
        self.enemy = enemy
        self.alive = True
        self.inAoI = True
        self.active = True

    def getID(self):
        return self.entryID

    def isEnemy(self):
        return self.enemy

    def isAlive(self):
        return self.alive

    def isInAoI(self):
        return self.inAoI

    def isActive(self):
        return self.active

    def getMatrix(self):
        return object()

    def setActive(self, active):
        changed = self.active != active
        self.active = active
        return changed


class MinimapVehiclesTests(RuntimeTest):
    def setUp(self):
        super(MinimapVehiclesTests, self).setUp()
        self.now = 100.0
        self.data = dict(copy.deepcopy(defaults()), enabled=True)
        self.callbacks = []
        self.published = []
        test = self

        class NativeVehicles(object):
            def __init__(self, *args, **kwargs):
                self._entries = {}
                self._arenaDP = test.arena
                self._ArenaVehiclesPlugin__showDestroyEntries = False
                self._ArenaVehiclesPlugin__isDestroyImmediately = False
                self.invoked = []
                self.activated = []

            def start(self):
                pass

            def stop(self):
                pass

            def _showVehicle(self, vehicleID, location):
                self._entries[vehicleID].inAoI = True

            def _hideVehicle(self, entry):
                entry.inAoI = False

            def _setInAoI(self, entry, isInAoI):
                entry.inAoI = isInAoI

            def _setActive(self, entryID, active):
                self.activated.append((entryID, active))

            def _invoke(self, entryID, method, *args):
                self.invoked.append((entryID, method) + args)

            def _setVehicleInfo(self, vehicleID, entry, vInfo, guiProps, isSpotted=False):
                pass

            def _getGuiPropsName(self, props):
                return props

        NativeVehicles.__name__ = 'ArenaVehiclesPlugin'
        class NativePersonal(object):
            def _calcCircularVisionRadius(self):
                return 445

        signal = module(connect=lambda *args: None, disconnect=lambda *args: None)
        service = module(onModSettingsChanged=signal, getComponentDict=lambda config: self.data)
        self.info = module(isAlive=lambda: True, team=2, player=module(name='Enemy'), getDisplayedName=lambda: 'IS-7',
                           vehicleType=module(level=10, classTag='heavyTank', maxHealth=2400, compactDescr=1))
        self.arena = module(getVehicleInfo=lambda vehicleID=None: self.info,
                            getPlayerGuiProps=lambda vehicleID, team: 'enemy')
        policy = self.load('core.minimap')
        deps = {
            'BigWorld': module(time=lambda: self.now),
            'account_helpers.settings_core': module(settings_constants=module()),
            'gui.Scaleform.daapi.view.battle.shared.minimap': module(plugins=module(
                ArenaVehiclesPlugin=NativeVehicles, PersonalEntriesPlugin=NativePersonal)),
            'gui.Scaleform.daapi.view.battle.shared.minimap.component': module(MinimapComponent=object),
            'gui.Scaleform.daapi.view.battle.shared.minimap.settings': module(
                CIRCLE_TYPE=module(), CIRCLE_STYLE=module(), VIEW_RANGE_CIRCLES_AS3_DESCR=module()),
            'helpers': module(dependency=module(descriptor=lambda interface: None)),
            'skeletons.gui.battle_session': module(IBattleSessionProvider=object),
            'driftkings.common.utils.formatting': module(hexToDecimal=lambda value: value),
            'driftkings.common.utils.wgutils': module(hasCompetingMarkers=lambda: False, getBattleTypes=lambda: ()),
            'driftkings.common.utils.game': module(checkKeys=lambda keys: False),
            'driftkings.core': module(minimap=policy),
            'driftkings.core.callbacks': module(callback=lambda delay, function: self.callbacks.append(function) or len(self.callbacks),
                                                cancelCallback=lambda handle: None),
            'driftkings.core.hooks': module(override=lambda *args: (lambda function: function)),
            'driftkings.core.keyboard': module(keyboard=module(subscribe=lambda handler: None, unsubscribe=lambda handler: None)),
            'driftkings.settings.service': module(settings_service=service),
            'driftkings.ui': module(g_events=module(onAltKey=lambda pressed: None)),
            'driftkings.settings.definitions.battle.minimap_enhancements': module(MinimapEnhancementsSettings=object),
            'driftkings.flash.batalha.minimap_enhancements': module(MinimapEnhancementsView=object),
        }
        self.api = source('battle/minimap_enhancements.py', deps)
        self.api['VIEWS'].add(self)
        self.plugin = self.api['ArenaVehiclesPlugin']()
        self.plugin.start()
        self.entry = Entry(7)
        self.plugin._entries[5] = self.entry

    def onVehicleData(self, payload):
        self.published.append(payload)

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

    def tick(self, seconds):
        self.now += seconds
        pending, self.callbacks[:] = list(self.callbacks), []
        for function in pending:
            function()

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
