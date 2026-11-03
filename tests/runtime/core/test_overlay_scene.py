# -*- coding: utf-8 -*-
"""The overlay scene forwards only changed properties, and keeps the full state for new views."""
from support import RuntimeTest, module, source


class OverlaySceneTests(RuntimeTest):
    def setUp(self):
        super(OverlaySceneTests, self).setUp()
        api = source('flash/core.py', {'driftkings.logger': module(get_logger=lambda name: None)})
        self.scene = api['OverlayScene']()
        self.sent = []
        self.view = module(update=lambda alias, props, duration: self.sent.append((alias, props, duration)),
                           createElement=lambda *args: None, reset=lambda elements: self.sent.append(('reset', elements)))
        self.scene.create('limits.L', 'image', {'x': 0, 'image': ''})
        self.scene.attach(self.view)
        del self.sent[:]

    def test_unchanged_properties_are_not_sent(self):
        self.assertTrue(self.scene.update('limits.L', {'x': 0, 'image': ''}, {'duration': 0.05}))
        self.assertEqual(self.sent, [])

    def test_only_changed_properties_are_sent(self):
        self.scene.update('limits.L', {'x': 10, 'image': ''}, {'duration': 0.05})
        self.assertEqual(self.sent, [('limits.L', {'x': 10}, 0.05)])
        self.scene.update('limits.L', {'x': 10, 'y': 4})
        self.assertEqual(self.sent[-1], ('limits.L', {'y': 4}, 0.0))

    def test_recreated_view_receives_every_stored_property(self):
        self.scene.update('limits.L', {'x': 10, 'image': 'left.png'})
        self.scene.attach(self.view)
        alias, elements = self.sent[-1]
        self.assertEqual(alias, 'reset')
        self.assertEqual(elements[0]['props'], {'x': 10, 'image': 'left.png'})

    def test_unknown_alias_is_rejected(self):
        self.assertFalse(self.scene.update('missing', {'x': 1}))
        self.assertEqual(self.sent, [])
