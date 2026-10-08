import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
from functools import partial
import unittest

ROOT = Path(__file__).resolve().parents[2]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ('source/scripts/client/Driftkings/core/' + name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

class Event:
    def __init__(self): self.listeners=[]
    def __iadd__(self, callback): self.listeners.append(callback); return self
    def __isub__(self, callback): self.listeners.remove(callback); return self

class HookTests(unittest.TestCase):
    def test_deferred_hooks_preserve_other_wrappers_on_stop(self):
        hooks = load('hooks').HookRegistry()
        target = NS(call=lambda x: x + 1)
        def install(handler):
            original = target.call
            target.call = lambda x: handler(original, x)
        hooks.declare('A', install, lambda original, x: original(x) * 2)
        self.assertEqual(target.call(3), 4)
        hooks.activate('A'); hooks.activate('A')
        self.assertEqual(target.call(3), 8)
        original = target.call
        target.call = lambda x: original(x) + 7
        hooks.deactivate('A')
        self.assertEqual(target.call(3), 11)

    def test_failed_install_disables_already_installed_hooks(self):
        hooks = load('hooks').HookRegistry()
        handlers=[]
        hooks.declare('A', handlers.append, lambda original: 99)
        def fail(handler): raise RuntimeError('missing client method')
        hooks.declare('A', fail, lambda original: 3)
        with self.assertRaises(RuntimeError): hooks.activate('A')
        self.assertEqual(handlers[0](lambda: 12), 12)

    def test_import_owner_captures_partial_and_nested_helper_declarations(self):
        hooks=load('hooks').HookRegistry(); hooks.current='Component'
        handlers=[]
        def handler(multiplier, original, value): return multiplier * original(value)
        hooks.declare('helper', handlers.append, partial(handler, 3))
        hooks.current=None; hooks.activate('Component')
        self.assertEqual(handlers[0](lambda value: value + 1, 2), 9)
        self.assertFalse(hooks.pending)

class ContextTests(unittest.TestCase):
    def test_repeated_spaces_cleanup_in_reverse_order_and_unsubscribe(self):
        events=[]
        modules=[(name,NS(onContextEntered=lambda space,n=name:events.append(('enter',n,space)),
                          onContextLeft=lambda space,n=name:events.append(('leave',n,space)))) for name in ('A','B')]
        loader=NS(onGUISpaceEntered=Event(),onGUISpaceLeft=Event(),getSpaceID=lambda:2)
        contexts=load('contexts').Contexts(modules,loader)
        contexts.start();contexts.start();contexts.enter(2);contexts.enter(3);contexts.leave(2);contexts.stop();contexts.stop()
        self.assertEqual(events,[('enter','A',2),('enter','B',2),('leave','B',2),('leave','A',2),('enter','A',3),('enter','B',3),('leave','B',3),('leave','A',3)])
        self.assertFalse(loader.onGUISpaceEntered.listeners)
        self.assertFalse(loader.onGUISpaceLeft.listeners)

    def test_one_failed_context_does_not_block_others(self):
        received=[]
        def fail(space): raise RuntimeError('failed')
        contexts=load('contexts').Contexts([('bad',NS(onContextEntered=fail)),('good',NS(onContextEntered=received.append))])
        with self.assertLogs('Driftkings.Contexts',level='ERROR'): contexts.enter(3)
        self.assertEqual(received,[3])

class CallbackTests(unittest.TestCase):
    def test_completion_cancel_owner_and_shutdown(self):
        jobs={};cancelled=[];calls=[]
        def schedule(delay, fn):
            token=len(jobs)+1;jobs[token]=fn;return token
        service=load('callbacks').CallbackService(NS(callback=schedule,cancelCallback=cancelled.append))
        def work(value):calls.append(value)
        work.__module__='Driftkings.battle.Test'
        first=service.schedule(0,work,1);jobs[first]()
        self.assertEqual(calls,[1]);self.assertFalse(service.pending)
        second=service.schedule(2,work,2)
        service.endBattle()
        self.assertEqual(cancelled,[second]);self.assertFalse(service.pending)
        service.cancel(second)
        service.schedule(3,work,3);service.stop()
        self.assertFalse(service.pending)

if __name__ == '__main__': unittest.main()
