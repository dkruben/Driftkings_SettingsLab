import ast
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import CAROUSEL_STATS, GLOBAL, MINIMAP_PLUGINS
from Driftkings.core import carousel as layout
from Driftkings.core.carousel_options import from_carousel
from Driftkings.settings import loader
from Driftkings.settings.carousel_store import CarouselStore, FILES
from Driftkings.settings.service import SettingsService, SettingsChanges, affects
from Driftkings.settings.settings_data import SettingsData
from Driftkings.settings.store import merge
from Driftkings.views.hangar.common import HangarController, card_payload


def load(path, name, namespace):
    tree = ast.parse((CLIENT / 'Driftkings' / path).read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if getattr(node, 'name', None) == name]
    exec(compile(tree, path, 'exec'), namespace)
    return namespace[name]


class CarouselSettingsOwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        replace = patch.object(loader, 'settings_loader', loader.SettingsLoader(self.tmp.name))
        replace.start()
        self.addCleanup(replace.stop)
        self.service = SettingsService(SettingsData())
        self.ns = dict(CAROUSEL_STATS=CAROUSEL_STATS, GLOBAL=GLOBAL, ComponentSettings=object,
                       CarouselStore=CarouselStore, FILES=FILES, merge=merge, settings_service=self.service,
                       HangarController=HangarController, affects=affects, layout=layout, from_carousel=from_carousel)
        cls = load('settings/templates/lobby/carousel.py', 'CarouselStatsSettings', self.ns)
        self.owner = cls()
        self.owner.ID = CAROUSEL_STATS.ID
        self.owner.configPath = str(Path(self.tmp.name) / 'legacy')
        self.owner.data = {}
        self.owner.readData()
        self.owner.data['carousel']['rows'] = 0
        self.owner.profileStore().save(self.owner.data)
        self.notifications = []
        self.service.onModSettingsChanged.connect(lambda part, values:self.notifications.append(values), CAROUSEL_STATS)

    def test_split_files_and_sorting_menu_roundtrip_notify_after_save(self):
        current = self.owner.data
        self.service.apply(self.owner, {'sortingCriteria':'-level, nation', 'carousel':{'rows':2}})
        self.assertIs(self.owner.data, current)
        self.assertEqual(current['carousel']['sorting_criteria'], ['-level', 'nation'])
        self.assertEqual(len(self.notifications), 1)
        self.assertIn(('carousel', 'rows'), self.notifications[0].paths)
        self.owner.readData()
        self.assertEqual(self.owner.data['sortingCriteria'], '-level, nation')
        self.assertEqual(self.owner.data['carousel']['rows'], 2)
        self.service.apply(self.owner, {'carousel':{'rows':2}})
        self.assertEqual(len(self.notifications), 1)

    def test_rejected_values_or_failed_save_preserve_files_memory_and_notifications(self):
        directory = Path(self.owner.profileStore().directory)
        files = {name:(directory/name).read_bytes() for name in FILES}
        before = deepcopy(self.owner.data)
        for values in ({'sortingCriteria':'not_a_criterion'}, {'carousel':{'rows':5}}):
            with self.assertRaises(ValueError): self.service.apply(self.owner, values)
            self.assertEqual(self.owner.data, before)
        with patch.object(CarouselStore, 'publish', side_effect=IOError('simulated save failure')):
            with self.assertRaises(IOError): self.service.apply(self.owner, {'carousel':{'rows':2}})
        self.assertEqual(self.owner.data, before)
        self.assertEqual({name:(directory/name).read_bytes() for name in FILES}, files)
        self.assertEqual(self.notifications, [])

    def test_controller_subscribes_once_and_limits_native_updates(self):
        model, presenter, child = Mock(), Mock(), NS(refreshSettings=Mock())
        self.ns['_component'] = lambda:NS(g_rowModels={model:1}, g_filterPresenters=[presenter])
        cls = load('views/hangar/carousel.py', 'CarouselController', self.ns)
        controller = cls()
        controller.views = {1:child}
        controller.start(); controller.start()
        signal = self.service.onModSettingsChanged
        changes = SettingsChanges({'carousel':{'rows':2}}, [('carousel','rows')])
        signal.emit(MINIMAP_PLUGINS.NAME, changes)
        child.refreshSettings.assert_not_called()
        signal.emit(CAROUSEL_STATS.NAME, changes)
        model.setCarouselRowCount.assert_called_once_with(1)
        presenter._VehicleFiltersDataProvider__updateModel.assert_not_called()
        child.refreshSettings.assert_called_once_with(changes)
        controller.stop(); controller.stop()
        signal.emit(CAROUSEL_STATS.NAME, changes)
        child.refreshSettings.assert_called_once()

    def test_visual_config_keeps_native_rows_and_reuses_vehicle_output(self):
        inventory = NS(getFreeSlots=Mock(return_value=3))
        self.ns['ServicesLocator'] = NS(itemsCache=NS(items=NS(stats=NS(vehicleSlots=10), inventory=inventory)))
        build_config = load('views/hangar/carousel.py', 'get_view_config', self.ns)
        before = deepcopy(self.owner.data)
        panel = build_config(self.owner, {'native':2})
        self.assertEqual(panel['effectiveRows'], layout.row_count(before['carousel'], 2))
        self.assertEqual((panel['totalSlots'],panel['freeSlots'],panel['usedSlots']), (10,3,7))
        self.assertEqual(self.owner.data, before)
        previous = {'config':dict(panel, visible=True), 'vehicles':{'7':{'normal':[]}}}
        self.owner.data['carousel']['backgroundAlpha'] = 25
        build_vehicles = Mock()
        result = card_payload(previous, True, True, lambda:build_config(self.owner, {'native':2}), build_vehicles)
        build_vehicles.assert_not_called()
        self.assertEqual(result['vehicles'], previous['vehicles'])
        self.assertEqual(result['config']['backgroundAlpha'], 25)


if __name__ == '__main__':
    unittest.main()
