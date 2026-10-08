from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'source/scripts/client'))
from Driftkings.settings.player_panel_store import defaults,validate

class PanelValidationTests(unittest.TestCase):
    def test_defaults_have_no_macro_warnings(self):
        self.assertEqual(validate(defaults()),[])
    def test_unknown_macro_reports_file_and_field_with_nested_formats(self):
        data=defaults()
        data['tab']['formatLeftNick']='{{name%.{{anonym?10|12}}s}} {{typo|--}} {{my-hp}}'
        warnings=validate(data)
        self.assertEqual(len(warnings),1)
        self.assertIn('statisticForm.json',warnings[0])
        self.assertIn('formatLeftNick',warnings[0])
        self.assertIn('Unknown macro: typo',warnings[0])
    def test_bad_reference_and_geometry_report_exact_location(self):
        data=defaults(); data['profiles']['short']['extraFieldsLeft']=[{'ref':'absent'}]
        with self.assertRaisesRegex(ValueError,r'panelShort.json:.*extraFieldsLeft\[0\]'):
            validate(data)
        data=defaults(); data['tab']['vehicleFieldWidthLeft']=-1
        with self.assertRaisesRegex(ValueError,'statisticForm.json:.*vehicleFieldWidthLeft'):
            validate(data)
    def test_unclosed_macro_and_missing_config_reference_are_reported(self):
        data=defaults(); data['loading']['formatLeftNick']='{{.missing}} {{name'
        warnings=validate(data)
        self.assertTrue(any('Unknown configuration reference' in warning for warning in warnings))
        self.assertTrue(any('Unclosed' in warning for warning in warnings))
