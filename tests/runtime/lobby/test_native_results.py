# -*- coding: utf-8 -*-
import json
import weakref
from support import Hooks, RuntimeTest, module, source
from test_native_clock import Model, View


class TrackingModel(Model):
    def __init__(self, properties=0, commands=0):
        self.commands = commands
        self.writes = []
        super(TrackingModel, self).__init__(properties, commands)

    def _setString(self, index, value):
        self.writes.append(value)
        super(TrackingModel, self)._setString(index, value)


class ResultsParent(object):
    arenaUniqueID = 123


class NativeResultsTests(RuntimeTest):
    def setUp(self):
        super(NativeResultsTests, self).setUp()
        self.catalog = self.load('interface_catalog')
        self.injected = []
        self.core = source('gameface/core.py', {
            'frameworks.wulf': module(ViewModel=TrackingModel), 'gui.impl.gen': module(R=None),
            'openwg_gameface': module(gf_mod_inject=lambda *a, **k: self.injected.append(a)),
            'driftkings.interface_catalog': self.catalog})

    def adapter(self):
        self.result = object()
        self.enabled = True
        self.hooks = Hooks()
        self.comp = module(_results_views=weakref.WeakKeyDictionary(), battle_performance_settings=object(),
            LOG=self.load('logger').get_logger('ResultsTest'),
            make_results_payload=lambda result: {'enabled': True, 'html': '<font color="#FFFFFF">WN8: 123</font>'})
        service = module(getStatsCtrl=lambda arena: module(getResults=lambda: self.result))
        settings = module(getComponentDict=lambda config: {'enabled': self.enabled, 'battleResultsWindow': True})
        api = source('gameface/lobby/battle_performance.py', {
            'driftkings._constants': self.load('_constants'), 'driftkings.interface_catalog': self.catalog,
            'driftkings.settings.service': module(settings_service=settings),
            'driftkings.core.hooks': module(override=self.hooks.override),
            'gui.impl.lobby.battle_results.random_battle_results_view': module(RandomBattleResultsView=ResultsParent),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'helpers': module(dependency=module(instance=lambda cls: service)),
            'skeletons.gui.battle_results': module(IBattleResultsService=object),
            'driftkings.gameface.core': module(INVALID_RES_ID=-1, resource_id=lambda key: 61,
                native_payload_model=self.core['native_payload_model'])})
        api['_component'] = lambda: self.comp
        api['install_results_gameface']()
        self.parent = ResultsParent()
        children = self.hooks.get('ResultsParent', '_getChildComponents')(lambda view: {7: 'official'}, self.parent)
        self.assertEqual(children[7], 'official')
        return children[61]()

    def test_native_model_has_two_properties_zero_commands_and_no_injection(self):
        model = self.core['native_payload_model']('driftkingsbattleEfficiency')()
        self.assertEqual((model.properties, model.commands), (2, 0))
        self.assertEqual(set(model.fields), set(('payload', 'DriftkingsUI')))
        self.assertFalse(self.injected)

    def test_payload_updates_deduplication_and_finalization(self):
        child = self.adapter()
        child._onLoading()
        expected = {'enabled': True, 'html': '<font color="#FFFFFF">WN8: 123</font>'}
        self.assertEqual(json.loads(child.model.fields['payload']), expected)
        child.refresh(123)
        self.assertEqual(len(child.model.writes), 1)
        self.enabled = False
        child.refresh(123)
        self.assertEqual(json.loads(child.model.fields['payload']), {'enabled': False})
        child._finalize()
        before = len(child.model.writes)
        child.refresh(123)
        self.assertEqual(len(child.model.writes), before)
        self.assertNotIn(self.parent, self.comp._results_views)
        self.assertFalse(self.injected)

    def test_absent_results_and_reopened_child_do_not_reuse_payload(self):
        child = self.adapter()
        self.result = None
        child._onLoading()
        self.assertEqual(json.loads(child.model.fields['payload']), {'enabled': False})
        child._finalize()
        other = self.adapter()
        other._onLoading()
        self.assertTrue(json.loads(other.model.fields['payload'])['enabled'])
        self.assertIsNot(other.model, child.model)

    def test_previous_four_models_still_have_zero_commands(self):
        names = ('DriftkingsHangarClock', 'DriftkingsMarksOnGunHangar', 'DriftkingsCrewProgression', 'DriftkingsCarouselStats')
        for name in names:
            commands = ('onRequestVehicles',) if name == 'DriftkingsCarouselStats' else ()
            model = self.core['native_payload_model'](name, commands)()
            self.assertEqual(model.commands, len(commands))
        self.assertFalse(self.injected)
