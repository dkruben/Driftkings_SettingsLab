# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, TEAM_PANELS
from driftkings.settings.service import affects, changed_paths, settings_service, SettingsChanges

"""Native roster bridge; all three screens share identity, health and macros."""
from copy import deepcopy
import time
import weakref

import BigWorld
from gui.Scaleform.daapi.view.battle.classic.players_panel import PlayersPanel
from gui.Scaleform.daapi.view.meta.BattleStatisticDataControllerMeta import BattleStatisticDataControllerMeta
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from realm import CURRENT_REALM

from driftkings._constants import BATTLE_ALIASES
from driftkings.common.utils.colorratting import getStatisticColor
from driftkings.core.battle_capabilities import battle_capabilities
from driftkings.core.battle_events import battleEvents
from driftkings.core.hooks import override
from driftkings.core.mode_adapters import adapter_for
from driftkings.core.panel_model import Roster
from driftkings.flash.battle.meta.players_panel import PlayersPanelMeta
from driftkings.logger import get_logger
from driftkings.settings.settings_data import profile_for_mode, PROFILES

LOG=get_logger('Driftkings.PlayerPanelPro')
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
        # Settings only change through apply/reload, which always signal: a version
        # counter replaces a deep comparison of the whole configuration every tick.
        self.configVersion=0
        self.cacheVersion=-1
        self.panelSnapshot=None
        self.lastPayload=None
        self.failures={}
        # Per-arena mode support; None leaves every screen to the native client.
        self.adapter=self.adapterArena=None
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
                if settings_service.getComponentDict(owner.config)[TEAM_PANELS.PERFORMANCE].get('diagnostics',False): LOG.info('Performance Flash: %s',message)
            def _dispose(self):
                if owner.view is self: owner.view=None
                super(RosterView,self)._dispose()
        self.screenClass=RosterView

    def getBattleViews(self):
        return ((ALIAS,self.screenClass,self.config),)

    def start(self):
        if self.active: return
        self.active=True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, TEAM_PANELS)
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
        from driftkings.gameface.battle.panel_gameface import GamefaceLoading
        if not hasattr(self, 'gameface'):
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
        if hasattr(self, 'gameface'):
            self.gameface.dispose()
        # Native page owns component destruction; end() clears its presentation.

    def onSettingsChanged(self, component, settings):
        self.configVersion+=1
        self.panelSnapshot=None
        if affects(settings, TEAM_PANELS.COLOR_SCALE):
            self.stats._appliedCache.clear()
        if affects(settings, GLOBAL.ENABLED, TEAM_PANELS.STATS_ENABLED, TEAM_PANELS.COLOR_SCALE):
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
        self.adapter=self.adapterArena=None
        self.cacheVersion=-1
        if hasattr(self,'gameface'): self.gameface.clear()
        self.lastRequest=0
        self.hovered=self.alt=False
        self.stats.reset()

    def component(self,event):
        if getattr(event,'alias','')!=ALIAS: self.refresh()

    def refresh(self,*args):
        if self.active and self.callback is None:
            self.callback=BigWorld.callback(0,self.tick)

    def modeAdapter(self):
        arena=getattr(BigWorld.player(),'arena',None)
        if arena is None: return None
        if arena is not self.adapterArena:
            self.adapterArena=arena
            mode=battle_capabilities.current_mode()
            self.adapter=adapter_for(mode)
            LOG.info('Team panels: mode=%s supported=%s',mode,
                     ','.join(screen for screen in ('loading','panel','tab') if self.supports(screen)) or 'none')
        return self.adapter

    def supports(self,screen):
        adapter=self.modeAdapter()
        return adapter is not None and bool(getattr(adapter,screen))

    def classicModes(self):
        # Halloween's HWPlayersPanel inherits the classic hooks without having its modes.
        adapter=self.modeAdapter()
        return adapter is not None and bool(adapter.panel_modes)

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
        if self.active and self.classicModes():
            self.panel=weakref.ref(panel)
            self.model.mode=profile_for_mode(mode)
            if not self.hovered and not self.alt: self.baseMode=mode
            self.refresh()
        return result

    def initialMode(self,original,panel):
        # ArenaPeriodController calls this on entry to BATTLE, after countdown.
        # Before that the client uses setLargeMode; later manual modes stay free.
        result=original(panel)
        settings=settings_service.getComponentDict(self.config)[TEAM_PANELS.PLAYERS_PANEL]
        selected=settings.get('startMode')
        if (self.active and self.classicModes() and settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]
                and settings[GLOBAL.ENABLED] and selected in PROFILES):
            panel._mode=PROFILES.index(selected)
            panel.as_setPanelModeS(panel._mode)
        return result

    def nativeHover(self,original,panel,mode):
        settings = settings_service.getComponentDict(self.config)
        if (not self.active or not self.classicModes() or not settings[GLOBAL.ENABLED]
                or not settings[TEAM_PANELS.PLAYERS_PANEL][GLOBAL.ENABLED]):
            return original(panel,mode)
        # Our Flash hit region owns expansion; native rollover would race it.

    def setMode(self,mode):
        panel=self.panel() if self.panel is not None else None
        if panel is not None: panel.as_setPanelModeS(mode)

    def restingMode(self):
        return 4 if self.hovered else self.baseMode

    def hover(self,expanded):
        expanded=bool(expanded)
        if not self.active or self.hovered==expanded: return
        # Track the pointer during ALT too, so releasing ALT restores the right mode.
        self.hovered=expanded
        if not self.alt: self.setMode(self.restingMode())

    def setAlt(self):
        selected=settings_service.getComponentDict(self.config)[TEAM_PANELS.PLAYERS_PANEL].get('altMode')
        if selected not in PROFILES: return
        alt=any(code in self.model.keys for code in (56,184))
        if alt!=self.alt:
            self.alt=alt
            self.setMode(PROFILES.index(selected) if alt else self.restingMode())

    def key(self,event):
        down=event.isKeyDown()
        self.model.key(event.key,down)
        if event.key in (56,184): self.setAlt()
        self.refresh()

    def releaseKeys(self):
        # Key-up is lost while the settings window blocks input or the client
        # loses focus (Alt+Tab); never leave ALT modes or HP holds stuck on.
        isKeyDown=getattr(BigWorld,'isKeyDown',None)
        if isKeyDown is None or not self.model.keys: return
        released=[code for code in self.model.keys if not isKeyDown(code)]
        for code in released: self.model.key(code,False)
        if released and set(released)&set((56,184)): self.setAlt()

    def logFailure(self,where):
        # Called from an except block; one traceback per part every 10 s.
        now=time.time()
        if now-self.failures.get(where,0)>=10:
            self.failures[where]=now
            LOG.exception('%s update failed',where)

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
        if data[TEAM_PANELS.PERFORMANCE].get('diagnostics',False):
            for name in changed:
                self.invalidationCauses[name]=self.invalidationCauses.get(name,0)+1
        return result,True

    def rows(self,mode=None,screens=None):
        player=BigWorld.player()
        arena=getattr(player,'arena',None)
        if arena is None: return []
        data=settings_service.getComponentDict(self.config)
        translations = {'Destroyed': self.config.i18n['UI_panel_destroyed']}
        if self.model.translations != translations:
            self.model.translations = translations
            self.rowCache.clear()
            self.screenCache.clear()
        if not data[TEAM_PANELS.PERFORMANCE].get('diagnostics',False): self.invalidationCauses.clear()
        if arena is not self.cacheArena or self.cacheVersion!=self.configVersion:
            changes = SettingsChanges(data, changed_paths(self.cacheConfig or {}, data))
            new_arena = arena is not self.cacheArena
            context_changed = new_arena or affects(changes, TEAM_PANELS.STATS_ENABLED,
                TEAM_PANELS.RATING, TEAM_PANELS.COLOR_SCALE, TEAM_PANELS.SPOTTED_ENABLED,
                (TEAM_PANELS.PERFORMANCE, 'minBattlesToShow'))
            shared_fields = affects(changes, TEAM_PANELS.TEMPLATES, TEAM_PANELS.HP_ENABLED,
                TEAM_PANELS.HP_VISIBILITY, TEAM_PANELS.HP_KEY)
            if new_arena:
                self.screenCache.clear()
                self.model.restricted=battle_capabilities.is_event_mode()
            # Keep rendered screens whose formats and macro inputs did not change.
            for cache in self.screenCache.values():
                for key in list(cache):
                    section = (TEAM_PANELS.PROFILES, key[1]) if isinstance(key, tuple) else key
                    if context_changed or shared_fields or affects(changes, section):
                        del cache[key]
            if context_changed:
                self.contextCache.clear()
            if context_changed or shared_fields or affects(changes, TEAM_PANELS.PROFILES,
                                                           TEAM_PANELS.LOADING, TEAM_PANELS.TAB):
                self.rowCache.clear()
            self.cacheArena=arena
            self.cacheConfig=deepcopy(data)
            self.cacheVersion=self.configVersion
            tracked=set((56,184)) if data[TEAM_PANELS.PLAYERS_PANEL].get('altMode') else set()
            if data.get(TEAM_PANELS.HP_VISIBILITY)=='hold':
                tracked.update(code for group in data[TEAM_PANELS.HP_KEY] for code in group)
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
        colorblind=bool(getattr(self.view,'isColorBlind',lambda: False)())
        shared=(colorblind,ownID,getattr(player,'team',0),self.model.mode,self.model.widths,getattr(arena,'guiType',None),CURRENT_REALM,self.model.restricted,
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
                values['colorblind']=colorblind
                values['frags']=stamp[6]; values['region']=CURRENT_REALM; values['battletype-key']=getattr(arena,'guiType',None)
                # Vehicle descriptors are engine objects; snapshot the mutable
                # dictionaries, but keep the immutable descriptor by reference.
                snapshot=(shared,dict(vehicle),deepcopy(stats),deepcopy(stamp[3]),stamp[4],deepcopy(stamp[5]),stamp[6],typeStamp)
                self.contextCache[ident]=(snapshot,values)
            contexts[ident]=dict(self.contextCache[ident][1])
        own=dict(('my-'+key,value) for key,value in contexts.get(ownID,{}).items())
        rows=[]
        hotkeys=tuple(frozenset(keys if self.trackedKeys is None else keys.intersection(self.trackedKeys)) for keys in (self.model.keys,self.model.toggled))
        profiles=data[TEAM_PANELS.PROFILES] if mode is None else {mode:data[TEAM_PANELS.PROFILES][mode]}
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
        self.modeAdapter()
        # Statistics, Gameface and Flash fail independently: a broken TAB must not
        # freeze the side panel, and a persistent error must not flood the log.
        try:
            self.releaseKeys()
            if not self.lastRequest or BigWorld.time()-self.lastRequest>15:
                self.lastRequest=BigWorld.time(); self.stats.loadStats()
        except Exception:
            self.logFailure('Statistics')
        try:
            data=settings_service.getComponentDict(self.config)
            enabled=data[GLOBAL.ENABLED]
            screens=set(self.visibleScreens)
            if hasattr(self,'gameface'): screens.update(self.gameface.active_screens())
            # Unsupported screens are neither resolved nor sent; the native view stays intact.
            screens=set(screen for screen in screens if self.supports(screen))
            rows=self.rows(self.model.mode,screens) if enabled and screens else []
        except Exception:
            self.logFailure('Roster'); rows=None
        if rows is not None and hasattr(self,'gameface'):
            try:
                self.gameface.update(enabled and self.supports('tab'),rows)
            except Exception:
                self.logFailure('Gameface roster')
        try:
            if rows is not None and self.view and self.view._isDAAPIInited():
                # The Flash panel settings are copied once per configuration version.
                if self.panelSnapshot is None:
                    self.panelSnapshot=deepcopy(data[TEAM_PANELS.PLAYERS_PANEL])
                payload={'enabled':enabled and self.supports('panel'),
                    'rows':rows,'panel':self.panelSnapshot, 'mode':self.model.mode,
                    'loadingClock':{'enabled':data[TEAM_PANELS.LOADING][GLOBAL.ENABLED],
                                    'format':data[TEAM_PANELS.LOADING].get('clockFormat','')},
                    'diagnostics':data[TEAM_PANELS.PERFORMANCE].get('diagnostics',False),
                    'hoverMode':profile_for_mode(self.baseMode),'hovered':self.hovered,
                    'hoverAreaWidth':data[TEAM_PANELS.PROFILES][profile_for_mode(self.baseMode)].get('expandAreaWidth',230),
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
            self.logFailure('Flash roster')
        if settings_service.getComponentDict(self.config)[TEAM_PANELS.PERFORMANCE].get('diagnostics',False):
            elapsed=(time.time()-started)*1000; metrics=self.metrics
            metrics['ticks']+=1; metrics['ms']+=elapsed; metrics['max']=max(metrics['max'],elapsed)
            metrics['resolved']+=self.resolvedRows
            if started-metrics['since']>=5:
                causes=u','.join(u'%s:%d'%item for item in sorted(self.invalidationCauses.items(),key=lambda item:(-item[1],item[0]))[:8]) or '-'
                LOG.info('Performance Python: ticks=%d avg=%.2fms max=%.2fms resolved=%d sent=%d invalidations=%s',
                         metrics['ticks'],metrics['ms']/metrics['ticks'],metrics['max'],metrics['resolved'],metrics['sent'],causes)
                self.invalidationCauses.clear()
                self.metrics={'ticks':0,'ms':0.0,'max':0.0,'resolved':0,'sent':0,'since':started}
        # refresh() can run synchronously during stats/native updates. Preserve
        # its queued tick instead of creating a second recurring chain.
        if self.active and self.callback is None:
            self.callback=BigWorld.callback(0.25,self.tick)
