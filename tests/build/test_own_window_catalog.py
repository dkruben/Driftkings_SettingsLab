"""Own battle window transport: Nine battle HUD cards share one document that loads the catalog
assets once; counts 20/0/2."""
import copy
import unittest
from unittest.mock import patch

from build_tools import generate_ui_catalog as catalog

FEATURE = 'DriftkingsTeamStrength'
SHARED = ['DriftkingsAimingCountdown', 'DriftkingsBattleEfficiency', 'DriftkingsFlightTime', 'DriftkingsMainGun', 'DriftkingsMarksOnGunBattle', 'DriftkingsOwnHealth', 'DriftkingsPenetration', 'DriftkingsTargetInformation', 'DriftkingsTeamStrength']


class OwnWindowCatalogTests(unittest.TestCase):
    def test_transport_counts_and_bootstrap(self):
        face = catalog.read_catalog()['GAMEFACE']
        counts = catalog.validate()
        self.assertEqual((counts['gameface'], counts['native'], counts['injected']), (22, 20, 0))
        # The two lobby windows load their own layouts and are neither injected nor native transports.
        self.assertEqual(sorted(name for name, spec in face.items() if spec['owner'] is None),
                         ['DriftkingsAccountManager', 'DriftkingsModSettings'])
        self.assertEqual(sorted(name for name, spec in face.items() if spec.get('transport') == 'own_window'), SHARED)
        self.assertEqual(sorted(catalog.OWN_WINDOW_FEATURES), SHARED)
        host = catalog.read_catalog()['BATTLE_HUD_HOST']
        self.assertEqual(host['resource'], 'mods/driftkings/battle_hud/window')
        self.assertNotIn(host['resource'], [spec['resource'] for spec in face.values()])
        self.assertEqual(host['asset_priority'], (FEATURE,))
        source = (catalog.ROOT / 'mod/res/scripts/client/driftkings/gameface/battle/own_window.py').read_text(encoding='utf-8')
        self.assertIn("resource_id(BATTLE_HUD_HOST['resource'])", source)
        self.assertNotIn('HOST_FEATURE', source)
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        for name in SHARED:
            self.assertNotIn(name, block)  # no OpenWG loading, hence no second copy of its scripts
        battle = [name for name, spec in face.items() if spec['context'] == 'battle' and name not in SHARED]
        self.assertEqual(len(battle), 0)
        self.assertNotIn('DriftkingsRatingPlayers', block)
        self.assertEqual(face['DriftkingsRatingPlayers']['transport'], 'native_document')

    def test_document_loads_the_catalog_assets_once_in_order(self):
        face = catalog.read_catalog()['GAMEFACE']
        spec = face[FEATURE]
        host = catalog.read_catalog()['BATTLE_HUD_HOST']
        document = (catalog.ROOT / 'mod' / catalog.asset_target(host['layout'])).read_text(encoding='utf-8')
        self.assertEqual(document, (catalog.ROOT / 'mod' / catalog.asset_target(spec['layout'])).read_text(encoding='utf-8'))
        self.assertEqual(catalog.outputs(), catalog.outputs())
        self.assertEqual(document.count('<script src='), 15)
        self.assertEqual(document.count('<link rel='), 8)
        for name in SHARED:
            for url in face[name]['scripts'] + face[name]['styles']:
                self.assertEqual(document.count('"%s"' % url), 1, url)
            # Dependencies shared with earlier cards are already loaded; each precedes its renderer.
            positions = [document.index(url) for url in face[name]['scripts']]
            self.assertTrue(all(pos < positions[-1] for pos in positions[:-1]), name)
        self.assertNotIn('bootstrap.js', document)
        # TeamStrength keeps the loading order validated in the client; OwnHealth's own assets follow.
        self.assertLess(document.index(spec['scripts'][-1]), document.index(face['DriftkingsOwnHealth']['scripts'][-1]))
        # The other feature's layout stays a placeholder: it is a position key, not a second document.
        other = (catalog.ROOT / 'mod' / catalog.asset_target(face['DriftkingsOwnHealth']['layout'])).read_text(encoding='utf-8')
        self.assertNotIn('<script', other)

    def test_infrastructure_resource_and_shared_manifest(self):
        import json
        declarations = [entry for path in (catalog.ROOT / 'mod/res/gui/gen_resources').glob('*.json')
                        for entry in json.loads(path.read_text(encoding='utf-8'))]
        self.assertEqual(len(declarations), 23)
        self.assertEqual(len(set(entry['id'] for entry in declarations)), 23)
        document = json.loads((catalog.ROOT / 'build_data/components.json').read_text(encoding='utf-8'))
        assets = document['components']['ui']['assets']
        from build_tools.components import normalize_asset
        targets = [normalize_asset(asset)['target'] for asset in assets]
        for target in ('res/gui/gen_resources/driftkings.battle_hud.json',
                       'res/gui/gameface/mods/driftkings/battle_hud/window.html'):
            self.assertEqual(targets.count(target), 1)
        self.assertEqual(document['components']['ui']['kind'], 'shared')

    def test_invalid_host_metadata_and_missing_packaging_are_rejected(self):
        for change, message in (
                (lambda data: data['BATTLE_HUD_HOST'].update(resource=data['GAMEFACE'][FEATURE]['resource']), 'collides'),
                (lambda data: data['BATTLE_HUD_HOST'].update(layout=data['GAMEFACE'][FEATURE]['layout']), 'Wrong battle HUD'),
                (lambda data: data['BATTLE_HUD_HOST'].update(asset_priority=(FEATURE, FEATURE)), 'asset priority'),
                (lambda data: data['BATTLE_HUD_HOST'].update(asset_priority=('unknown',)), 'asset priority')):
            data = copy.deepcopy(catalog.read_catalog())
            change(data)
            with patch.object(catalog, 'read_catalog', return_value=data):
                with self.assertRaisesRegex(ValueError, message):
                    catalog.validate()
        paths = set()
        for spec in catalog.read_catalog()['GAMEFACE'].values():
            paths.update(catalog.asset_target(url) for url in [spec['layout']] + spec['scripts'] + spec['styles'] + ([spec['plugin']] if 'plugin' in spec else []))
            paths.update('res/' + url for url in spec.get('documents', []))
        paths.update(path.relative_to(catalog.ROOT / 'mod').as_posix()
                     for path in (catalog.ROOT / 'mod/res/gui/gen_resources').glob('*.json'))
        with self.assertRaisesRegex(ValueError, 'Battle HUD host is not packaged'):
            catalog.validate(plan={'assets': [{'target': target} for target in paths]})

    def test_manifest_expansion_matches_baseline_and_packages_all_contracts(self):
        import json
        from build_tools.components import read_components
        from build_tools.validate_build_data import expand_asset
        config = json.loads((catalog.ROOT / 'build_data/build_config.json').read_text(encoding='utf-8'))
        assets = [item for manifest in read_components(catalog.ROOT, config['components']['source'])
                  for asset in manifest['assets']
                  for item in expand_asset(catalog.ROOT, asset, config['assets']['exclude'])]
        # Independent packaging baseline. 335 = 333 + the optional Remove Fog helper (exe and helper.json), restored
        # as an optional, default-OFF feature. Not a second manifest.
        self.assertEqual(len(assets), 335)
        self.assertEqual(len({item['target'] for item in assets}), 335)
        self.assertEqual(catalog.validate(plan={'assets': assets})['native'], 20)
        with self.assertRaisesRegex(ValueError, 'Duplicate packaging target'):
            catalog.validate(plan={'assets': assets + assets[:1]})

    def test_duplicate_catalog_keys_cannot_be_silently_overwritten(self):
        original = catalog.Path.read_text
        def read(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            if path == catalog.ROOT / catalog.SOURCE:
                value = value.replace("GAMEFACE = {", "GAMEFACE = {'duplicate': {}, 'duplicate': {},", 1)
            return value
        with patch.object(catalog.Path, 'read_text', read):
            with self.assertRaisesRegex(ValueError, 'Duplicate catalog identity'):
                catalog.read_catalog()

    def test_duplicate_owners_resources_and_functional_host_are_rejected(self):
        for change, message in (
                (lambda face: face['DriftkingsOwnHealth'].update(owner=face[FEATURE]['owner']), 'duplicate JS owner'),
                (lambda face: face['DriftkingsOwnHealth'].update(resource=face[FEATURE]['resource']), 'Duplicate component resource'),
                (lambda face: face.update(Infrastructure=dict(face[FEATURE], resource=catalog.read_catalog()['BATTLE_HUD_HOST']['resource'])), 'collides')):
            data = copy.deepcopy(catalog.read_catalog())
            change(data['GAMEFACE'])
            with patch.object(catalog, 'read_catalog', return_value=data):
                with self.assertRaisesRegex(ValueError, message):
                    catalog.validate()

    def test_missing_layout_is_rejected_without_mutating_files(self):
        original = catalog.Path.is_file
        host_path = catalog.ROOT / 'mod' / catalog.asset_target(catalog.read_catalog()['BATTLE_HUD_HOST']['layout'])
        with patch.object(catalog.Path, 'is_file', lambda path: False if path == host_path else original(path)):
            with self.assertRaisesRegex(ValueError, 'Missing battle HUD host layout'):
                catalog.validate()

    def test_corrupt_declarations_documents_and_dual_root_selection_are_rejected(self):
        import json
        original = catalog.Path.read_text
        host = catalog.ROOT / 'mod/res/gui/gameface/mods/driftkings/battle_hud/window.html'
        old = catalog.ROOT / 'mod/res/gui/gameface/mods/driftkings/battle_statistics/model.html'
        declaration = catalog.ROOT / 'mod/res/gui/gen_resources/driftkings.battle_hud.json'
        python_host = catalog.ROOT / 'mod/res/scripts/client/driftkings/gameface/battle/own_window.py'
        def remove_script(value):
            return value.replace('<script src="coui://gui/gameface/mods/driftkings/shared/marks_panel.js"></script>', '')
        def reorder(value):
            return value.replace('shared/marks_panel.js', 'SWAP').replace('shared/flash_lines.js', 'shared/marks_panel.js').replace('SWAP', 'shared/flash_lines.js')
        for target, change, message in (
                (declaration, lambda value: '[]', 'R resources and Gameface catalog differ'),
                (declaration, lambda value: json.dumps(json.loads(value) * 2), 'Duplicate R resource'),
                (host, remove_script, 'Own window document must load'),
                (host, reorder, 'Own window document must load'),
                (host, lambda value: value.replace('coui://gui/', 'https://invalid/'), 'Own window document must load'),
                (old, lambda value: value.replace('<body>', '<body id="drift">'), 'Stale generated UI catalog'),
                (python_host, lambda value: value.replace("resource = resource_id(BATTLE_HUD_HOST['resource'])", "resource_id('mods/driftkings/battle_statistics/model'); resource = resource_id(BATTLE_HUD_HOST['resource'])"), 'only the neutral root')):
            def read(path, *args, **kwargs):
                value = original(path, *args, **kwargs)
                return change(value) if path == target else value
            with patch.object(catalog.Path, 'read_text', read):
                with self.assertRaisesRegex(ValueError, message):
                    catalog.validate()

    def test_missing_or_duplicate_manifest_outputs_are_rejected(self):
        from build_tools.components import read_components
        manifests = read_components(catalog.ROOT, 'build_data/components.json')
        target = catalog.asset_target(catalog.read_catalog()['BATTLE_HUD_HOST']['layout'])
        for duplicate in (False, True):
            changed = copy.deepcopy(manifests)
            ui = next(item for item in changed if item['id'] == 'ui')
            asset = next(item for item in ui['assets'] if item['target'] == target)
            if duplicate:
                ui['assets'].append(asset)
            else:
                ui['assets'].remove(asset)
            with patch('build_tools.components.read_components', return_value=changed):
                with self.assertRaisesRegex(ValueError, 'Duplicate manifest target' if duplicate else 'missing from ui manifest'):
                    catalog.validate()

    def test_other_features_and_stale_documents_are_rejected(self):
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsRatingPlayers']['transport'] = 'own_window'
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'reserved for battle HUD cards'):
                catalog.validate()
        data = copy.deepcopy(catalog.read_catalog())
        del data['GAMEFACE'][FEATURE]['transport']
        with patch.object(catalog, 'read_catalog', return_value=data):
            # A feature with an owner must now declare its transport explicitly (no OpenWG default).
            with self.assertRaisesRegex(ValueError, 'Unknown transport: ' + FEATURE):
                catalog.validate()
        for name, change in ((FEATURE, lambda scripts: scripts[:-1]), (FEATURE, lambda scripts: scripts[::-1]),
                             (FEATURE, lambda scripts: scripts + scripts[:1]),
                             ('DriftkingsOwnHealth', lambda scripts: scripts[:-1]),
                             ('DriftkingsOwnHealth', lambda scripts: scripts + ['coui://gui/gameface/mods/driftkings/shared/flash_text.js'])):
            data = copy.deepcopy(catalog.read_catalog())
            spec = data['GAMEFACE'][name]
            spec['scripts'] = change(spec['scripts'])
            with patch.object(catalog, 'read_catalog', return_value=data):
                with self.assertRaisesRegex(ValueError, 'Own window document must load|Duplicate assets'):
                    catalog.validate()


if __name__ == '__main__':
    unittest.main()
