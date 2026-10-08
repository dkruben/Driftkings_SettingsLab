package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.geom.Point;
    import flash.text.TextField;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;
    import flash.events.Event;
    public class PanelRenderer
    {
        private var common:NativeState;
        public var widths:Array = [0,0];
        private var measuredWidths:Array = [0,0];
        public var matched:int=0;
        public var drawn:int=0;
        public var reused:int=0;
        private var itemCache:Dictionary=new Dictionary(true);
        private var rowCache:Dictionary=new Dictionary(true);
        public function PanelRenderer(s:NativeState) { common=s; }
        public function begin():void
        {
            matched=drawn=reused=0; measuredWidths=[0,0];
            for each (var record:PanelRow in rowCache) record.used=false;
        }
        public function end():void
        {
            for (var item:Object in rowCache) if (!rowCache[item].used)
            { rowCache[item].dispose(); delete rowCache[item]; }
        }
        public function restore():void { begin(); end(); widths=[0,0]; itemCache=new Dictionary(true); }
        private function nativeY(item:Object):Number
        { return rowCache[item] ? Number(rowCache[item].state.base(item,"y")) : Number(item.y); }
        private function childrenChanged(event:Event):void
        { if (itemCache[event.currentTarget]) itemCache[event.currentTarget].time=-1000; }
        private function collect(node:DisplayObjectContainer,items:Array):void
        {
            if (!node) return;
            for (var i:int=0;i<node.numChildren;++i)
            {
                var child:DisplayObject=node.getChildAt(i);
                if ("playerNameFullTF" in child && "vehicleTF" in child && "holderItemID" in child)
                    items.push(child);
                else if (child is DisplayObjectContainer) collect(child as DisplayObjectContainer,items);
            }
        }
        public function draw(panel:Object, payload:Object):void
        {
            if (!payload.panel.enabled) return;
            var mode:String=payload.mode;
            var rows:Array=payload.rows;
            var globals:Object=payload.panel;
            var now:int=getTimer();
            var layout:String=[globals.iconAlpha,globals.alpha,globals.removeSelectedBackground,
                globals.removeHealthPoints,App.appWidth,App.appHeight].join(":");
            for each (var left:Boolean in [true,false])
            {
                var list:Object=left ? panel.listLeft : panel.listRight;
                if (!list) continue;
                // Holders and the ID lookup are protected client members.
                var cached:Object=itemCache[list], stale:Boolean=!cached || cached.mode!==mode || getTimer()-cached.time>=1000;
                if (!stale) for each (var existing:DisplayObject in cached.items)
                    if (!existing.stage || !(list as DisplayObjectContainer).contains(existing)) { stale=true; break; }
                if (stale)
                {
                    if (!cached)
                    {
                        (list as DisplayObjectContainer).addEventListener(Event.ADDED,childrenChanged,false,0,true);
                        (list as DisplayObjectContainer).addEventListener(Event.REMOVED,childrenChanged,false,0,true);
                    }
                    var discovered:Array=[]; collect(list as DisplayObjectContainer,discovered);
                    itemCache[list]=cached={items:discovered,mode:mode,time:getTimer()};
                }
                var items:Array=cached.items;
                items.sort(function(a:Object,b:Object):Number { return nativeY(a)-nativeY(b); });
                var entries:Array=[], maxNick:Number=0;
                for (var itemIndex:int=0;itemIndex<items.length;++itemIndex)
                {
                    var item:Object=items[itemIndex];
                    var record:PanelRow=rowCache[item];
                    if (!record) rowCache[item]=record=new PanelRow(now,itemIndex+(left ? 0 : 5));
                    var state:NativeState=record.state;
                    var row:Object=RowLookup.find(rows,itemIndex,left,state.originalText(item.playerNameFullTF));
                    if (!row) continue;
                    var cfg:Object=row.panels[mode];
                    if (!item || !cfg || !cfg.enabled) continue;
                    ++matched;
                    var side:String=left ? "Left" : "Right";
                    if (record.update(item,row,mode,layout+":"+side,now)) record.prepare(item,cfg,side);
                    maxNick=Math.max(maxNick,record.nickWidth);
                    entries.push({item:item,row:row,cfg:cfg,record:record});
                }
                if (mode=="none" && entries.length && "inviteReceivedIndicator" in list)
                {
                    var invite:Object=list.inviteReceivedIndicator;
                    var inviteCfg:Object=entries[0].cfg;
                    if (invite)
                    {
                        common.setValue(invite,"alpha",NativeState.number(inviteCfg.inviteIndicatorAlpha,100)/100);
                        common.setValue(invite,"x",common.base(invite,"x")+(left ? 1 : -1)*NativeState.number(inviteCfg.inviteIndicatorX));
                        common.setValue(invite,"y",common.base(invite,"y")+NativeState.number(inviteCfg.inviteIndicatorY));
                    }
                }
                for each (var entry:Object in entries)
                {
                    item=entry.item; cfg=entry.cfg; row=entry.row;
                    record=entry.record; state=record.state;
                    var extra:ExtraFields=record.extra;
                    // A wider nickname changes the shared column, so layout
                    // must also refresh otherwise unchanged members of this team.
                    if (!record.dirty && record.maxNick!==maxNick) record.prepare(item,cfg,side);
                    record.maxNick=maxNick;
                    if (!record.dirty)
                    {
                        ++reused;
                        measuredWidths[left ? 0 : 1]=Math.max(measuredWidths[left ? 0 : 1],record.panelWidth);
                        continue;
                    }
                    ++drawn; record.panelWidth=0;
                    if (mode=="none")
                    {
                        var hidden:Object=cfg.extraFields[left ? "leftPanel" : "rightPanel"];
                        var index:int=cfg.fixedPosition ? row.fixedIndex : row.index;
                        if (index<0) index=entries.indexOf(entry);
                        var hiddenX:Number=NativeState.number(hidden.x), hiddenY:Number=NativeState.number(hidden.y,65);
                        if (cfg.layout=="horizontal") hiddenX += index*NativeState.number(hidden.width,350);
                        else hiddenY += index*NativeState.number(hidden.height,25);
                        extra.draw(panel as DisplayObjectContainer,"none:"+row.id,cfg.fields,left,0,hiddenY,left ? hiddenX : App.appWidth-hiddenX);
                        record.commit(item);
                        continue;
                    }
                    state.setValue(item.playerNameCutTF,"visible",false);
                    var fields:Object={frags:item.fragsTF,badge:item.badge,nick:item.playerNameFullTF,vehicle:item.vehicleTF,prestige:item.prestigeLevel};
                    for (var name:String in fields) state.setValue(fields[name],"visible",cfg.standardFields.indexOf(name)>=0);
                    var last:Number=left ? 276 : -276;
                    for (var i:int=cfg.standardFields.length-1;i>=0;--i)
                    {
                        name=cfg.standardFields[i];
                        var field:DisplayObject=fields[name] as DisplayObject;
                        if (!field) continue;
                        var w:Number=state.base(field,"width");
                        if (name=="nick") w=Math.min(NativeState.number(cfg.nickMaxWidth,158),Math.max(NativeState.number(cfg.nickMinWidth,46),maxNick));
                        else if (name=="frags" || name=="badge" || name=="vehicle") w=NativeState.number(cfg[name+"Width"],w);
                        if (left) last-=w-1;
                        state.setValue(field,"width",Math.max(0,w));
                        state.setValue(field,"x",last+(left ? 1 : -1)*NativeState.number(cfg[name+"OffsetX"+side]));
                        if (!left) last+=w-1;
                    }
                    var squadSpace:Number=cfg.removeSquadIcon ? 0 : 25;
                    state.setValue(item,"x",-last+(left ? squadSpace : -squadSpace));
                    state.setValue(item.hit,"x",-item.x);
                    state.setValue(item.hit,"width",Math.max(0,339+(left ? item.x : -item.x)));
                    measuredWidths[left ? 0 : 1]=Math.max(measuredWidths[left ? 0 : 1],339+(left ? item.x : -item.x));
                    record.panelWidth=339+(left ? item.x : -item.x);
                    if ("dynamicSquad" in item && item.dynamicSquad)
                    {
                        state.setValue(item.dynamicSquad,"x",-item.x);
                        if ("squadIcon" in item.dynamicSquad) state.setValue(item.dynamicSquad.squadIcon,"alpha",cfg.removeSquadIcon ? 0 : NativeState.number(cfg.squadIconAlpha,100)/100);
                    }
                    state.setValue(item.vehicleIcon,"x",(left ? 291 : -293)+(left ? 1 : -1)*NativeState.number(cfg["vehicleIconOffsetX"+side]));
                    if (!left) state.setValue(item.vehicleIcon,"scaleX",1);
                    state.setValue(item.vehicleIcon,"alpha",NativeState.number(globals.iconAlpha,100)/100);
                    state.setValue(item.vehicleLevel,"x",(left ? 310 : -311)+(left ? 1 : -1)*NativeState.number(cfg["vehicleLevelOffsetX"+side])-item.vehicleLevel.width/2);
                    state.setValue(item.vehicleLevel,"alpha",NativeState.number(cfg.vehicleLevelAlpha,100)/100);
                    state.setValue(item.badge,"alpha",NativeState.number(cfg.badgeAlpha,100)/100);
                    state.setValue(item.spottedIndicator,"alpha",cfg.removeSpottedIndicator ? 0 : NativeState.number(cfg.spottedIndicatorAlpha,100)/100);
                    state.setValue(item.spottedIndicator,"x",state.base(item.spottedIndicator,"x")+NativeState.number(cfg.spottedIndicatorOffsetX));
                    state.setValue(item.spottedIndicator,"y",state.base(item.spottedIndicator,"y")+NativeState.number(cfg.spottedIndicatorOffsetY));
                    for each (name in ["bg","deadBg","normAltBg","deadAltBg"])
                        if (name in item) state.setValue(item[name],"alpha",NativeState.number(globals.alpha,80)/100);
                    if (globals.removeSelectedBackground) state.setValue(item.selfBg,"alpha",0);
                    if (globals.removeHealthPoints && "hpBarPlayersPanelListItem" in item) state.setValue(item.hpBarPlayersPanelListItem,"visible",false);
                    if (cfg.fixedPosition && row.fixedIndex>=0 && row.index>=0)
                        state.setValue(item,"y",state.base(item,"y")+(int(row.fixedIndex)-int(row.index))*25);
                    // XVM's mirrored icons bind to the registration point on
                    // both sides. width is an atlas bound, not an extra offset.
                    var edge:Number=item.vehicleIcon.x;
                    extra.draw(item as DisplayObjectContainer,"panel:"+row.id,cfg.fields,left,edge,0,-item.x);
                    record.commit(item);
                }
                // Hidden/unbound sides have no measurement. Keep their last
                // valid width so opening TAB does not invalidate every macro.
                // A measured "none" profile still publishes its real zero.
                if (entries.length) widths[left ? 0 : 1]=measuredWidths[left ? 0 : 1];
            }
            for each (var button:String in ["panelSwitch"])
                if (button in panel && globals.removePanelsModeSwitcher) common.setValue(panel[button],"visible",false);
        }
    }
}
