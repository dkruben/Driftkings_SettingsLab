# -*- coding: utf-8 -*-
"""Actual crew adapter/controller and CrewDetails with isolated Wulf services."""
import json

from support import Hooks, RuntimeTest, module, source
from test_native_clock import Model, View, Descriptor, PluginMap, RandomHangar, UserMissionsPresenter


class Signal(object):
    def __init__(self):
        self.callbacks = []

    def connect(self, callback, *args):
        self.callbacks.append(callback)

    def disconnect(self, callback):
        self.callbacks.remove(callback)


class Tooltip(object):
    def __init__(self):
        self.children = {}
        self.tankmanID = 222

    def getChildView(self, key):
        return self.children.get(key)

    def setChildView(self, key, value):
        self.children[key] = value


class NativeCrewRuntimeTests(RuntimeTest):
    def setUp(self):
        super(NativeCrewRuntimeTests, self).setUp()
        self.hooks = Hooks()
        self.catalog = self.load('interface_catalog')
        self.constants = self.load('_constants')
        self.injected, self.installed, self.details_installs = [], [], []
        self.signal = Signal()
        self.settings = {'enabled': True, 'showCrewProgression': True, 'showCrewTooltips': True}
        self.service = module(onModSettingsChanged=self.signal, getComponentDict=lambda config: self.settings)
        self.current = module(isPresent=lambda: True, item=module(intCD=11), onChanged=object())
        self.cache = module(items=module(getTankman=lambda key: module(descriptor=module(totalXP=lambda: 500))), onSyncCompleted=object())
        self.alias = [44]
        core = source('gameface/core.py', {
            'frameworks.wulf': module(ViewModel=Model), 'gui.impl.gen': module(R=None),
            'openwg_gameface': module(gf_mod_inject=lambda *args, **kwargs: self.injected.append(args)),
            'driftkings.interface_catalog': self.catalog})
        self.core = core
        common = source('gameface/lobby/common.py', {
            'driftkings.core.settings_controller': self.load('core.settings_controller'),
            'driftkings.gameface.payloads': self.load('gameface.payloads')})
        self.shared = dict(common, install_card=lambda *args: self.installed.append(args))
        self.api = source('gameface/lobby/crew_progression.py', {
            'CurrentVehicle': module(g_currentVehicle=self.current),
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=self.cache)),
            'driftkings._constants': self.constants,
            'driftkings.gameface.lobby.common': module(**self.shared),
            'driftkings.interface_catalog': self.catalog,
            'driftkings.lobby.crew_progression': module(collect_rows=lambda *args: [{'slot': 0, 'id': 101, 'lines': ['XP'], 'kinds': ['xp']}]),
            'driftkings.logger': self.load('logger'),
            'driftkings.settings.service': module(settings_service=self.service),
            'driftkings.views.crew_progression_model': module(progression_lines=lambda row, *args: row['lines'], progression_kinds=lambda row, *args: row['kinds']),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.impl.gen.view_models.views.lobby.hangar.user_missions_plugin_model': module(UserMissionsPluginModel=Descriptor),
            'gui.impl.lobby.hangar.presenters.user_missions_presenter': module(UserMissionsPresenter=UserMissionsPresenter),
            'driftkings.core.hooks': module(override=self.hooks.override),
            'driftkings.gameface.core': module(INVALID_RES_ID=-1, resource_id=lambda key: self.alias[0], native_payload_model=core['native_payload_model']),
            'driftkings.gameface.lobby': module(crew_details=module(install=lambda: self.details_installs.append(True)))})
        self.api['install'](module(lang='en', i18n={}))

    def test_payload_events_shared_controller_and_real_details_survive(self):
        controller = self.api['g_controller']
        controller.start(); controller.start()
        self.assertEqual(len(self.signal.callbacks), 1)
        parent = RandomHangar(); controller.visible[parent] = True
        child = self.installed[0][1](parent, 44); child._onLoading()
        payload = json.loads(child.model.fields['payload'])
        self.assertEqual(payload, {'config': {'visible': True}, 'vehicleId': 11,
                                  'rows': [{'slot': 0, 'id': 101, 'lines': ['XP'], 'kinds': ['xp']}]})
        self.assertEqual([event for event, callback in child._getEvents()], [self.current.onChanged, self.cache.onSyncCompleted])
        self.current.item.intCD = 22; child._getEvents()[0][1]()
        self.assertEqual(json.loads(child.model.fields['payload'])['vehicleId'], 22)
        self.settings['showCrewProgression'] = False
        controller.onSettingsChanged(None, {})
        self.assertEqual(json.loads(child.model.fields['payload']), {'config': {'visible': False}, 'rows': []})
        # Install and exercise the PROTECTED actual CrewDetails implementation, still OpenWG.
        details = source('gameface/lobby/crew_details.py', {
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=self.cache)),
            'driftkings._constants': self.constants,
            'driftkings.core.crew_progression': module(nonnegative=lambda value: value),
            'driftkings.core.hooks': module(override=self.hooks.override),
            'driftkings.gameface.lobby': module(crew_progression=module(**self.api)),
            'driftkings.gameface.lobby.common': module(publish_card=self.load('gameface.payloads').publish_card),
            'driftkings.interface_catalog': self.catalog,
            'driftkings.lobby.crew_progression': module(collect_tankman=lambda *args: {'lines': ['detail XP'], 'kinds': ['xp']}),
            'driftkings.logger': self.load('logger'),
            'driftkings.settings.service': module(settings_service=self.service),
            'driftkings.views.crew_progression_model': module(integer=lambda value, lang: str(value), translated=lambda *args: 'Total {xp}',
                progression_lines=lambda row, *args: row['lines'], progression_kinds=lambda row, *args: row['kinds']),
            'gui.impl.lobby.crew.barracks_view': module(BarracksView=type('BarracksView', (object,), {})),
            'gui.impl.lobby.crew.container_vews.personal_file.personal_file_view': module(PersonalFileView=type('PersonalFileView', (object,), {})),
            'gui.impl.lobby.crew.container_vews.service_record.service_record_view': module(ServiceRecordView=type('ServiceRecordView', (object,), {})),
            'gui.impl.lobby.crew.tooltips.tankman_tooltip': module(TankmanTooltip=Tooltip),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'driftkings.gameface.core': module(INVALID_RES_ID=-1, resource_id=lambda key: 45, payload_model=self.core['payload_model'])})
        details['install']()
        tooltip = Tooltip(); self.hooks.get('Tooltip', '_onLoading')(lambda *args: None, tooltip)
        detail = tooltip.children[45]; detail._onLoading()
        self.assertTrue(json.loads(detail.model.fields['payload'])['config']['visible'])
        self.assertEqual(len(self.injected), 1)  # only CrewDetails; no injection for CrewProgression.
        child._finalize()
        self.assertIs(controller.views[tooltip], detail)
        controller.onSettingsChanged(None, {})
        self.assertIn('detail XP', json.loads(detail.model.fields['payload'])['lines'])
        controller.stop(); controller.stop()
        self.assertIn(tooltip, controller.views)
        self.assertFalse(json.loads(detail.model.fields['payload'])['config']['visible'])
        controller.start(); detail.refresh()
        self.assertTrue(json.loads(detail.model.fields['payload'])['config']['visible'])
        self.assertEqual(self.details_installs, [True])
        detail._finalize(); self.assertFalse(controller.views)
        # A late finalize must not remove a replacement View at the same parent key.
        stale = self.installed[0][1](parent, 44)
        other = module(refresh=lambda: None)
        controller.views[parent] = other
        stale._finalize()
        self.assertIs(controller.views[parent], other)

    def test_three_descriptors_collision_and_owner_replacement(self):
        plugins = PluginMap()
        for alias, name in [(42, 'DriftkingsHangarClock'), (43, 'DriftkingsMarksOnGunHangar')]:
            descriptor = Descriptor(); descriptor.setUrl(self.catalog.GAMEFACE[name]['plugin']); plugins[alias] = descriptor
        vm = Model(); vm.getPlugins = lambda: plugins
        presenter = module(viewModel=vm)
        loading = self.hooks.get('UserMissionsPresenter', '_onLoading')
        finalize = self.hooks.get('UserMissionsPresenter', '_finalize')
        loading(lambda *args: None, presenter)
        self.assertEqual(set(plugins), set((42, 43, 44)))
        owned = plugins[44]; loading(lambda *args: None, presenter); self.assertIs(plugins[44], owned)
        finalize(lambda *args: None, presenter); self.assertEqual(set(plugins), set((42, 43)))
        loading(lambda *args: None, presenter)
        replacement = Descriptor(); replacement.setUrl(plugins[44].getUrl()); plugins[44] = replacement
        finalize(lambda *args: None, presenter); self.assertIs(plugins[44], replacement)
        plugins.pop(44); self.alias[0] = -1
        loading(lambda *args: None, presenter)
        self.assertEqual(set(plugins), set((42, 43)))
        self.assertFalse(self.injected)
