# -*- coding: utf-8 -*-
from driftkings._constants import ROMAN_NUMERALS, TEAM_PANELS
from driftkings.core.panel_macros import Macros, truth
from driftkings.settings.team_panel_store import resolve_fields

# Preserve the panel macro's existing zero slot and upper bound (tier XI).
ROMAN=('',) + ROMAN_NUMERALS[:-1]
TYPES={'lightTank':'LT','mediumTank':'MT','heavyTank':'HT','AT-SPG':'TD','SPG':'SPG'}
# Numeric account and vehicle statistics hidden in event modes (colours are kept).
STATISTICS=('wn8','eff','wgr','winrate','xwn8','xeff','battles','kb','r','xr','t-kb','t-hb',
            't_battles','t_winrate','t_wins','t-battles','t-winrate','t-wins','tdv','tdb','tfb','tsb',
            'spg_battles','spg_percent','mark_of_mastery')

class Roster(object):
    def __init__(self, translations=None):
        self.translations = translations or {}
        # Event modes: colours stay, numbers and HP are hidden. Set per arena by
        # the roster owner, so reset() between arena updates must not clear it.
        self.restricted = False
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
        available=bool(data[TEAM_PANELS.STATS_ENABLED] and stats and 'battles' in stats and stats['battles']>=data[TEAM_PANELS.PERFORMANCE]['minBattlesToShow'])
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
            'a:spotted':100 if state in ('spotted','lost') and data[TEAM_PANELS.SPOTTED_ENABLED] else 0,
            'c:system':'#FFDD33' if own else ('#96FF00' if ally else '#F50800'),
            'sys-color-key':'player' if own else ('ally' if ally else 'enemy'),
            'stat-available':'stat' if available else '', 'pp.mode':TEAM_PANELS.MODES.index(self.mode),
            'pp.widthLeft':self.widths[0],'pp.widthRight':self.widths[1],
            'squad-num':vehicle.get('prebattleID') or None,
            'rankBadgeId':vehicle.get('rankBadgeId'), 'bp-stage':vehicle.get('bpStage'),
            'tk':'tk' if vehicle.get('isTeamKiller') else ''})
        values['r']=values.get(data[TEAM_PANELS.RATING])
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
        values['xr']=values.get({'wn8':'xwn8','eff':'xeff','wgr':'xwgr','winrate':'xwr'}.get(data[TEAM_PANELS.RATING],data[TEAM_PANELS.RATING]))
        values['r_size']={'xwn8':2,'xeff':2,'winrate':2,'wgr':5}.get(data[TEAM_PANELS.RATING],4)
        values['kb']=values.get('battles',0)/1000.0 if available else None
        for key,divisor in (('t-kb',1000.0),('t-hb',100.0)):
            values[key]=values.get('t-battles',0)/divisor if available else None
        for key in ('wn8','eff','wgr','winrate','xwn8','xeff','battles','t-battles','t-winrate','tdv','tdb','tfb','tsb'):
            source={'t-battles':'battles','t-winrate':'winrate'}.get(key,key)
            value=values.get(key)
            values['c:'+key]='#'+color(source,value,data[TEAM_PANELS.COLOR_SCALE]).lstrip('#') if value is not None and available else '#AAAAAA'
            values['a:'+key]=100 if value is not None and available else 0
        for key,target in (('r',data[TEAM_PANELS.RATING]),('xr',data[TEAM_PANELS.RATING]),('kb','battles')):
            values['c:'+key]=values.get('c:'+target,'#AAAAAA')
            values['a:'+key]=values.get('a:'+target,0)
        # Formats colour names with {{stat-color?..}}, which survives event modes.
        values['stat-color']='stat' if available else ''
        if self.restricted:
            for key in STATISTICS: values[key]=None
            values['stat-available']=''
        return values

    def screen(self,settings,values,data,side,dependencies=None):
        macros=Macros(values,data,self.translations,dependencies)
        if dependencies is not None: dependencies.update(('stat-available','stat-color'))
        result=macros.resolve(settings)
        # In event modes the numbers are hidden, but the player still has statistics.
        available=truth(values['stat-available']) or truth(values.get('stat-color'))
        result['enabled']=bool(settings.get('enabled',True) and (available or settings.get('showUnavailable',True)))
        fields=[]
        entries=settings.get('extraFields'+side,[])
        if isinstance(settings.get('extraFields'),dict):
            entries=settings['extraFields'][side.lower()+'Panel']['formats']
        for field in resolve_fields(entries,data[TEAM_PANELS.TEMPLATES]):
            field=macros.resolve(field)
            if not truth(field.get('enabled',True)): continue
            isHP=field.get('id','').startswith('hp')
            if isHP:
                mode=data.get(TEAM_PANELS.HP_VISIBILITY,'always')
                if not data[TEAM_PANELS.HP_ENABLED] or mode=='never' or self.restricted: continue
                # Groups are combined with AND; keys within each group are alternatives.
                if mode=='hold' and not all(any(code in self.keys for code in group)
                                            for group in data.get(TEAM_PANELS.HP_KEY,[[56,184]])): continue
            # The common HP selector governs background, bar and text together,
            # including older templates which carried their own ALT conditions.
            hotkey=None if isHP else field.get('hotKeyCode')
            if hotkey is not None:
                # A macro may resolve to text; like rows(), treat it as no hotkey.
                try: hotkey=int(hotkey)
                except (ValueError,TypeError,OverflowError): hotkey=None
            if hotkey is not None:
                # Left/right ALT are interchangeable in the default marker fields.
                codes=(56,184) if int(hotkey)==56 else (int(hotkey),)
                active=any(code in (self.keys if truth(field.get('onHold',False)) else self.toggled) for code in codes)
                if truth(field.get('visibleOnHotKey',True)) != active: continue
            fields.append(field)
        result['fields']=fields
        result.pop('extraFieldsLeft',None); result.pop('extraFieldsRight',None)
        return result
