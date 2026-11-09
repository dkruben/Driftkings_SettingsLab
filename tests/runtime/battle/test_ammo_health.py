# -*- coding: utf-8 -*-
"""Docked health uses the tracker, respects settings and releases its lifecycle."""
from support import RuntimeTest, Settings, game_source, module


class Meta(object):
    def _populate(self):
        pass

    def _dispose(self):
        pass

    def _sendChanged(self, *args):
        self.sent.append(args)


class AmmoHealthTests(RuntimeTest):
    def setUp(self):
        super(AmmoHealthTests, self).setUp()
        self.settings = {'enabled': True, 'style': 5,
                         'avgColor': {'saturation': 0.7, 'brightness': 0.9}}
        self.state = {'current': 1440, 'maximum': 2000, 'battle': True, 'alive': True}
        self.signals = []
        service = Settings(self.settings).service()
        service.settings_service.onModSettingsChanged = module(
            connect=lambda *args: self.signals.append(('connect', args)),
            disconnect=lambda *args: self.signals.append(('disconnect', args)))
        component = module(vehicle_health_settings='vehicle_health', tracker=module(state=self.state))
        self.api, _ = game_source('flash/battle/vehicle_health.py', {
            'importlib': module(import_module=lambda name: component),
            'driftkings.settings.service': service,
            'driftkings.flash.battle.meta.vehicle_health': module(AmmoHealthMeta=Meta),
            'driftkings.common.utils.formatting': self.load('common.utils.formatting'),
        }, real=('driftkings._constants',))
        self.view = self.api['AmmoHealthView']()
        self.view.sent = []

    def test_docked_styles_publish_health_and_native_numeric_color(self):
        for style in (5, 6, 7):
            self.settings['style'] = style
            self.view.refresh()
            method, fraction, text, color, skin, enabled = self.view.sent[-1]
            self.assertEqual(method, 'as_setHealth')
            self.assertEqual((fraction, text, skin, enabled), (.72, '1440 / 2000', style - 5, True))
            self.assertTrue(isinstance(color, int))

    def test_floating_styles_and_inactive_states_hide_docked_bar(self):
        for style in range(5):
            self.settings['style'] = style
            self.view.refresh()
            self.assertFalse(self.view.sent[-1][-1])
        self.settings['style'] = 5
        for key, value in (('alive', False), ('battle', False), ('maximum', 0)):
            old = self.state[key]
            self.state[key] = value
            self.view.refresh()
            self.assertFalse(self.view.sent[-1][-1])
            self.state[key] = old
        self.settings['enabled'] = False
        self.view.refresh()
        self.assertFalse(self.view.sent[-1][-1])

    def test_tracker_refresh_fanout_and_disposal(self):
        self.view._populate()
        self.state['current'] = 900
        self.api['refresh_views']()
        self.assertEqual(self.view.sent[-1][2], '900 / 2000')
        self.view._dispose()
        count = len(self.view.sent)
        self.api['refresh_views']()
        self.assertEqual(len(self.view.sent), count)
        self.assertEqual([item[0] for item in self.signals], ['connect', 'disconnect'])
