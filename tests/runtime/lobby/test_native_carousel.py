# -*- coding: utf-8 -*-
"""Actual carousel adapter and Wulf command contract with isolated native services."""
import json
from support import Hooks, RuntimeTest, module, source
from support.baselines import baseline
from test_native_clock import Model, View, Descriptor, PluginMap, RandomHangar, UserMissionsPresenter


class Command(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def __call__(self, args):
        for handler in list(self.handlers):
            handler(args)


class CommandModel(Model):
    def __init__(self, properties=0, commands=0):
        self.commands = commands
        self.names = []
        super(CommandModel, self).__init__(properties, commands)

    def _addCommand(self, name):
        self.names.append(name)
        return Command()


class NativeView(View):
    def _onLoading(self, *args):
        for event, handler in self._getEvents():
            event += handler

    def _finalize(self):
        for event, handler in self._getEvents():
            event -= handler


class NativeCarouselTests(RuntimeTest):
    def setUp(self):
        super(NativeCarouselTests, self).setUp()
        self.catalog = self.load('interface_catalog')
        self.injected = []
        self.core = source('gameface/core.py', {
            'frameworks.wulf': module(ViewModel=CommandModel), 'gui.impl.gen': module(R=None),
            'openwg_gameface': module(gf_mod_inject=lambda *a, **k: self.injected.append(a)),
            'driftkings.interface_catalog': self.catalog})

    def test_factory_default_equivalence_and_native_command(self):
        # Source of native_payload_model as recorded from commit 501aec36.
        previous = baseline('native_crew')['sources']['native_payload_model']
        namespace = dict(self.core)
        eval(compile(previous, '<baseline>', 'exec'), namespace)
        for name in ('DriftkingsHangarClock', 'DriftkingsMarksOnGunHangar', 'DriftkingsCrewProgression'):
            old = namespace['native_payload_model'](name)()
            current = self.core['native_payload_model'](name)()
            self.assertEqual((old.properties, old.commands, old.names), (2, 0, []))
            self.assertEqual((current.properties, current.commands, current.names), (2, 0, []))
            self.assertEqual(set(old.fields), set(current.fields))
            self.assertEqual(old.fields['payload'], current.fields['payload'])
            self.assertEqual(old.fields['DriftkingsUI'].fields, current.fields['DriftkingsUI'].fields)
        current = self.core['native_payload_model']('DriftkingsCarouselStats', ('onRequestVehicles',))()
        self.assertEqual((current.properties, current.commands, current.names), (2, 1, ['onRequestVehicles']))
        self.assertFalse(self.injected)
        for name, spec in self.catalog.GAMEFACE.items():
            if spec['owner'] is not None and spec.get('transport', 'openwg') == 'openwg':
                self.core['payload_model'](name)()
        self.assertEqual(len(self.injected), 15)

    def adapter(self):
        hooks, installed, builds = Hooks(), [], []
        cache = module(onSyncCompleted=Command())
        current = module(onChanged=Command())
        common = source('gameface/lobby/common.py', {
            'driftkings.core.settings_controller': self.load('core.settings_controller'),
            'driftkings.gameface.payloads': self.load('gameface.payloads')})
        settings = module(getComponentDict=lambda config: {'enabled': True})
        comp = module(LOG=self.load('logger').get_logger('CarouselTest'), vehicle_carousel_settings=object(),
                      g_rowModels={}, g_data=module(invalidate=lambda: None,
                      build_panel_model=lambda ids: builds.append(ids) or {'config': {'visible': True}, 'vehicles': dict((str(i), {}) for i in ids)}))
        shared = dict(common, install_card=lambda *args: installed.append(args))
        alias = [46]
        api = source('gameface/lobby/vehicle_carousel.py', {
            'driftkings._constants': self.load('_constants'), 'driftkings.core': module(carousel=object()),
            'driftkings.core.carousel_options': module(from_carousel=lambda c: c),
            'driftkings.core.hooks': module(override=hooks.override),
            'driftkings.interface_catalog': self.catalog,
            'driftkings.settings.service': module(affects=lambda *args: True, settings_service=settings),
            'CurrentVehicle': module(g_currentVehicle=current),
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=cache)),
            'driftkings.common.utils.compat': module(string_types=(str, type(u''))),
            'driftkings.gameface.lobby.common': module(**shared),
            'gui.impl.pub.view_component': module(ViewComponent=NativeView),
            'gui.impl.gen.view_models.views.lobby.hangar.user_missions_plugin_model': module(UserMissionsPluginModel=Descriptor),
            'gui.impl.lobby.hangar.presenters.user_missions_presenter': module(UserMissionsPresenter=UserMissionsPresenter),
            'driftkings.gameface.core': module(INVALID_RES_ID=-1, native_payload_model=self.core['native_payload_model'], resource_id=lambda k: alias[0])})
        api['_component'] = lambda: comp
        api['get_view_config'] = lambda *args: {}
        comp.g_controller = api['CarouselController']()
        api['install_gameface']()
        parent = RandomHangar(); comp.g_controller.visible[parent] = True
        child = installed[0][1](parent, 46)
        return api, comp, parent, child, hooks, builds, alias

    def test_command_binding_validation_payload_and_disposal(self):
        api, comp, parent, child, hooks, builds, alias = self.adapter()
        child.requestVehicles({'ids': '123'})
        self.assertEqual(child._vehicleIds, ())  # Before loading.
        child._onLoading()
        cmd = child.getViewModel().onRequestVehicles
        self.assertEqual(len(cmd.handlers), 1)
        self.assertIsNone(cmd({'ids': '789,123,456,123,bad,-5,4.5'}))
        self.assertEqual(child._vehicleIds, (123, 456, 789))
        self.assertEqual(set(json.loads(child.model.fields['payload'])['vehicles']), set(('123', '456', '789')))
        count = len(builds); cmd({'ids': '456,789,123'})
        self.assertEqual(len(builds), count)
        for args in (None, [], '123', {'ids': []}, {'ids': '1' * 2049}):
            child.requestVehicles(args)
            self.assertEqual(child._vehicleIds, (123, 456, 789))
        cmd({'ids': ','.join(str(i) for i in range(125))})
        self.assertEqual(child._vehicleIds, tuple(range(120)))
        cmd({'ids': ''}); self.assertEqual(child._vehicleIds, ())
        child._finalize(); self.assertEqual(len(cmd.handlers), 0)
        before = len(builds); cmd({'ids': '999'}); child.requestVehicles({'ids': '999'})
        self.assertEqual(len(builds), before); self.assertEqual(child._vehicleIds, ())
        self.assertNotIn(parent, comp.g_controller.views)
        self.assertFalse(self.injected)

    def test_descriptor_only_removes_owned_instance(self):
        api, comp, parent, child, hooks, builds, alias = self.adapter()
        plugins = PluginMap()
        for i in (42, 43, 44):
            descriptor = Descriptor(); descriptor.setUrl('protected-' + str(i)); plugins[i] = descriptor
        vm = Model(); vm.getPlugins = lambda: plugins
        presenter = module(viewModel=vm)
        loading = hooks.get('UserMissionsPresenter', '_onLoading')
        finalize = hooks.get('UserMissionsPresenter', '_finalize')
        self.assertEqual(loading(lambda *args: 'original', presenter), 'original')
        owned = plugins[46]; loading(lambda *args: None, presenter); self.assertIs(plugins[46], owned)
        self.assertEqual(owned.getUrl(), self.catalog.GAMEFACE['DriftkingsCarouselStats']['plugin'])
        replacement = Descriptor(); replacement.setUrl(owned.getUrl()); plugins[46] = replacement
        finalize(lambda *args: None, presenter); self.assertIs(plugins[46], replacement)
        plugins.pop(46); loading(lambda *args: None, presenter)
        finalize(lambda *args: None, presenter); self.assertEqual(set(plugins), set((42, 43, 44)))
        alias[0] = -1; loading(lambda *args: None, presenter)
        self.assertEqual(set(plugins), set((42, 43, 44)))
