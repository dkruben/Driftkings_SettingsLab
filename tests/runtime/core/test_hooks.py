# -*- coding: utf-8 -*-
"""Real installers and registry lifecycle, without client classes."""
import sys
import traceback
from support import RuntimeTest


class HookTests(RuntimeTest):
    def setUp(self):
        super(HookTests, self).setUp()
        self.api = self.load('core.hooks')
        self.owner = 'test.owner'
        self.api.hooks.current = self.owner

    def activate(self):
        self.api.hooks.current = None
        self.api.hooks.activate(self.owner)

    def test_normal_method_activation_deactivation_and_reactivation(self):
        class Target(object):
            def method(self, value):
                return value + 1
        calls = []
        @self.api.override(Target, 'method')
        def handler(original, instance, value):
            calls.append(value)
            return original(instance, value) * 2
        target = Target()
        self.assertEqual(target.method(2), 3)
        self.activate()
        self.assertEqual(target.method(2), 6)
        installed = Target.__dict__['method']
        self.api.hooks.deactivate(self.owner)
        self.assertEqual(target.method(2), 3)
        self.api.hooks.activate(self.owner)
        self.assertIs(Target.__dict__['method'], installed)
        self.assertEqual(target.method(2), 6)
        self.assertEqual(calls, [2, 2])

    def test_inherited_static_and_class_descriptors(self):
        for typed in (False, True):
            class Parent(object):
                factor = 3
                @staticmethod
                def static(value):
                    return value + 1
                @classmethod
                def classified(cls, value):
                    return cls.factor * value
            class Target(Parent):
                pass
            install_static = self.api.overrideStaticMethod if typed else self.api.override
            install_class = self.api.overrideClassMethod if typed else self.api.override
            @install_static(Target, 'static')
            def static(original, value):
                return original(value) * 2
            @install_class(Target, 'classified')
            def classified(original, cls, value):
                return original(value) + cls.factor
            self.activate()
            self.assertEqual(Target.static(2), 6)
            self.assertEqual(Target().static(2), 6)
            self.assertEqual(Target.classified(2), 9)
            self.assertEqual(Target().classified(2), 9)
            self.assertEqual(Parent.static(2), 3)
            self.api.hooks.deactivate(self.owner)
            self.assertEqual(Target.static(2), 3)
            self.assertEqual(Target.classified(2), 6)
            self.api.hooks.current = self.owner

    def test_property_get_set_delete_and_typed_getter(self):
        class Target(object):
            def __init__(self):
                self.raw = 2
            def get(self):
                return self.raw
            def set(self, value):
                self.raw = value
            def delete(self):
                self.raw = 0
            value = property(get, set, delete, 'native property')
        def get(original, instance):
            return original(instance) * 2
        def set(original, instance, value):
            return original(instance, value + 1)
        def delete(original, instance):
            original(instance)
            instance.raw += 1
        self.api.override(Target, 'value', get, set, delete)
        self.activate()
        target = Target()
        self.assertEqual(target.value, 4)
        target.value = 5
        self.assertEqual(target.raw, 6)
        del target.value
        self.assertEqual(target.raw, 1)
        self.assertEqual(Target.value.__doc__, 'native property')
        self.api.hooks.deactivate(self.owner)
        target.value = 5
        self.assertEqual(target.value, 5)
        del target.value
        self.assertEqual(target.raw, 0)
        self.api.hooks.current = self.owner
        self.api.overrideMethod(Target, 'value')(get)
        self.activate()
        target.raw = 3
        self.assertEqual(target.value, 12)
        self.api.hooks.deactivate(self.owner)
        self.assertEqual(target.value, 3)

    def test_discard_and_duplicate_declarations(self):
        class Target(object):
            def method(self):
                return 1
        def handler(original, instance):
            return original(instance) + 1
        self.api.override(Target, 'method')(handler)
        self.api.override(Target, 'method')(handler)
        self.assertEqual(len(self.api.hooks.installations), 1)
        self.activate()
        self.assertEqual(Target().method(), 2)
        self.api.hooks.discard(self.owner)
        self.assertEqual(Target().method(), 1)
        self.api.hooks.activate(self.owner)
        self.assertEqual(Target().method(), 1)

    def test_private_attribute_resolution_and_defaults(self):
        introspection = self.load('core.introspection')
        class Target(object):
            __value = 5
        self.assertEqual(introspection.find_attr_name(Target, 'value'), '_Target__value')
        self.assertEqual(introspection.find_attr(Target, 'value'), 5)
        self.assertEqual(introspection.find_attr(Target, 'missing', 9), 9)
        with self.assertRaises(AttributeError):
            introspection.find_attr(Target, 'missing')

    def test_exception_traceback_keeps_original_and_handler_frames(self):
        class Target(object):
            def method(self):
                raise ValueError('native failure')
        @self.api.override(Target, 'method')
        def handler(original, instance):
            return original(instance)
        self.activate()
        try:
            Target().method()
        except ValueError:
            frames = traceback.extract_tb(sys.exc_info()[2])
            names = [frame[2] for frame in frames]
            self.assertIn('handler', names)
            self.assertIn('method', names)
        else:
            self.fail('Original exception did not propagate')

    def test_owner_subscriptions_disconnect_and_reconnect(self):
        signal = self.load('core.signals').Signal()
        calls = []
        @self.api.on_event(signal)
        def on_signal(value):
            calls.append(value)
        signal(1)
        self.activate()
        signal(2)
        self.api.hooks.deactivate(self.owner)
        signal(3)
        self.api.hooks.activate(self.owner)
        signal(4)
        self.assertEqual(calls, [2, 4])

    def test_private_method_and_module_function(self):
        import types
        class Target(object):
            def __method(self, value):
                return value + 1
            def public(self, value):
                return self.__method(value)
        @self.api.override(Target, 'method')
        def handler(original, instance, value):
            return original(instance, value) * 2
        target_module = types.ModuleType('target')
        target_module.function = lambda value: value + 1
        @self.api.override(target_module, 'function')
        def function(original, value):
            return original(value) * 3
        self.activate()
        self.assertEqual(Target().public(2), 6)
        self.assertEqual(target_module.function(2), 9)
        self.api.hooks.deactivate(self.owner)
        self.assertEqual(Target().public(2), 3)
        self.assertEqual(target_module.function(2), 3)
