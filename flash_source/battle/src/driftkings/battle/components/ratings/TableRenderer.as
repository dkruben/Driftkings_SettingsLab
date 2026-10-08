package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.text.TextField;
    public class TableRenderer
    {
        private var state:NativeState;
        private var extra:ExtraFields;
        public var matched:int=0;
        public function TableRenderer(s:NativeState,e:ExtraFields) { state=s; extra=e; }
        private function at(owner:Object,key:String,index:int):Object
        { return key in owner && owner[key] && index>=0 && index<owner[key].length ? owner[key][index] : null; }
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
                var row:Object=RowLookup.find(payload.rows,tab ? i%count : i,left,nick.text);
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
                move(icon,sign*(NativeState.number(cfg["vehicleIconOffsetX"+side])-prestige));
                move(tier,sign*(NativeState.number(cfg["vehicleIconOffsetX"+side])-prestige));
                move(type,sign*(NativeState.number(cfg["vehicleIconOffsetX"+side])+prestige));
                if (icon) state.setValue(icon,"alpha",(cfg.darkenNotReadyIcon===false ? 1 : state.base(icon,"alpha"))*NativeState.number(cfg.vehicleIconAlpha,100)/100);
                if (cfg.removeVehicleLevel) state.setValue(tier,"alpha",0);
                if (cfg.removeVehicleTypeIcon) state.setValue(type,"alpha",0);
                var badge:Object=at(owner,tab ? "rankBadgesCollection" : "badges"+suffix,i);
                if (cfg.removeRankBadgeIcon) state.setValue(badge,"alpha",0);
                var elite:Object=at(owner,tab ? "prestigeLevelCollection" : "prestigeLevels"+suffix,i);
                move(elite,sign*NativeState.number(cfg["prestigeOffsetX"+side]));
                if (cfg.removePrestigeLevel) state.setValue(elite,"alpha",0);
                for each (var name:String in tab ? ["icoTesterCollection","testerBackCollection"] : ["icoTesters"+suffix,"backTesters"+suffix])
                    if (cfg.removeTesterIcon) state.setValue(at(owner,name,i),"alpha",0);
                var squad:Object=at(owner,tab ? "squadCollection" : "squads"+suffix,i);
                move(squad,sign*NativeState.number(cfg["squadIconOffsetX"+side]));
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
            var width:Number=absolute ? NativeState.number(cfg[prefix+"FieldWidth"+side],field.width) : field.width+NativeState.number(cfg[prefix+"FieldWidthDelta"+side]);
            var shift:Number=sign*NativeState.number(cfg[prefix+"FieldOffsetX"+side])+additional;
            if (prefix=="frags") shift+=(field.width-width)/2;
            else if (prefix=="name" && sign<0 || prefix=="vehicle" && sign>0) shift+=field.width-width;
            extra.drawText(field,String(text),field.x+shift,Math.max(0,width),NativeState.flag(cfg[prefix+"FieldShowBorder"]));
            state.setValue(field,"visible",false);
        }
    }
}
