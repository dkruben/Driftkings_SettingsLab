# -*- coding: utf-8 -*-
import json
import weakref

from support import Hooks, RuntimeTest, module, source


class Model(object):
    def __init__(self, properties=0, commands=0):
        self.fields = {}
        self.properties = properties
        self._initialize()

    def _initialize(self):
        pass

    def _addStringProperty(self, name, value):
        self.fields[name] = value

    def _addViewModelProperty(self, name, value):
        self.fields[name] = value

    def _addCommand(self, name):
        return lambda *args: None

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _setString(self, index, value):
        self.fields['payload'] = value


class PluginMap(dict):
    def set(self, key, value):
        self[key] = value

    def remove(self, key):
        self.pop(key, None)


class Descriptor(object):
    def setUrl(self, url):
        self.url = url

    def getUrl(self):
        return self.url


class View(object):
    def __init__(self, layoutID=None, model=Model):
        self.model = model()

    def getViewModel(self):
        return self.model

    def _onLoading(self, *args):
        pass

    def _finalize(self):
        pass


class RandomHangar(object):
    pass


class UserMissionsPresenter(object):
    pass


class NativeClockTests(RuntimeTest):
    def setUp(self):
        super(NativeClockTests, self).setUp()
        self.catalog = self.load('interface_catalog')
        self.injected = []
        self.core = source('gameface/core.py', {
            'frameworks.wulf': module(ViewModel=Model), 'gui.impl.gen': module(R=None),
            'openwg_gameface': module(gf_mod_inject=lambda model, *a, **k: self.injected.append(model)),
            'driftkings.interface_catalog': self.catalog})

    def test_native_model_has_no_injection_and_other_nineteen_stay_on_openwg(self):
        model = self.core['native_payload_model']('DriftkingsHangarClock')()
        self.assertEqual(model.properties, 2)
        self.assertEqual(set(model.fields), set(('payload', 'DriftkingsUI')))
        self.assertFalse(self.injected)
        for name, spec in self.catalog.GAMEFACE.items():
            if spec['owner'] is not None and name != 'DriftkingsHangarClock':
                self.core['payload_model'](name)()
        self.assertEqual(len(self.injected), 19)
        self.assertRaises(ValueError, self.core['native_payload_model'], 'DriftkingsFooterLauncher')

    def test_native_registration_payload_and_disposal(self):
        hooks = Hooks()
        constants = self.load('_constants')
        controller = module(active=True, views=weakref.WeakKeyDictionary(), visible=weakref.WeakKeyDictionary())
        component = module(g_clockController=controller, main_settings='main')
        hangar = module(hangar_preferences_settings='hangar')
        values = {'main': {'enabled': True, 'clock': {'enabled': True, 'formats': [{'format': '%H:%M'}]}},
                  'hangar': {'enabled': True, constants.HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET: False}}
        resolved = [42]
        api = source('gameface/lobby/main.py', {
            'helpers': module(getClientLanguage=lambda: 'pt'),
            'importlib': module(import_module=lambda name: component if name.endswith('components.main') else hangar),
            'driftkings._constants': constants,
            'driftkings.core.hooks': module(override=hooks.override),
            'driftkings.gameface.lobby.common': module(HangarController=object, publish_card=self.load('gameface.payloads').publish_card),
            'driftkings.interface_catalog': self.catalog,
            'driftkings.settings.service': module(affects=lambda *args: True, settings_service=module(getComponentDict=lambda key: values[key])),
            'gui.impl.lobby.hangar.random.random_hangar': module(RandomHangar=RandomHangar),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.impl.gen.view_models.views.lobby.hangar.user_missions_plugin_model': module(UserMissionsPluginModel=Descriptor),
            'gui.impl.lobby.hangar.presenters.user_missions_presenter': module(UserMissionsPresenter=UserMissionsPresenter),
            'driftkings.gameface.core': module(INVALID_RES_ID=-1, resource_id=lambda key: resolved[0], native_payload_model=self.core['native_payload_model'])})
        api['calendar_names'] = lambda: {'days': ['Segunda']}
        api['install_clock_gameface']()
        plugins = PluginMap()
        vm = Model()
        vm.getPlugins = lambda: plugins
        presenter = module(viewModel=vm)
        load = hooks.get('UserMissionsPresenter', '_onLoading')
        self.assertEqual(load(lambda parent: 'native', presenter), 'native')
        self.assertEqual(plugins[42].getUrl(), self.catalog.GAMEFACE['DriftkingsHangarClock']['plugin'])
        descriptor = plugins[42]
        records = self.capture_log('Driftkings.gameface.lobby.main')
        load(lambda parent: None, presenter)
        self.assertIs(plugins[42], descriptor)
        self.assertTrue(records)
        parent = RandomHangar()
        controller.visible[parent] = True
        children = hooks.get('RandomHangar', '_getChildComponents')(lambda parent: {}, parent)
        child = children[42]()
        child._onLoading()
        payload = json.loads(child.model.fields['payload'])
        self.assertTrue(payload['config']['visible'])
        self.assertTrue(payload['config']['hidePrestige'])
        self.assertEqual(payload['config']['formats'][0]['format'], '%H:%M')
        values['hangar'][constants.HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET] = True
        child.refresh()
        self.assertFalse(json.loads(child.model.fields['payload'])['config']['hidePrestige'])
        child._finalize()
        self.assertFalse(list(controller.views))
        finalize = hooks.get('UserMissionsPresenter', '_finalize')
        self.assertEqual(finalize(lambda parent: 'disposed', presenter), 'disposed')
        self.assertNotIn(42, plugins)
        resolved[0] = -1
        self.assertEqual(load(lambda parent: 'native failure isolated', presenter), 'native failure isolated')
        self.assertFalse(plugins)
        self.assertTrue(any('Could not register' in record.getMessage() for record in records))
        self.assertFalse(self.injected)
