# -*- coding: utf-8 -*-
"""Common Test enters the mod without using the production update channel."""
from support import RuntimeTest, module, source


class CommonTestStartupTests(RuntimeTest):
    def test_supported_realms_start_and_stop_the_core_once(self):
        for realm in ('EU', 'NA', 'ASIA', 'CT'):
            calls = []

            class Core(object):
                def start(self):
                    calls.append('start')

                def stop(self):
                    calls.append('stop')

            api = source('../gui/mods/mod_driftkings.py', {
                'realm': module(CURRENT_REALM=realm), 'driftkings.core': module(Core=Core)})
            api['init']()
            api['init']()
            api['fini']()
            api['fini']()
            self.assertEqual(calls, ['start', 'stop'], realm)

    def test_unknown_realms_do_not_import_the_core(self):
        api = source('../gui/mods/mod_driftkings.py', {'realm': module(CURRENT_REALM='RU')})
        api['init']()
        self.assertIsNone(api['_core'])

    def test_common_test_does_not_start_production_updater(self):
        api = source('core/updater/lifecycle.py', {'realm': module(CURRENT_REALM='CT')})
        service = api['LifecycleMixin']()
        service.active = False
        service._runtime_transport = True
        service.start()
        self.assertFalse(service.active)
