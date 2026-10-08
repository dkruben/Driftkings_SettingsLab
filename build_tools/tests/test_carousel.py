import copy
import sys
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
def load(path, name):
    spec=importlib.util.spec_from_file_location(name, ROOT/path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
layout=load('source/scripts/client/Driftkings/core/carousel.py','carousel_layout')
registry=load('source/scripts/client/Driftkings/settings/registry.py','carousel_registry')

class CarouselTests(unittest.TestCase):
    def test_profiles_are_independent_and_empty_fields_are_respected(self):
        data=layout.defaults()
        original=data['small']['extraFields'][0]['x']
        data['normal']['extraFields'][0]['x']=90
        self.assertEqual(data['small']['extraFields'][0]['x'],original)
        data['normal']['extraFields']=[]
        self.assertEqual(layout.build_profile(data['normal'],lambda x:x,True)['extraFields'],[])

    def test_macro_aliases_format_fallback_and_colors(self):
        values={'winRate':52.7,'avgDamage':1800,'vehicle':'Tigre II','wn8':None}
        render=lambda s:layout.render(s,values,lambda key,value:'#ABCDEF',lambda key:'gui/test.png')
        self.assertEqual(render('{{v.name}} {{v.winrate%2d~%}} {{v.tdb%d}}'), 'Tigre II 52% 1800')
        self.assertEqual(render('{{wn8|----}} {{v.c_winrate}} {{c:wn8|#CCCCCC}}'), '---- #ABCDEF #CCCCCC')
        self.assertEqual(render('{{winRate:.1f}} {{icon:damage}}'), '52.7 gui/test.png')
        self.assertEqual(render('{{invalid!?yes|no}}'), '--')

    def test_render_limits_hide_disabled_fields_and_supports_backgrounds(self):
        profile=layout.defaults()['normal']
        profile['extraFields']=[{'enabled':False,'format':'hidden'}, {'x':99999,'alpha':-5,'bgColor':'0x123456','width':100,'format':'value'}]
        result=layout.build_profile(profile,lambda s:s,False)
        self.assertEqual(len(result['extraFields']),1)
        self.assertEqual(result['extraFields'][0]['x'],600)
        self.assertEqual(result['extraFields'][0]['alpha'],0)
        self.assertEqual(result['extraFields'][0]['bgColor'],'0x123456')

    def test_rows_default_explicit_and_profile_selection(self):
        cfg=layout.defaults()
        cfg.update(cellType='default',rows=0)
        self.assertEqual(layout.row_count(cfg,2),2)
        cfg['cellType']='normal'; self.assertEqual(layout.row_count(cfg,2),1)
        cfg['cellType']='small'; self.assertEqual(layout.row_count(cfg,1),2)
        cfg['rows']=1; self.assertEqual(layout.row_count(cfg,2),1)
        for rows in (3,4):
            cfg['rows']=rows
            self.assertEqual(layout.row_count(cfg,1),rows)
            self.assertEqual(layout.row_count(cfg,2),rows)

    def test_nested_menu_preserves_unexposed_fields_and_converts_option_values(self):
        data={'enabled':True,'carousel':layout.defaults()}
        fields=[{'type':'Dropdown','varName':'mode','path':['carousel','cellType'],
                 'options':[{'label':'Auto'},{'label':'Normal'},{'label':'Small'}], 'optionValues':['default','normal','small']},
                {'type':'ColorChoice','varName':'color','path':['carousel','normal','extraFields',0,'color']}]
        data['carousel']['normal']['extraFields'][0]['color']='#010203'
        data['carousel']['normal']['custom']={'keep':42}
        config=NS(ID='Test',data=data,i18n={},createTemplate=lambda:{'column1':fields},onApplySettings=data.update)
        menu=registry.SettingsRegistry();menu.register(config)
        values=menu.describe('Test')['values']; values.update(mode=2,color='#FFFFFF')
        menu.apply('Test',values)
        self.assertEqual(data['carousel']['cellType'],'small')
        self.assertEqual(data['carousel']['normal']['extraFields'][0]['color'],'#FFFFFF')
        self.assertEqual(data['carousel']['normal']['custom'],{'keep':42})
        self.assertEqual(menu.describe('Test')['defaults']['color'],'#010203')
        bad=menu.describe('Test')['values'];bad['mode']=10
        with self.assertRaises(ValueError):menu.apply('Test',bad)
