"""Pure build/contract tests. No game process, network, Inno or Windows required."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.build_installer import installer_messages, supported_realms


class DiscoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.code = (ROOT / 'installer/setup/wizard.iss').read_text(encoding='utf-8-sig')
        self.setup = (ROOT / 'installer/setup/driftkings.iss').read_text(encoding='utf-8-sig')

    def test_root_validation_precedes_copy_and_directory_page_advance(self):
        for marker in ('\\version.xml', '\\res\\packages', '\\win64\\WorldOfTanks.exe',
                       '\\win32\\WorldOfTanks.exe'):
            self.assertIn(marker, self.code)
        next_page = self.code.split('function NextButtonClick', 1)[1].split('procedure InitializeWizard', 1)[0]
        self.assertIn('Error := ClientError', next_page)
        preflight = self.code.split('function PrepareToInstall', 1)[1].split('procedure CollectConfigs', 1)[0]
        self.assertLess(preflight.index('Result := ClientError'), preflight.index('ExistingDependenciesError'))
        self.assertIn('DisableDirPage=no', self.setup)
        self.assertIn('AppendDefaultDirName=no', self.setup)

    def test_discovery_supports_registry_views_and_bounded_local_scans(self):
        for hive in ('HKCU32', 'HKLM32', 'HKCU64', 'HKLM64'):
            self.assertIn('RegistryInstallations(' + hive + ')', self.code)
        self.assertIn("'InstallLocation'", self.code)
        self.assertIn('GetDriveType(Drive) = 3', self.code)
        self.assertIn('((Item.Attributes and $400) = 0)', self.code)
        self.assertIn("if Realm = 'SEA' then Realm := 'ASIA'", self.code)
        self.assertIn("Version <> '{#GameVersion}'", self.code)
        self.assertIn("'{#SupportedRealms}'", self.code)
        self.assertIn("ExpandConstant('{param:DIR|}') = ''", self.code)
        self.assertIn('CompareText(Installations[I], Root) = 0', self.code)

    def test_uninstall_registration_is_unique_per_validated_game_root(self):
        self.assertIn('AppId={code:InstallationId}', self.setup)
        self.assertIn('UsePreviousAppDir=no', self.setup)
        self.assertIn('GetSHA256OfString(Lowercase(SelectedRoot))', self.code)
        self.assertIn('SelectedRoot := GameRoot(WizardDirValue)', self.code)

    def test_malformed_realm_elements_report_validation_errors(self):
        for realms in ([{}], [['NA']], [None], [1], ['NA', {}]):
            with self.assertRaisesRegex(ValueError, 'Invalid supported_realms'):
                supported_realms({'game': {'realm': 'NA', 'supported_realms': realms}})


class StartupRegressionTests(unittest.TestCase):
    def test_profile_lookup_during_initialize_does_not_expand_app(self):
        code = (ROOT / 'installer/setup/wizard.iss').read_text(encoding='utf-8-sig')
        config_root = code.split('function ConfigRoot: String;', 1)[1].split('function IsReparseDirectory', 1)[0]
        self.assertNotIn('ExpandConstant', config_root)
        self.assertIn('AddBackslash(WizardDirValue)', config_root)



class WizardExperienceTests(unittest.TestCase):
    def setUp(self):
        self.code = (ROOT / 'installer/setup/wizard.iss').read_text(encoding='utf-8-sig')
        self.setup = (ROOT / 'installer/setup/driftkings.iss').read_text(encoding='utf-8-sig')

    def test_dark_style_background_and_whats_new_page_are_configured(self):
        for directive in ('WizardStyle=modern dark', 'WizardBackColor=', 'WizardSizePercent=',
                          'DirExistsWarning=no', 'InfoBeforeFile={#InputDir}\\changelog.generated.txt',
                          '#include InputDir + "\\languages.generated.iss"'):
            self.assertIn(directive, self.setup)
        self.assertNotIn('[CustomMessages]', self.setup)
        self.assertNotIn('[Languages]', self.setup)

    def test_hover_preview_uses_a_built_in_callback_and_stops_its_timer(self):
        self.assertIn('CreateCallback(@HoverTimerProc)', self.code)
        self.assertIn('LB_ITEMFROMPOINT', self.code)
        deinit = self.code.split('procedure DeinitializeSetup;', 1)[1].split('end;', 1)[0]
        self.assertIn('KillTimer(0, HoverTimer)', deinit)
        self.assertNotIn('InnoCallback', self.code)
        self.assertNotIn('botva', self.code.lower())

    def test_existing_profile_can_be_kept_or_reset_from_the_wizard(self):
        refresh = self.code.split('procedure RefreshProfileChoice;', 1)[1].split('procedure ProfileChoiceClick', 1)[0]
        self.assertIn('ResetConfig := ResetRequested or (Existing and ResetProfileRadio.Checked)', refresh)
        self.assertIn("ResetRequested := ExpandConstant('{param:RESETCONFIG|0}') = '1'", self.code)
        self.assertIn('KeepProfileRadio.Checked := not ResetRequested', self.code)
        # Skipping the component pages still depends on the effective reset choice.
        self.assertIn('HasProfile and not ResetConfig', self.code.split('function ShouldSkipPage', 1)[1])

    def test_every_wizard_language_translates_every_text_the_code_uses(self):
        self.assertIn('WizardForm.FinishedLabel.Caption := InstallSummary', self.code)
        document = installer_messages(ROOT)
        languages = set(document['languages'])
        self.assertEqual(languages, {'en', 'pt', 'cs', 'de', 'es', 'fr', 'hu', 'it', 'ja', 'ko', 'pl', 'ru', 'th', 'tr', 'uk'})
        used = set(re.findall(r"CustomMessage\('(\w+)'\)", self.code))
        self.assertTrue(used)
        self.assertTrue(used.issubset(document['custom_messages']), used - set(document['custom_messages']))
        for section in ('custom_messages', 'messages'):
            for key, values in document[section].items():
                self.assertEqual(set(values), languages, key)
        for path in document['languages'].values():
            self.assertTrue(path.startswith('compiler:'))

    def test_translated_placeholders_are_rejected_when_they_differ(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'installer/setup'
            target.mkdir(parents=True)
            document = json.loads((ROOT / 'installer/setup/messages.json').read_text(encoding='utf-8'))
            document['custom_messages']['SummaryInstalled']['de'] = 'Driftkings ist installiert.'
            (target / 'messages.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'placeholders differ: de/SummaryInstalled'):
                installer_messages(temp)
