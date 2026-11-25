# -*- coding: utf-8 -*-
"""Driftkings is standalone: OpenWG Gameface and ModsListAPI are not declared, shipped or imported."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.validate_build_data import build_plan, read_json

OBSOLETE_PACKAGES = ('net.openwg.gameface', 'me.poliroid.modslistapi', 'openwg_packages/driftkings_fonts')
# The passive compatibility observer names the optional third-party modules; it never imports them.
OPTIONAL_OBSERVER = Path('mod/res/scripts/client/driftkings/core/mod_compatibility.py')
EXTERNAL_IMPORT = re.compile(r'^\s*(from|import)\s+(openwg_gameface|gui\.modsListApi)\b|gf_mod_inject', re.M)


def runtime_sources():
    return sorted((ROOT / 'mod/res/scripts/client/driftkings').rglob('*.py'))


class StandaloneDistributionTests(unittest.TestCase):
    def test_build_config_declares_no_external_ui_packages(self):
        config = read_json(ROOT / 'build_data/build_config.json')
        self.assertNotIn('ui_dependencies', config)
        self.assertEqual(build_plan(ROOT)['dependencies'], [])

    def test_no_obsolete_package_is_tracked_or_present_in_the_build_inputs(self):
        wotmods = ROOT / 'res/wotmods'
        self.assertEqual(list(wotmods.glob('*.wotmod')) if wotmods.is_dir() else [], [])
        for path in ROOT.joinpath('res').rglob('*') if (ROOT / 'res').is_dir() else []:
            self.assertFalse(any(name in path.as_posix() for name in OBSOLETE_PACKAGES), path)

    def test_runtime_never_imports_openwg_gameface_or_modslistapi(self):
        offenders = []
        for path in runtime_sources():
            relative = path.relative_to(ROOT)
            if relative == OPTIONAL_OBSERVER:
                continue
            if EXTERNAL_IMPORT.search(path.read_text(encoding='utf-8')):
                offenders.append(relative.as_posix())
        self.assertEqual(offenders, [])

    def test_only_the_passive_observer_names_optional_external_modules(self):
        text = (ROOT / OPTIONAL_OBSERVER).read_text(encoding='utf-8')
        self.assertIn("'OpenWGGameface'", text)
        self.assertIn('Never imports or initializes external mods', text)
        self.assertIsNone(re.search(r'^\s*(from|import)\s+(openwg_gameface|gui\.modsListApi)', text, re.M))

    def test_gameface_payloads_resolve_to_native_transports_only(self):
        sys.modules.pop('driftkings.interface_catalog', None)
        sys.path.insert(0, str(ROOT / 'mod/res/scripts/client'))
        try:
            from driftkings.interface_catalog import GAMEFACE
        finally:
            sys.path.remove(str(ROOT / 'mod/res/scripts/client'))
        transports = set(spec.get('transport') for spec in GAMEFACE.values() if spec['owner'] is not None)
        self.assertEqual(transports, set(['native_document', 'native_user_missions', 'native_battle_results', 'own_window']))

    def test_no_openwg_package_or_transport_survives_in_generators_or_installer(self):
        for folder in ('build_tools', 'installer'):
            for path in (ROOT / folder).rglob('*'):
                if not path.is_file() or path.suffix not in ('.py', '.cs', '.iss', '.json', '.ps1', '.cjs'):
                    continue
                text = path.read_text(encoding='utf-8', errors='ignore')
                for name in OBSOLETE_PACKAGES:
                    self.assertNotIn(name, text, path.relative_to(ROOT).as_posix())
                self.assertNotIn("'openwg')", text, path.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    unittest.main()
