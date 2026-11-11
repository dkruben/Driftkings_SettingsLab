"""Own battle window transport: TeamStrength only, document loads the catalog assets once, counts 6/14/2."""
import copy
import unittest
from unittest.mock import patch

from build_tools import generate_ui_catalog as catalog

FEATURE = 'DriftkingsTeamStrength'


class OwnWindowCatalogTests(unittest.TestCase):
    def test_transport_counts_and_bootstrap(self):
        face = catalog.read_catalog()['GAMEFACE']
        counts = catalog.validate()
        self.assertEqual((counts['gameface'], counts['native'], counts['injected']), (22, 6, 14))
        # The two lobby windows load their own layouts and are neither injected nor native transports.
        self.assertEqual(sorted(name for name, spec in face.items() if spec['owner'] is None),
                         ['DriftkingsAccountManager', 'DriftkingsModSettings'])
        self.assertEqual([name for name, spec in face.items() if spec.get('transport') == 'own_window'], [FEATURE])
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        self.assertNotIn(FEATURE, block)  # no OpenWG loading, hence no second copy of its scripts
        battle = [name for name, spec in face.items() if spec['context'] == 'battle' and name != FEATURE]
        self.assertEqual(len(battle), 8)
        for name in battle + ['DriftkingsRatingPlayers']:
            self.assertIn('"%s"' % name, block)
            self.assertNotIn('transport', face[name])

    def test_document_loads_the_catalog_assets_once_in_order(self):
        spec = catalog.read_catalog()['GAMEFACE'][FEATURE]
        document = (catalog.ROOT / 'mod' / catalog.asset_target(spec['layout'])).read_text(encoding='utf-8')
        for url in spec['scripts'] + spec['styles']:
            self.assertEqual(document.count('"%s"' % url), 1, url)
        self.assertNotIn('bootstrap.js', document)
        positions = [document.index(url) for url in spec['scripts']]
        self.assertEqual(positions, sorted(positions))

    def test_other_features_and_stale_documents_are_rejected(self):
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsMainGun']['transport'] = 'own_window'
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'TeamStrength only'):
                catalog.validate()
        for change in (lambda scripts: scripts[:-1], lambda scripts: scripts[::-1], lambda scripts: scripts + scripts[:1]):
            data = copy.deepcopy(catalog.read_catalog())
            spec = data['GAMEFACE'][FEATURE]
            spec['scripts'] = change(spec['scripts'])
            with patch.object(catalog, 'read_catalog', return_value=data):
                with self.assertRaisesRegex(ValueError, 'Own window document must load|Duplicate assets'):
                    catalog.validate()


if __name__ == '__main__':
    unittest.main()
