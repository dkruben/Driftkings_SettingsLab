# -*- coding: utf-8 -*-
import json
import weakref

from support import Hooks, RuntimeTest, module, source
from test_native_clock import Model, View, Descriptor, PluginMap, RandomHangar, UserMissionsPresenter


class NativeHangarMarksTests(RuntimeTest):
    def test_payload_events_registration_collision_and_individual_disposal(self):
        hooks = Hooks()
        catalog = self.load('interface_catalog')
        constants = self.load('_constants')
        injected = []
        core = source('gameface/core.py', {
            'frameworks.wulf': module(ViewModel=Model), 'gui.impl.gen': module(R=None),
            'openwg_gameface': module(gf_mod_inject=lambda *a, **k: injected.append(a)),
            'driftkings.interface_catalog': catalog})
        controller = module(views=weakref.WeakKeyDictionary(), visible=weakref.WeakKeyDictionary())
        component = module(g_controller=controller, LOG=self.load('logger').get_logger('test.native_marks'),
                           hangar_marks_of_excellence_settings='settings', has_marks_tier=lambda: True,
                           g_data=module(build_panel_model=lambda: {'vehicle': 'one', 'currentMark': 90}))
        installed = []
        current_event, sync_event = object(), object()
        resolved = [43]
        native_core = module(INVALID_RES_ID=-1, resource_id=lambda key: resolved[0],
                             native_payload_model=core['native_payload_model'])
        api = source('gameface/lobby/hangar_marks_of_excellence.py', {
            'importlib': module(import_module=lambda name: component),
            'driftkings._constants': constants,
            'CurrentVehicle': module(g_currentVehicle=module(onChanged=current_event)),
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=module(onSyncCompleted=sync_event))),
            'driftkings.common.utils.colorratting': module(getStatisticColor=lambda *a: '#ffffff'),
            'driftkings.gameface.lobby.common': module(HangarController=object,
                card_payload=lambda previous, config_only, visible, config, build: dict(build(), config={'visible': visible}),
                publish_card=self.load('gameface.payloads').publish_card,
                install_card=lambda *args: installed.append(args)),
            'driftkings.interface_catalog': catalog,
            'driftkings.settings.service': module(affects=lambda *a: True, settings_service=module(getComponentDict=lambda key: {'enabled': True, 'showInHangar': True})),
            'driftkings.views.marks_model': module(number_locale=lambda *a: {}),
            'driftkings.core.hooks': module(override=hooks.override),
            'driftkings.gameface.core': native_core,
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.impl.gen.view_models.views.lobby.hangar.user_missions_plugin_model': module(UserMissionsPluginModel=Descriptor),
            'gui.impl.lobby.hangar.presenters.user_missions_presenter': module(UserMissionsPresenter=UserMissionsPresenter)})
        api['install_gameface']()
        marks = installed[0][1]
        parent = RandomHangar()
        controller.visible[parent] = True
        child = marks(parent, 43)
        self.assertEqual([event for event, callback in child._getEvents()], [current_event, sync_event])
        child._onLoading()
        self.assertEqual(json.loads(child.model.fields['payload'])['vehicle'], 'one')
        component.g_data.build_panel_model = lambda: {'vehicle': 'two', 'currentMark': 91}
        child._getEvents()[0][1]()
        self.assertEqual(json.loads(child.model.fields['payload'])['vehicle'], 'two')
        child._finalize()
        previous = child.model.fields['payload']
        child.refresh()
        self.assertEqual(child.model.fields['payload'], previous)
        self.assertFalse(controller.views)
        clock = Descriptor(); clock.setUrl(catalog.GAMEFACE['DriftkingsHangarClock']['plugin'])
        plugins = PluginMap({42: clock})
        vm = Model(); vm.getPlugins = lambda: plugins
        presenter = module(viewModel=vm)
        loading = hooks.get('UserMissionsPresenter', '_onLoading')
        finalize = hooks.get('UserMissionsPresenter', '_finalize')
        loading(lambda *a: None, presenter)
        self.assertEqual(set(plugins), set((42, 43)))
        owned = plugins[43]
        loading(lambda *a: None, presenter)
        self.assertIs(plugins[43], owned)
        finalize(lambda *a: None, presenter)
        self.assertEqual(plugins, {42: clock})
        loading(lambda *a: None, presenter)
        replacement = Descriptor(); replacement.setUrl(plugins[43].getUrl())
        plugins[43] = replacement
        finalize(lambda *a: None, presenter)
        self.assertIs(plugins[43], replacement)  # same URL is insufficient ownership.
        plugins.pop(43)
        resolved[0] = -1
        loading(lambda *a: None, presenter)
        self.assertEqual(plugins, {42: clock})
        self.assertFalse(injected)
        # Exercise BOTH actual registration hooks in either order, not only a prefilled map.
        clock_core = module(INVALID_RES_ID=-1, resource_id=lambda key: 42,
                            native_payload_model=core['native_payload_model'])
        clock_api = source('gameface/lobby/main.py', {
            'helpers': module(getClientLanguage=lambda: 'pt'),
            'importlib': module(import_module=lambda name: component),
            'driftkings._constants': constants,
            'driftkings.core.hooks': module(override=hooks.override),
            'driftkings.gameface.lobby.common': module(HangarController=object, publish_card=lambda *a: None),
            'driftkings.interface_catalog': catalog,
            'driftkings.logger': self.load('logger'),
            'driftkings.settings.service': module(affects=lambda *a: True, settings_service=module()),
            'gui.impl.lobby.hangar.random.random_hangar': module(RandomHangar=RandomHangar),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.impl.gen.view_models.views.lobby.hangar.user_missions_plugin_model': module(UserMissionsPluginModel=Descriptor),
            'gui.impl.lobby.hangar.presenters.user_missions_presenter': module(UserMissionsPresenter=UserMissionsPresenter),
            'driftkings.gameface.core': clock_core})
        clock_api['install_clock_gameface']()
        clock_load = hooks.get('UserMissionsPresenter', '_onLoading')
        clock_finalize = hooks.get('UserMissionsPresenter', '_finalize')
        resolved[0] = 43
        for order in ((clock_load, loading), (loading, clock_load)):
            plugins.clear()
            for load in order:
                load(lambda *a: None, presenter)
            self.assertEqual(set(plugins), set((42, 43)))
            clock_finalize(lambda *a: None, presenter)
            self.assertEqual(set(plugins), set((43,)))
            clock_load(lambda *a: None, presenter)
            finalize(lambda *a: None, presenter)
            self.assertEqual(set(plugins), set((42,)))
