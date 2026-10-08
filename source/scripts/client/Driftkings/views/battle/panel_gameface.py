# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, PLAYER_PANEL_PRO
from Driftkings.settings.service import settings_service
"""Gameface roster bridge for the current random TAB and White Tiger loading."""
import json
import logging
import math
import weakref
from Driftkings.core.hooks import override

class GamefaceLoading(object):
    def __init__(self,owner):
        self.owner=owner
        self.children=weakref.WeakKeyDictionary()
        from frameworks.wulf import ViewModel, ViewSettings
        from frameworks.wulf.gui_constants import ShowingStatus
        from gui.impl.pub import ViewImpl
        from Driftkings.ui.gameface import attach_assets, resource_id
        bridge=self
        class RatingModel(ViewModel):
            def __init__(self):
                super(RatingModel,self).__init__(properties=3,commands=1)
            def _initialize(self):
                super(RatingModel,self)._initialize()
                self._addStringProperty('payload','{}')
                self.onPerformance = self._addCommand('onPerformance')
                root='coui://gui/gameface/mods/Driftkings/RatingPlayers/'
                attach_assets(self,'DriftkingsRatingPlayers',styles=[root+'ratings.css'],scripts=[root+'ratings.js'])
        class RatingView(ViewImpl):
            def _getEvents(self):
                return tuple(super(RatingView,self)._getEvents()) + (
                    (self.getViewModel().onPerformance, bridge.reportPerformance),)
        def install(viewClass,event,screen):
            @override(viewClass,event)
            def loading(original,view,*args,**kwargs):
                result=original(view,*args,**kwargs)
                if bridge.owner.active:
                    try:
                        resource=resource_id('mods/Driftkings/RatingPlayers/model')
                        child=RatingView(ViewSettings(resource,model=RatingModel()))
                        view.setChildView(resource,child)
                        bridge.children[view]={'child':child,'screen':screen,'data':None,
                            'visible':view.showingStatus in (ShowingStatus.SHOWING,ShowingStatus.SHOWN)}
                        bridge.owner.refresh()
                        logging.getLogger('Driftkings.PlayerPanelPro').info('Gameface roster attached: %s',screen)
                    except Exception:
                        logging.getLogger('Driftkings.PlayerPanelPro').exception('Gameface roster bridge failed')
                return result
            @override(viewClass,'_finalize')
            def finalize(original,view,*args,**kwargs):
                bridge.children.pop(view,None)
                return original(view,*args,**kwargs)
            def visibility(event,visible):
                @override(viewClass,event)
                def changed(original,view,*args,**kwargs):
                    result=original(view,*args,**kwargs)
                    if view in bridge.children:
                        bridge.children[view]['visible']=visible
                        bridge.owner.refresh()
                    return result
            visibility('_onShown',True)
            visibility('_onHidden',False)
        try:
            from gui.impl.battle.battle_page.tab_view import TabView
            install(TabView,'_onLoaded','tab')
        except ImportError:
            pass
        try:
            from white_tiger.gui.impl.battle.white_tiger_battle_loading import WhiteTigerBattleLoadingView
            install(WhiteTigerBattleLoadingView,'_onLoading','loading')
        except ImportError:
            pass

    def active_screens(self):
        return set(record['screen'] for record in self.children.values() if record.get('visible',True))

    def reportPerformance(self, args):
        if (not self.owner.active or not settings_service.getComponentDict(self.owner.config).get(GLOBAL.ENABLED, True)
                or not settings_service.getComponentDict(self.owner.config)[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics', False)
                or not isinstance(args, dict)):
            return
        try:
            calls, total, maximum, elapsed, rows = [float(args[key]) for key in
                ('calls', 'totalMs', 'maxMs', 'windowMs', 'rows')]
            if any(math.isnan(value) or math.isinf(value) or value < 0
                   for value in (calls, total, maximum, elapsed, rows)):
                return
            if calls < 1 or calls != int(calls) or rows != int(rows) or maximum > total:
                return
            reason = args.get('reason')
            if reason not in ('interval', 'hidden', 'dispose'):
                return
            drawn, reused, searches = [float(args.get(key, 0)) for key in
                ('rowsDrawn', 'rowsReused', 'searches')]
            if any(math.isnan(value) or math.isinf(value) or value < 0 or value != int(value)
                   for value in (drawn, reused, searches)):
                return
        except (KeyError, TypeError, ValueError, OverflowError):
            return
        logging.getLogger('Driftkings.PlayerPanelPro').info(
            'Performance Gameface: screen=tab calls=%d avg=%.2fms max=%.2fms window=%.0fms rows=%d reason=%s rowsDrawn=%d rowsReused=%d searches=%d',
            int(calls), total / calls, maximum, elapsed, int(rows), reason, int(drawn), int(reused), int(searches))

    def update(self,enabled,rows):
        if not self.children: return
        for view,record in list(self.children.items()):
            screen=record['screen']
            if not record.get('visible',True) or not enabled:
                data={'enabled':False,'screen':screen,'rows':[]}
            elif screen=='tab':
                result=[{'id':row['id'],'ally':row['ally'],'aliases':row['aliases'],'cfg':row['tab']} for row in rows]
                players=view.viewModel.playerList
                order={'left':[p.getVehicleId() for p in players.getAllies()],
                       'right':[p.getVehicleId() for p in players.getEnemies()]}
                data={'enabled':enabled,'screen':screen,'rows':result,'order':order,
                      'diagnostics':settings_service.getComponentDict(self.owner.config)[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False)}
            else:
                result=[]
                for row in rows:
                    side='Left' if row['ally'] else 'Right'
                    cfg=row['loading']
                    result.append({'ally':row['ally'],'loadingEnabled':cfg['enabled'],
                        'loadingNick':cfg.get('format'+side+'Nick'), 'loadingVehicle':cfg.get('format'+side+'Vehicle')})
                data={'enabled':enabled,'screen':screen,'rows':result}
            # Resolved row configs are immutable snapshots. Compare before
            # serializing: most battle ticks have no TAB/loading changes.
            if data!=record.get('data'):
                payload=json.dumps(data)
                with record['child'].getViewModel().transaction() as model: model._setString(0,payload)
                record['data']=data

    def clear(self):
        self.update(False,[])
        self.children.clear()
