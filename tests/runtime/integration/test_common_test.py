# -*- coding: utf-8 -*-
"""Common Test enters the mod without using the production update channel."""
from support import RuntimeTest, module, source


class CommonTestStartupTests(RuntimeTest):
    def test_supported_realms_start_and_stop_the_core_once(self):
        for realm in ('EU', 'NA', 'ASIA', 'CN', 'CT'):
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
        def unexpected():
            self.fail('The excluded realm reached Core')
        for realm in ('RU', 'PT_RU', 'LESTA', 'UNKNOWN', ''):
            api = source('../gui/mods/mod_driftkings.py', {
                'realm': module(CURRENT_REALM=realm), 'driftkings.core': module(Core=unexpected)})
            api['init']()
            api['fini']()
            self.assertIsNone(api['_core'], realm)

    def test_partial_startup_cleans_up_and_releases_core_even_if_stop_fails(self):
        calls = []

        class Core(object):
            def start(self):
                calls.append('start')
                raise RuntimeError('partial start')

            def stop(self):
                calls.append('stop')
                raise RuntimeError('partial cleanup')

        self.capture_log('Driftkings.Loader')
        api = source('../gui/mods/mod_driftkings.py', {
            'realm': module(CURRENT_REALM='CN'), 'driftkings.core': module(Core=Core)})
        api['init']()
        self.assertIsNone(api['_core'])
        api['fini']()
        api['init']()
        self.assertEqual(calls, ['start', 'stop', 'start', 'stop'])

    def test_common_test_does_not_start_production_updater(self):
        api = source('core/updater/lifecycle.py', {'realm': module(CURRENT_REALM='CT')})
        service = api['LifecycleMixin']()
        service.active = False
        service._runtime_transport = True
        service.start()
        self.assertFalse(service.active)
