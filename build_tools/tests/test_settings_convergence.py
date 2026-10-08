import ast
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import GLOBAL, MINIMAP_PLUGINS, SIXTH_SENSE, PLAYER_PANEL_PRO, MARKS_ON_GUN_BATTLE
from Driftkings.settings.dependencies import option_dependencies
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData
from Driftkings.settings.template_schema import field


def method(path, cls, name, namespace):
    tree = ast.parse((CLIENT / 'Driftkings' / path).read_text(encoding='utf-8-sig'))
    parent = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls)
    node = next(n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


class SettingsConvergenceTests(unittest.TestCase):
    def test_inverse_boolean_and_enum_dependencies_use_ui_values(self):
        controls = [field(['defaultIcon'], 'Default'), field(['defaultIconName'], 'Icon', 'Dropdown'),
                    field(['userIcon'], 'User', 'Dropdown')]
        deps = option_dependencies(SIXTH_SENSE.ID, controls)
        self.assertEqual(deps['defaultIconName'], {'defaultIcon': [True]})
        self.assertEqual(deps['userIcon'], {'defaultIcon': [False]})
        controls = [field(['hpVisibility'], 'HP', 'Dropdown', choices=['never', 'hold', 'always']),
                    field(['hpKey'], 'Key', 'HotKey')]
        self.assertEqual(option_dependencies(PLAYER_PANEL_PRO.ID, controls)['hpKey'], {'hpVisibility': [1]})

    def test_nested_dependencies_are_scoped_and_support_custom_profiles(self):
        controls = [field(['profiles', 'custom', 'enabled'], 'Profile'),
                    field(['profiles', 'custom', 'bar', 'enabled'], 'Bar'),
                    field(['profiles', 'custom', 'bar', 'width'], 'Width', 'Slider', 1, 100),
                    field(['profiles', 'other', 'width'], 'Other', 'Slider', 1, 100)]
        deps = option_dependencies(PLAYER_PANEL_PRO.ID, controls)
        self.assertEqual(deps['profiles.custom.bar.width'], {'profiles.custom.enabled': [True],
                                                           'profiles.custom.bar.enabled': [True]})
        self.assertNotIn('profiles.other.width', deps)
        self.assertNotIn('profiles.custom.enabled', deps)

    def test_minimap_refresh_covers_flash_options_without_rebuilding_native_circles(self):
        service = SettingsService(SettingsData())
        personal, vehicles, view = Mock(), Mock(), Mock()
        controller = NS(config=NS(data={'enabled': True, 'presentation': {'alternativeEnabled': True}}), minimapZoom=False,
                    setAlternative=Mock())
        refresh = method('battle/minimap.py', 'MinimapController', 'onModSettingsChanged',
                         dict(settings_service=service, GLOBAL=GLOBAL, MINIMAP_PLUGINS=MINIMAP_PLUGINS,
                              PERSONAL=[personal], VEHICLES=[vehicles], VIEWS=[view]))
        for key in ('health', 'icons', 'mapSize', 'extraCircles', 'artilleryAim', 'showVehicleTypes'):
            with self.subTest(key=key):
                view.reset_mock()
                refresh(controller, MINIMAP_PLUGINS.NAME, {key: {}})
                view.onAltKey.assert_called_once_with(False)
                personal.refreshPresentation.assert_not_called()
                vehicles.refreshLabels.assert_not_called()
        refresh(controller, MINIMAP_PLUGINS.NAME, {'labels': {}})
        vehicles.refreshLabels.assert_called_once()
        personal.refreshPresentation.assert_not_called()
        refresh(controller, MINIMAP_PLUGINS.NAME, {'circles': {}})
        personal.refreshPresentation.assert_called_once()
        vehicles.refreshLabels.assert_called_once()

    def test_marks_drag_saves_changed_position_before_updating_display(self):
        service = SettingsService(SettingsData())
        config = NS(ID=MARKS_ON_GUN_BATTLE.ID, data={'panel': {'x': 1, 'y': 2}})
        saved = []
        def save(changes):
            # A mutation before service.apply would have suppressed this save.
            saved.append(changes)
            config.data['panel'].update(changes['panel'])
        config.onApplySettings = save
        view = NS(data={'label': {'x': 1, 'y': 2}}, setupSize=Mock())
        move = method('views/battle/gun_marks.py', 'Flash', '__updatePosition',
                      dict(settings_service=service, _component=lambda: NS(config=config),
                           ElementType=NS(LABEL='label'), MARKS_ON_GUN_BATTLE=MARKS_ON_GUN_BATTLE))
        move(view, 'unrelated', {'x': 99})
        self.assertEqual(saved, [])
        move(view, config.ID, {'x': 10, 'y': None})
        self.assertEqual(saved, [{'panel': {'x': 10, 'y': 2}}])
        self.assertEqual(view.data['label'], {'x': 10, 'y': 2})
        move(view, config.ID, {'x': 10})
        self.assertEqual(len(saved), 1)

    def test_marks_owner_keeps_new_numeric_values_instead_of_restoring_previous_ones(self):
        class Storage:
            def onApplySettings(self, values): self.saved = values
        path = CLIENT / 'Driftkings/settings/templates/battle/gun_marks.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'MarksOnGunBattleSettings')
        node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == 'onApplySettings']
        namespace = dict(ComponentSettings=Storage, MARKS_ON_GUN_BATTLE=MARKS_ON_GUN_BATTLE)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
        owner = namespace['MarksOnGunBattleSettings']()
        owner.onApplySettings({'panel': {'x': 42, 'y': -50, 'width': 200, 'text': 'transient'}})
        self.assertEqual(owner.saved, {'panel': {'x': 42.0, 'y': -50.0, 'width': 200.0}})

    def test_reticle_state_never_overwrites_stored_preferences(self):
        from Driftkings._constants import DISPERSION_CIRCLE
        from Driftkings.settings.settings_data import defaults
        tree = ast.parse((CLIENT / 'Driftkings/battle/dispersion_circle.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ReticleState')
        native, custom = {'native': 'native'}, {'custom': 'custom'}
        aih, factory = NS(GUN_MARKER_MIN_SIZE=5), NS(_GUN_MARKER_LINKAGES=native)
        namespace = dict(settings_service=SettingsService(SettingsData()), GLOBAL=GLOBAL,
            DISPERSION_CIRCLE=DISPERSION_CIRCLE, aih_constants=aih, gm_factory=factory,
            CUSTOM_GUN_MARKER_LINKAGES=custom)
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'dispersion', 'exec'), namespace)
        config = NS(data=defaults(DISPERSION_CIRCLE.ID))
        config.data['showClientAndServerReticleBeta'] = True
        config.data['percentCorrection'] = 50
        before = deepcopy(config.data)
        state = namespace['ReticleState'](config)
        state.start()
        self.addCleanup(state.stop)
        self.assertTrue(state.showClientAndServerReticle)
        self.assertEqual(state.reticleScaleFactor, 1.355)
        self.assertEqual(factory._GUN_MARKER_LINKAGES, dict(native, **custom))
        self.assertEqual(config.data, before)
        config.data['enabled'] = False
        before = deepcopy(config.data)
        state.applySettings()
        self.assertFalse(state.showClientAndServerReticle)
        self.assertIs(factory._GUN_MARKER_LINKAGES, native)
        self.assertEqual(aih.GUN_MARKER_MIN_SIZE, 5)
        self.assertEqual(config.data, before)
        config.data['enabled'] = True
        state.applySettings()
        self.assertTrue(state.showClientAndServerReticle)

    def test_card_layout_reuses_vehicle_data_but_reopening_rebuilds(self):
        from Driftkings.views.hangar.common import card_payload
        previous = {'config': {'visible': True, 'x': 1}, 'vehicle': 'T-34', 'average': 2000}
        build = Mock(return_value={'config': {}, 'vehicle': 'Tiger'})
        config = lambda: {'x': 8}
        result = card_payload(previous, True, True, config, build)
        build.assert_not_called()
        self.assertEqual(result['average'], 2000)
        self.assertEqual(result['config'], {'x': 8, 'visible': True})
        self.assertEqual(previous['config']['x'], 1)
        hidden = card_payload(result, True, False, config, build)
        self.assertNotIn('vehicle', hidden)
        reopened = card_payload(hidden, True, True, config, build)
        build.assert_called_once()
        self.assertEqual(reopened['vehicle'], 'Tiger')

    def test_carousel_native_models_update_only_for_relevant_options(self):
        from Driftkings._constants import CAROUSEL_STATS
        from Driftkings.settings.service import SettingsChanges, affects
        from Driftkings.views.hangar.common import HangarController
        tree = ast.parse((CLIENT / 'Driftkings/views/hangar/carousel.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CarouselController')
        model, presenter, child = Mock(), Mock(), NS(refreshSettings=Mock())
        component = NS(g_rowModels={model: 2}, g_filterPresenters=[presenter])
        ns = dict(HangarController=HangarController, _component=lambda: component,
                  affects=affects, GLOBAL=GLOBAL, CAROUSEL_STATS=CAROUSEL_STATS)
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'carousel', 'exec'), ns)
        controller = ns['CarouselController']()
        controller.views = {1: child}
        controller.onApplySettings(SettingsChanges({'carousel': {'rows': 2, 'backgroundAlpha': 50}},
                                                   [('carousel', 'backgroundAlpha')]))
        model.setCarouselRowCount.assert_not_called()
        presenter._VehicleFiltersDataProvider__updateModel.assert_not_called()
        child.refreshSettings.assert_called_once()
        controller.onApplySettings(SettingsChanges({'carousel': {'rows': 1}}, [('carousel', 'rows')]))
        model.setCarouselRowCount.assert_called_once_with(2)
        presenter._VehicleFiltersDataProvider__updateModel.assert_not_called()
        controller.onApplySettings(SettingsChanges({'carousel': {}}, [('carousel', 'nations_order')]))
        presenter._VehicleFiltersDataProvider__updateModel.assert_called_once()
        self.assertFalse(controller.updatingSettings)
        model.reset_mock()
        controller.onApplySettings(SettingsChanges({'carousel': {}}, [('carousel', 'cellType')]))
        model.setCarouselRowCount.assert_called_once_with(2)

    def test_hangar_views_rebuild_only_when_vehicle_output_changes(self):
        from Driftkings._constants import CAROUSEL_STATS, MARKS_ON_GUN_HANGAR
        from Driftkings.settings.service import SettingsChanges, affects
        for path, cls, layout_path, data_path in (
            ('views/hangar/carousel.py', 'CarouselView', ('carousel', 'backgroundAlpha'), ('carousel', 'normal', 'extraFields')),
            ('views/hangar/gun_marks.py', 'MarksView', ('panel', 'x'), ('goalSelection',))):
            with self.subTest(view=cls):
                callback = method(path, cls, 'refreshSettings', dict(affects=affects, GLOBAL=GLOBAL,
                            CAROUSEL_STATS=CAROUSEL_STATS, MARKS_ON_GUN_HANGAR=MARKS_ON_GUN_HANGAR))
                view = NS(refresh=Mock())
                callback(view, SettingsChanges({}, [layout_path]))
                view.refresh.assert_called_once_with(config_only=True)
                view.refresh.reset_mock()
                callback(view, SettingsChanges({}, [data_path]))
                view.refresh.assert_called_once_with(config_only=False)

    def test_minimap_dependencies_follow_visibility_and_display_mode(self):
        controls = [field(['health', 'visibility'], 'HP', 'Dropdown', choices=['never', 'key', 'always']),
                    field(['health', 'mode'], 'Mode', 'Dropdown', choices=['value', 'percent', 'bar']),
                    field(['health', 'width'], 'Width', 'Slider', 10, 100),
                    field(['health', 'fontSize'], 'Font', 'Slider', 8, 24),
                    field(['lostMarker', 'fade'], 'Fade'),
                    field(['lostMarker', 'minimumAlpha'], 'Alpha', 'Slider', 0, 100),
                    field(['labels', 'customColors'], 'Colors'),
                    field(['labels', 'allyColor'], 'Ally', 'ColorChoice')]
        deps = option_dependencies(MINIMAP_PLUGINS.ID, controls)
        self.assertEqual(deps['health.width'], {'health.visibility': [1, 2], 'health.mode': [2]})
        self.assertEqual(deps['health.fontSize'], {'health.visibility': [1, 2], 'health.mode': [0, 1]})
        self.assertEqual(deps['lostMarker.minimumAlpha'], {'lostMarker.fade': [True]})
        self.assertEqual(deps['labels.allyColor'], {'labels.customColors': [True]})

    def test_hangar_publication_skips_identical_output_and_retries_failed_transactions(self):
        from contextlib import contextmanager
        from Driftkings.views.hangar.common import publish_card
        sent = []
        failure = [False]
        @contextmanager
        def transaction():
            yield NS(_setString=lambda index, value: sent.append(value))
            if failure[0]:
                raise RuntimeError('transaction failed')
        view = NS(_lastPayload=None, getViewModel=lambda: NS(transaction=transaction))
        first = {'config': {'visible': True}, 'vehicle': 'Tiger'}
        self.assertTrue(publish_card(view, first))
        self.assertFalse(publish_card(view, deepcopy(first)))
        self.assertEqual(len(sent), 1)
        changed = {'config': {'visible': True, 'x': 12}, 'vehicle': 'Tiger'}
        failure[0] = True
        with self.assertRaises(RuntimeError):
            publish_card(view, changed)
        self.assertEqual(view._lastPayload, first)
        failure[0] = False
        self.assertTrue(publish_card(view, changed))
        hidden = {'config': {'visible': False}}
        self.assertTrue(publish_card(view, hidden))
        self.assertFalse(publish_card(view, deepcopy(hidden)))
        self.assertTrue(publish_card(view, changed))
        with self.assertRaises(ValueError):
            publish_card(view, {'config': {'x': float('nan')}})
        self.assertEqual(view._lastPayload, changed)

    def test_carousel_vehicle_requests_deduplicate_but_retry_after_publication_failure(self):
        request = method('views/hangar/carousel.py', 'CarouselView', 'requestVehicles', {'basestring': str})
        view = NS(_vehicleIds=(1, 2), _lastPayload={'config': {}}, refresh=Mock())
        request(view, {'ids': '2,1,2'})
        view.refresh.assert_not_called()
        request(view, {'ids': '2,3'})
        self.assertEqual(view._vehicleIds, (2, 3))
        view.refresh.assert_called_once()
        view.refresh.reset_mock()
        view._lastPayload = None
        request(view, {'ids': '2,3'})
        view.refresh.assert_called_once()

    def test_minimap_zoom_layout_requires_alternative_and_zoom(self):
        controls = [field(['presentation', 'alternativeEnabled'], 'Alternative'),
                    field(['presentation', 'zoom'], 'Zoom'),
                    field(['presentation', 'center'], 'Center'),
                    field(['presentation', 'sizeIndex'], 'Size', 'Slider', 0, 5)]
        deps = option_dependencies(MINIMAP_PLUGINS.ID, controls)
        for key in ('center', 'sizeIndex'):
            self.assertEqual(deps['presentation.' + key], {
                'presentation.alternativeEnabled': [True], 'presentation.zoom': [True]})
