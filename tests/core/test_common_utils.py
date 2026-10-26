# -*- coding: utf-8 -*-
"""Utility imports stay light; exception boundaries always report failures."""
from support import RuntimeTest, module, source


class CommonUtilsTests(RuntimeTest):
    def test_exception_boundary_logs_without_exposing_arguments(self):
        api = self.load('common.utils.exceptions')
        records = []
        class Logger(object):
            def exception(self, *args):
                records.append(args)
        api.get_logger = lambda name: Logger()
        @api.log_exceptions
        def guarded(secret):
            raise ValueError('failed')
        self.assertIsNone(guarded('private-data'))
        self.assertEqual(guarded.__name__, 'guarded')
        self.assertEqual(records, [('Callback failed: %s', 'guarded')])
        @api.log_exceptions
        def successful(value):
            return value + 1
        self.assertEqual(successful(4), 5)

    def test_wg_helpers_do_not_access_resources_during_import(self):
        api = source('common/utils/wgutils.py', {
            'BigWorld': module(player=lambda: 'player', target=lambda: 'target', entity=lambda value: value),
            'ResMgr': module(),
        })
        self.assertIsNone(api['_competing_markers_installed'])
        self.assertIsNone(api['_battle_types'])
        self.assertEqual(api['getPlayer'](), 'player')
        self.assertEqual(api['getTarget'](), 'target')
        self.assertEqual(api['getEntity'](5), 5)
        checks = []
        def find():
            checks.append(True)
            return False
        api['_findCompetingMarkers'] = find
        self.assertFalse(api['hasCompetingMarkers']())
        self.assertFalse(api['hasCompetingMarkers']())
        self.assertEqual(len(checks), 1)

    def test_pure_formatting_needs_no_client(self):
        api = self.load('common.utils.formatting')
        self.assertEqual(api.hexToDecimal('F98600'), int('F98600', 16))
        self.assertEqual(api.replaceMacros('HP: {hp}', {'{hp}': '100'}), 'HP: 100')
        self.assertEqual(api.percentToRgb(0), '#FF8080')

    def test_central_callbacks_cancel_the_migrated_owner(self):
        api = self.load('core.callbacks')
        queued = {}
        cancelled = []
        def schedule(delay, method):
            queued[1] = method
            return 1
        service = api.CallbackService(module(callback=schedule, cancelCallback=lambda token: cancelled.append(token)))
        def task():
            return None
        task.__module__ = 'driftkings.battle.target_information'
        service.schedule(0.5, task)
        self.assertEqual(service.snapshot()['pending'], 1)
        service.endBattle()
        self.assertEqual(cancelled, [1])
        self.assertEqual(service.snapshot()['pending'], 0)
