package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.events.Event;
    import flash.events.MouseEvent;
    import flash.geom.Point;
    import flash.text.TextField;
    import flash.utils.getQualifiedClassName;
    import flash.utils.getTimer;
    import net.wg.gui.battle.components.BattleUIDisplayable;
    import flash.display.Stage;
    import net.wg.data.constants.generated.LAYER_NAMES;

    public class RatingScreens extends BattleUIDisplayable
    {
        public var reportState:Function;
        public var hoverPanel:Function;
        public var reportWidths:Function;
        public var reportScreens:Function;
        public var reportPerformance:Function;
        private var payload:Object={enabled:false,rows:[]};
        private var state:NativeState=new NativeState();
        private var extra:ExtraFields=new ExtraFields();
        private var panels:PanelRenderer=new PanelRenderer(state);
        private var tables:TableRenderer=new TableRenderer(state,extra);
        private var clock:LoadingClock=new LoadingClock(extra);
        private var bindings:Array=[];
        private var mouseStage:Stage;
        private var lastScan:int=0;
        private var lastRender:int=-100;
        private var dirty:Boolean=true;
        private var lastReport:String="";
        private var lastWidths:String="";
        private var hover:Boolean=false;
        private var lastScreens:String="";
        private var profileStart:int=0,profileFrames:int=0,profileTime:int=0,profileMax:int=0,profileScans:int=0;
        private var profileSearch:int=0,profilePanel:int=0,profileTable:int=0,profileCleanup:int=0;
        private var profileDrawn:int=0,profileReused:int=0;
        public function RatingScreens()
        {
            super(); mouseEnabled=mouseChildren=false;
            addEventListener(Event.ENTER_FRAME,frame,false,0,true);
            addEventListener(Event.ADDED_TO_STAGE,attached,false,0,true);
        }
        private function attached(event:Event):void
        {
            if (mouseStage) mouseStage.removeEventListener(MouseEvent.MOUSE_MOVE,mouse);
            mouseStage=stage;
            mouseStage.addEventListener(MouseEvent.MOUSE_MOVE,mouse,false,0,true);
        }
        public function as_setRoster(value:Object):void
        {
            if (value && value.rowUpdates)
            {
                var byID:Object={}, row:Object;
                for each (row in payload.rows) byID[row.id]=row;
                for each (row in value.rowUpdates) byID[row.id]=row;
                value.rows=[];
                for each (var id:Number in value.rowOrder) if (byID[id]) value.rows.push(byID[id]);
            }
            payload=value || {enabled:false,rows:[]}; dirty=true;
        }
        private function scan(node:DisplayObject,screen:String=""):void
        {
            if (node===this || !node.visible) return;
            var owner:Object=node, kind:String=getQualifiedClassName(node).toLowerCase();
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
            for each (var current:Object in bindings) if (current.owner===owner && current.screen===screen) return;
            bindings.push({owner:owner,screen:screen});
        }
        private function showing(node:DisplayObject):Boolean
        {
            if (!node || !node.stage) return false;
            while (node) { if (!node.visible) return false; node=node.parent; }
            return true;
        }
        private function frame(event:Event):void
        {
            var now:int=getTimer();
            // Native fields may change independently (TAB, mode, resolution).
            // Poll them at 10 Hz; payload changes are drawn on the next frame.
            if (!dirty && now-lastRender<100) return;
            lastRender=now; dirty=false;
            extra.begin();
            if (!payload.enabled || !payload.rows.length) { panels.restore(); state.restore(); extra.end(); bindings=[]; return; }
            state.begin();
            panels.begin();
            var checkpoint:int;
            try
            {
                // Keep discovered views across hidden/visible transitions. Scan
                // once a second for replacement views instead of every 250 ms.
                if (!lastScan || now-lastScan>1000)
                {
                    checkpoint=getTimer();
                    bindings=bindings.filter(function(binding:Object,index:int,list:Array):Boolean { return Boolean(binding.owner.stage); });
                    var container:DisplayObjectContainer=App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS)) as DisplayObjectContainer;
                    if (container) scan(container);
                    lastScan=now;
                    ++profileScans;
                    profileSearch+=getTimer()-checkpoint;
                }
                tables.matched=0;
                var visiblePanel:Boolean=false,visibleLoading:Boolean=false,visibleTab:Boolean=false;
                for each (var binding:Object in bindings)
                {
                    if (!showing(binding.owner as DisplayObject)) continue;
                    if (binding.screen=="panel") visiblePanel=true;
                    else if (binding.screen=="tab") visibleTab=true;
                    else visibleLoading=true;
                    checkpoint=getTimer();
                    if (binding.screen=="panel")
                    { panels.draw(binding.owner,payload); profilePanel+=getTimer()-checkpoint; }
                    else
                    {
                        if (binding.screen=="clock") clock.draw(binding.owner,payload);
                        else
                        {
                            tables.draw(binding.owner,payload,binding.screen,true);
                            if (binding.screen!="tab") tables.draw(binding.owner,payload,binding.screen,false);
                        }
                        profileTable+=getTimer()-checkpoint;
                    }
                }
                var screens:String=[visiblePanel,visibleLoading,visibleTab].join(",");
                if (screens!==lastScreens && reportScreens!=null)
                { lastScreens=screens; reportScreens(visiblePanel,visibleLoading,visibleTab); }
                var widths:String=panels.widths.join(",");
                if (widths!=lastWidths && reportWidths!=null)
                { lastWidths=widths; reportWidths(panels.widths[0],panels.widths[1]); }
                var report:String="bindings="+bindings.length+"; panel rows="+panels.matched+"; table rows="+tables.matched+"; mode="+payload.mode;
                if (report!=lastReport && reportState!=null) { lastReport=report; reportState(report); }
            }
            catch(error:Error)
            {
                var failure:String=error.toString();
                if (failure!=lastReport && reportState!=null) { lastReport=failure; reportState(failure); }
            }
            checkpoint=getTimer();
            panels.end();
            state.commit();
            extra.end();
            profileCleanup+=getTimer()-checkpoint;
            profileDrawn+=panels.drawn; profileReused+=panels.reused;
            if (payload.diagnostics)
            {
                var elapsed:int=getTimer()-now;
                ++profileFrames; profileTime+=elapsed; profileMax=Math.max(profileMax,elapsed);
                if (now-profileStart>=5000 && reportPerformance!=null)
                {
                    reportPerformance("frames="+profileFrames+" avg="+(profileTime/profileFrames).toFixed(2)+"ms max="+profileMax+"ms scans="+profileScans+
                        " search="+(profileSearch/profileFrames).toFixed(2)+"ms panel="+(profilePanel/profileFrames).toFixed(2)+
                        "ms table="+(profileTable/profileFrames).toFixed(2)+"ms cleanup="+(profileCleanup/profileFrames).toFixed(2)+
                        "ms rowsDrawn="+profileDrawn+" rowsReused="+profileReused);
                    profileStart=now; profileFrames=profileTime=profileMax=profileScans=0;
                    profileSearch=profilePanel=profileTable=profileCleanup=profileDrawn=profileReused=0;
                }
            }
            else
            {
                profileStart=now; profileFrames=profileTime=profileMax=profileScans=0;
                profileSearch=profilePanel=profileTable=profileCleanup=profileDrawn=profileReused=0;
            }
        }
        private function mouse(event:MouseEvent):void
        {
            if (!payload.enabled || !payload.panel.enabled || !payload.rows.length) return;
            var requested:Boolean=false;
            if (payload.hoverMode=="large") return;
            var area:Number=NativeState.number(payload.hoverAreaWidth,230);
            for each (var binding:Object in bindings)
            {
                if (binding.screen!="panel" || !showing(binding.owner as DisplayObject)) continue;
                var panel:DisplayObject=binding.owner as DisplayObject;
                var point:Point=panel.globalToLocal(new Point(event.stageX,event.stageY));
                var height:Number="panelHeight" in binding.owner ? binding.owner.panelHeight : panel.height;
                requested=area>0 && point.y>=0 && point.y<=height &&
                    (point.x<area || point.x>App.appWidth-area);
            }
            if (requested!=hover && hoverPanel!=null) { hover=requested; hoverPanel(requested); }
        }
        override protected function onDispose():void
        {
            removeEventListener(Event.ENTER_FRAME,frame);
            removeEventListener(Event.ADDED_TO_STAGE,attached);
            if (mouseStage) mouseStage.removeEventListener(MouseEvent.MOUSE_MOVE,mouse);
            mouseStage=null;
            panels.restore(); state.restore(); extra.dispose(); bindings=[];
            super.onDispose();
        }
    }
}
