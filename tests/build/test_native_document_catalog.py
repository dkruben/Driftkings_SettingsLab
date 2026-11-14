"""Pinned document loading uses the existing patch pipeline, without compiling or installing."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from build_tools import generate_ui_catalog as catalog
from build_tools.validate_build_data import apply_patch_set, build_plan, read_gameface_resource
from support.baselines import baseline, json_hash

ROOT = catalog.ROOT
GAME = Path(os.environ.get('DK_CT_GAME', 'C:/Games/World_of_Tanks_CT'))


class NativeDocumentsTests(unittest.TestCase):
    def documents(self):
        config = json.loads((ROOT / 'build_data/build_config.json').read_text())
        return [(key, spec) for key, spec in config['generators'].items() if key.startswith('native_document_')]

    def test_native_context_contracts_and_authorized_seasonal_removal(self):
        face = catalog.read_catalog()['GAMEFACE']
        self.assertEqual(catalog.validate(), {'flash': 7, 'gameface': 22, 'native': 20, 'injected': 0})
        for name in catalog.NATIVE_DOCUMENT_FEATURES:
            current = dict(face[name])
            self.assertEqual(current.pop('transport'), 'native_document')
            self.assertTrue(current.pop('documents'))
            if name == 'DriftkingsRatingPlayers':
                self.assertNotIn(catalog.PREFIX + 'panel_gameface/halloween_tab.js', current['scripts'])
                # Compare all retained renderer/data contracts to the unchanged historical baseline.
                current['scripts'] = current['scripts'][:-1] + [catalog.PREFIX + 'panel_gameface/halloween_tab.js'] + current['scripts'][-1:]
            self.assertEqual(json_hash(current), baseline('native_carousel')['catalog'][name], name)
        remaining = [name for name, spec in face.items() if spec['owner'] is not None
                     and spec.get('transport', 'openwg') == 'openwg']
        self.assertEqual(remaining, [])

    def test_exact_document_coverage_assets_and_existing_generators_preserved(self):
        face = catalog.read_catalog()['GAMEFACE']
        documents = [resource for spec in face.values() if spec.get('transport') == 'native_document'
                     for resource in spec['documents']]
        self.assertEqual(len(documents), 9)
        self.assertEqual(len(set(documents)), 9)
        generators = self.documents()
        self.assertEqual(sorted(spec['resource'] for _, spec in generators), sorted(documents))
        plan = build_plan(ROOT)
        for key, generator in generators:
            self.assertEqual(generator['kind'], 'gameface_patch')
            self.assertEqual(generator['implementation'], 'replace_exact')
            metadata = json.loads((ROOT / generator['patch_file']).read_text())
            self.assertEqual((metadata['realm'], metadata['client_build']), ('CT', '995'))
            feature = metadata['feature']
            self.assertIn(metadata['resource'], face[feature]['documents'])
            for digest in ('source_sha256', 'output_sha256'):
                self.assertRegex(metadata[digest], r'^[a-f0-9]{64}$')
            replacement = metadata['operations'][0]['replace']
            self.assertEqual(replacement, catalog.document_assets(face[feature]) + '</body>')
            scripts = re.findall(r'<script defer src="([^"]+)"></script>', replacement)
            self.assertEqual(scripts, face[feature]['scripts'])
            self.assertEqual(len(scripts), len(set(scripts)))
            self.assertEqual(sum(item['generator'] == key for item in plan['assets']), 1)
            self.assertTrue(any(item['target'] == 'res/' + generator['resource'] for item in plan['assets']))

    @unittest.skipUnless((GAME / 'res/packages/gui-part1.pkg').is_file(), 'Read-only CT resources not available')
    def test_actual_client_buffers_fail_closed_and_preserve_every_native_byte(self):
        for _, generator in self.documents():
            metadata = json.loads((ROOT / generator['patch_file']).read_text())
            raw = read_gameface_resource(GAME, generator['game_packages'], generator['resource'])
            result = apply_patch_set(raw, metadata)
            assets = catalog.document_assets(catalog.read_catalog()['GAMEFACE'][metadata['feature']]).encode('utf-8')
            self.assertEqual(result.count(assets), 1)
            self.assertEqual(result.replace(assets, b'', 1), raw)
            self.assertEqual(hashlib.sha256(result).hexdigest(), metadata['output_sha256'])
            with self.assertRaises(ValueError):
                apply_patch_set(raw + b' ', metadata)
            with self.assertRaises(ValueError):
                apply_patch_set(result, metadata)

    def test_catalog_rejects_stale_document_assets_and_unapproved_context(self):
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsFooterLauncher']['scripts'].reverse()
        data['GAMEFACE']['DriftkingsFooterLauncher']['styles'].append(catalog.PREFIX + 'shared/marks_tokens.css')
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'Native document assets differ'):
                catalog.validate()
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsModSettings']['transport'] = 'native_document'
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'approved context'):
                catalog.validate()
