# -*- coding: utf-8 -*-
"""Hangar preferences: the low ammo carousel text changes only the carousel state lookup."""
from support import RuntimeTest, Settings, game_source, module, stub

STATES = module(AMMO_NOT_FULL='ammoNotFull', AMMO_NOT_FULL_EVENTS='ammoNotFullEvents')


class HangarPreferencesTests(RuntimeTest):
    def setUp(self):
        super(HangarPreferencesTests, self).setUp()
        self.data = {'enabled': True}
        self.api, self.hooks = game_source('lobby/hangar_preferences.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'gui.shared.gui_items.Vehicle': stub('Vehicle', Vehicle=stub('VehicleClass', VEHICLE_STATE=STATES)),
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {'resource': 'resource'}),
        }, real=('driftkings._constants',))
        self.lookup = self.hooks.get('MENU', 'tankcarousel_vehiclestates')
        self.native = lambda key: '#menu:tankCarousel/vehicleStates/' + key

    def test_low_ammo_uses_the_low_ammo_text(self):
        self.assertEqual(self.lookup(self.native, 'MENU', 'ammoNotFull'), '#menu:tankCarousel/vehicleStates/ammoNotFullEvents')

    def test_other_states_and_a_disabled_module_are_native(self):
        self.assertEqual(self.lookup(self.native, 'MENU', 'battle'), '#menu:tankCarousel/vehicleStates/battle')
        self.data['enabled'] = False
        self.assertEqual(self.lookup(self.native, 'MENU', 'ammoNotFull'), '#menu:tankCarousel/vehicleStates/ammoNotFull')

    def test_translations_are_no_longer_wrapped(self):
        self.assertNotIn(('i18n', 'makeString'), self.hooks.overrides)
