package driftkings.battle.components.ratings
{
    // Each holder owns its overrides. Reusing a row must not require touching
    // every property merely to keep the shared end-of-frame cleanup happy.
    public class PanelRow
    {
        public var state:NativeState=new NativeState();
        public var extra:ExtraFields=new ExtraFields();
        public var used:Boolean=false;
        public var dirty:Boolean=false;
        public var nickWidth:Number=0;
        public var panelWidth:Number=0;
        public var maxNick:Number=-1;
        private var row:Object;
        private var mode:String;
        private var layout:String;
        private var signature:String;
        private var components:Array;
        private var nextAudit:int;
        public function PanelRow(now:int,slot:int)
        { nextAudit=now+100+(slot%10)*100; }
        private function parts(item:Object):Array
        {
            var result:Array=[];
            for each (var name:String in ["playerNameFullTF","vehicleTF","fragsTF","vehicleIcon","playerNameCutTF",
                "hit","badge","prestigeLevel","vehicleLevel","spottedIndicator","dynamicSquad",
                "bg","deadBg","normAltBg","deadAltBg","selfBg","hpBarPlayersPanelListItem"])
                result.push(name in item ? item[name] : null);
            var squad:Object="dynamicSquad" in item ? item.dynamicSquad : null;
            result.push(squad && "squadIcon" in squad ? squad.squadIcon : null);
            return result;
        }
        private function stamp(item:Object):String
        {
            var values:Array=[item.holderItemID,item.x,item.y,item.visible];
            for each (var field:Object in [item.playerNameFullTF,item.vehicleTF,item.fragsTF])
                if (field) values.push(field.text,field.x,field.width,field.visible,field.autoSize);
            values.push(item.vehicleIcon.x,item.playerNameCutTF.visible);
            return values.join("\u001f");
        }
        public function update(item:Object,value:Object,newMode:String,key:String,now:int):Boolean
        {
            used=true;
            dirty=dirty || row!==value || mode!==newMode || layout!==key || signature!==stamp(item);
            var current:Array=parts(item);
            if (!components) dirty=true;
            else for (var i:int=0;i<current.length;++i) if (current[i]!==components[i]) dirty=true;
            // Filters and less frequent native properties are checked at 1 Hz,
            // staggered across holders to avoid a full-panel spike every second.
            if (now>=nextAudit)
            { nextAudit=now+1000; if (!dirty) dirty=state.changed() || extra.changed(); }
            row=value; mode=newMode; layout=key;
            return dirty;
        }
        public function prepare(item:Object,cfg:Object,side:String):void
        {
            dirty=true;
            state.begin(); extra.begin();
            if (mode=="none") { nickWidth=0; return; }
            state.text(item.playerNameFullTF,cfg["nickFormat"+side],cfg["nickShadow"+side]);
            state.text(item.vehicleTF,cfg["vehicleFormat"+side],cfg["vehicleShadow"+side]);
            state.text(item.fragsTF,cfg["fragsFormat"+side],cfg["fragsShadow"+side]);
            nickWidth=item.playerNameFullTF.textWidth+4;
        }
        public function commit(item:Object):void
        {
            state.commit(); extra.end();
            signature=stamp(item); components=parts(item); dirty=false;
        }
        public function dispose():void { state.restore(); extra.dispose(); }
    }
}
