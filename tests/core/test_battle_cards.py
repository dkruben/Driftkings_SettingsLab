# -*- coding: utf-8 -*-
"""Shared battle cards preserve native ownership and UI lifecycle."""
from support import RuntimeTest, module, source


class BattleCardTests(RuntimeTest):
    def setUp(self):
        super(BattleCardTests, self).setUp()
        self.hooks = {}
        self.published = []
        self.connections = []
        self.cursor = False
        self.resource = 42
        test = self
        class Model(object):
            def __init__(self, **kwargs):
                self._initialize()
            def _initialize(self):
                pass
            def _addStringProperty(self, *args):
                pass
            def _addCommand(self, name):
                return name
        class View(object):
            def __init__(self, layoutID, model):
                self.model = model()
                self.enabled = True
                self.destroyed = False
            def getViewModel(self):
                return self.model
            def _onLoaded(self, *args, **kwargs):
                pass
            def _getEvents(self):
                return ()
            def _getListeners(self):
                return ()
            def _finalize(self):
                pass
            def setEnabled(self, value):
                self.enabled = value
            def destroy(self):
                self.destroyed = True
                self._finalize()
        class Parent(object):
            child = None
            def getChildView(self, resource):
                return self.child
        self.Parent = Parent
        def override(cls, name):
            def decorate(function):
                test.hooks[name] = function
                return function
            return decorate
        signal = module(connect=lambda *args: self.connections.append(args),
                        disconnect=lambda handler: self.connections.__setitem__(slice(None),
                            [entry for entry in self.connections if entry[0] != handler]))
        self.deps = {
            'driftkings.settings.service': module(settings_service=module(onModSettingsChanged=signal)),
            'driftkings.gameface.payloads': module(publish_card=lambda child, payload: self.published.append(payload)),
            'gui.impl.battle.random.hud': module(RandomHUDView=Parent),
            'frameworks.wulf': module(ViewModel=Model),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.shared': module(events=module(GameEvent=module(GUI_VISIBILITY=1, SHOW_CURSOR=2, HIDE_CURSOR=3)),
                                 EVENT_BUS_SCOPE=module(BATTLE=1, GLOBAL=2)),
            'driftkings.core.hooks': module(override=override),
            'driftkings.gameface.core': module(attach_assets=lambda *args: None, resource_id=lambda path: self.resource),
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {'resource': 'test'}),
            'GUI': module(mcursor=lambda: module(visible=self.cursor)),
        }
        base = source('gameface/batalha/common.py', self.deps)
        # Python 2 restricts metadata writes when source() replaces builtins.
        base['setattr'] = lambda target, name, value: setattr(target, name, value)
        self.base = base['BattleCardAdapter']
        class Adapter(self.base):
            def __init__(self):
                super(Adapter, self).__init__('test', 'namespace',
                    module(info=lambda *args: None, warning=lambda *args: None, exception=lambda *args: None),
                    'Test', active=True)
                self.positions = []
            def refresh(self):
                self.publish({'state': 'test'}, {'locked': False}, self.active and self.visible and self.hudVisible)
            def savePosition(self, child, args):
                self.positions.append(args)
        self.adapter = Adapter()
        self.adapter.install()
        self.assertEqual(self.hooks['_getChildComponents'].__module__, Adapter.__module__)

    def child(self, attached=True):
        parent = self.Parent()
        factories = self.hooks['_getChildComponents'](lambda parent: {3: 'native'}, parent)
        self.assertEqual(factories[3], 'native')
        child = factories[42]()
        if attached:
            parent.child = child
        return parent, child

    def test_pending_attachment_and_foreign_replacement(self):
        parent, child = self.child(False)
        child._onLoaded()
        self.assertEqual(self.published, [])
        self.assertIn(parent, self.adapter.views)
        parent.child = child
        self.adapter.refresh()
        self.assertTrue(child._attached)
        foreign = object()
        parent.child = foreign
        self.adapter.refresh()
        self.assertNotIn(parent, self.adapter.views)
        self.adapter.dispose()
        self.assertIs(parent.child, foreign)
        self.assertFalse(child.destroyed)

    def test_cursor_visibility_settings_and_owned_disposal(self):
        parent, child = self.child()
        child._onLoaded()
        self.assertFalse(self.published[-1]['config']['draggable'])
        child._showCursor(None)
        self.assertTrue(self.published[-1]['config']['draggable'])
        child._visibility(module(ctx={'visible': False}))
        self.assertFalse(self.published[-1]['config']['visible'])
        child._visibility(module(ctx={'visible': True}))
        self.adapter.setBattleHudVisible(False)
        self.assertFalse(self.published[-1]['config']['visible'])
        self.adapter.setBattleHudVisible(True)
        self.assertTrue(self.published[-1]['config']['visible'])
        child._hideCursor(None)
        self.assertFalse(self.published[-1]['config']['draggable'])
        child._savePosition({'x': 10})
        self.assertEqual(self.adapter.positions, [{'x': 10}])
        self.assertEqual(len(child._getEvents()), 1)
        self.assertEqual(len(child._getListeners()), 3)
        self.adapter.install()
        self.assertEqual(len(self.connections), 1)
        self.adapter.dispose()
        self.assertEqual(self.connections, [])
        self.assertEqual(len(self.adapter.views), 0)
        self.assertTrue(child.destroyed)
        self.assertFalse(child.enabled)

    def test_collision_missing_resource_and_tuple_native_children(self):
        parent = self.Parent()
        children = self.hooks['_getChildComponents']
        result = children(lambda parent: {42: 'foreign'}, parent)
        self.assertEqual(result, {42: 'foreign'})
        self.assertEqual(len(self.adapter.views), 0)
        self.resource = -1
        self.assertEqual(children(lambda parent: (1, 2), parent), {1: None, 2: None})

    def test_finalize_and_new_battle_child(self):
        parent, child = self.child()
        child._onLoaded()
        child._finalize()
        self.assertNotIn(parent, self.adapter.views)
        self.assertFalse(child._ready)
        second_parent, second = self.child()
        second._onLoaded()
        self.assertIn(second_parent, self.adapter.views)
        self.adapter.setVisible(False)
        self.assertFalse(self.published[-1]['config']['visible'])
        self.adapter.setVisible(True)
        self.assertTrue(self.published[-1]['config']['visible'])

    def test_marks_keep_replay_policy_state_and_position_settings(self):
        constants = self.load('_constants')
        key = constants.BATTLE_MARKS_OF_EXCELLENCE
        settings = source('settings/default_values.py', {})['DEFAULTS'][key.NAME]
        settings[key.SHOW_IN_REPLAY] = False
        settings[key.GAMEFACE]['locked'] = False
        changes, cleared, attached = [], [], []
        signal = self.load('core.signals').Signal()
        state = module(changed=signal, clear=lambda context: cleared.append(context),
                       snapshot=lambda context: {'state': 'progress'}, publish=lambda *args: True)
        service = self.deps['driftkings.settings.service'].settings_service
        service.getComponentDict = lambda config: settings
        service.apply = lambda config, values: changes.append(values)
        component = module(config=module(lang='en', i18n={'UI_description': 'Marks'}))
        deps = dict(self.deps)
        deps.update({
            'importlib': module(import_module=lambda name: component),
            'driftkings._constants': constants,
            'driftkings.gameface.batalha.common': module(BattleCardAdapter=self.base),
            'driftkings.core.marks_state': module(marks_state=state),
            'driftkings.core.hud_visibility': module(hudVisibility=module(
                attach=lambda adapter: attached.append(adapter), detach=lambda adapter: attached.remove(adapter))),
            'driftkings.views.marks_model': module(moved_panel=self.load('views.marks_model').moved_panel,
                                                  finite=lambda value: float(value),
                number_locale=lambda language: {'decimalSeparator': '.', 'groupSeparator': ','}),
            'BattleReplay': module(isPlaying=lambda: True),
        })
        adapter = source('gameface/batalha/battle_marks_of_excellence.py', deps)['BattleMarksAdapter']()
        adapter.install()
        adapter.startBattle()
        self.assertFalse(adapter.active)
        self.assertEqual(attached, [])
        settings[key.SHOW_IN_REPLAY] = True
        adapter.startBattle()
        self.assertTrue(adapter.active)
        self.assertEqual(attached, [adapter])
        adapter.savePosition(module(), {'x': 99999, 'y': -99999})
        self.assertEqual(changes[-1][key.PANEL]['x'], 7680)
        self.assertEqual(changes[-1][key.PANEL]['y'], -4320)
        settings[key.GAMEFACE]['locked'] = True
        adapter.savePosition(module(), {'x': 1, 'y': 2})
        self.assertEqual(len(changes), 1)
        adapter.stopBattle()
        self.assertFalse(adapter.active)
        self.assertEqual(attached, [])
        self.assertEqual(cleared, ['battle', 'battle'])
        # Avoid a second stop in dispose: native HudVisibility.detach is idempotent.
        deps['driftkings.core.hud_visibility'].hudVisibility.detach = lambda adapter: None
        adapter.dispose()
        adapter.refresh = lambda: changes.append('unexpected refresh')
        signal('battle')
        self.assertEqual(len(changes), 1)
