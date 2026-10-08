# -*- coding: utf-8 -*-
from Driftkings._constants import PLAYER_PANEL_PRO
from Driftkings.core.panel_macros import Macros, truth
from Driftkings.settings.player_panel_store import resolve_fields

ROMAN=('','I','II','III','IV','V','VI','VII','VIII','IX','X','XI')
TYPES={'lightTank':'LT','mediumTank':'MT','heavyTank':'HT','AT-SPG':'TD','SPG':'SPG'}

class Roster(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.vehicles={}
        self.metadata={}
        self.health={}
        self.spotted={}
        self.order={'left':[], 'right':[]}
        self.initial={'left':[], 'right':[]}
        self.keys=set()
        self.toggled=set()
        self.mode='large'
        self.widths=(0,0)

    def sync(self,vehicles):
        for ident,vehicle in vehicles.items():
            old=self.vehicles.get(ident)
            signature=(vehicle.get('accountDBID'),getattr(getattr(vehicle.get('vehicleType'),'type',None),'compactDescr',None))
            alive=vehicle.get('isAlive',True)
            if old and (old[0]!=signature or not old[1] and alive):
                self.health.pop(ident,None)
                self.spotted.pop(ident,None)
            self.vehicles[ident]=(signature,alive)
            if not alive:
                self.set_health(ident,0)
                self.spotted[ident]='dead'
        for ident in set(self.vehicles)-set(vehicles):
            self.vehicles.pop(ident,None)
            self.health.pop(ident,None)
            self.spotted.pop(ident,None)

    def set_health(self,ident,hp,maximum=None):
        if hp is None or hp<0: return
        previous=self.health.get(ident,{})
        self.health[ident]={'hp':max(0,int(hp)), 'max':max(int(maximum or previous.get('max',0)),int(hp))}
        if hp>0 and ident in self.vehicles and not self.vehicles[ident][1]:
            self.vehicles[ident]=(self.vehicles[ident][0],True)
            self.spotted.pop(ident,None)

    def visibility(self,ident,visible):
        if self.spotted.get(ident)=='dead': return
        self.spotted[ident]='spotted' if visible else ('lost' if self.spotted.get(ident) in ('spotted','lost') else 'neverSeen')

    def set_order(self,side,ids):
        self.order[side]=list(ids)
        self.initial[side].extend(ident for ident in ids if ident not in self.initial[side])

    def key(self,code,down):
        if down and code not in self.keys:
            if code in self.toggled: self.toggled.remove(code)
            else: self.toggled.add(code)
        if down: self.keys.add(code)
        else: self.keys.discard(code)

    def values(self,ident,vehicle,stats,playerID,team,data,color):
        vtype=vehicle.get('vehicleType')
        descriptor=getattr(vtype,'type',None)
        name=vehicle.get('name','')
        clan=vehicle.get('clanAbbrev','')
        level=getattr(vtype,'level',0)
        tags=getattr(descriptor,'tags',set())
        tag=next((key for key in TYPES if key in tags),'')
        alive=vehicle.get('isAlive',True)
        hp=self.health.get(ident,{})
        maximum=hp.get('max') or getattr(vtype,'maxHealth',0)
        state=self.spotted.get(ident,'neverSeen')
        own=ident==playerID
        ally=vehicle.get('team')==team
        available=bool(data[PLAYER_PANEL_PRO.STATS_ENABLED] and stats and 'battles' in stats and stats['battles']>=data[PLAYER_PANEL_PRO.PERFORMANCE]['minBattlesToShow'])
        values=dict(stats or {}) if available else {}
        for key in ('t_battles','t_winrate','t_wins'):
            if key in values: values[key.replace('_','-')]=values[key]
        for key in tuple(values):
            if values[key]==u'\u2014': values[key]=None
        values.update({'name':name,'clannb':clan,'clan':'[%s]'%clan if clan else '',
            'nick':name+(' [%s]'%clan if clan else ''),'veh-id':ident,
            'vehicle':getattr(descriptor,'userString',''),'vehicle-short':getattr(descriptor,'shortUserString',''),
            'vehiclename':getattr(descriptor,'name','').replace(':','-'),
            'level':level,'rlevel':ROMAN[level] if 0<=level<len(ROMAN) else str(level),
            'vtype':TYPES.get(tag,''),'vtype-key':TYPES.get(tag,''),'vtype-l':tag,
            'nation':getattr(descriptor,'name','').partition(':')[0],
            'premium':'premium' if 'premium' in tags else '', 'special':'special' if 'special' in tags else '',
            'alive':'alive' if alive else '', 'ally':'ally' if ally else '', 'player':'pl' if own else '',
            'anonym':'anonym' if vehicle.get('isAnonymized') else '',
            'ready':'ready' if vehicle.get('isReady',bool(hp)) else '',
            'hp':hp.get('hp',maximum) if alive else 0,'hp-max':maximum,
            'spotted':state if state in ('spotted','lost') else '',
            'c:spotted':'#FFBB00' if state=='spotted' else '#D9D9D9',
            'a:spotted':100 if state in ('spotted','lost') and data[PLAYER_PANEL_PRO.SPOTTED_ENABLED] else 0,
            'c:system':'#FFDD33' if own else ('#96FF00' if ally else '#F50800'),
            'sys-color-key':'player' if own else ('ally' if ally else 'enemy'),
            'xvm-stat':'stat' if available else '', 'pp.mode':('none','short','medium','medium2','large').index(self.mode),
            'pp.widthLeft':self.widths[0],'pp.widthRight':self.widths[1],
            'squad-num':vehicle.get('prebattleID') or None,
            'rankBadgeId':vehicle.get('rankBadgeId'), 'bp-stage':vehicle.get('bpStage'),
            'tk':'tk' if vehicle.get('isTeamKiller') else ''})
        values['r']=values.get(data[PLAYER_PANEL_PRO.RATING])
        meta=self.metadata.get(ident,{})
        status=meta.get('playerStatus',0)
        userTags=meta.get('userTags',[])
        values.update({'squad-num':meta.get('squadIndex') or None,
                       'squad':'sq' if status & 4 else '',
                       'selected':'sel' if status & 8 else '',
                       'tk':'tk' if status & 1 else values['tk'],
                       'friend':'friend' if 'friend' in userTags else '',
                       'ignored':'ignored' if 'ignored' in userTags or 'tmp_ignored' in userTags else '',
                       'muted':'muted' if 'muted' in userTags else '',
                       'chatban':'chatban' if 'ban/chat' in userTags else ''})
        if 'vehicleStatus' in meta:
            values['ready']='ready' if meta['vehicleStatus'] & 2 else ''
        badge=meta.get('badge') or {}
        icon=badge.get('icon','')
        if icon.startswith('badge_') and icon[6:].isdigit():
            values['rankBadgeId']=int(icon[6:])
        values['bp-stage']=badge.get('content')
        values['hasBadges']='true' if any(m.get('hasSelectedBadge') for m in self.metadata.values()) else ''
        values['xr']=values.get({'wn8':'xwn8','eff':'xeff','wgr':'xwgr','winrate':'xwr'}.get(data[PLAYER_PANEL_PRO.RATING],data[PLAYER_PANEL_PRO.RATING]))
        values['r_size']={'xwn8':2,'xeff':2,'winrate':2,'wgr':5}.get(data[PLAYER_PANEL_PRO.RATING],4)
        values['kb']=values.get('battles',0)/1000.0 if available else None
        for key,divisor in (('t-kb',1000.0),('t-hb',100.0)):
            values[key]=values.get('t-battles',0)/divisor if available else None
        for key in ('wn8','eff','wgr','winrate','xwn8','xeff','battles','t-battles','t-winrate','tdv','tdb','tfb','tsb'):
            source={'t-battles':'battles','t-winrate':'winrate'}.get(key,key)
            value=values.get(key)
            values['c:'+key]='#'+color(source,value,data[PLAYER_PANEL_PRO.COLOR_SCALE]).lstrip('#') if value is not None and available else '#AAAAAA'
            values['a:'+key]=100 if value is not None and available else 0
        for key,target in (('r',data[PLAYER_PANEL_PRO.RATING]),('xr',data[PLAYER_PANEL_PRO.RATING]),('kb','battles')):
            values['c:'+key]=values.get('c:'+target,'#AAAAAA')
            values['a:'+key]=values.get('a:'+target,0)
        return values

    def screen(self,settings,values,data,side,dependencies=None):
        macros=Macros(values,data,{'Destroyed':'Destruido'},dependencies)
        if dependencies is not None: dependencies.add('xvm-stat')
        result=macros.resolve(settings)
        result['enabled']=bool(settings.get('enabled',True) and (truth(values['xvm-stat']) or settings.get('showUnavailable',True)))
        fields=[]
        entries=settings.get('extraFields'+side,[])
        if isinstance(settings.get('extraFields'),dict):
            entries=settings['extraFields'][side.lower()+'Panel']['formats']
        for field in resolve_fields(entries,data[PLAYER_PANEL_PRO.TEMPLATES]):
            field=macros.resolve(field)
            if not truth(field.get('enabled',True)): continue
            isHP=field.get('id','').startswith('hp')
            if isHP:
                mode=data.get(PLAYER_PANEL_PRO.HP_VISIBILITY,'always')
                if not data[PLAYER_PANEL_PRO.HP_ENABLED] or mode=='never': continue
                # Groups are combined with AND; keys within each group are alternatives.
                if mode=='hold' and not all(any(code in self.keys for code in group)
                                            for group in data.get(PLAYER_PANEL_PRO.HP_KEY,[[56,184]])): continue
            # The common HP selector governs background, bar and text together,
            # including older templates which carried their own ALT conditions.
            hotkey=None if isHP else field.get('hotKeyCode')
            if hotkey is not None:
                # Left/right ALT are interchangeable in the default XVM fields.
                codes=(56,184) if int(hotkey)==56 else (int(hotkey),)
                active=any(code in (self.keys if truth(field.get('onHold',False)) else self.toggled) for code in codes)
                if truth(field.get('visibleOnHotKey',True)) != active: continue
            fields.append(field)
        result['fields']=fields
        result.pop('extraFieldsLeft',None); result.pop('extraFieldsRight',None)
        return result
