# -*- coding: utf-8 -*-
import json

from support import Hooks, RuntimeTest, game_source, module, source


class View(object):
    def __init__(self, **kwargs):
        self.model = module(onOpen=object(), _setString=lambda i, value: setattr(self, 'payload', json.loads(value)))
        self.destroyed = False

    def getViewModel(self):
        return self.model

    def _onLoading(self, *args):
        pass

    def _getEvents(self):
        return ()

    def _finalize(self):
        pass

    def destroy(self):
        self.destroyed = True
        self._finalize()


class Footer(object):
    def __init__(self):
        self.child = None

    def getChildView(self, resource):
        return self.child

    def setChildView(self, resource, child):
        self.child = child
        child._onLoading()


class LauncherTests(RuntimeTest):
    def setUp(self):
        super(LauncherTests, self).setUp()
        self.hooks = Hooks()
        self.calls = []
        self.controller = module(space=1, open=lambda: self.calls.append('open'))
        self.api = source('gameface/lobby/launcher.py', {
            'gui.impl.lobby.page.lobby_footer': module(LobbyFooter=Footer),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'skeletons.gui.app_loader': module(GuiGlobalSpaceID=module(LOBBY=1)),
            'driftkings.core.hooks': module(override=self.hooks.override),
            'driftkings.gameface.core': module(payload_model=lambda *a: object, resource_id=lambda key: 42),
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'launcher'})})
        self.launcher = self.api['FooterLauncher'](self.controller, 'Settings')

    def attach(self, footer):
        return self.hooks.get('Footer', '_initChildren')(lambda parent: 'native', footer)

    def test_callback_single_child_context_and_cleanup(self):
        self.launcher.start()
        self.launcher.start()
        footer = Footer()
        self.assertEqual(self.attach(footer), 'native')
        child = footer.child
        self.attach(footer)
        self.assertIs(footer.child, child)
        child.open()
        self.assertEqual(self.calls, ['open'])
        self.controller.space = 2
        self.launcher.refresh()
        self.assertFalse(child.payload['visible'])
        child.open()
        self.assertEqual(self.calls, ['open'])
        self.launcher.stop()
        self.assertTrue(child.destroyed)
        self.assertFalse(list(self.launcher.views))

    def test_optional_footer_overrides_are_registered(self):
        class Variant(Footer):
            pass
        self.api['import_module'] = lambda path: module(**dict((name, Variant) for unused, name in self.api['FOOTERS']))
        self.launcher.start()
        footer = Variant()
        hook = self.hooks.get('Variant', '_initChildren')
        self.assertEqual(hook(lambda parent: 'variant', footer), 'variant')
        self.assertIsNotNone(footer.child)
        self.launcher.stop()
        self.assertTrue(footer.child.destroyed)

    def test_cycles_and_failed_attachment_preserve_native_behavior(self):
        self.launcher.start()
        for unused in range(3):
            footer = Footer()
            self.attach(footer)
            footer.child.destroy()
            self.assertFalse(list(self.launcher.views))
        bad = Footer()
        def fail(*args):
            raise RuntimeError('unsupported footer')
        bad.setChildView = fail
        records = self.capture_log('Driftkings.Launcher')
        self.assertEqual(self.attach(bad), 'native')
        self.assertTrue(any('Could not attach' in record.getMessage() for record in records))
        self.launcher.stop()
        footer = Footer()
        self.attach(footer)
        self.assertIsNone(footer.child)


class SettingsLauncherServiceTests(RuntimeTest):
    def test_service_without_modslist_and_repeated_context_cycles(self):
        events = []
        class ForbiddenAPI(object):
            def __getattr__(self, name):
                raise AssertionError('ModsList must not be used')
        class Launcher(object):
            def __init__(self, controller, title):
                events.append('create')
            def start(self):
                events.append('start')
            def refresh(self):
                events.append('refresh')
            def stop(self):
                events.append('stop')
        controller = module(start=lambda settings: None, stop=lambda: None,
                            onContextEntered=lambda space: None, onContextLeft=lambda space: None)
        settings = module(strings={'title': 'Settings'}, start=lambda lang: None)
        api = source('settings/__init__.py', {
            'driftkings.settings.loader': module(settings_loader=None),
            'driftkings.settings.settings_data': module(user_settings=None),
            'driftkings.settings.registry': module(registry=module(register=lambda value: None)),
            'helpers': module(getClientLanguage=lambda: 'en', getClientVersion=lambda: 'CT'),
            'driftkings.settings.profiles': module(ProfileSettings=lambda *args: None),
            'driftkings.gameface.lobby.settings_window': module(controller=controller),
            'driftkings.settings.panel': module(settings=settings),
            'driftkings.settings.panel.sections': module(SectionPanelBinding=lambda *args: None),
            'driftkings.gameface.lobby.launcher': module(FooterLauncher=Launcher),
            'driftkings.core.diagnostics': module(diagnostics=module(configure=lambda value: None)),
            'gui.modsListApi': ForbiddenAPI()})
        service = api['SettingsService']()
        for unused in range(3):
            service.start()
            service.start()
            self.assertTrue(service.active)
            service.onContextEntered(1)
            service.onContextLeft(1)
            service.stop()
        self.assertEqual(events.count('create'), 1)
        self.assertEqual(events.count('start'), 3)
        self.assertEqual(events.count('stop'), 3)
        self.assertEqual(events.count('refresh'), 6)


class ExistingSettingsControllerTests(RuntimeTest):
    def test_launcher_delegation_preserves_single_window_shortcut_and_contexts(self):
        player = module(arena=None, databaseID=7)
        api, unused = game_source('gameface/lobby/settings_window.py', {
            'BigWorld': module(player=lambda: player, isKeyDown=lambda key: False),
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'settings'}),
            'gui.impl.pub': module(ViewImpl=object),
            'gui.impl.pub.window_impl': module(WindowImpl=object),
            'skeletons.gui.app_loader': module(GuiGlobalSpaceID=module(LOBBY=1, BATTLE=2, REPLAY=3)),
            'driftkings.settings.panel.presenter': module(CORE_ID='core', MAX_REQUEST=2048, Presenter=object)})
        controller = api['SettingsController']()
        controller.api = module(get=lambda *args: [[68]])
        windows = []
        class Window(object):
            def __init__(self, owner):
                self.owner = owner
                self.content = module(presenter=module(capture=None, handle=lambda data: {'close': True}))
                windows.append(self)
            def load(self):
                pass
            def destroy(self):
                self.owner.windowClosed(self)
        api['SettingsWindow'] = Window
        controller.onContextEntered(0)
        self.assertFalse(controller.open())
        controller.onContextEntered(1)
        self.assertTrue(controller.open())
        self.assertFalse(controller.open())
        self.assertEqual(len(windows), 1)
        controller.close()
        event = module(key=68, isKeyDown=lambda: True)
        controller.onKey(event)
        self.assertEqual(len(windows), 2)
        controller.onKey(event)
        self.assertIsNone(controller.window)
        controller.open()
        controller.onContextLeft(1)
        self.assertIsNone(controller.window)
        controller.onContextEntered(2)
        self.assertFalse(controller.open())
        player.arena = object()
        self.assertTrue(controller.open())
        controller.close()
