package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;
    public class panelrenderer
    {
        private var common:nativestate;
        public var widths:Array = [0,0];
        private var measuredWidths:Array = [0,0];
        public var matched:int=0;
        public var drawn:int=0;
        public var reused:int=0;
        private var items:panelitems=new panelitems();
        private var rowCache:Dictionary=new Dictionary(true);

        public function panelrenderer(s:nativestate)
        {
            common=s;
        }
        public function begin():void
        {
            matched=drawn=reused=0;
            measuredWidths=[0,0];
            for each (var record:panelrow in rowCache)
                record.used=false;
        }
        public function end():void
        {
            for (var item:Object in rowCache)
            {
                if (rowCache[item].used) continue;
                rowCache[item].dispose();
                delete rowCache[item];
            }
        }
        public function restore():void
        {
            items.reset();
            begin();
            end();
            widths=[0,0];
        }
        public function dispose():void
        {
            restore();
            common=null;
        }
        private function nativeY(item:Object):Number
        {
            return rowCache[item] ? Number(rowCache[item].state.base(item,"y")) : Number(item.y);
        }
        private function measure(left:Boolean,width:Number):void
        {
            measuredWidths[left ? 0 : 1]=Math.max(measuredWidths[left ? 0 : 1],width);
        }
        // Native row backgrounds are sized for the stock columns. Keep their
        // outer edge where the client drew it and their inner edge at the same
        // distance from the vehicle icon, so any column width stays covered.
        private function fitBackground(state:nativestate,item:Object,background:Object,left:Boolean):void
        {
            if (!background) return;
            var x:Number=Number(state.base(background,"x")), current:Number=Number(background.scaleX);
            var scale:Number=Number(state.base(background,"scaleX"));
            if (!scale || !current) return;
            // Only scaleX is overridden; derive the native width from the current one.
            var w:Number=Number(background.width)*Math.abs(scale/current);
            if (!(w>0)) return;
            // A mirrored background (negative scaleX) extends left of its x.
            var start:Number=scale<0 ? x-w : x, finish:Number=scale<0 ? x : x+w;
            var shift:Number=Number(state.base(item,"x"))-Number(item.x);
            var icon:Number=Number(item.vehicleIcon.x)-Number(state.base(item.vehicleIcon,"x"));
            if (left) { start+=shift; finish+=icon; }
            else { finish+=shift; start+=icon; }
            if (!(finish>start)) return;
            // Scale rather than width: setting width would drop the mirroring sign.
            state.setValue(background,"scaleX",scale*(finish-start)/w);
            state.setValue(background,"x",scale<0 ? finish : start);
        }
        public function draw(panel:Object, payload:Object):void
        {
            if (!payload.panel.enabled) return;
            var mode:String=payload.mode;
            var globals:Object=payload.panel;
            var now:int=getTimer();
            var layout:String=[globals.iconAlpha,globals.alpha,globals.removeSelectedBackground,
                globals.removeHealthPoints,App.appWidth,App.appHeight].join(":");
            for each (var left:Boolean in [true,false])
            {
                var list:Object=left ? panel.listLeft : panel.listRight;
                if (!list) continue;
                var side:String=left ? "Left" : "Right";
                var entries:Array=match(list as DisplayObjectContainer,payload.rows,mode,left,layout,now);
                var maxNick:Number=0;
                for each (var entry:Object in entries) maxNick=Math.max(maxNick,entry.record.nickWidth);
                if (mode=="none" && entries.length && "inviteReceivedIndicator" in list)
                    drawInvite(list.inviteReceivedIndicator,entries[0].cfg,left);
                for each (entry in entries)
                {
                    var record:panelrow=entry.record;
                    // A wider nickname changes the shared column, so layout
                    // must also refresh otherwise unchanged members of this team.
                    if (!record.dirty && record.maxNick!==maxNick) record.prepare(entry.item,entry.cfg,side);
                    record.maxNick=maxNick;
                    if (!record.dirty)
                    {
                        ++reused;
                        measure(left,record.panelWidth);
                        continue;
                    }
                    ++drawn; record.panelWidth=0;
                    if (mode=="none") drawHidden(panel as DisplayObjectContainer,entry,entries.indexOf(entry),left);
                    else drawRow(entry,globals,left,side,maxNick);
                    record.commit(entry.item);
                }
                // Hidden/unbound sides have no measurement. Keep their last
                // valid width so opening TAB does not invalidate every macro.
                // A measured "none" profile still publishes its real zero.
                if (entries.length) widths[left ? 0 : 1]=measuredWidths[left ? 0 : 1];
            }
            for each (var button:String in ["panelSwitch"])
                if (button in panel && globals.removePanelsModeSwitcher) common.setValue(panel[button],"visible",false);
        }
        // Pairs the native rows of one side with their payload rows, in native order.
        private function match(list:DisplayObjectContainer,rows:Array,mode:String,left:Boolean,layout:String,now:int):Array
        {
            // Holders and the ID lookup are protected client members.
            var found:Array=items.find(list,mode);
            found.sort(function(a:Object,b:Object):Number { return nativeY(a)-nativeY(b); });
            var side:String=left ? "Left" : "Right";
            var entries:Array=[];
            for (var itemIndex:int=0;itemIndex<found.length;++itemIndex)
            {
                var item:Object=found[itemIndex];
                var record:panelrow=rowCache[item];
                if (!record) rowCache[item]=record=new panelrow(now,itemIndex+(left ? 0 : 5));
                var row:Object=rowlookup.find(rows,itemIndex,left,record.state.originalText(item.playerNameFullTF));
                if (!row) continue;
                var cfg:Object=row.panels[mode];
                if (!item || !cfg || !cfg.enabled) continue;
                ++matched;
                if (record.update(item,row,mode,layout+":"+side,now)) record.prepare(item,cfg,side);
                entries.push({item:item,row:row,cfg:cfg,record:record});
            }
            return entries;
        }
        private function drawInvite(invite:Object,cfg:Object,left:Boolean):void
        {
            if (!invite) return;
            common.setValue(invite,"alpha",nativestate.number(cfg.inviteIndicatorAlpha,100)/100);
            common.setValue(invite,"x",common.base(invite,"x")+(left ? 1 : -1)*nativestate.number(cfg.inviteIndicatorX));
            common.setValue(invite,"y",common.base(invite,"y")+nativestate.number(cfg.inviteIndicatorY));
        }
        // The "none" panel mode shows only the extra fields, stacked from a fixed origin.
        private function drawHidden(panel:DisplayObjectContainer,entry:Object,position:int,left:Boolean):void
        {
            var cfg:Object=entry.cfg, row:Object=entry.row;
            var hidden:Object=cfg.extraFields[left ? "leftPanel" : "rightPanel"];
            var index:int=cfg.fixedPosition ? row.fixedIndex : row.index;
            if (index<0) index=position;
            var hiddenX:Number=nativestate.number(hidden.x), hiddenY:Number=nativestate.number(hidden.y,65);
            if (cfg.layout=="horizontal") hiddenX += index*nativestate.number(hidden.width,350);
            else hiddenY += index*nativestate.number(hidden.height,25);
            entry.record.extra.draw(panel,"none:"+row.id,cfg.fields,left,0,hiddenY,left ? hiddenX : App.appWidth-hiddenX);
        }
        private function drawRow(entry:Object,globals:Object,left:Boolean,side:String,maxNick:Number):void
        {
            var item:Object=entry.item, cfg:Object=entry.cfg, row:Object=entry.row;
            var record:panelrow=entry.record, state:nativestate=record.state;
            var last:Number=layoutColumns(item,cfg,state,left,side,maxNick);
            var squadSpace:Number=cfg.removeSquadIcon ? 0 : 25;
            state.setValue(item,"x",-last+(left ? squadSpace : -squadSpace));
            state.setValue(item.hit,"x",-item.x);
            state.setValue(item.hit,"width",Math.max(0,339+(left ? item.x : -item.x)));
            measure(left,339+(left ? item.x : -item.x));
            record.panelWidth=339+(left ? item.x : -item.x);
            if ("dynamicSquad" in item && item.dynamicSquad)
            {
                state.setValue(item.dynamicSquad,"x",-item.x);
                if ("squadIcon" in item.dynamicSquad) state.setValue(item.dynamicSquad.squadIcon,"alpha",cfg.removeSquadIcon ? 0 : nativestate.number(cfg.squadIconAlpha,100)/100);
            }
            styleRow(item,cfg,state,globals,left,side);
            if (cfg.fixedPosition && row.fixedIndex>=0 && row.index>=0)
                state.setValue(item,"y",state.base(item,"y")+(int(row.fixedIndex)-int(row.index))*25);
            // Mirrored icons bind to the registration point on
            // both sides. width is an atlas bound, not an extra offset.
            var edge:Number=item.vehicleIcon.x;
            record.extra.draw(item as DisplayObjectContainer,"panel:"+row.id,cfg.fields,left,edge,0,-item.x);
        }
        // Lays out the standard text columns from the outer edge inwards; returns the inner edge.
        private function layoutColumns(item:Object,cfg:Object,state:nativestate,left:Boolean,side:String,maxNick:Number):Number
        {
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
                if (name=="nick") w=Math.min(nativestate.number(cfg.nickMaxWidth,158),Math.max(nativestate.number(cfg.nickMinWidth,46),maxNick));
                else if (name=="frags" || name=="badge" || name=="vehicle") w=nativestate.number(cfg[name+"Width"],w);
                if (left) last-=w-1;
                state.setValue(field,"width",Math.max(0,w));
                state.setValue(field,"x",last+(left ? 1 : -1)*nativestate.number(cfg[name+"OffsetX"+side]));
                if (!left) last+=w-1;
            }
            return last;
        }
        // Icons, indicators and backgrounds of one row.
        private function styleRow(item:Object,cfg:Object,state:nativestate,globals:Object,left:Boolean,side:String):void
        {
            state.setValue(item.vehicleIcon,"x",(left ? 291 : -293)+(left ? 1 : -1)*nativestate.number(cfg["vehicleIconOffsetX"+side]));
            if (!left) state.setValue(item.vehicleIcon,"scaleX",1);
            state.setValue(item.vehicleIcon,"alpha",nativestate.number(globals.iconAlpha,100)/100);
            state.setValue(item.vehicleLevel,"x",(left ? 310 : -311)+(left ? 1 : -1)*nativestate.number(cfg["vehicleLevelOffsetX"+side])-item.vehicleLevel.width/2);
            state.setValue(item.vehicleLevel,"alpha",nativestate.number(cfg.vehicleLevelAlpha,100)/100);
            state.setValue(item.badge,"alpha",nativestate.number(cfg.badgeAlpha,100)/100);
            state.setValue(item.spottedIndicator,"alpha",cfg.removeSpottedIndicator ? 0 : nativestate.number(cfg.spottedIndicatorAlpha,100)/100);
            state.setValue(item.spottedIndicator,"x",state.base(item.spottedIndicator,"x")+nativestate.number(cfg.spottedIndicatorOffsetX));
            state.setValue(item.spottedIndicator,"y",state.base(item.spottedIndicator,"y")+nativestate.number(cfg.spottedIndicatorOffsetY));
            var name:String;
            for each (name in ["bg","deadBg","normAltBg","deadAltBg"])
                if (name in item) state.setValue(item[name],"alpha",nativestate.number(globals.alpha,80)/100);
            if (globals.removeSelectedBackground) state.setValue(item.selfBg,"alpha",0);
            for each (name in ["bg","deadBg","normAltBg","deadAltBg","selfBg"])
                if (name in item) fitBackground(state,item,item[name],left);
            if (globals.removeHealthPoints && "hpBarPlayersPanelListItem" in item) state.setValue(item.hpBarPlayersPanelListItem,"visible",false);
        }
    }
}
