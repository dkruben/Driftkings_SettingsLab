import importlib.util
from pathlib import Path
import types
import unittest

path = Path(__file__).resolve().parents[2] / 'source/scripts/client/Driftkings/core/__init__.py'
spec = importlib.util.spec_from_file_location('loader', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ComponentLoaderTests(unittest.TestCase):
    def test_order_and_idempotent_lifecycle(self):
        events = []
        def importer(name):
            events.append('import:' + name)
            return types.SimpleNamespace(init=lambda: events.append('init:' + name),
                                         fini=lambda: events.append('fini:' + name))
        loader = module.Core(['battle.a', 'lobby.b'], importer, services=())
        loader.start(); loader.start(); loader.stop(); loader.stop(); loader.start()
        self.assertEqual(events, ['import:Driftkings.battle.a', 'import:Driftkings.lobby.b',
                                  'init:Driftkings.battle.a', 'init:Driftkings.lobby.b',
                                  'fini:Driftkings.lobby.b', 'fini:Driftkings.battle.a'])

    def test_failure_does_not_prevent_other_components_or_cleanup(self):
        events = []
        def importer(name):
            if name.endswith('.bad'): raise ImportError('test')
            def start():
                if name.endswith('.partial'): raise RuntimeError('test')
                events.append(name)
            return types.SimpleNamespace(init=start, fini=lambda: events.append('stop:' + name))
        loader = module.Core(['components.bad', 'battle.partial', 'lobby.good'], importer, services=())
        with self.assertLogs('Driftkings.Loader', level='ERROR'): loader.start()
        loader.stop()
        self.assertEqual(loader.failures, ['components.bad', 'battle.partial'])
        self.assertIn('Driftkings.lobby.good', events)
        self.assertIn('stop:Driftkings.battle.partial', events)

    def test_core_collects_views_before_services_start_and_stops_services(self):
        events = []
        service = types.SimpleNamespace(register=lambda *args: events.append(('view', args)),
                                        start=lambda: events.append('service.start'),
                                        stop=lambda: events.append('service.stop'))
        component = types.SimpleNamespace(getBattleViews=lambda: (('view', object, None),),
                                          init=lambda: events.append('component.init'),
                                          fini=lambda: events.append('component.fini'))
        core = module.Core(['battle.example'], lambda _: component, services=(service,))
        core.start(); core.stop()
        self.assertEqual(events[0][0], 'view')
        self.assertEqual(events[1:], ['service.start', 'component.init', 'component.fini', 'service.stop'])

    def test_context_failure_still_allows_component_and_service_cleanup(self):
        events = []
        def fail(): raise RuntimeError('context unavailable')
        contexts = types.SimpleNamespace(start=fail, stop=fail)
        component = types.SimpleNamespace(fini=lambda: events.append('component'))
        service = types.SimpleNamespace(start=lambda: None, stop=lambda: events.append('service'))
        core = module.Core(['battle.example'], lambda _: component, services=(service,),
                           context_factory=lambda _: contexts)
        with self.assertLogs('Driftkings.Loader', level='ERROR'):
            core.start()
            core.stop()
        self.assertEqual(events, ['component', 'service'])
        self.assertEqual(core.failures, ['Contexts'])

    def test_partial_start_is_cleaned_immediately_once_with_hooks_inactive(self):
        events = []
        active = set()
        hooks = types.SimpleNamespace(current=None, activate=active.add,
                                      deactivate=active.discard)
        def importer(name):
            def start():
                events.append(('init', name))
                if name.endswith('.bad'): raise RuntimeError('partial startup')
            def stop():
                self.assertNotIn(name, active)
                events.append(('fini', name))
            return types.SimpleNamespace(init=start, fini=stop)
        core = module.Core(['battle.bad', 'battle.good'], importer,
                           services=(), hook_manager=hooks)
        with self.assertLogs('Driftkings.Loader', level='ERROR'): core.start()
        self.assertEqual(events, [('init', 'Driftkings.battle.bad'),
                                  ('fini', 'Driftkings.battle.bad'),
                                  ('init', 'Driftkings.battle.good')])
        self.assertEqual([name for name, _ in core.initialized], ['battle.good'])
        core.stop(); core.stop()
        self.assertEqual(events.count(('fini', 'Driftkings.battle.bad')), 1)
        self.assertEqual(events[-1], ('fini', 'Driftkings.battle.good'))
        self.assertFalse(active)

    def test_failed_cleanup_does_not_interrupt_next_component(self):
        events = []
        def fail(): raise RuntimeError('test failure')
        bad = types.SimpleNamespace(init=fail, fini=fail)
        good = types.SimpleNamespace(init=lambda: events.append('started'),
                                     fini=lambda: events.append('stopped'))
        core = module.Core(['battle.bad', 'battle.good'],
                           lambda name: bad if name.endswith('.bad') else good,
                           services=())
        with self.assertLogs('Driftkings.Loader', level='ERROR'): core.start()
        core.stop()
        self.assertEqual(events, ['started', 'stopped'])
