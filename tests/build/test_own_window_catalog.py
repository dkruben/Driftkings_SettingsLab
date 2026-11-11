"""Own battle window transport: Nine battle HUD cards share one document that loads the catalog
assets once; counts 14/6/2."""
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
        self.assertEqual((counts['gameface'], counts['native'], counts['injected']), (22, 14, 6))
        # The two lobby windows load their own layouts and are neither injected nor native transports.
        self.assertEqual(sorted(name for name, spec in face.items() if spec['owner'] is None),
                         ['DriftkingsAccountManager', 'DriftkingsModSettings'])
        self.assertEqual(sorted(name for name, spec in face.items() if spec.get('transport') == 'own_window'), SHARED)
        self.assertEqual((catalog.OWN_WINDOW_HOST, sorted(catalog.OWN_WINDOW_FEATURES)), (FEATURE, SHARED))
        source = (catalog.ROOT / 'mod/res/scripts/client/driftkings/gameface/battle/own_window.py').read_text(encoding='utf-8')
        self.assertIn("HOST_FEATURE = '%s'" % catalog.OWN_WINDOW_HOST, source)
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        for name in SHARED:
            self.assertNotIn(name, block)  # no OpenWG loading, hence no second copy of its scripts
        battle = [name for name, spec in face.items() if spec['context'] == 'battle' and name not in SHARED]
        self.assertEqual(len(battle), 0)
        for name in battle + ['DriftkingsRatingPlayers']:
            self.assertIn('"%s"' % name, block)
            self.assertNotIn('transport', face[name])

    def test_document_loads_the_catalog_assets_once_in_order(self):
        face = catalog.read_catalog()['GAMEFACE']
        spec = face[FEATURE]
        document = (catalog.ROOT / 'mod' / catalog.asset_target(spec['layout'])).read_text(encoding='utf-8')
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

    def test_other_features_and_stale_documents_are_rejected(self):
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsFooterLauncher']['transport'] = 'own_window'
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'reserved for battle HUD cards'):
                catalog.validate()
        data = copy.deepcopy(catalog.read_catalog())
        del data['GAMEFACE'][FEATURE]['transport']
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'host must use own_window'):
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
