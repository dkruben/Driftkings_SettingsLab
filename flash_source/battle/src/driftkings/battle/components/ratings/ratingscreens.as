package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.events.Event;
    import flash.events.MouseEvent;
    import flash.geom.Point;
    import flash.utils.getTimer;
    import net.wg.gui.battle.components.BattleUIDisplayable;
    import flash.display.Stage;
    import net.wg.data.constants.generated.LAYER_NAMES;

    public class ratingscreens extends BattleUIDisplayable
    {
        public var reportState:Function;
        public var hoverPanel:Function;
        public var reportWidths:Function;
        public var reportScreens:Function;
        public var reportPerformance:Function;
        private var payload:Object={enabled:false,rows:[]};
        private var state:nativestate=new nativestate();
        private var extra:extrafields=new extrafields();
        private var panels:panelrenderer=new panelrenderer(state);
        private var tables:tablerenderer=new tablerenderer(state,extra);
        private var clock:loadingclock=new loadingclock(extra);
        private var bindings:viewbindings;
        private var profiler:frameprofiler=new frameprofiler();
        private var mouseStage:Stage;
        private var lastScan:int=0;
        private var lastRender:int=-100;
        private var dirty:Boolean=true;
        private var lastReport:String="";
        private var lastWidths:String="";
        private var hover:Boolean=false;
        private var lastScreens:String="";
        public function ratingscreens()
        {
            super(); mouseEnabled=mouseChildren=false;
            bindings=new viewbindings(this);
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
        private function frame(event:Event):void
        {
            var now:int=getTimer();
            // Native fields may change independently (TAB, mode, resolution).
            // Poll them at 10 Hz; payload changes are drawn on the next frame.
            if (!dirty && now-lastRender<100) return;
            lastRender=now; dirty=false;
            extra.begin();
            if (!payload.enabled) { panels.restore(); state.restore(); extra.end(); bindings.clear(); return; }
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
                    bindings.refresh(App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS)) as DisplayObjectContainer);
                    lastScan=now;
                    ++profiler.scans;
                    profiler.search+=getTimer()-checkpoint;
                }
                // Visibility produces the Python rows. Discover views even when the
                // loading screen has closed and no rows are currently requested.
                reportVisibleScreens();
                if (payload.rows.length) drawViews();
                else { panels.restore(); state.restore(); }
            }
            catch(error:Error)
            {
                // Report through the Python diagnostic callback, suppressing repeats.
                var failure:String=error.toString();
                if (failure!=lastReport && reportState!=null) { lastReport=failure; reportState(failure); }
            }
            checkpoint=getTimer();
            panels.end();
            state.commit();
            extra.end();
            profiler.cleanup+=getTimer()-checkpoint;
            profiler.drawn+=panels.drawn; profiler.reused+=panels.reused;
            profiler.finish(now,Boolean(payload.diagnostics),reportPerformance);
        }
        private function reportVisibleScreens():void
        {
            var visiblePanel:Boolean=false,visibleLoading:Boolean=false,visibleTab:Boolean=false;
            for each (var binding:Object in bindings.list)
            {
                if (!viewbindings.showing(binding.owner as DisplayObject)) continue;
                if (binding.screen=="panel") visiblePanel=true;
                else if (binding.screen=="tab") visibleTab=true;
                else visibleLoading=true;
            }
            var screens:String=[visiblePanel,visibleLoading,visibleTab].join(",");
            if (screens!==lastScreens && reportScreens!=null)
            { lastScreens=screens; reportScreens(visiblePanel,visibleLoading,visibleTab); }
        }
        // Draws every visible view, then reports what changed to Python.
        private function drawViews():void
        {
            tables.matched=0;
            for each (var binding:Object in bindings.list)
            {
                if (!viewbindings.showing(binding.owner as DisplayObject)) continue;
                var checkpoint:int=getTimer();
                if (binding.screen=="panel")
                { panels.draw(binding.owner,payload); profiler.panel+=getTimer()-checkpoint; }
                else
                {
                    if (binding.screen=="clock") clock.draw(binding.owner,payload);
                    else
                    {
                        tables.draw(binding.owner,payload,binding.screen,true);
                        if (binding.screen!="tab") tables.draw(binding.owner,payload,binding.screen,false);
                    }
                    profiler.table+=getTimer()-checkpoint;
                }
            }
            var widths:String=panels.widths.join(",");
            if (widths!=lastWidths && reportWidths!=null)
            { lastWidths=widths; reportWidths(panels.widths[0],panels.widths[1]); }
            var report:String="bindings="+bindings.list.length+"; panel rows="+panels.matched+"; table rows="+tables.matched+"; mode="+payload.mode;
            if (report!=lastReport && reportState!=null) { lastReport=report; reportState(report); }
        }
        private function mouse(event:MouseEvent):void
        {
            if (!payload.enabled || !payload.panel.enabled || !payload.rows.length) return;
            var requested:Boolean=false;
            if (payload.hoverMode=="large") return;
            var area:Number=nativestate.number(payload.hoverAreaWidth,230);
            for each (var binding:Object in bindings.list)
            {
                if (binding.screen!="panel" || !viewbindings.showing(binding.owner as DisplayObject)) continue;
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
            panels.dispose();
            state.restore();
            extra.dispose();
            bindings.clear();
            super.onDispose();
        }
    }
}
