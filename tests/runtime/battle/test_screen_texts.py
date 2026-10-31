# -*- coding: utf-8 -*-
"""Battle efficiency and team strength texts at a fixed place on the screen in Gameface."""
import copy

from support import RuntimeTest, game_source, module

SHADOW = {'alpha': 0.8, 'angle': 90, 'blurX': 2, 'blurY': 2, 'color': '#000000', 'distance': 0, 'enabled': True,
          'quality': 4, 'strength': 2}
# The defaults shipped before the migration; saved profiles keep this shape.
DEFAULTS = {
    'battle_performance': {'enabled': True, 'format': 'WN8: {wn8}', 'position': {'x': 125, 'y': 36}, 'textLock': False,
                           'textShadow': SHADOW, 'textStyle': {'align': 'center', 'color': '#FFFFFF', 'font': '$TitleFont', 'size': 16}},
    'battle_statistics': {'enabled': True, 'background': True, 'format': '{header}', 'textLock': False, 'textShadow': SHADOW,
                          'textFormat': {'bold': False, 'color': '#DBD7D2', 'font': '$FieldFont', 'italic': True, 'size': 16},
                          'textPosition': {'alignX': 'right', 'alignY': 'top', 'alpha': 1.0, 'border': False, 'drag': True,
                                           'visible': True, 'x': -58.0, 'y': 2.0}},
}


class ScreenTextTests(RuntimeTest):
    def setUp(self):
        super(ScreenTextTests, self).setUp()
        self.data = copy.deepcopy(DEFAULTS)
        configs = dict((name, module(NAME=name)) for name in self.data)
        components = {'driftkings.components.battle_performance': module(battle_performance_settings=configs['battle_performance']),
                      'driftkings.battle.battle_statistics': module(battle_statistics_settings=configs['battle_statistics'])}
        self.applied = []

        class Service(object):
            def getComponentDict(service, config):
                return self.data[config.NAME]

            def apply(service, config, values):
                self.applied.append((config.NAME, values))

        self.api, _ = game_source('gameface/battle/screen_texts.py', {
            'importlib': module(import_module=lambda name: components[name]),
            'driftkings.settings.service': module(settings_service=Service()),
            'driftkings.views.marks_model': self.load('views.marks_model'),
            'driftkings.core.hud_visibility': module(hudVisibility=module(attach=lambda view: None, detach=lambda view: None)),
            'driftkings.gameface.battle.common': module(BattleCardAdapter=self.load('gameface.battle.common').BattleCardAdapter),
        }, real=('driftkings._constants',))

    def adapter(self, name):
        adapter = self.api[name]()
        adapter.published = []
        adapter.publish = lambda payload, config, enabled: adapter.published.append((payload, config, enabled))
        return adapter

    @staticmethod
    def child(cursor=True, gui=True):
        return module(_cursorVisible=cursor, _guiVisible=gui)

    def test_efficiency_keeps_the_saved_position_style_and_shadow(self):
        adapter = self.adapter('BattleEfficiencyAdapter')
        adapter.startBattle()
        # Nothing to show until the component formats a text and shows it.
        self.assertFalse(adapter.published[-1][2])
        adapter.setText("WN8: <font color='#FF0000'>1500</font>")
        self.assertFalse(adapter.published[-1][2])
        adapter.show(True)
        payload, config, enabled = adapter.published[-1]
        self.assertTrue(enabled)
        self.assertEqual(payload, {'text': "WN8: <font color='#FF0000'>1500</font>",
                                   'style': {'font': '$TitleFont', 'size': 16, 'color': '#FFFFFF', 'align': 'center'}})
        # A position without an anchor stays at the top-left offset, as in the Flash overlay.
        self.assertEqual(config, {'x': 125, 'y': 36, 'alpha': 1.0, 'shadow': SHADOW, 'locked': False})

    def test_team_strength_keeps_its_anchor_opacity_and_text_format(self):
        adapter = self.adapter('TeamStrengthAdapter')
        adapter.startBattle()
        adapter.setText('Team strength: 50.00 | 50.00')
        adapter.show(True)
        payload, config, enabled = adapter.published[-1]
        self.assertTrue(enabled)
        self.assertEqual(payload['style'], {'font': '$FieldFont', 'size': 16, 'color': '#DBD7D2', 'bold': False,
                                            'italic': True, 'align': 'left'})
        self.assertEqual(config, {'x': -58.0, 'y': 2.0, 'alignX': 'right', 'alignY': 'top', 'alpha': 1.0,
                                  'shadow': SHADOW, 'locked': False})

    def test_text_hides_when_disabled_hidden_or_after_the_battle(self):
        adapter = self.adapter('BattleEfficiencyAdapter')
        adapter.startBattle()
        adapter.setText('WN8: 1500')
        adapter.show(True)
        self.data['battle_performance']['enabled'] = False
        adapter.refresh()
        self.assertFalse(adapter.published[-1][2])
        self.data['battle_performance']['enabled'] = True
        adapter.setBattleHudVisible(False)
        self.assertFalse(adapter.published[-1][2])
        adapter.setBattleHudVisible(True)
        adapter.show(False)
        self.assertFalse(adapter.published[-1][2])
        adapter.show(True)
        adapter.stopBattle()
        self.assertFalse(adapter.published[-1][2])
        self.assertEqual((adapter.text, adapter.shown), ('', False))

    def test_lock_is_published_and_blocks_saving_a_drag(self):
        adapter = self.adapter('TeamStrengthAdapter')
        adapter.startBattle()
        self.data['battle_statistics']['textLock'] = True
        adapter.refresh()
        self.assertTrue(adapter.published[-1][1]['locked'])
        adapter.savePosition(self.child(), {'x': 10, 'y': 10, 'alignX': 'left', 'alignY': 'top'})
        self.assertEqual(self.applied, [])

    def test_dragged_position_lands_in_the_module_position_object(self):
        efficiency = self.adapter('BattleEfficiencyAdapter')
        efficiency.startBattle()
        efficiency.savePosition(self.child(), {'x': 40.6, 'y': -12.2, 'alignX': 'center', 'alignY': 'bottom'})
        self.assertEqual(self.applied, [('battle_performance', {'position': {'x': 41, 'y': -12, 'alignX': 'center', 'alignY': 'bottom'}})])
        strength = self.adapter('TeamStrengthAdapter')
        strength.startBattle()
        strength.savePosition(self.child(), {'x': -70, 'y': 4, 'alignX': 'right', 'alignY': 'top'})
        self.assertEqual(self.applied[-1], ('battle_statistics', {'textPosition': {'x': -70, 'y': 4, 'alignX': 'right', 'alignY': 'top'}}))

    def test_position_is_not_saved_without_the_battle_cursor_or_outside_battle(self):
        adapter = self.adapter('BattleEfficiencyAdapter')
        args = {'x': 10, 'y': 10, 'alignX': 'left', 'alignY': 'top'}
        adapter.savePosition(self.child(), args)
        adapter.startBattle()
        adapter.savePosition(self.child(cursor=False), args)
        adapter.savePosition(self.child(gui=False), args)
        adapter.savePosition(self.child(), {'x': 'bad', 'y': 1})
        self.assertEqual(self.applied, [])
