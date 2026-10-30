# -*- coding: utf-8 -*-
"""The battle-space event owns its native subscription only while active."""
from support import RuntimeTest, module, source


class UIEventsTests(RuntimeTest):
    def setUp(self):
        super(UIEventsTests, self).setUp()
        self.Signal = self.load('core.signals').Signal
        self.loader = module(onGUISpaceEntered=self.Signal())
        self.locator = module(appLoader=self.loader)
        self.api = source('ui/common/events.py', {
            'Event': module(SafeEvent=self.Signal),
            'gui.shared.personality': module(ServicesLocator=self.locator),
            'skeletons.gui.app_loader': module(GuiGlobalSpaceID=module(BATTLE='battle')),
        })

    def test_import_does_not_subscribe_and_start_stop_are_idempotent(self):
        events = self.api['g_events']
        loaded = []
        events.onBattleLoaded += lambda: loaded.append(True)
        self.assertEqual(len(self.loader.onGUISpaceEntered), 0)
        events.start()
        events.start()
        self.assertEqual(len(self.loader.onGUISpaceEntered), 1)
        self.loader.onGUISpaceEntered('lobby')
        self.assertEqual(loaded, [])
        self.loader.onGUISpaceEntered('battle')
        self.assertEqual(loaded, [True])
        events.stop()
        events.stop()
        self.assertEqual(len(self.loader.onGUISpaceEntered), 0)
        self.loader.onGUISpaceEntered('battle')
        self.assertEqual(loaded, [True])
        events.start()
        self.loader.onGUISpaceEntered('battle')
        self.assertEqual(loaded, [True, True])
        events.stop()

    def test_stop_uses_the_loader_that_received_the_subscription(self):
        events = self.api['Events']()
        events.start()
        replacement = module(onGUISpaceEntered=self.Signal())
        self.locator.appLoader = replacement
        events.stop()
        self.assertEqual(len(self.loader.onGUISpaceEntered), 0)
        self.assertEqual(len(replacement.onGUISpaceEntered), 0)
        events.start()
        self.assertEqual(len(replacement.onGUISpaceEntered), 1)
        events.stop()
