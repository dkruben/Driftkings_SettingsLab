# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, PLAYER_PANEL_PRO
from Driftkings.settings.service import settings_service, SettingsChanges, changed_paths, affects
"""Native roster bridge; all three screens share identity, health and macros."""
from Driftkings._constants import BATTLE_ALIASES
import logging
import time
import weakref
from copy import deepcopy
import BigWorld
from Driftkings.meta.battle.players_panel import PlayersPanelMeta
from gui.Scaleform.daapi.view.battle.classic.players_panel import PlayersPanel
from gui.Scaleform.daapi.view.meta.BattleStatisticDataControllerMeta import BattleStatisticDataControllerMeta
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from Driftkings.core.hooks import override
from Driftkings.core.battle_events import battleEvents
from Driftkings.core.panel_model import Roster
from Driftkings.settings.settings_data import PROFILES, profile_for_mode
from Driftkings.common import getStatisticColor

LOG=logging.getLogger('Driftkings.PlayerPanelPro')
ALIAS=BATTLE_ALIASES.PLAYERS_PANEL

class RatingViews(object):
    def __init__(self,config,stats):
        self.config,self.stats=config,stats
        self.model=Roster()
        self.active=False
        self.view=self.arena=self.panel=None
        self.callback=None
        self.lastRequest=0
        self.baseMode=4
        self.hovered=False
        self.alt=False
        self.requestedHP=None
        self.rowCache={}
        self.screenCache={}
        self.invalidationCauses={}
        self.contextCache={}
        self.visibleScreens=set(('panel','loading','tab'))
        self.metrics={'ticks':0,'ms':0.0,'max':0.0,'resolved':0,'sent':0,'since':0.0}
        self.resolvedRows=0
        self.trackedKeys=None
        self.cacheConfig=None
        self.cacheArena=None
        self.lastPayload=None
        owner=self
        class RosterView(PlayersPanelMeta):
            def _populate(self):
                super(RosterView,self)._populate()
                owner.view=self
                owner.lastPayload=None
                owner.refresh()
                LOG.info('Roster v2 Flash ready')
            def reportState(self,state):
                LOG.info('Roster v2: %s',state)
            def hoverPanel(self,expanded):
                owner.hover(expanded)
            def reportWidths(self,left,right):
                owner.model.widths=(left,right)
            def reportScreens(self,panel,loading,tab):
                owner.visibleScreens=set(name for name,visible in (('panel',panel),('loading',loading),('tab',tab)) if visible)
                owner.refresh()
            def reportPerformance(self,message):
                if settings_service.getComponentDict(owner.config)[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False): LOG.info('Performance Flash: %s',message)
            def _dispose(self):
                if owner.view is self: owner.view=None
                super(RosterView,self)._dispose()
        self.screenClass=RosterView

    def getBattleViews(self):
        return ((ALIAS,self.screenClass,self.config),)

    def start(self):
        if self.active: return
        self.active=True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, PLAYER_PANEL_PRO)
        self.subscriptions=((battleEvents.started,self.refresh),(battleEvents.loaded,self.refresh),
            (battleEvents.ended,self.end),(battleEvents.health,self.health),
            (battleEvents.appeared,self.appeared),(battleEvents.visibility,self.visibility),
            (battleEvents.killed,self.killed),(battleEvents.key,self.key))
        for signal,callback in self.subscriptions: signal.connect(callback)
        battleEvents.acquire(self)
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED,self.component,scope=EVENT_BUS_SCOPE.GLOBAL)
        for method in ('as_setVehiclesDataS','as_addVehiclesInfoS','as_updateVehiclesInfoS','as_updateVehicleStatusS'):
            override(BattleStatisticDataControllerMeta,method,self.captureOrder)
        override(PlayersPanel,'updateVehicleHealth',self.nativeHealth)
        override(PlayersPanel,'as_setPanelModeS',self.nativeMode)
        override(PlayersPanel,'setInitialMode',self.initialMode)
        override(PlayersPanel,'tryToSetPanelModeByMouse',self.nativeHover)
        from Driftkings.views.battle.panel_gameface import GamefaceLoading
        self.gameface=GamefaceLoading(self)
        self.refresh()

    def stop(self):
        if not self.active: return
        self.active=False
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        for signal,callback in self.subscriptions: signal.disconnect(callback)
        battleEvents.release(self)
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_REGISTERED,self.component,scope=EVENT_BUS_SCOPE.GLOBAL)
        self.end()
        # Native page owns component destruction; end() clears its presentation.

    def onSettingsChanged(self, component, settings):
        if affects(settings, PLAYER_PANEL_PRO.COLOR_SCALE):
            self.stats._appliedCache.clear()
        if affects(settings, GLOBAL.ENABLED, PLAYER_PANEL_PRO.STATS_ENABLED, PLAYER_PANEL_PRO.COLOR_SCALE):
            self.lastRequest = 0
        self.refresh()

    def end(self,*args):
        if self.callback is not None: BigWorld.cancelCallback(self.callback)
        self.callback=None
        if self.view and self.view._isDAAPIInited(): self.view.as_setRosterS({'enabled':False,'rows':[]})
        self.view=self.arena=self.panel=None
        self.model.reset()
        self.rowCache.clear()
        self.screenCache.clear()
        self.invalidationCauses.clear()
        self.contextCache.clear()
        self.visibleScreens=set(('panel','loading','tab'))
        self.cacheConfig=self.cacheArena=self.lastPayload=None
        if hasattr(self,'gameface'): self.gameface.clear()
        self.lastRequest=0
        self.hovered=self.alt=False
        self.stats.reset()

    def component(self,event):
        if getattr(event,'alias','')!=ALIAS: self.refresh()

    def refresh(self,*args):
        if self.active and self.callback is None:
            self.callback=BigWorld.callback(0,self.tick)

    def captureOrder(self,original,controller,data,*args,**kwargs):
        result=original(controller,data,*args,**kwargs)
        if self.active and isinstance(data,dict):
            arena=getattr(BigWorld.player(),'arena',None)
            if arena is not self.arena:
                self.model.reset(); self.arena=arena
            for side in ('left','right'):
                ids=data.get(side+'ItemsIDs')
                if ids is not None: self.model.set_order(side,ids)
            for entries in data.values():
                if not isinstance(entries,(tuple,list)): continue
                for entry in entries:
                    if isinstance(entry,dict) and 'vehicleID' in entry:
                        self.model.metadata.setdefault(entry['vehicleID'],{}).update(entry)
            self.refresh()
        return result

    def health(self,ident,hp,*args):
        if self.active:
            self.model.set_health(ident,hp)
            self.refresh()

    def appeared(self,ident):
        entity=BigWorld.entity(ident)
        if entity is not None:
            self.model.set_health(ident,getattr(entity,'health',None),getattr(entity,'maxHealth',None))
            self.model.visibility(ident,True)
        self.refresh()

    def visibility(self,ident,visible):
        self.model.visibility(ident,visible)
        if visible: self.appeared(ident)
        else: self.refresh()

    def killed(self,ident,*args):
        self.model.set_health(ident,0)
        self.model.spotted[ident]='dead'
        self.refresh()

    def nativeHealth(self,original,panel,ident,hp,maximum):
        result=original(panel,ident,hp,maximum)
        if self.active: self.model.set_health(ident,hp,maximum); self.refresh()
        return result

    def nativeMode(self,original,panel,mode):
        result=original(panel,mode)
        if self.active:
            self.panel=weakref.ref(panel)
            self.model.mode=profile_for_mode(mode)
            if not self.hovered and not self.alt: self.baseMode=mode
            self.refresh()
        return result

    def initialMode(self,original,panel):
        # ArenaPeriodController calls this on entry to BATTLE, after countdown.
        # Before that the client uses setLargeMode; later manual modes stay free.
        result=original(panel)
        settings=settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PLAYERS_PANEL]
        selected=settings.get('startMode')
        if self.active and settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] and settings[GLOBAL.ENABLED] and selected in PROFILES:
            panel._mode=PROFILES.index(selected)
            panel.as_setPanelModeS(panel._mode)
        return result

    def nativeHover(self,original,panel,mode):
        if not self.active or not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] or not settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PLAYERS_PANEL][GLOBAL.ENABLED]:
            return original(panel,mode)
        # Our Flash hit region owns expansion; native rollover would race it.

    def setMode(self,mode):
        panel=self.panel() if self.panel is not None else None
        if panel is not None: panel.as_setPanelModeS(mode)

    def hover(self,expanded):
        if not self.active or self.alt or self.hovered==bool(expanded): return
        self.hovered=bool(expanded)
        self.setMode(4 if self.hovered else self.baseMode)

    def key(self,event):
        down=event.isKeyDown()
        self.model.key(event.key,down)
        selected=settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PLAYERS_PANEL].get('altMode')
        if event.key in (56,184) and selected in PROFILES:
            self.alt=any(code in self.model.keys for code in (56,184))
            self.setMode(PROFILES.index(selected) if self.alt else self.baseMode)
        self.refresh()

    def resolvedScreen(self,ident,key,settings,values,data,side,hotkeys):
        cache=self.screenCache.setdefault(ident,{})
        cached=cache.get(key)
        if cached is None:
            changed=['cold']
        else:
            changed=[name for name,value in cached['values'].items() if values.get(name)!=value]
            if cached['hotkeys']!=hotkeys: changed.append('hotkeys')
            if cached['side']!=side: changed.append('side')
            if not changed: return cached['result'],False
        dependencies=set()
        result=self.model.screen(settings,values,data,side,dependencies)
        cache[key]={'values':deepcopy(dict((name,values.get(name)) for name in dependencies)),
                    'hotkeys':hotkeys,'side':side,'result':result}
        if data[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False):
            for name in changed:
                self.invalidationCauses[name]=self.invalidationCauses.get(name,0)+1
        return result,True

    def rows(self,mode=None,screens=None):
        player=BigWorld.player()
        arena=getattr(player,'arena',None)
        if arena is None: return []
        data=settings_service.getComponentDict(self.config)
        if not data[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False): self.invalidationCauses.clear()
        if arena is not self.cacheArena or data!=self.cacheConfig:
            changes = SettingsChanges(data, changed_paths(self.cacheConfig or {}, data))
            new_arena = arena is not self.cacheArena
            context_changed = new_arena or affects(changes, PLAYER_PANEL_PRO.STATS_ENABLED,
                PLAYER_PANEL_PRO.RATING, PLAYER_PANEL_PRO.COLOR_SCALE, PLAYER_PANEL_PRO.SPOTTED_ENABLED,
                (PLAYER_PANEL_PRO.PERFORMANCE, 'minBattlesToShow'))
            shared_fields = affects(changes, PLAYER_PANEL_PRO.TEMPLATES, PLAYER_PANEL_PRO.HP_ENABLED,
                PLAYER_PANEL_PRO.HP_VISIBILITY, PLAYER_PANEL_PRO.HP_KEY)
            if new_arena:
                self.screenCache.clear()
            # Keep rendered screens whose formats and macro inputs did not change.
            for cache in self.screenCache.values():
                for key in list(cache):
                    section = (PLAYER_PANEL_PRO.PROFILES, key[1]) if isinstance(key, tuple) else key
                    if context_changed or shared_fields or affects(changes, section):
                        del cache[key]
            if context_changed:
                self.contextCache.clear()
            if context_changed or shared_fields or affects(changes, PLAYER_PANEL_PRO.PROFILES,
                                                           PLAYER_PANEL_PRO.LOADING, PLAYER_PANEL_PRO.TAB):
                self.rowCache.clear()
            self.cacheArena=arena
            self.cacheConfig=deepcopy(data)
            tracked=set((56,184)) if data[PLAYER_PANEL_PRO.PLAYERS_PANEL].get('altMode') else set()
            if data.get(PLAYER_PANEL_PRO.HP_VISIBILITY)=='hold':
                tracked.update(code for group in data[PLAYER_PANEL_PRO.HP_KEY] for code in group)
            dynamic=[False]
            def track(value):
                if isinstance(value,dict):
                    if 'hotKeyCode' in value:
                        try:
                            code=int(value['hotKeyCode']); tracked.add(code)
                            if code in (56,184): tracked.update((56,184))
                        except (ValueError,TypeError): dynamic[0]=True
                    for item in value.values(): track(item)
                elif isinstance(value,list):
                    for item in value: track(item)
            track(data)
            self.trackedKeys=None if dynamic[0] else tracked
        self.model.sync(arena.vehicles)
        contexts={}
        ownID=getattr(player,'playerVehicleID',0)
        self.resolvedRows=0
        shared=(ownID,getattr(player,'team',0),self.model.mode,self.model.widths,getattr(arena,'guiType',None),
                any(m.get('hasSelectedBadge') for m in self.model.metadata.values()))
        for ident,vehicle in arena.vehicles.items():
            stats=self.stats.getPlayersInfo(vehicle.get('accountDBID',0))
            vtype=vehicle.get('vehicleType'); descriptor=getattr(vtype,'type',None)
            typeStamp=tuple(getattr(vtype,key,None) for key in ('level','maxHealth'))+tuple(getattr(descriptor,key,None) for key in ('compactDescr','userString','shortUserString','name'))
            stamp=(shared,vehicle,stats,self.model.health.get(ident),self.model.spotted.get(ident),
                   self.model.metadata.get(ident),getattr(arena,'statistics',{}).get(ident,{}).get('frags',0),typeStamp)
            cached=self.contextCache.get(ident)
            if cached is None or cached[0]!=stamp:
                values=self.model.values(ident,vehicle,stats,ownID,getattr(player,'team',0),data,getStatisticColor)
                values['frags']=stamp[6]; values['region']='EU'; values['battletype-key']=getattr(arena,'guiType',None)
                # Vehicle descriptors are engine objects; snapshot the mutable
                # dictionaries, but keep the immutable descriptor by reference.
                snapshot=(shared,dict(vehicle),deepcopy(stats),deepcopy(stamp[3]),stamp[4],deepcopy(stamp[5]),stamp[6],typeStamp)
                self.contextCache[ident]=(snapshot,values)
            contexts[ident]=dict(self.contextCache[ident][1])
        own=dict(('my-'+key,value) for key,value in contexts.get(ownID,{}).items())
        rows=[]
        hotkeys=tuple(frozenset(keys if self.trackedKeys is None else keys.intersection(self.trackedKeys)) for keys in (self.model.keys,self.model.toggled))
        profiles=data[PLAYER_PANEL_PRO.PROFILES] if mode is None else {mode:data[PLAYER_PANEL_PRO.PROFILES][mode]}
        active=frozenset(('panel','loading','tab') if screens is None else screens)
        for cache in (self.rowCache,self.contextCache,self.screenCache):
            for ident in set(cache)-set(contexts): cache.pop(ident,None)
        for ident,values in contexts.items():
            vehicle=arena.vehicles[ident]
            values.update(own)
            side='Left' if values['ally'] else 'Right'
            ids=self.model.order[side.lower()]
            initial=self.model.initial[side.lower()]
            index=ids.index(ident) if ident in ids else -1
            fixedIndex=initial.index(ident) if ident in initial else -1
            meta=self.model.metadata.get(ident,{})
            aliases=[values['name'],values['nick']]
            aliases.extend(meta[key] for key in ('playerName','playerFullName','playerFakeName') if meta.get(key))
            stamp=(values,index,fixedIndex,hotkeys,mode,aliases,active)
            cached=self.rowCache.get(ident)
            if cached is not None and cached[0]==stamp:
                rows.append(cached[1])
                continue
            row={'id':ident,'ally':bool(values['ally']),'name':values['name'],'nick':values['nick'],
                 'index':index,'fixedIndex':fixedIndex,'panels':{},'aliases':aliases}
            # Each screen tracks the macro values actually read, including
            # conditions, nested names and fallbacks. Hidden screens stay lazy.
            rebuilt=False
            if 'panel' in active:
                for name,profile in profiles.items():
                    key=('panel',name)
                    result,changed=self.resolvedScreen(ident,key,profile,values,data,side,hotkeys)
                    row['panels'][name]=result
                    rebuilt=rebuilt or changed
            for screen in ('loading','tab'):
                if screen in active:
                    result,changed=self.resolvedScreen(ident,screen,data[screen],values,data,side,hotkeys)
                    row[screen]=result
                    rebuilt=rebuilt or changed
                else: row[screen]={'enabled':False}
            if rebuilt: self.resolvedRows+=1
            self.rowCache[ident]=(deepcopy(stamp),row)
            rows.append(row)
        return rows

    def tick(self):
        self.callback=None
        started=time.time()
        if not self.active: return
        player=BigWorld.player()
        arena=getattr(player,'arena',None)
        if arena is None: return
        if arena is not self.arena:
            self.model.reset(); self.arena=arena; self.lastRequest=0
        try:
            if not self.lastRequest or BigWorld.time()-self.lastRequest>15:
                self.stats.loadStats(); self.lastRequest=BigWorld.time()
            enabled=settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]
            screens=set(self.visibleScreens)
            if hasattr(self,'gameface'): screens.update(self.gameface.active_screens())
            rows=self.rows(self.model.mode,screens) if enabled else []
            if hasattr(self,'gameface'): self.gameface.update(settings_service.getComponentDict(self.config)[GLOBAL.ENABLED],rows)
            if self.view and self.view._isDAAPIInited():
                payload={'enabled':enabled,
                    'rows':rows,'panel':deepcopy(settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PLAYERS_PANEL]), 'mode':self.model.mode,
                    'loadingClock':{'enabled':settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.LOADING][GLOBAL.ENABLED],
                                    'format':settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.LOADING].get('clockFormat','')},
                    'diagnostics':settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False),
                    'hoverMode':profile_for_mode(self.baseMode),'hovered':self.hovered,
                    'hoverAreaWidth':settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PROFILES][profile_for_mode(self.baseMode)].get('expandAreaWidth',230),
                    'time':{'H':time.strftime('%H'),'i':time.strftime('%M'),'s':time.strftime('%S')}}
                if payload!=self.lastPayload:
                    wire=dict(payload)
                    if self.lastPayload is not None:
                        previous=dict((row['id'],row) for row in self.lastPayload['rows'])
                        wire.pop('rows')
                        wire['rowUpdates']=[row for row in rows if previous.get(row['id'])!=row]
                        wire['rowOrder']=[row['id'] for row in rows]
                    self.view.as_setRosterS(wire)
                    if payload['diagnostics']: self.metrics['sent']+=len(wire.get('rowUpdates',rows))
                    # Cached rows are replaced, never edited; only settings need
                    # a snapshot to detect edits made by the configuration UI.
                    self.lastPayload=payload
        except Exception:
            LOG.exception('Roster update failed')
        if settings_service.getComponentDict(self.config)[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False):
            elapsed=(time.time()-started)*1000; metrics=self.metrics
            metrics['ticks']+=1; metrics['ms']+=elapsed; metrics['max']=max(metrics['max'],elapsed)
            metrics['resolved']+=self.resolvedRows
            if started-metrics['since']>=5:
                causes=u','.join(u'%s:%d'%item for item in sorted(self.invalidationCauses.items(),key=lambda item:(-item[1],item[0]))[:8]) or '-'
                LOG.info('Performance Python: ticks=%d avg=%.2fms max=%.2fms resolved=%d sent=%d invalidations=%s',
                         metrics['ticks'],metrics['ms']/metrics['ticks'],metrics['max'],metrics['resolved'],metrics['sent'],causes)
                self.invalidationCauses.clear()
                self.metrics={'ticks':0,'ms':0.0,'max':0.0,'resolved':0,'sent':0,'since':started}
        self.callback=BigWorld.callback(0.25,self.tick)
