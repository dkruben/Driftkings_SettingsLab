import ast
import copy
import re
import types
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/scripts/client'))
from Driftkings.settings.player_panel_store import PlayerPanelStore, defaults, split, join, resolve_fields, validate, FILES
from Driftkings.settings.store import SettingsStore

class UnifiedPanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'panels'
        self.store=PlayerPanelStore(str(self.path))

    def test_xvm_schema_roundtrip_and_defaults(self):
        data=self.store.load()
        self.assertEqual(data,defaults())
        self.assertEqual(data,join(split(data)))
        self.assertEqual(len(list(self.path.glob('*.json'))),9)
        for name,fields in [('short',['frags']),('medium',['frags','badge','nick']),('medium2',['frags','vehicle'])]:
            self.assertEqual(data['profiles'][name]['standardFields'],fields)
        data['profiles']['short']['standardFields']=['nick','frags','vehicle']
        data['profiles']['short']['nickFormatLeft']='{{name}} {{frags}}'
        data['loading']['vehicleFieldWidthDeltaLeft']=45
        self.store.save(data)
        self.assertEqual(self.store.load(),data)

    def test_shipped_json_matches_python_defaults(self):
        for name,value in zip(FILES,split(defaults())):
            self.assertEqual(json.loads((ROOT/'res/configs/Driftkings/default/player_panel_pro'/name).read_text()),value,name)

    def test_old_hp_switch_loads_as_never_without_resetting_other_settings(self):
        self.store.load()
        path=self.path/'general.json'
        saved=json.loads(path.read_text()); saved.pop('hpVisibility'); saved.pop('hpKey')
        saved.update(hpEnabled=False,rating='eff')
        path.write_text(json.dumps(saved))
        data=self.store.load()
        self.assertEqual(data['hpVisibility'],'never')
        self.assertEqual(data['hpKey'],[[56,184]])
        self.assertEqual(data['rating'],'eff')
        self.store.save(data)
        self.assertEqual(self.store.load(),data)

    def test_hp_visibility_and_key_validation(self):
        for key,value in [('hpVisibility','toggle'),('hpKey',[]),('hpKey',[[True]]),
                          ('hpKey',[[327]]),('hpKey',[[56],[]])]:
            data=defaults(); data[key]=value
            with self.assertRaises(ValueError): validate(data)

    def test_hp_mouse_binding_survives_save_and_reload(self):
        data = self.store.load()
        data['hpKey'] = [[29, 157], [259]]
        self.store.save(data)
        self.assertEqual(self.store.load()['hpKey'], [[29, 157], [259]])

    def test_loading_tips_removed_preserving_custom_main_settings(self):
        original=self.store.load()
        path=self.path/'battleLoading.json'
        loading=dict(original['loading'],vehicleFieldOffsetXLeft=26,formatLeftNick='{{name}} custom')
        loading['tips']={'vehicleFieldOffsetXLeft':-120,'formatLeftNick':'old tips'}
        path.write_text(json.dumps(loading))
        loaded=self.store.load()
        expected=dict(loading); expected.pop('tips')
        self.assertEqual(loaded['loading'],expected)
        self.assertEqual(json.loads(path.read_text()),expected)
        self.assertEqual(loaded['profiles'],original['profiles'])
        self.assertEqual(loaded,self.store.load())
        # Saving data from an older caller cannot reintroduce the duplicate.
        loaded['loading']['tips']={}
        self.store.save(loaded)
        self.assertNotIn('tips',json.loads(path.read_text()))

    def test_references_override_without_mutating_templates(self):
        data=defaults(); templates=copy.deepcopy(data['templates'])
        fields=resolve_fields([{'ref':'hp','x':123}],data['templates'])
        self.assertEqual(fields[0]['x'],123)
        self.assertEqual(fields[0]['id'],'hp')
        self.assertEqual(templates,data['templates'])
        for entries in ([{'ref':'missing'}],[3]):
            with self.assertRaises(ValueError): resolve_fields(entries,templates)
        with self.assertRaises(ValueError): resolve_fields([{'ref':'hp'}],{'hp':{'ref':'hp'}})

    def test_invalid_standard_fields_and_geometry_do_not_publish(self):
        data=self.store.load()
        before={p.name:p.read_bytes() for p in self.path.glob('*.json')}
        for key,value in [('standardFields',['nick','nick']),('standardFields',['bogus']),('fragsWidth',float('nan')),('fragsWidth',True),('fragsWidth',-1)]:
            changed=copy.deepcopy(data); changed['profiles']['short'][key]=value
            with self.assertRaises(ValueError): self.store.save(changed)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.path.glob('*.json')})

    def test_reset_v1_preserves_backup_and_color_choice(self):
        self.path.mkdir()
        old={'colorScale':2,'rating':'eff'}
        p=self.path/'general.json'; p.write_text(json.dumps(old))
        loaded=self.store.load()
        self.assertEqual(loaded['schemaVersion'],2)
        self.assertEqual(loaded['colorScale'],2)
        self.assertEqual(loaded['rating'],'eff')
        self.assertEqual(json.loads((self.path/'general.json.v1').read_text()),old)
        self.assertEqual(self.store.load(),loaded)

    def test_bad_json_is_not_overwritten(self):
        self.path.mkdir(); p=self.path/'general.json'; p.write_text('{bad')
        with self.assertRaises(ValueError): self.store.load()
        self.assertEqual(p.read_text(),'{bad')

    def test_atomic_save_rolls_back(self):
        data=self.store.load(); changed=copy.deepcopy(data); changed['rating']='eff'
        original=SettingsStore.write; calls=[]
        def fail_once(store,value):
            calls.append(store.path)
            if len(calls)==3: raise IOError('disk full')
            return original(store,value)
        with patch.object(SettingsStore,'write',fail_once):
            with self.assertRaises(IOError): self.store.save(changed)
        self.assertEqual(self.store.load(),data)

    def test_services_not_present(self):
        value=json.dumps(defaults())
        for token in ('xmqp','clanicon','xvm-user','x-enabled','clanIcon'):
            self.assertNotIn(token,value)

    def test_visual_menu_saves_json_arrays_and_template_colors(self):
        from Driftkings.settings.registry import SettingsRegistry
        from Driftkings.settings.store import merge
        tree=ast.parse((ROOT/'source/scripts/client/Driftkings/settings/templates/battle/players_panel.py').read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='player_panel_columns')
        from Driftkings._constants import PLAYER_PANEL_PRO, GLOBAL
        from Driftkings.settings.template_schema import field
        from Driftkings.settings.service import settings_service
        namespace={'re':re, 'PLAYER_PANEL_PRO':PLAYER_PANEL_PRO, 'GLOBAL':GLOBAL, 'nested_field':field,
                   'settings_service': settings_service}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'template','exec'),namespace)
        config=types.SimpleNamespace(ID='PlayerPanelPro',data=self.store.load(),i18n={})
        # Custom solid backgrounds remain editable even with image defaults.
        config.data['templates']['hpBarBg']['bgColor']='#000000'
        from Driftkings.settings.template_schema import build_template
        config.TRANSLATED_TITLE=False
        config.getControlColumns=lambda:namespace['player_panel_columns'](config)
        config.createTemplate=lambda:build_template(config)
        def apply(values):
            candidate=merge(config.data,values)
            self.store.save(candidate)
            config.data=candidate
        config.onApplySettings=apply
        common=types.ModuleType('Driftkings.common'); common.color_tables=[{'ScaleColor':'Default'}]
        with patch.dict(sys.modules,{'Driftkings.common':common}):
            registry=SettingsRegistry(); registry.register(config)
            description=registry.describe(config.ID); values=description['values']
            self.assertNotIn('hpEnabled',values)
            hp=next(c for c in description['controls'] if c.get('varName')=='hpVisibility')
            self.assertEqual(hp['optionValues'],['always','hold','never'])
            self.assertEqual(next(c for c in description['controls'] if c.get('varName')=='hpKey')['type'],'HotKey')
            values['hpVisibility']=1; values['hpKey']=[[35]]
            self.assertFalse(any(key.startswith('loading.tips') for key in values))
            self.assertEqual(json.loads(values['profiles.short.standardFields']),['frags'])
            control=next(c for c in description['controls'] if c.get('varName')=='templates.hpBarBg.bgColor')
            self.assertEqual(control['type'],'ColorChoice')
            values['profiles.short.standardFields']='["vehicle", "frags"]'
            values['templates.hpBarBg.bgColor']='#123456'
            registry.apply(config.ID,values)
            loaded=self.store.load()
            self.assertEqual(loaded['hpVisibility'],'hold')
            self.assertEqual(loaded['hpKey'],[[35]])
            self.assertEqual(loaded['profiles']['short']['standardFields'],['vehicle','frags'])
            self.assertEqual(loaded['templates']['hpBarBg']['bgColor'],'#123456')
            before=copy.deepcopy(loaded)
            values=registry.describe(config.ID)['values']; values['profiles.short.standardFields']='[bad'
            with self.assertRaises(ValueError): registry.apply(config.ID,values)
            self.assertEqual(self.store.load(),before)
