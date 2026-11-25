# -*- coding: utf-8 -*-
"""T-N1: native marks-of-excellence card (BattleMarksAdapter) on the real BattleCardAdapter contract.

Covers replay-policy gating, native attach and detach, locked and hidden guards, visibility and position
settings, and disposal. The panel clamp itself is covered by tests/runtime/core/test_panel_anchor.py; the
position test here checks that the adapter uses it. Only game boundaries are stubbed.
"""
from support import RuntimeTest, module, source


class Parent(object):
    """Host of the shared window: exposes the child under the card's resource id."""
    child = None

    def getChildView(self, resource):
        return self.child


class Child(object):
    """Native card view with the state BattleCardView keeps (common.py)."""
    def __init__(self):
        self._lastPayload = None
        self._guiVisible = True
        self._cursorVisible = False
        self._ready = True
        self._attached = False
        self._lastVisible = None
        self.enabled = True
        self.destroyed = False

    def setEnabled(self, value):
        self.enabled = value

    def destroy(self):
        self.destroyed = True


class MarksAdapterTests(RuntimeTest):
    def setUp(self):
        super(MarksAdapterTests, self).setUp()
        self.constants = self.load('_constants')
        self.GLOBAL = self.constants.GLOBAL
        self.KEY = self.constants.BATTLE_MARKS_OF_EXCELLENCE
        self.settings = source('settings/default_values.py', {})['DEFAULTS'][self.KEY.NAME]
        self.settings[self.GLOBAL.ENABLED] = True
        self.settings[self.KEY.SHOW_IN_REPLAY] = False
        self.settings[self.KEY.GAMEFACE]['locked'] = True
        self.replay = [False]
        self.applied = []
        self.published = []
        self.attached, self.detached = [], []
        self.marks = self.load('core.marks_state').marks_state
        self.marks.clear('battle')
        real_model = self.load('views.marks_model')
        signal = self.load('core.signals').Signal()
        component = module(battle_marks_of_excellence_settings=module(
            lang='en', i18n={'UI_description': 'Marks', 'UI_mog_title': 'Title'}))
        service = module(getComponentDict=lambda config: self.settings,
                         apply=lambda config, changes: self.applied.append(changes),
                         onModSettingsChanged=signal)
        catalog = {'driftkings.settings.service': module(settings_service=service),
                   'driftkings.gameface.payloads': module(
                       publish_card=lambda child, payload: self.published.append((child, payload))),
                   'driftkings.interface_catalog': module(gameface_spec=lambda feature: {
                       'resource': 'marks', 'transport': 'own_window'}),
                   'driftkings.gameface.core': module(resource_id=lambda path: 42)}
        base = source('gameface/battle/common.py', catalog)['BattleCardAdapter']
        deps = dict(catalog)
        deps.update({
            'driftkings.gameface.battle.common': module(BattleCardAdapter=base),
            'driftkings._constants': self.constants,
            'driftkings.core.marks_state': module(marks_state=self.marks),
            'driftkings.core.hud_visibility': module(hudVisibility=module(
                attach=lambda view: self.attached.append(view), detach=lambda view: self.detached.append(view))),
            'driftkings.views.marks_model': module(moved_panel=real_model.moved_panel,
                                                  number_locale=real_model.number_locale),
            'importlib': module(import_module=lambda name: component),
            'BattleReplay': module(isPlaying=lambda: self.replay[0]),
        })
        self.adapter = source('gameface/battle/battle_marks_of_excellence.py', deps)['BattleMarksAdapter']()
        self.parents = []

    def attach_card(self):
        """Register a ready, attached native child the way own_window.py registers hosted cards."""
        parent, child = Parent(), Child()
        self.adapter.views[parent] = child
        parent.child = child
        self.parents.append(parent)
        return parent, child

    def last(self):
        return self.published[-1][1]

    def live(self):
        self.adapter.startBattle()
        self.assertTrue(self.adapter.active)

    # Replay-policy gating

    def test_replay_without_show_in_replay_does_not_start_or_attach(self):
        self.replay[0] = True
        self.settings[self.KEY.SHOW_IN_REPLAY] = False
        self.adapter.startBattle()
        self.assertFalse(self.adapter.active)
        self.assertEqual(self.attached, [])

    def test_replay_with_show_in_replay_starts_and_attaches_once(self):
        self.replay[0] = True
        self.settings[self.KEY.SHOW_IN_REPLAY] = True
        self.adapter.startBattle()
        self.assertTrue(self.adapter.active)
        self.assertEqual(self.attached, [self.adapter])

    def test_live_battle_starts_regardless_of_the_replay_setting(self):
        self.settings[self.KEY.SHOW_IN_REPLAY] = False
        self.replay[0] = False
        self.live()
        self.assertEqual(self.attached, [self.adapter])

    def test_global_switch_off_blocks_start(self):
        self.settings[self.GLOBAL.ENABLED] = False
        self.adapter.startBattle()
        self.assertFalse(self.adapter.active)
        self.assertEqual(self.attached, [])

    # Native attachment and detachment

    def test_start_clears_previous_marks_and_a_second_start_does_nothing(self):
        self.marks.publish('battle', {'state': 'progress', 'vehicleId': 7})
        self.live()
        self.assertEqual(self.marks.snapshot('battle')['state'], 'unavailable')
        self.adapter.startBattle()
        self.assertEqual(self.attached, [self.adapter])

    def test_stop_detaches_clears_state_and_deactivates(self):
        self.live()
        self.marks.publish('battle', {'state': 'progress', 'vehicleId': 7})
        self.adapter.stopBattle()
        self.assertFalse(self.adapter.active)
        self.assertEqual(self.detached, [self.adapter])
        self.assertEqual(self.marks.snapshot('battle')['state'], 'unavailable')

    # Locked-state and hidden-state guards on position saves

    def test_locked_panel_refuses_position_saves(self):
        self.live()
        _, child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.KEY.GAMEFACE]['locked'] = True
        self.adapter.savePosition(child, {'x': 10, 'y': 20})
        self.assertEqual(self.applied, [])

    def test_unlocked_panel_with_visible_cursor_saves_the_dragged_position(self):
        self.live()
        _, child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.KEY.GAMEFACE]['locked'] = False
        self.adapter.savePosition(child, {'x': 10, 'y': 20})
        self.assertEqual(len(self.applied), 1)
        self.assertEqual(self.applied[-1][self.KEY.PANEL]['x'], 10)
        self.assertEqual(self.applied[-1][self.KEY.PANEL]['y'], 20)

    def test_hidden_card_cursor_or_hud_refuse_position_saves(self):
        self.live()
        self.settings[self.KEY.GAMEFACE]['locked'] = False
        _, child = self.attach_card()
        child._cursorVisible = False
        self.adapter.savePosition(child, {'x': 10, 'y': 20})
        child._cursorVisible = True
        child._guiVisible = False
        self.adapter.savePosition(child, {'x': 10, 'y': 20})
        child._guiVisible = True
        self.adapter.setBattleHudVisible(False)
        self.adapter.savePosition(child, {'x': 10, 'y': 20})
        self.assertEqual(self.applied, [])

    def test_inactive_card_refuses_position_saves(self):
        _, child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.KEY.GAMEFACE]['locked'] = False
        self.adapter.savePosition(child, {'x': 10, 'y': 20})
        self.assertEqual(self.applied, [])

    # Position settings: clamp through the shared panel model, anchors and invalid input

    def test_dragged_position_is_clamped_and_its_anchor_travels_with_it(self):
        self.live()
        _, child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.KEY.GAMEFACE]['locked'] = False
        self.adapter.savePosition(child, {'x': 99999, 'y': -99999, 'alignX': 'right', 'alignY': 'bottom'})
        panel = self.applied[-1][self.KEY.PANEL]
        self.assertEqual((panel['x'], panel['y']), (7680, -4320))
        self.assertEqual((panel['alignX'], panel['alignY']), ('right', 'bottom'))

    def test_unknown_anchor_and_non_numeric_position_are_ignored(self):
        self.live()
        _, child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.KEY.GAMEFACE]['locked'] = False
        self.adapter.savePosition(child, {'x': 'bad', 'y': 1})
        self.assertEqual(self.applied, [])
        self.adapter.savePosition(child, {'x': 5, 'y': 6, 'alignX': 'middle'})
        self.assertNotEqual(self.applied[-1][self.KEY.PANEL].get('alignX'), 'middle')

    # Visibility behaviour of the published card

    def test_visibility_follows_card_hud_and_battle_state(self):
        self.live()
        _, child = self.attach_card()
        self.adapter.refresh()
        self.assertTrue(self.last()['config']['visible'])
        self.assertFalse(self.last()['config']['draggable'])
        child._guiVisible = False
        self.adapter.refresh()
        self.assertFalse(self.last()['config']['visible'])
        child._guiVisible = True
        self.adapter.setBattleHudVisible(False)
        self.assertFalse(self.last()['config']['visible'])
        self.adapter.setBattleHudVisible(True)
        self.assertTrue(self.last()['config']['visible'])
        self.adapter.stopBattle()
        self.assertFalse(self.last()['config']['visible'])

    def test_draggable_requires_unlocked_panel_and_visible_cursor(self):
        self.live()
        _, child = self.attach_card()
        child._cursorVisible = True
        self.settings[self.KEY.GAMEFACE]['locked'] = True
        self.adapter.refresh()
        self.assertFalse(self.last()['config']['draggable'])
        self.settings[self.KEY.GAMEFACE]['locked'] = False
        self.adapter.refresh()
        self.assertTrue(self.last()['config']['draggable'])

    def test_published_config_carries_the_configured_panel_position(self):
        self.live()
        _, child = self.attach_card()
        self.adapter.refresh()
        config = self.last()['config']
        self.assertEqual(config['x'], self.settings[self.KEY.PANEL]['x'])
        self.assertEqual(config['y'], self.settings[self.KEY.PANEL]['y'])

    # Disposal

    def test_dispose_is_idempotent_and_releases_the_owned_child(self):
        self.live()
        _, child = self.attach_card()
        self.adapter.dispose()
        self.adapter.dispose()
        self.assertTrue(child.destroyed)
        self.assertEqual(self.detached, [self.adapter])
        self.assertEqual(len(self.adapter.views), 0)
        self.assertFalse(self.adapter.active)

    def test_dispose_keeps_a_foreign_replacement_child(self):
        self.live()
        parent, child = self.attach_card()
        foreign = Child()
        parent.child = foreign
        self.adapter.dispose()
        self.assertFalse(child.destroyed)
        self.assertFalse(foreign.destroyed)
