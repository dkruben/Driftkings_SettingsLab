"""Static contracts for installer destination safety. No Setup, Inno Setup, registry or game client is used.

Executable installer tests must run in an isolated Windows environment with PowerShell argument arrays; they are not
part of this suite.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def function_body(code, header, following):
    start = code.index(header)
    return code[start:code.index(following, start)]


class DestinationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = (ROOT / 'installer/setup/wizard.iss').read_text(encoding='utf-8-sig')
        cls.validator = function_body(cls.code, 'function DestinationError', 'function ClientError')
        cls.initialize = function_body(cls.code, 'function InitializeSetup', 'procedure RefreshProfileChoice')
        cls.discovery = function_body(cls.code, 'procedure DiscoverInstallations', 'function NextButtonClick')
        cls.next_button = function_body(cls.code, 'function NextButtonClick', 'procedure InitializeWizard')
        cls.prepare = function_body(cls.code, 'function PrepareToInstall', 'procedure CollectConfigs')

    def test_an_explicit_destination_is_validated_as_a_game_root(self):
        self.assertIn('function ExplicitDestination', self.code)
        self.assertIn("ExpandConstant('{param:DIR|}')", self.code)
        self.assertIn('DestinationError(ExplicitDestination)', self.initialize)
        self.assertIn('MsgBox(Error, mbCriticalError, MB_OK)', self.initialize)
        self.assertIn('Result := False', self.initialize)

    def test_an_invalid_explicit_destination_aborts_before_the_wizard(self):
        # InitializeSetup runs before any page or any write; returning False stops the installation.
        self.assertLess(self.code.index('function InitializeSetup'), self.code.index('procedure InitializeWizard'))
        self.assertIn("if ExplicitDestination = '' then Exit;", self.initialize)

    def test_missing_worldoftanks_executable_is_rejected(self):
        game_root = function_body(self.code, 'function GameRoot', 'function ReadClient')
        for marker in ("'\\WorldOfTanks.exe'", "'\\win64\\WorldOfTanks.exe'", "'\\win32\\WorldOfTanks.exe'"):
            self.assertIn(marker, game_root)
        self.assertIn("DirExists(Path + '\\res\\packages')", game_root)
        self.assertIn("if (Normalized = '') or (Root = '') or (CompareText(Root, Normalized) <> 0) then Exit;",
                      self.validator)

    def test_only_the_exact_game_root_is_accepted_never_a_substitute(self):
        # A folder inside a game (GameRoot walks upwards) is refused rather than replaced by its root.
        self.assertIn('CompareText(Root, Normalized) <> 0', self.validator)
        self.assertNotIn('GameRoot(WizardDirValue)', self.validator)

    def test_every_caller_uses_the_same_validator(self):
        self.assertIn('Result := DestinationError(WizardDirValue);', self.code)
        self.assertIn('Error := ClientError', self.next_button)
        self.assertIn('Result := ClientError', self.prepare)
        self.assertIn('DestinationError(ExplicitDestination)', self.initialize)

    def test_no_page_or_start_handler_rewrites_the_destination(self):
        for name, body in (('NextButtonClick', self.next_button), ('PrepareToInstall', self.prepare)):
            self.assertNotIn('DirEdit.Text :=', body, name)
        writers = [line for line in self.code.splitlines() if 'DirEdit.Text :=' in line]
        self.assertEqual(len(writers), 1, writers)
        self.assertIn('WizardForm.DirEdit.Text := Installations[InstallationList.ItemIndex]', writers[0])

    def test_discovery_never_selects_or_replaces_an_explicit_destination(self):
        self.assertIn("if ExplicitDestination = '' then begin", self.discovery)
        guarded = self.discovery.split("if ExplicitDestination = '' then begin", 1)[1].split('InstallationList.ItemIndex := Match', 1)[0]
        self.assertIn('GameRoot(WizardDirValue)', guarded)
        self.assertIn(" | {#GameVersion} | ", guarded)
        self.assertLess(self.discovery.index('Match := -1'), self.discovery.index('if ExplicitDestination'))
        self.assertIn('if Match >= 0 then SelectInstallation(InstallationList);', self.discovery)

    def test_automatic_discovery_still_runs_without_an_explicit_destination(self):
        for source in ('RegistryInstallations(HKCU32)', 'RegistryInstallations(HKLM32)', 'ScanGameFolders(Drive)'):
            self.assertIn(source, self.discovery)
        self.assertIn('GetDriveType(Drive) = 3', self.code)
        self.assertIn("ExpandConstant('{param:DIR|}') = ''", self.discovery)

    def test_validation_precedes_every_write(self):
        order = [self.prepare.index(item) for item in ('Result := ClientError', 'ExistingDependenciesError',
                                                       'ConfigurationPathError', 'WbemScripting.SWbemLocator')]
        self.assertEqual(order, sorted(order))
        self.assertIn('SelectedRoot := GameRoot(WizardDirValue);', self.prepare)
        self.assertLess(self.prepare.index('SelectedRoot := GameRoot(WizardDirValue);'),
                        self.prepare.index("Result := '';"))

    def test_the_running_game_protection_is_unchanged(self):
        self.assertIn("Name = ''WorldOfTanks.exe''", self.prepare)
        self.assertIn("Result := CustomMessage('CloseGame');", self.prepare)
        self.assertIn("Result := CustomMessage('ProcessCheckFailed');", self.prepare)

    def test_no_test_only_discovery_override_exists(self):
        for marker in ('DKTEST', 'DK_INSTALLER', 'GetEnv', 'DK_TEST', 'DK_ROOT'):
            self.assertNotIn(marker, self.code, marker)


if __name__ == '__main__':
    unittest.main()
