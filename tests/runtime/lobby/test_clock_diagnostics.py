# -*- coding: utf-8 -*-
from support import Hooks, RuntimeTest, module, source


class Log(object):
    def __init__(self):
        self.infos, self.exceptions = [], []

    def info(self, *args):
        self.infos.append(args)

    def exception(self, *args):
        self.exceptions.append(args)


class Bus(object):
    def __init__(self):
        self.added, self.removed = [], []

    def addListener(self, event, handler, scope=None, priority=None):
        self.added.append((event, handler))

    def removeListener(self, event, handler, scope=None):
        self.removed.append((event, handler))


class Dispatcher(object):
    def __init__(self):
        self.entity = None

    def getEntity(self):
        return self.entity


class Frontline(object):
    pass


class Onslaught(object):
    pass


class RandomHangar(object):
    pass


class Instance(object):
    pass


class ClockDiagnosticsTests(RuntimeTest):
    def setUp(self):
        super(ClockDiagnosticsTests, self).setUp()
        self.log = Log()
        self.bus = Bus()
        self.dispatcher = Dispatcher()
        self.hooks = Hooks()
        self.api = source('gameface/lobby/clock_diagnostics.py', {
            'driftkings.logger': module(get_logger=lambda name: self.log),
            'driftkings.core.hooks': module(override=self.hooks.override),
            'gui.shared': module(EVENT_BUS_SCOPE=module(LOBBY='LOBBY'),
                                 events=module(PrebattleEvent=module(SWITCHED='PrebattleEvent/SWITCHED')),
                                 g_eventBus=self.bus),
            'gui.prb_control.dispatcher': module(g_prbLoader=module(getDispatcher=lambda: self.dispatcher)),
        })

    def enable(self):
        self.api['ENABLED'] = True

    def test_disabled_by_default_and_silent(self):
        self.assertFalse(self.api['ENABLED'])
        self.api['emit']('hangar.loaded', hangar='RandomHangar#1')
        self.assertFalse(self.log.infos)
        calls = []
        self.assertIsNone(self.api['guarded'](lambda: calls.append(1))())
        self.assertFalse(calls)

    def test_identify_is_stable_per_instance(self):
        first, second = Instance(), Instance()
        self.assertEqual(self.api['identify'](first, 'RandomHangar'), self.api['identify'](first, 'RandomHangar'))
        self.assertNotEqual(self.api['identify'](first, 'RandomHangar'), self.api['identify'](second, 'RandomHangar'))
        self.assertTrue(self.api['identify'](first, 'RandomHangar').startswith('RandomHangar#'))

    def test_changed_reports_only_real_state_changes(self):
        self.assertTrue(self.api['changed']('x', (True,)))
        self.assertFalse(self.api['changed']('x', (True,)))
        self.assertTrue(self.api['changed']('x', (False,)))
        self.api['forget']('x')
        self.assertTrue(self.api['changed']('x', (False,)))

    def test_failures_are_isolated_and_reported_once(self):
        self.enable()

        def broken():
            raise ValueError('diagnostic bug')

        wrapped = self.api['guarded'](broken)
        self.assertIsNone(wrapped())
        self.assertIsNone(wrapped())
        self.assertEqual(len(self.log.exceptions), 1)

    def test_listener_is_attached_once_and_removed_on_destroy(self):
        self.enable()
        self.dispatcher.entity = Frontline()
        self.api['install_lifecycle'](RandomHangar)
        hangar = RandomHangar()
        load = self.hooks.get('RandomHangar', '_onLoading')
        finalize = self.hooks.get('RandomHangar', '_finalize')
        self.assertEqual(load(lambda h: 'loaded', hangar), 'loaded')
        self.assertEqual(load(lambda h: 'loaded', hangar), 'loaded')
        self.assertEqual(len(self.bus.added), 1)
        self.assertEqual(self.bus.added[0][0], 'PrebattleEvent/SWITCHED')
        self.assertEqual(finalize(lambda h: 'finalized', hangar), 'finalized')
        self.assertEqual(len(self.bus.removed), 1)
        self.assertIs(self.bus.removed[0][1], self.bus.added[0][1])
        finalize(lambda h: 'finalized', hangar)
        self.assertEqual(len(self.bus.removed), 1)

    def test_session_start_is_announced_with_uniform_prefix(self):
        self.enable()
        self.api['install_lifecycle'](RandomHangar)
        first = self.log.infos[0]
        self.assertEqual(first[1], '[Driftkings][ClockDiag]')
        self.assertEqual(first[2], 'session.started')
        self.assertIn('session=' + self.api['SESSION'], first[-1])

    def test_attach_failure_never_breaks_hangar_loading(self):
        self.enable()

        def failing_add(event, handler, scope=None, priority=None):
            raise RuntimeError('bus unavailable')

        self.bus.addListener = failing_add
        self.api['install_lifecycle'](RandomHangar)
        load = self.hooks.get('RandomHangar', '_onLoading')
        self.assertEqual(load(lambda h: 'loaded', RandomHangar()), 'loaded')
        self.assertEqual(len(self.log.exceptions), 1)

    def test_mode_lookup_failure_never_breaks_hangar_loading(self):
        self.enable()
        self.api['install_lifecycle'](RandomHangar)
        self.dispatcher.getEntity = lambda: 1 / 0
        load = self.hooks.get('RandomHangar', '_onLoading')
        self.assertEqual(load(lambda h: 'loaded', RandomHangar()), 'loaded')
        self.assertTrue(self.bus.added)

    def test_mode_switch_logs_only_changes(self):
        self.enable()
        self.api['install_lifecycle'](RandomHangar)
        hangar = RandomHangar()
        self.hooks.get('RandomHangar', '_onLoading')(lambda h: None, hangar)
        handler = self.bus.added[0][1]
        self.dispatcher.entity = Frontline()
        handler(None)
        handler(None)
        self.dispatcher.entity = Onslaught()
        handler(None)
        switches = [args[-1] for args in self.log.infos if args[2] == 'mode.switched']
        self.assertEqual(len(switches), 2)
        self.assertIn('mode=Frontline', switches[0])
        self.assertIn('mode=Onslaught', switches[1])

    def test_payload_summary_has_no_account_data(self):
        summary = self.api['payload_summary']({'config': {'visible': True, 'hidePrestige': False,
                                                          'formats': [{'format': '%H:%M'}],
                                                          'calendar': {'days': ['x']}, 'locale': 'pt'}})
        self.assertEqual(summary, {'visible': True, 'hidePrestige': False, 'formats': 1})
