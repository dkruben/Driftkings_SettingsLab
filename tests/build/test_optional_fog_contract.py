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
                         'build_tools/build_installer.py', 'build_tools/publish_release.py'):
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

    def test_public_release_notes_do_not_advertise_unreleased_remove_fog(self):
        release = json.loads(read('build_data/release.json'))
        text = ' '.join(release['changelog']).lower()
        self.assertNotIn('remove fog', text)
        self.assertNotIn('removed the remove fog', text)
        for name in ('README.md', 'CONTRIBUTING.md', 'docs/releases/WGMODS-0.1.7-draft.md', 'docs/STATUS.md'):
            self.assertNotIn('permanently discontinued', read(name).lower(), name)

    def test_tooltip_explains_default_activation_package_and_disabling(self):
        text = read('mod/res/mods/driftkings/text/en.yml')
        tooltip = [line for line in text.splitlines() if line.startswith('battle_preferences.UI_setting_removeFog_tooltip')][0]
        for required in ('Off by default', 'changed only by you', 'separate package', 'after you close the game',
                         'Close and reopen the game', 'turn this option off', 'Resetting settings to defaults turns it off',
                         'Turning this mod off also removes the package'):
            self.assertIn(required, tooltip)


    def test_historical_leaf_transformation_is_exact(self):
        # Equivalent to the v0.1.6 helper: the same three boolean leaves and three density leaves, nothing else.
        helper = read('installer/source/fogpackage.cs')
        self.assertIn('static readonly HashSet<string> BooleanLeaves = new HashSet<string> { "Fog/enable", '
                      '"VolumetricFog/enabled", "VolumetricFog/enableGameplay" };', helper)
        self.assertIn('static readonly HashSet<string> DensityLeaves = new HashSet<string> { '
                      '"Fog/deferred/density", "Fog/simplifiedDeferred/density", "Fog/forward/density" };', helper)
        self.assertIn('replacement = new byte[0];', helper)
        self.assertIn('replacement = new byte[4];', helper)
        self.assertNotIn('REMOVE_FOG_EFFECT_VERIFIED', read('mod/res/scripts/client/driftkings/_constants.py'))

    def test_control_is_functional_and_not_gated(self):
        definition = read('mod/res/scripts/client/driftkings/settings/definitions/battle/battle_preferences.py')
        self.assertIn('control(BATTLE_PREFERENCES.REMOVE_FOG),', definition)
        for relative in ('mod/res/scripts/client/driftkings/core/fog_package.py',
                         'mod/res/scripts/client/driftkings/settings/definitions/battle/battle_preferences.py'):
            self.assertNotIn('REMOVE_FOG_EFFECT_VERIFIED', read(relative), relative)
        for relative in ('mod/res/mods/driftkings/text/%s.yml' % name for name in
                         ('en', 'cs', 'de', 'es', 'fr', 'hu', 'it', 'ja', 'ko', 'pl', 'pt', 'ru', 'th', 'tr', 'uk',
                          'vi', 'zh_cn', 'zh_tw')):
            self.assertNotIn('UI_fog_unavailable', read(relative), relative)

    def test_uninstall_removes_only_the_recorded_and_unchanged_auxiliary_package(self):
        helper = read('installer/source/fogpackage.cs')
        self.assertIn('owned.txt', helper)
        setup = read('installer/setup/wizard.iss')
        self.assertIn('procedure CurUninstallStepChanged', setup)
        self.assertIn('GetSHA256OfFile(Target)', setup)
        self.assertIn("ExtractFileName(Target) <> 'Driftkings.RemoveFog.wotmod'", setup)
        self.assertIn(r"Pos(App + '\mods\', Target) <> 1", setup)


if __name__ == '__main__':
    unittest.main()
