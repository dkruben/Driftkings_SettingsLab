import sys
import types
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/scripts/client'))
from Driftkings.core.panel_model import Roster
from Driftkings.core.panel_macros import Macros
from Driftkings.settings.player_panel_store import defaults

class HealthLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.model=Roster(); self.data=defaults()
        self.vehicle={'accountDBID':42,'name':'A<&','clanAbbrev':'TEST','team':1,'isAlive':True,
                      'vehicleType':types.SimpleNamespace(level=8,maxHealth=1500,type=types.SimpleNamespace(compactDescr=10,userString='Tank full',shortUserString='Tank',name='usa:test',tags={'heavyTank'}))}
    def values(self):
        return self.model.values(1,self.vehicle,None,1,1,self.data,lambda *a:'FFFFFF')
    def test_damage_before_appearance_and_out_of_sight(self):
        self.model.set_health(1,800,1500)
        self.model.sync({1:self.vehicle})
        self.model.visibility(1,True); self.model.visibility(1,False)
        self.assertEqual(self.values()['hp'],800)
        self.assertEqual(self.values()['spotted'],'lost')
        self.assertEqual(Macros(self.values()).render('{{hp-ratio:70}}'),'38')
    def test_respawn_same_id_resets_old_death(self):
        self.model.sync({1:self.vehicle}); self.model.set_health(1,0,1500)
        self.vehicle['isAlive']=False; self.model.sync({1:self.vehicle})
        self.assertEqual(self.values()['hp'],0)
        self.vehicle['isAlive']=True; self.model.sync({1:self.vehicle})
        self.assertEqual(self.values()['hp'],1500)
        self.assertEqual(self.values()['spotted'],'')
    def test_new_vehicle_id_has_separate_health(self):
        self.model.set_health(1,200,1500)
        self.model.sync({1:self.vehicle,2:self.vehicle})
        self.assertNotIn(2,self.model.health)
        self.assertEqual(self.model.health[1]['hp'],200)
    def test_initial_order_stable_after_death_new_ids_appended(self):
        self.model.set_order('left',[1,2,3]); self.model.set_order('left',[3,2,1,4])
        self.assertEqual(self.model.initial['left'],[1,2,3,4])
        self.assertEqual(self.model.order['left'],[3,2,1,4])
    def test_hp_hold_and_always_and_spotted_toggle(self):
        values=self.values(); cfg=self.data['profiles']['short']
        self.assertTrue(any(f.get('id')=='hp' for f in self.model.screen(cfg,values,self.data,'Left')['fields']))
        self.data['hpVisibility']='hold'
        self.assertFalse(any(f.get('id')=='hp' for f in self.model.screen(cfg,values,self.data,'Left')['fields']))
        self.model.key(184,True)
        self.assertTrue(any(f.get('id')=='hp' for f in self.model.screen(cfg,values,self.data,'Left')['fields']))
        self.model.key(184,False)
        self.assertFalse(self.model.screen(cfg,values,self.data,'Left')['fields'])
        self.data['hpVisibility']='always'
        self.assertTrue(any(f.get('id')=='hp' for f in self.model.screen(cfg,values,self.data,'Left')['fields']))
        self.data['hpEnabled']=False
        self.assertFalse(any(f.get('id')=='hp' for f in self.model.screen(cfg,values,self.data,'Left')['fields']))

    def test_hp_modes_override_old_template_hotkeys_and_leave_spotted_visible(self):
        self.vehicle['team']=2
        cfg=self.data['profiles']['medium2']
        self.data['templates']['hp'].update(hotKeyCode=56,onHold=True)
        def ids():
            return [f['id'] for f in self.model.screen(cfg,self.values(),self.data,'Right')['fields']]
        self.assertEqual(ids(),['hpBarBg','hpBar','hp','enemySpottedMarker'])
        self.data['hpVisibility']='hold'; self.data['hpKey']=[[29,157],[35]]
        self.model.key(35,True)
        self.assertEqual(ids(),['enemySpottedMarker'])
        self.model.key(157,True)
        self.assertIn('hp',ids())
        self.model.key(35,False)
        self.assertEqual(ids(),['enemySpottedMarker'])
        self.data['hpVisibility']='never'
        self.model.key(35,True)
        self.assertEqual(ids(),['enemySpottedMarker'])

    def test_legacy_hp_textures_health_and_layer_order(self):
        cfg=self.data['profiles']['medium2']
        self.model.set_health(1,750,1500)
        fields=self.model.screen(cfg,self.values(),self.data,'Left')['fields']
        self.assertEqual([f['id'] for f in fields],['hpBarBg','hpBar','hp'])
        self.assertEqual(fields[1]['width'],'36')
        self.assertTrue(fields[1]['src'].endswith('/hp_alive_l.png'))
        self.assertEqual(fields[2]['format'],'750/1500')
        self.vehicle['team']=2
        fields=self.model.screen(cfg,self.values(),self.data,'Right')['fields']
        self.assertTrue(fields[1]['src'].endswith('/hp_alive_r.png'))
        self.model.set_health(1,0,1500); self.vehicle['isAlive']=False
        fields=self.model.screen(cfg,self.values(),self.data,'Right')['fields']
        self.assertNotIn('hpBar',[f['id'] for f in fields])
        self.assertEqual(next(f for f in fields if f['id']=='hp')['format'],'0/1500')

    def test_legacy_spotted_images_all_states_and_disabled(self):
        self.vehicle['team']=2
        cfg=self.data['profiles']['medium2']
        for state in ('neverSeen','spotted','lost','dead'):
            self.model.spotted[1]=state; self.vehicle['isAlive']=state!='dead'
            fields=self.model.screen(cfg,self.values(),self.data,'Right')['fields']
            marker=next(f for f in fields if f['id']=='enemySpottedMarker')
            self.assertTrue(marker['src'].endswith('/'+state+'.png'))
        self.data['spottedEnabled']=False
        fields=self.model.screen(cfg,self.values(),self.data,'Right')['fields']
        self.assertNotIn('enemySpottedMarker',[f['id'] for f in fields])
    def test_no_stats_does_not_remove_identity_or_frags(self):
        values=self.values(); values['frags']=3
        macro=Macros(values)
        self.assertEqual(macro.render('{{name}}'),'A&lt;&amp;')
        self.assertEqual(macro.render('{{vehicle}} / {{vehicle-short}}'),'Tank full / Tank')
        self.assertEqual(macro.render('{{wn8|----}} / {{frags}}'),'---- / 3')
