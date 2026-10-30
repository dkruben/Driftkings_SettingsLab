"""Pure build/contract tests. No game process, network, Inno or Windows required."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.build_installer import supported_realms


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

