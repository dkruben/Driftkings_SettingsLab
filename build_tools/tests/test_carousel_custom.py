import ast
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core import carousel as layout
from Driftkings.core.carousel_assets import CarouselImages, ICON_ROOT
from Driftkings.core.carousel_tiers import battle_tiers
from Driftkings.settings.carousel_store import validate, documents


class CarouselCustomTests(unittest.TestCase):
    def test_vehicle_metadata_is_available_without_a_dossier(self):
        path=ROOT/'source/scripts/client/Driftkings/lobby/carousel.py'
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body=[n for n in tree.body if getattr(n,'name','') in ('collect','number')]
        namespace=dict(math=math,battle_tiers=battle_tiers,CLASS_COLORS={'heavyTank':'#957D5B'},
                       getVehicleInfoData=lambda cd:{'key':'usa:A80_T26_E4_SuperPershing','wn8expDamage':1500},
                       ServicesLocator=NS(itemsCache=NS(items=NS(getVehicleDossier=lambda cd:None))))
        exec(compile(tree,str(path),'exec'),namespace)
        vehicle=NS(intCD=1,level=8,type='heavyTank',shortUserName='Tank',isPremium=True,nationName='usa')
        values=namespace['collect'](vehicle)
        self.assertEqual((values['battletiermin'],values['battletiermax']),(8,9))
        self.assertEqual(values['classColor'],'#957D5B')
        self.assertEqual(values['vehicle'],'Tank')
        self.assertEqual(values['battles'],0)
        self.assertEqual(values['wn8expd'],1500)

    def values(self):
        return dict(vehicle='Tigre II', battles=2, winRate=50, hitRate=75,
                    avgDamage=1800, avgFrags=1, wn8expd=1500, wn8effd=1.2,
                    mastery=4, marksOnGun=1, marks=66.3, nation='germany',
                    battletiermin=8, battletiermax=10, selected=True,
                    premium=True, classColor='#957D5B', **{'battletype-key':'random'})

    def render(self, text, values=None):
        return layout.render(text, self.values() if values is None else values,
                             lambda key,value:'#ABCDEF',lambda key:'gui/marks.png')

    def test_requested_macros_including_nested_condition_and_class_color(self):
        self.assertEqual(self.render('{{v.c_wn8effd}} / {{v.wn8expd%d}}'), '#ABCDEF / 1500')
        self.assertEqual(self.render('{{v.c_type}}'), '#957D5B')
        self.assertEqual(self.render('{{battletype-key!=ranked?{{v.battletiermin}}-{{v.battletiermax}}|ranked}}'), '8-10')
        self.assertEqual(self.render('{{v.tfb?{{v.wn8expd%d}}|}}'), '1500')
        self.assertEqual(self.render('{{v.selected?100|0}}', {}), '0')

    def test_profiles_resolve_common_shadow_and_overrides_without_mutation(self):
        cfg=layout.config_defaults(); before=copy.deepcopy(cfg)
        validate(documents(cfg))
        normal=layout.build_profile(cfg['carousel']['normal'],self.render,True)
        small=layout.build_profile(cfg['carousel']['small'],self.render,True)
        self.assertEqual(normal['extraFields'][0]['alpha'],100)
        self.assertEqual(normal['extraFields'][0]['shadow']['distance'],0)
        self.assertEqual(normal['extraFields'][0]['shadow']['strength'],2)
        self.assertEqual(small['extraFields'][2]['shadow']['color'],'0xFC3700')
        self.assertEqual(small['extraFields'][2]['shadow']['alpha'],85)
        for profile in (normal, small):
            self.assertNotIn('{{',json.dumps(profile))
        self.assertEqual(cfg,before)
        cfg['carousel']['normal']['extraFields'][0]['shadow']='$ref:missing'
        with self.assertRaises(ValueError): validate(documents(cfg))

    def test_external_images_cache_shared_across_cards_and_rejects_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/ICON_ROOT/'#957D5B.png'
            target.parent.mkdir(parents=True)
            target.write_bytes((ROOT/'res/mods/Driftkings/Carroucel/#957D5B.png').read_bytes())
            images=CarouselImages(folder)
            field={'format':"<img src='%s#957D5B.png'>" % ICON_ROOT}
            cards={str(i):{'normal':{'extraFields':[field,field]}} for i in range(40)}
            with patch('builtins.open',wraps=open) as opened:
                first=images.collect(cards)
                self.assertEqual(images.collect(cards),first)
                self.assertEqual(opened.call_count,1)
            self.assertEqual(len(first),1)
            self.assertTrue(first[ICON_ROOT+'#957D5B.png'].startswith('data:image/png;base64,'))
            self.assertEqual(images.resolve(ICON_ROOT+'../private.png'),'')
            self.assertEqual(images.resolve('https://example.com/p.png'),'')
            field['showIcons']=False
            self.assertEqual(images.collect(cards),{})

    def test_supplied_external_paths_are_available_for_every_class(self):
        images=CarouselImages(ROOT/'res')
        for color in ('#1EA2D2','#53B329','#957D5B','#B87AB2','#F13439'):
            values=self.values(); values['classColor']=color
            profiles={mode:layout.build_profile(cfg,lambda text:self.render(text,values),True)
                      for mode,cfg in layout.defaults().items() if mode in ('normal','small')}
            assets=images.collect({'1':profiles})
            self.assertEqual(len(assets),4)
            self.assertTrue(all(assets.values()))

    def test_marks_icon_matches_current_client_singular_and_plural(self):
        path=ROOT/'source/scripts/client/Driftkings/lobby/carousel.py'
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body=[n for n in tree.body if getattr(n,'name','')=='render_macro']
        namespace=dict(layout=layout,bounded=lambda val,lo,hi,fallback:max(lo,min(hi,val)),ICONS={})
        exec(compile(tree,str(path),'exec'),namespace)
        for count in (1,2,3):
            result=namespace['render_macro']('{{icon:marksOnGun}}',dict(marksOnGun=count,nation='usa'))
            self.assertTrue(result.endswith('usa_%d_%s.png' % (count,'mark' if count==1 else 'marks')))
