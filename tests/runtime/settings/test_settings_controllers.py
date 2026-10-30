# -*- coding: utf-8 -*-
"""Hangar controllers share subscription ownership without changing update order."""
import ast
import os
from support import CLIENT, RuntimeTest, module, source


class SettingsControllerTests(RuntimeTest):
    def setUp(self):
        super(SettingsControllerTests, self).setUp()
        self.events = []
        self.listeners = []
        def connect(handler, section):
            self.events.append(('connect', handler.__self__.active))
            self.listeners.append((handler, section))
        def disconnect(handler):
            self.events.append(('disconnect', handler.__self__.active))
            self.listeners[:] = [entry for entry in self.listeners if entry[0] != handler]
        self.service = module(onModSettingsChanged=module(connect=connect, disconnect=disconnect))
        self.base = source('core/settings_controller.py', {
            'driftkings.settings.service': module(settings_service=self.service)})['SettingsController']
        self.constants = self.load('_constants')

    def controller(self, relative, name, extra=None):
        # Execute the real class while avoiding the module's unrelated game hooks.
        with open(os.path.join(CLIENT, relative), 'rb') as stream:
            text = stream.read().decode('utf-8-sig')
        tree = ast.parse(text.encode('utf-8'))
        index = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.ClassDef) and node.name == name)
        node = tree.body[index]
        end = tree.body[index + 1].lineno - 1 if index + 1 < len(tree.body) else len(text.splitlines())
        selected = '\n'.join(text.splitlines()[node.lineno - 1:end])
        namespace = {'SettingsController': self.base, 'HANGAR_PREFERENCES': self.constants.HANGAR_PREFERENCES,
                     'TECH_TREE_MARKS_OF_EXCELLENCE': self.constants.TECH_TREE_MARKS_OF_EXCELLENCE}
        namespace.update(extra or {})
        eval(compile(selected.encode('utf-8'), relative, 'exec'), namespace)
        return namespace[name]()

    def test_hangar_and_tree_are_idempotent_and_restartable(self):
        for relative, name, section in (
            ('lobby/hangar_preferences.py', 'HangarOptionsController', self.constants.HANGAR_PREFERENCES),
            ('lobby/tech_tree_marks_of_excellence.py', 'TechTreeController', self.constants.TECH_TREE_MARKS_OF_EXCELLENCE)):
            controller = self.controller(relative, name)
            self.assertFalse(controller.active)
            controller.stop()
            self.assertEqual(self.events, [])
            controller.start()
            controller.start()
            self.assertEqual(len(self.listeners), 1)
            self.assertIs(self.listeners[0][1], section)
            controller.stop()
            controller.stop()
            self.assertEqual(self.listeners, [])
            self.assertEqual(self.events, [('connect', True), ('disconnect', False)])
            controller.start()
            self.assertTrue(controller.active)
            controller.stop()
            self.assertEqual(self.listeners, [])
            self.events[:] = []

    def test_clock_refreshes_after_connect_and_after_disconnect(self):
        common = source('gameface/lobby/common.py', {'driftkings.core.settings_controller': module(SettingsController=self.base)})
        changes = []
        controller = self.controller('gameface/lobby/main.py', 'ClockController', {
            'HangarController': common['HangarController'], 'MAIN': self.constants.MAIN, 'GLOBAL': self.constants.GLOBAL,
            'affects': lambda values, *options: changes.append(options) or True})
        class Parent(object):
            pass
        parent = Parent()
        def refresh():
            self.events.append(('refresh', controller.active, len(self.listeners)))
        child = module(refresh=refresh)
        controller.views[parent] = child
        controller.start()
        controller.start()
        controller.stop()
        controller.stop()
        self.assertEqual(self.events, [('connect', True), ('refresh', True, 1),
                                       ('disconnect', False), ('refresh', False, 0)])
        # Clock fields are live: any change under main.clock republishes them.
        del self.events[:]
        controller.start()
        controller.onSettingsChanged(self.constants.MAIN.NAME, {'clock': {'formats': []}})
        self.assertEqual(changes, [('enabled', 'clock')])
        self.assertEqual(self.events[-1], ('refresh', True, 1))
        controller.stop()
        self.assertEqual(self.listeners, [])

    def test_clock_observes_hangar_prestige_and_ignores_other_sections(self):
        common = source('gameface/lobby/common.py', {'driftkings.core.settings_controller': module(SettingsController=self.base)})
        service = self.load('settings.service')
        controller = self.controller('gameface/lobby/main.py', 'ClockController', {
            'HangarController': common['HangarController'], 'MAIN': self.constants.MAIN,
            'GLOBAL': self.constants.GLOBAL, 'affects': service.affects})
        refreshed = []
        controller.onApplySettings = lambda: refreshed.append(True)
        controller.start()
        self.assertIsNone(self.listeners[0][1])
        refreshed[:] = []
        for key in ('enabled', self.constants.HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET):
            controller.onSettingsChanged(self.constants.HANGAR_PREFERENCES.NAME, {key: False})
        self.assertEqual(len(refreshed), 2)
        controller.onSettingsChanged('vehicle_health', {'enabled': False})
        controller.onSettingsChanged(self.constants.HANGAR_PREFERENCES.NAME, {'lowAmmoPercentage': 20})
        self.assertEqual(len(refreshed), 2)
        controller.stop()
        self.assertEqual(self.listeners, [])
