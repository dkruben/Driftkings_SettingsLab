package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.text.TextField;
    public class tablerenderer
    {
        private var state:nativestate;
        private var extra:extrafields;
        public var matched:int=0;
        public function tablerenderer(s:nativestate,e:extrafields) { state=s; extra=e; }
        private function at(owner:Object,key:String,index:int):Object
        { return key in owner && owner[key] && index>=0 && index<owner[key].length ? owner[key][index] : null; }
        public function drawFrontline(owner:Object,payload:Object,screen:String):void
        {
            // Lists recycle renderers while scrolling and filtering by sector. Resolve
            // their current DAAPI identity every draw, never their visible row index.
            var ids:Object={}, accounts:Object={};
            for each (var row:Object in payload.rows)
            {
                ids[row.id]=row;
                if (row.accountDBID>0)
                {
                    var account:String=String(row.accountDBID);
                    accounts[account]=accounts.hasOwnProperty(account) ? null : row;
                }
            }
            frontlineList(owner.team1PlayerList as DisplayObjectContainer,ids,accounts,screen);
            frontlineList(owner.team2PlayerList as DisplayObjectContainer,ids,accounts,screen);
        }
        private function frontlineList(list:DisplayObjectContainer,ids:Object,accounts:Object,screen:String):void
        {
            if (!list) return;
            for (var i:int=0;i<list.numChildren;++i)
            {
                var child:DisplayObject=list.getChildAt(i), renderer:Object=child;
                if (!child.visible) continue;
                if ("getData" in renderer && renderer.getData is Function &&
                    (screen=="tab" ? "playerName" in renderer && "vehicleName" in renderer : "textField" in renderer && "vehicleField" in renderer))
                {
                    var data:Object=renderer.getData();
                    if (!data) continue;
                    var row:Object=ids[data.vehicleID];
                    if (!row && data.accountDBID>0) row=accounts[String(data.accountDBID)];
                    if (!row || data.accountDBID>0 && row.accountDBID!=data.accountDBID) continue;
                    var cfg:Object=row[screen];
                    if (!cfg || !cfg.enabled) continue;
                    var nick:TextField=(screen=="tab" ? renderer.playerName : renderer.textField) as TextField;
                    var vehicle:TextField=(screen=="tab" ? renderer.vehicleName : renderer.vehicleField) as TextField;
                    var side:String=row.ally ? "Left" : "Right";
                    frontlineText(nick,cfg["format"+side+"Nick"],cfg.nameFieldShowBorder);
                    frontlineText(vehicle,cfg["format"+side+"Vehicle"],cfg.vehicleFieldShowBorder);
                    if (screen=="tab") frontlineText(renderer.frags as TextField,cfg["format"+side+"Frags"],cfg.fragsFieldShowBorder);
                    ++matched;
                }
                else if (child is DisplayObjectContainer) frontlineList(child as DisplayObjectContainer,ids,accounts,screen);
            }
        }
        private function frontlineText(field:TextField,text:*,border:*):void
        {
            if (!field || !state.base(field,"visible") || text===null || text===undefined) return;
            // Native widths/positions leave room for ranks, lives and sector icons.
            extra.drawText(field,String(text),field.x,field.width,nativestate.flag(border));
            state.setValue(field,"visible",false);
        }
        public function draw(owner:Object,payload:Object,screen:String,left:Boolean=true):void
        {
            var tab:Boolean=screen=="tab", suffix:String=left ? "Ally" : "Enemy";
            var nicks:Object=tab ? owner.playerNameCollection : owner["textFields"+suffix];
            var vehicles:Object=tab ? owner.vehicleNameCollection : owner["vehicleFields"+suffix];
            if (!nicks || !vehicles) return;
            var count:int=tab ? ("numRows" in owner ? int(owner.numRows) : nicks.length/2) : nicks.length;
            for (var i:int=0;i<nicks.length && i<vehicles.length;++i)
            {
                if (tab) left=i<count;
                suffix=left ? "Ally" : "Enemy";
                var side:String=left ? "Left" : "Right", sign:int=left ? 1 : -1;
                var nick:TextField=nicks[i] as TextField, vehicle:TextField=vehicles[i] as TextField;
                if (!nick || !vehicle || !state.base(nick,"visible")) continue;
                var row:Object=rowlookup.find(payload.rows,tab ? i%count : i,left,nick.text);
                if (!row) continue;
                var cfg:Object=row[screen=="tips" ? "loading" : screen];
                if (!cfg || !cfg.enabled) continue;
                ++matched;
                var prestige:Number=tab && cfg.removePrestigeLevel ? 15 : 0;
                format(nick,cfg["format"+side+"Nick"],cfg,"name",side,sign,tab,0);
                format(vehicle,cfg["format"+side+"Vehicle"],cfg,"vehicle",side,sign,tab,sign*prestige);
                var frags:TextField=at(owner,"fragsCollection",i) as TextField;
                if (tab && frags) format(frags,cfg["format"+side+"Frags"],cfg,"frags",side,sign,true,0);
                var icon:Object=at(owner,tab ? "vehicleIconCollection" : "vehicleIcons"+suffix,i);
                var tier:Object=at(owner,tab ? "vehicleLevelCollection" : "vehicleLevelIcons"+suffix,i);
                var type:Object=at(owner,tab ? "vehicleTypeCollection" : "vehicleTypeIcons"+suffix,i);
                move(icon,sign*(nativestate.number(cfg["vehicleIconOffsetX"+side])-prestige));
                move(tier,sign*(nativestate.number(cfg["vehicleIconOffsetX"+side])-prestige));
                move(type,sign*(nativestate.number(cfg["vehicleIconOffsetX"+side])+prestige));
                if (icon) state.setValue(icon,"alpha",(cfg.darkenNotReadyIcon===false ? 1 : state.base(icon,"alpha"))*nativestate.number(cfg.vehicleIconAlpha,100)/100);
                if (cfg.removeVehicleLevel) state.setValue(tier,"alpha",0);
                if (cfg.removeVehicleTypeIcon) state.setValue(type,"alpha",0);
                var badge:Object=at(owner,tab ? "rankBadgesCollection" : "badges"+suffix,i);
                if (cfg.removeRankBadgeIcon) state.setValue(badge,"alpha",0);
                var elite:Object=at(owner,tab ? "prestigeLevelCollection" : "prestigeLevels"+suffix,i);
                move(elite,sign*nativestate.number(cfg["prestigeOffsetX"+side]));
                if (cfg.removePrestigeLevel) state.setValue(elite,"alpha",0);
                for each (var name:String in tab ? ["icoTesterCollection","testerBackCollection"] : ["icoTesters"+suffix,"backTesters"+suffix])
                    if (cfg.removeTesterIcon) state.setValue(at(owner,name,i),"alpha",0);
                var squad:Object=at(owner,tab ? "squadCollection" : "squads"+suffix,i);
                move(squad,sign*nativestate.number(cfg["squadIconOffsetX"+side]));
                if (cfg.removeSquadIcon) state.setValue(squad,"alpha",0);
                if (cfg.removePlayerStatusIcon) state.setValue(at(owner,"playerStatusCollection",i),"alpha",0);
                var edge:Number=icon ? Number(icon.x)+(left ? 0 : Number(icon.width)) : vehicle.x;
                extra.draw(owner as DisplayObjectContainer,screen+":"+row.id,cfg.fields,left,edge,nick.y,left ? 0 : Number(owner.width));
            }
        }
        private function move(target:Object,dx:Number):void
        { if (target) state.setValue(target,"x",state.base(target,"x")+dx); }
        private function format(field:TextField,text:*,cfg:Object,prefix:String,side:String,sign:int,absolute:Boolean,additional:Number):void
        {
            if (text===null || text===undefined) return;
            var width:Number=absolute ? nativestate.number(cfg[prefix+"FieldWidth"+side],field.width) : field.width+nativestate.number(cfg[prefix+"FieldWidthDelta"+side]);
            var shift:Number=sign*nativestate.number(cfg[prefix+"FieldOffsetX"+side])+additional;
            if (prefix=="frags") shift+=(field.width-width)/2;
            else if (prefix=="name" && sign<0 || prefix=="vehicle" && sign>0) shift+=field.width-width;
            extra.drawText(field,String(text),field.x+shift,Math.max(0,width),nativestate.flag(cfg[prefix+"FieldShowBorder"]));
            state.setValue(field,"visible",false);
        }
    }
}
