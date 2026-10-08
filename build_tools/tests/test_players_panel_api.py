from settings_support import settings_globals
import ast
import logging
import sys
import types
import unittest
import weakref
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/scripts/client'))
from Driftkings.core.panel_model import Roster
from Driftkings.settings.settings_data import PROFILES,profile_for_mode
from Driftkings.settings.player_panel_store import defaults

class PanelAPITests(unittest.TestCase):
    def test_tab_configuration_keeps_panel_loading_and_macro_context_cached(self):
        from unittest.mock import Mock
        before = self.view.rows('large', {'panel', 'tab', 'loading'})[0]
        context = self.view.contextCache[1]
        self.view.model.screen = Mock(wraps=self.view.model.screen)
        self.view.config.data['tab']['formatLeftVehicle'] = 'Updated {{name}}'
        after = self.view.rows('large', {'panel', 'tab', 'loading'})[0]
        self.assertEqual(self.view.model.screen.call_count, 1)
        self.assertEqual(after['tab']['formatLeftVehicle'], 'Updated A')
        self.assertIs(after['panels']['large'], before['panels']['large'])
        self.assertIs(after['loading'], before['loading'])
        self.assertIs(self.view.contextCache[1], context)

    def test_diagnostics_and_unused_profile_changes_do_not_rebuild_visible_screen(self):
        from unittest.mock import Mock
        before = self.view.rows('large', {'panel', 'tab'})[0]
        self.view.model.screen = Mock(wraps=self.view.model.screen)
        self.view.config.data['performance']['diagnostics'] = True
        self.view.config.data['profiles']['short']['fragsFormatLeft'] = 'Changed'
        after = self.view.rows('large', {'panel', 'tab'})[0]
        self.view.model.screen.assert_not_called()
        self.assertIs(after['panels']['large'], before['panels']['large'])
        self.assertIs(after['tab'], before['tab'])
        short = self.view.rows('short', {'panel'})[0]
        self.assertEqual(short['panels']['short']['fragsFormatLeft'], 'Changed')

    def test_stat_threshold_change_refreshes_all_macro_contexts(self):
        self.view.stats.getPlayersInfo = lambda ident: {'battles': 100, 'wn8': 2200}
        self.view.config.data['tab']['formatLeftVehicle'] = '{{wn8|missing}}'
        before = self.view.rows('large', {'panel', 'tab'})[0]
        self.assertEqual(before['tab']['formatLeftVehicle'], '2200')
        self.view.config.data['performance']['minBattlesToShow'] = 101
        after = self.view.rows('large', {'panel', 'tab'})[0]
        self.assertEqual(after['tab']['formatLeftVehicle'], 'missing')
        self.assertIsNot(after['panels']['large'], before['panels']['large'])

    def test_own_health_does_not_invalidate_unused_my_macros_for_other_players(self):
        from unittest.mock import Mock
        for ident in range(2,31):
            self.player.arena.vehicles[ident]={'accountDBID':42+ident,'name':'Player%d'%ident,'team':2,'isAlive':True}
        self.view.model.set_health(1,1000,1000)
        self.view.rows('large',{'panel','tab'})
        self.view.model.screen=Mock(wraps=self.view.model.screen)
        self.view.model.set_health(1,500,1000)
        self.view.rows('large',{'panel','tab'})
        self.assertEqual(self.view.resolvedRows,1)
        self.assertEqual(self.view.model.screen.call_count,1)

    def test_cached_condition_tracks_new_branch_then_dynamic_macro_name(self):
        self.view.config.data['tab']['formatLeftVehicle']='{{my-hp>500?{{wn8|none}}|{{{{vehicle}}}}}}'
        descriptor=types.SimpleNamespace(compactDescr=1,userString='hp',shortUserString='hp',name='usa:Test',tags=set())
        self.player.arena.vehicles[1]['vehicleType']=types.SimpleNamespace(type=descriptor,level=8,maxHealth=1000)
        self.view.model.set_health(1,1000,1000)
        self.assertEqual(self.view.rows('large',{'tab'})[0]['tab']['formatLeftVehicle'],'none')
        self.view.model.set_health(1,400,1000)
        self.assertEqual(self.view.rows('large',{'tab'})[0]['tab']['formatLeftVehicle'],'400')
        self.view.model.set_health(1,300,1000)
        self.assertEqual(self.view.rows('large',{'tab'})[0]['tab']['formatLeftVehicle'],'300')

    def test_ratio_template_dependency_refreshes_max_health(self):
        self.view.config.data['templates']['testRatio']={'id':'ratio','width':'{{hp-ratio:70}}'}
        self.view.config.data['tab']['extraFieldsLeft']=[{'ref':'testRatio'}]
        self.view.model.set_health(1,500,1000)
        old=self.view.rows('large',{'tab'})[0]['tab']
        self.view.model.set_health(1,500,2000)
        new=self.view.rows('large',{'tab'})[0]['tab']
        self.assertEqual(old['fields'][0]['width'],'35')
        self.assertEqual(new['fields'][0]['width'],'18')

    def test_missing_stat_becoming_available_invalidates_cached_fallback(self):
        self.view.config.data['tab']['formatLeftVehicle']='{{wn8|--}}'
        self.assertEqual(self.view.rows('large',{'tab'})[0]['tab']['formatLeftVehicle'],'--')
        self.view.stats.getPlayersInfo=lambda ident:{'battles':100,'wn8':2200}
        row=self.view.rows('large',{'tab'})[0]
        self.assertEqual(row['tab']['formatLeftVehicle'],'2200')

    def test_optional_diagnostics_count_only_causes_that_rebuild_formats(self):
        self.view.config.data['tab']['formatLeftVehicle']='{{hp}}'
        self.view.config.data['performance']['diagnostics']=True
        self.view.model.set_health(1,1000,1000)
        self.view.rows('large',{'tab'})
        self.assertEqual(self.view.invalidationCauses,{'cold':1})
        self.view.invalidationCauses.clear()
        self.view.model.set_health(1,500,1000)
        self.view.rows('large',{'tab'})
        self.assertEqual(self.view.invalidationCauses,{'hp':1})
        self.view.invalidationCauses.clear()
        self.view.model.widths=(400,400)
        self.view.rows('large',{'tab'})
        self.assertEqual(self.view.invalidationCauses,{})
        self.view.config.data['performance']['diagnostics']=False
        self.view.rows('large',{'tab'})
        self.assertEqual(self.view.invalidationCauses,{})

    def test_tab_switch_reuses_resolved_screens_for_thirty_players(self):
        from unittest.mock import Mock
        for ident in range(2,31):
            self.player.arena.vehicles[ident]={'accountDBID':42+ident,'name':'Player%d'%ident,'team':2,'isAlive':True}
        self.view.model.screen=Mock(wraps=self.view.model.screen)
        panel=self.view.rows('large',{'panel'})
        self.assertEqual(self.view.model.screen.call_count,30)
        tab=self.view.rows('large',{'tab'})
        self.assertEqual(self.view.model.screen.call_count,60)
        for unused in range(5):
            again=self.view.rows('large',{'panel'})
            self.assertEqual(self.view.resolvedRows,0)
            self.assertIs(again[0]['panels']['large'],panel[0]['panels']['large'])
            again=self.view.rows('large',{'tab'})
            self.assertEqual(self.view.resolvedRows,0)
            self.assertIs(again[0]['tab'],tab[0]['tab'])
        self.assertEqual(self.view.model.screen.call_count,60)
        self.view.model.set_health(2,400,1000)
        self.view.rows('large',{'panel'})
        self.assertEqual(self.view.resolvedRows,1)
        self.assertEqual(self.view.model.screen.call_count,61)
        self.view.rows('large',{'tab'})
        self.assertEqual(self.view.resolvedRows,0) # Default TAB does not use HP.
        self.assertEqual(self.view.model.screen.call_count,61)

    def test_hidden_screen_refreshes_hp_stats_and_preserves_published_snapshot(self):
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'Enemy','team':2,'isAlive':True}
        self.view.config.data['tab']['formatRightVehicle']='{{hp}} / {{wn8}}'
        self.view.model.set_health(2,1000,1000)
        self.view.stats.getPlayersInfo=lambda ident:{'battles':100,'wn8':1000}
        old=next(r for r in self.view.rows('large',{'tab'}) if r['id']==2)['tab']
        self.view.model.set_health(2,300,1000)
        self.view.stats.getPlayersInfo=lambda ident:{'battles':100,'wn8':2000}
        self.view.rows('large',{'panel'})
        self.assertIs(self.view.screenCache[2]['tab']['result'],old) # Kept lazy until shown.
        new=next(r for r in self.view.rows('large',{'tab'}) if r['id']==2)['tab']
        self.assertEqual(old['formatRightVehicle'],'1000 / 1000')
        self.assertEqual(new['formatRightVehicle'],'300 / 2000')

    def test_hidden_screen_observes_own_macros_and_config_edits(self):
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'Enemy','team':2,'isAlive':True}
        self.view.config.data['tab']['formatRightVehicle']='{{my-hp}}'
        self.view.model.set_health(1,1000,1000)
        self.view.rows('large',{'tab'})
        self.view.model.set_health(1,400,1000)
        self.view.rows('large',{'panel'})
        new=next(r for r in self.view.rows('large',{'tab'}) if r['id']==2)
        self.assertEqual(new['tab']['formatRightVehicle'],'400')
        self.view.config.data['tab']['formatRightVehicle']='HP: {{my-hp}}'
        self.view.rows('large',set())
        new=next(r for r in self.view.rows('large',{'tab'}) if r['id']==2)
        self.assertEqual(new['tab']['formatRightVehicle'],'HP: 400')

    def test_hidden_panel_observes_hotkeys_and_cached_profiles_stay_distinct(self):
        self.view.config.data['hpVisibility']='hold'
        self.view.rows('large',{'panel'})
        self.view.rows('large',{'tab'})
        self.view.model.key(56,True)
        self.view.rows('large',{'tab'})
        row=self.view.rows('large',{'panel'})[0]
        fields=dict((f['id'],f) for f in row['panels']['large']['fields'])
        self.assertIn('hp',fields)
        large=row['panels']['large']
        short=self.view.rows('short',{'panel'})[0]['panels']['short']
        self.assertIsNot(short,large)
        self.assertIs(self.view.rows('large',{'panel'})[0]['panels']['large'],large)

    def test_screen_cache_is_released_on_departure_arena_change_and_end(self):
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'Enemy','team':2,'isAlive':True}
        self.view.rows('large')
        del self.player.arena.vehicles[2]
        self.view.rows('large',set())
        self.assertNotIn(2,self.view.screenCache)
        old=self.view.screenCache[1]
        self.player.arena=types.SimpleNamespace(vehicles=dict(self.player.arena.vehicles),statistics={})
        self.view.rows('large',{'panel'})
        self.assertIsNot(self.view.screenCache[1],old)
        self.assertNotIn('tab',self.view.screenCache[1])
        self.view.end()
        self.assertEqual(self.view.screenCache,{})

    def test_only_changed_player_rebuilds_values_and_hidden_screens_are_lazy(self):
        from unittest.mock import Mock
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'Enemy','team':2,'isAlive':True}
        self.view.model.values=Mock(wraps=self.view.model.values)
        self.view.rows('large',{'panel'})
        self.assertEqual(self.view.model.values.call_count,2)
        self.view.rows('large',{'panel'})
        self.assertEqual(self.view.model.values.call_count,2)
        self.view.model.set_health(2,500,1000)
        rows=self.view.rows('large',{'panel'})
        self.assertEqual(self.view.model.values.call_count,3)
        self.assertEqual(self.view.resolvedRows,1)
        self.assertTrue(all(row['tab']=={'enabled':False} for row in rows))
        rows=self.view.rows('large',{'tab'})
        self.assertTrue(all(not row['panels'] for row in rows))
        self.assertTrue(all(row['tab']['enabled'] for row in rows))

    def test_movement_keys_do_not_invalidate_rows_but_configured_hotkeys_do(self):
        self.view.config.data['hpVisibility']='hold'
        first=self.view.rows('large')[0]
        self.view.model.key(17,True)  # W, not a roster hotkey.
        self.assertIs(self.view.rows('large')[0],first)
        self.view.model.key(56,True)
        self.assertIsNot(self.view.rows('large')[0],first)

    def test_changed_vehicle_descriptor_refreshes_cached_context(self):
        vehicle=self.player.arena.vehicles[1]
        descriptor=types.SimpleNamespace(compactDescr=1,userString='Old',shortUserString='Old',name='usa:Old',tags=set())
        vehicle['vehicleType']=types.SimpleNamespace(type=descriptor,level=8,maxHealth=1000)
        first=self.view.rows('large')[0]
        descriptor.userString='New'; descriptor.compactDescr=2
        second=self.view.rows('large')[0]
        self.assertIsNot(first,second)
        self.assertIn('New',second['tab']['formatLeftVehicle'])

    def test_flash_transport_sends_only_changed_row_and_removes_departed(self):
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'Enemy','team':2,'isAlive':True}
        self.view.config.data['profiles']['large']['vehicleFormatRight']='{{hp}}'
        sent=[]
        namespace=self.view.tick.__globals__
        namespace['BigWorld'].time=lambda:1
        namespace['time']=types.SimpleNamespace(time=lambda:100,strftime=lambda fmt:'00')
        self.view.stats.loadStats=lambda:None
        self.view.arena=self.player.arena
        self.view.view=types.SimpleNamespace(_isDAAPIInited=lambda:True,as_setRosterS=sent.append)
        self.view.tick(); self.assertEqual(len(sent[0]['rows']),2)
        self.view.tick(); self.assertEqual(len(sent),1)
        self.view.model.set_health(2,500,1000)
        self.view.tick()
        self.assertNotIn('rows',sent[-1])
        self.assertEqual([row['id'] for row in sent[-1]['rowUpdates']],[2])
        self.player.arena.vehicles.pop(2)
        self.view.tick(); self.assertEqual(sent[-1]['rowOrder'],[1])

    def setUp(self):
        self.player=types.SimpleNamespace(team=1,playerVehicleID=1,arena=types.SimpleNamespace(vehicles={1:{'accountDBID':42,'name':'A','team':1,'isAlive':True}},statistics={1:{'frags':3}}))
        path=ROOT/'source/scripts/client/Driftkings/views/battle/player_ratings.py'
        node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='RatingViews')
        self.cancelled=[]; self.callbacks=[]
        world=types.SimpleNamespace(player=lambda:self.player,cancelCallback=self.cancelled.append,callback=lambda delay,fn:self.callbacks.append(fn) or len(self.callbacks),entity=lambda ident:None)
        namespace={'BigWorld':world,'Roster':Roster,'PlayersPanelMeta':object,'PROFILES':PROFILES,'profile_for_mode':profile_for_mode,'weakref':weakref,'deepcopy':deepcopy,'getStatisticColor':lambda *args:'FFFFFF','LOG':logging.getLogger('test')}
        settings_globals(namespace, 'views.battle.player_ratings')
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
        config=types.SimpleNamespace(data=defaults())
        stats=types.SimpleNamespace(getPlayersInfo=lambda ident:None,reset=lambda:None)
        self.view=namespace['RatingViews'](config,stats); self.view.active=True
    def test_native_order_metadata_and_original_preserved(self):
        calls=[]
        packet={'leftItemsIDs':[1], 'leftVehicleInfos':[{'vehicleID':1,'squadIndex':2,'userTags':['friend']}]}
        original=lambda controller,data:calls.append(data) or 'original'
        self.assertEqual(self.view.captureOrder(original,None,packet),'original')
        self.assertEqual(self.view.model.order['left'],[1])
        self.assertEqual(self.view.model.metadata[1]['squadIndex'],2)
        self.view.captureOrder(original,None,{'leftItemsIDs':None})
        self.assertEqual(self.view.model.order['left'],[1])
        self.player.arena=types.SimpleNamespace(vehicles={},statistics={})
        self.view.captureOrder(original,None,{})
        self.assertEqual(self.view.model.order['left'],[])
        self.assertEqual(self.view.model.metadata,{})
    def test_loading_tab_panel_share_frags_identity_and_missing_stats(self):
        rows=self.view.rows(); row=rows[0]
        self.assertEqual(row['panels']['short']['fragsFormatLeft'],'3')
        self.assertEqual(row['tab']['formatLeftFrags'],'3')
        self.assertIn('A',row['loading']['formatLeftNick'])
        self.view.config.data['loading']['enabled']=False
        row=self.view.rows()[0]
        self.assertFalse(row['loading']['enabled']); self.assertNotIn('tips',row)
        self.assertTrue(row['tab']['enabled'])
    def test_hover_restores_base_mode_without_writing_client_setting(self):
        class Panel:
            def __init__(self): self.calls=[]
            def as_setPanelModeS(self,mode): self.calls.append(mode)
        panel=Panel(); self.view.panel=weakref.ref(panel); self.view.baseMode=1
        self.view.hover(True); self.view.hover(True); self.view.hover(False)
        self.assertEqual(panel.calls,[4,1])

    def test_initial_mode_after_countdown_is_medium2_and_manual_mode_survives(self):
        owner=self.view
        class Panel:
            def __init__(self): self.calls=[]; self._mode=4
            def as_setPanelModeS(self,mode):
                owner.nativeMode(lambda panel,value:self.calls.append(value),self,mode)
        panel=Panel()
        self.assertEqual(panel._mode,4)  # Native countdown uses large.
        def initial(panel):
            panel._mode=2; panel.as_setPanelModeS(2)
            return 'native'
        self.assertEqual(owner.initialMode(initial,panel),'native')
        self.assertEqual((panel._mode,owner.baseMode,owner.model.mode),(3,3,'medium2'))
        panel._mode=1; panel.as_setPanelModeS(1)
        owner.hover(True); owner.hover(False)
        self.assertEqual(panel.calls[-3:],[1,4,1])
    def test_end_cancels_updates_and_clears_arena_state(self):
        self.view.callback=8; self.view.model.set_health(1,700,1500)
        self.view.end()
        self.assertEqual(self.cancelled,[8]); self.assertEqual(self.view.model.health,{})
        self.assertIsNone(self.view.callback); self.assertIsNone(self.view.arena)
    def test_native_health_delegates_before_caching(self):
        calls=[]
        self.assertEqual(self.view.nativeHealth(lambda *args:calls.append(args) or 9,None,1,500,1500),9)
        self.assertEqual(calls,[(None,1,500,1500)])
        self.assertEqual(self.view.model.health[1]['hp'],500)

    def test_unchanged_rows_reuse_resolved_macros_and_only_send_active_profile(self):
        first=self.view.rows('short')[0]
        self.assertEqual(set(first['panels']),{'short'})
        self.assertIs(first,self.view.rows('short')[0])
        self.assertIsNot(first,self.view.rows('large')[0])

    def test_cache_invalidates_for_health_keys_stats_order_and_settings(self):
        self.view.config.data['hpVisibility']='hold'
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'B','team':2,'isAlive':True}
        previous=self.view.rows('short')
        def update():
            current=self.view.rows('short')
            self.assertIsNot(previous[0],current[0])
            return current
        self.view.model.set_health(1,500,1500); previous=update()
        self.view.model.key(56,True); previous=update()
        self.view.stats.getPlayersInfo=lambda ident:{'battles':1000,'wn8':2000}
        previous=update()
        self.view.model.set_order('left',[1]); previous=update()
        self.view.config.data['profiles']['short']['fragsFormatLeft']='{{hp}}'
        previous=update()
        self.assertEqual(previous[0]['panels']['short']['fragsFormatLeft'],'500')
        self.player.arena.vehicles.pop(2)
        self.view.rows('short')
        self.assertNotIn(2,self.view.rowCache)

    def test_new_arena_cannot_reuse_old_resolved_rows(self):
        previous=self.view.rows('short')[0]
        self.player.arena=types.SimpleNamespace(vehicles=dict(self.player.arena.vehicles),statistics={1:{'frags':3}})
        self.assertIsNot(previous,self.view.rows('short')[0])

    def test_native_name_alias_change_invalidates_row_identity(self):
        previous=self.view.rows('large')[0]
        self.view.model.metadata[1]={'playerFakeName':'Anonymous','playerFullName':'Anonymous[CLAN]'}
        current=self.view.rows('large')[0]
        self.assertIsNot(previous,current)
        self.assertIn('Anonymous[CLAN]',current['aliases'])

    def test_battle_panel_resolves_statistics_hp_and_enemy_spotted(self):
        self.player.arena.vehicles[2]={'accountDBID':43,'name':'Enemy','team':2,'isAlive':True}
        self.view.stats.getPlayersInfo=lambda ident:{'battles':1000,'wn8':2165,'winrate':49}
        self.view.model.set_health(2,500,1000)
        self.view.model.visibility(2,True)
        self.view.model.key(56,True)
        row=next(r for r in self.view.rows('large') if r['id']==2)
        profile=row['panels']['large']
        self.assertIn('2165',profile['nickFormatRight'])
        self.assertNotIn('{{',profile['nickFormatRight'])
        fields=dict((field['id'],field) for field in profile['fields'])
        self.assertEqual(fields['hpBar']['width'],'36')
        self.assertIn('500',fields['hp']['format'])
        self.assertTrue(fields['enemySpottedMarker']['src'].endswith('/spotted.png'))
        self.view.model.visibility(2,False)
        row=next(r for r in self.view.rows('large') if r['id']==2)
        fields=dict((field['id'],field) for field in row['panels']['large']['fields'])
        self.assertTrue(fields['enemySpottedMarker']['src'].endswith('/lost.png'))
