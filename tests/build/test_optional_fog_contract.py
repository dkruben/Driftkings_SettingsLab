# -*- coding: utf-8 -*-
"""Optional Remove Fog contract: default OFF, no installer or updater removal, standalone, approved wording."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8-sig', errors='replace')


class OptionalFogContractTests(unittest.TestCase):
    def test_default_profile_is_off(self):
        config = json.loads(read('res/configs/driftkings/default/battle_preferences.json'))
        self.assertIs(config['removeFog'], False)

    def test_runtime_default_is_off_and_choice_is_explicit(self):
        source = read('mod/res/scripts/client/driftkings/settings/default_values.py')
        self.assertIn("'removeFog': False", source)
        fog = read('mod/res/scripts/client/driftkings/core/fog_package.py')
        self.assertIn("CHOICE_FILE = 'choice.json'", fog)
        self.assertIn("chosen if chosen is not None else False", fog)
        # A legacy profile value never becomes the intent; only read_choice() does.
        self.assertNotIn("values[BATTLE_PREFERENCES.REMOVE_FOG] = True", fog)

    def test_launch_path_only_converges_to_off_and_never_installs(self):
        # Startup may schedule removal (effective OFF with an owned package) and never an install.
        fog = read('mod/res/scripts/client/driftkings/core/fog_package.py')
        startup = fog[fog.index('    def startup(self):'):fog.index('    def prepare(self, profile_file):')]
        self.assertIn('self.schedule(False)', startup)
        self.assertNotIn('self.schedule(True)', startup)
        self.assertIn("if package_evidence(self.target) == 'owned':", startup)
        self.assertIn('if self.current_intent() is not True:', startup)

    def test_installer_and_updater_never_remove_the_optional_package(self):
        for relative in ('installer/source/installer.cs', 'installer/source/modpackinstaller.cs',
                         'installer/setup/wizard.iss', 'build_tools/build_installer.py', 'build_tools/publish_release.py'):
            text = read(relative)
            self.assertNotIn('RetireLegacyFog', text, relative)
            self.assertNotIn('retire-legacy-fog', text, relative)

    def test_standalone_fog_module_has_no_external_gameface_or_modslistapi_dependency(self):
        fog = read('mod/res/scripts/client/driftkings/core/fog_package.py')
        self.assertIsNone(re.search(r'openwg|modslistapi|gf_mod_inject', fog, re.I))

    def test_helper_and_metadata_are_declared_for_the_optional_resource(self):
        config = json.loads(read('build_data/build_config.json'))
        generator = config['generators']['fog_package_helper']
        self.assertEqual(generator['output'], 'build/native/fog/Driftkings.FogPackage.exe')
        self.assertEqual(generator['source'], 'installer/source/fogpackage.cs')
        self.assertNotIn('driftkings/core/fog_package.py', config['python']['exclude'])

    def test_helper_removes_only_verified_owned_packages_and_keeps_a_recovery_copy(self):
        helper = read('installer/source/fogpackage.cs')
        self.assertIn('ModId = "driftkings.removefog"', helper)
        off = helper[helper.index('if (!enabled) {'):helper.index('string packages = Path.Combine(root, "res", "packages");')]
        self.assertIn('File.Copy(target, copy, false)', off)
        self.assertIn('"cache", "fog", "recovery"', off)
        self.assertLess(off.index('File.Copy(target, copy, false)'), off.index('File.Delete(target)'))
        self.assertIn('if (File.Exists(target)) Require(Owned(target), "Optional package belongs to another mod");', helper)

    def test_controller_effective_state_is_the_only_source_for_the_panel(self):
        fog = read('mod/res/scripts/client/driftkings/core/fog_package.py')
        self.assertIn('def effective_state(self):', fog)
        self.assertIn("'off-package-loaded'", fog)

    def test_release_notes_describe_the_optional_feature_without_discontinuation(self):
        release = json.loads(read('build_data/release.json'))
        text = ' '.join(release['changelog']).lower()
        self.assertIn('optional', text)
        self.assertIn('off by default', text)
        self.assertNotIn('removed the remove fog', text)
        for name in ('README.md', 'CONTRIBUTING.md', 'docs/releases/WGMODS-0.1.7-draft.md', 'docs/STATUS.md'):
            self.assertNotIn('permanently discontinued', read(name).lower(), name)

    def test_approved_tooltip_wording_is_kept(self):
        text = read('mod/res/mods/driftkings/text/en.yml')
        self.assertIn('Builds a separate package from this installation', text)
        self.assertIn('Turning this mod off also removes the package', text)


if __name__ == '__main__':
    unittest.main()
