package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.text.TextField;
    import flash.utils.getQualifiedClassName;

    // Native views the ratings draw on: players panel, TAB, loading screens and their clock.
    public class viewbindings
    {
        public var list:Array=[];
        private var ignored:DisplayObject;

        public function viewbindings(ignored:DisplayObject)
        {
            this.ignored=ignored;
        }
        public static function showing(node:DisplayObject):Boolean
        {
            if (!node || !node.stage) return false;
            while (node) { if (!node.visible) return false; node=node.parent; }
            return true;
        }
        // Keep views that are still on stage, then look for new ones.
        public function refresh(container:DisplayObjectContainer):void
        {
            list=list.filter(function(binding:Object,index:int,all:Array):Boolean { return Boolean(binding.owner.stage); });
            if (container) scan(container);
        }
        public function clear():void
        {
            list=[];
        }
        private function scan(node:DisplayObject,screen:String=""):void
        {
            if (node===ignored || !node.visible) return;
            var owner:Object=node, kind:String=getQualifiedClassName(node).toLowerCase();
            // Frontline tables are library symbols (FrontlineFullStatsTableUI in the TAB,
            // FrontlineStatsTableUI on loading), not the AS3 class names: match their lists.
            if (/frontline/.test(kind) && "team1PlayerList" in owner && "team2PlayerList" in owner)
            { bind(owner,/fullstats/.test(kind) ? "frontlineTab" : "frontlineLoading"); return; }
            if (/battleloading/.test(kind)) screen=/tip/.test(kind) ? "tips" : "loading";
            if ((screen=="loading" || screen=="tips") && "helpTip" in owner && owner.helpTip is TextField)
                bind(owner,"clock");
            if ("listLeft" in owner && "listRight" in owner)
            { bind(owner,"panel"); return; }
            if ("playerNameCollection" in owner && "vehicleNameCollection" in owner)
            { bind(owner,"tab"); return; }
            if ("textFieldsAlly" in owner && "vehicleFieldsAlly" in owner)
            { bind(owner,screen=="tips" ? "tips" : "loading"); return; }
            var container:DisplayObjectContainer=node as DisplayObjectContainer;
            if (container) for (var i:int=0;i<container.numChildren;++i) scan(container.getChildAt(i),screen);
        }
        private function bind(owner:Object,screen:String):void
        {
            for each (var current:Object in list) if (current.owner===owner && current.screen===screen) return;
            list.push({owner:owner,screen:screen});
        }
    }
}
