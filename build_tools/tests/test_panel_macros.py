import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/scripts/client'))
from Driftkings.core.panel_macros import Macros

class MacroTests(unittest.TestCase):
    def test_dependencies_follow_nested_names_conditions_and_active_branch(self):
        used=set()
        macro=Macros({'kind':'hp','hp':500,'alive':'alive','name':'Player'},dependencies=used)
        self.assertEqual(macro.render('{{alive?{{{{kind}}}}|{{name}}}}'),'500')
        self.assertEqual(used,{'alive','kind','hp'})

    def test_dependencies_include_missing_values_and_used_fallback(self):
        used=set()
        macro=Macros({'name':'Player'},dependencies=used)
        self.assertEqual(macro.render('{{missing|{{name}}}}'),'Player')
        self.assertEqual(used,{'missing','name'})

    def test_dependencies_follow_referenced_formats_and_ratio_inputs(self):
        used=set()
        macro=Macros({'hp':500,'hp-max':1000,'width':70},
                     {'bar':'{{hp-ratio:{{width}}}}'},dependencies=used)
        self.assertEqual(macro.render('{{.bar}}'),'35')
        self.assertEqual(used,{'hp','hp-max','width'})

    def test_nested_truncation_and_conditional(self):
        macro=Macros({'name':'abcdefghijklmnop','anonym':'anonym','alive':'alive','ready':''})
        self.assertEqual(macro.render('{{name%.{{anonym?10|12}}s~..}}'),'abcdefghij..')
        self.assertEqual(macro.render('{{alive?{{ready?#FF|#80}}|#00}}'),'#80')
    def test_defaults_percent_suffix_and_comparisons(self):
        macro=Macros({'r':1234,'winrate':52.1,'tdv':1.345,'frags':0})
        self.assertEqual(macro.render('{{r%4d|----}} {{winrate%2d~%|--%}} {{tdv%3.01f|-.-}}'),'1234 52% 1.3')
        self.assertEqual(macro.render('{{missing|{{frags=0?none|some}}}}'),'none')
        self.assertEqual(macro.render('{{missing%2d~k|--k}}'),'--k')
    def test_html_identity_is_escaped_once_and_never_reparsed(self):
        self.assertEqual(Macros({'name':'<&{{r}}'}).render('{{name}}'),'&lt;&amp;{{r}}')
        self.assertEqual(Macros({}).render('<b>{{missing|--}}</b>'),'<b>--</b>')
    def test_localization_and_config_references(self):
        macro=Macros({}, {'playersPanel':{'alpha':80}}, {'Destroyed':'Destruido'})
        self.assertEqual(macro.render('{{.playersPanel.alpha}} {{l10n:Destroyed}}'),'80 Destruido')
    def test_hp_ratio_and_dynamic_properties(self):
        macro=Macros({'hp':500,'hp-max':1500,'alive':''})
        self.assertEqual(macro.render('{{hp-ratio:70}}'),'24')
        self.assertEqual(macro.resolve({'enabled':'{{alive?true|false}}','alpha':'{{alive?100|0}}'}),{'enabled':False,'alpha':'0'})
    def test_unknown_services_and_python_expressions_are_not_executed(self):
        macro=Macros({})
        self.assertEqual(macro.render('{{xvm-user|none}} {{py:__import__("os")|disabled}}'),'none disabled')
    def test_recursion_is_bounded(self):
        value='{{missing|'*40+'ok'+'}}'*40
        self.assertEqual(Macros({}).render(value),'')

    def test_config_expression_references_are_expanded_and_bounded(self):
        self.assertEqual(Macros({'name':'Test'},{'nick':'<b>{{name}}</b>'}).render('{{.nick}}'),'<b>Test</b>')
        self.assertEqual(Macros({}, {'loop':'{{.loop}}'}).render('{{.loop}}'),'')
    def test_boolean_property_macro_resolves_false(self):
        self.assertEqual(Macros({'flag':False}).resolve({'enabled':'{{flag}}'}),{'enabled':False})
