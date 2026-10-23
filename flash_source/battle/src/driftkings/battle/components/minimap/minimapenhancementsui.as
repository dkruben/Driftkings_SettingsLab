package driftkings.battle.components.minimap
{
    import driftkings.battle.base.battledisplayable;
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.events.TimerEvent;
    import flash.geom.ColorTransform;
    import flash.utils.Timer;
    import net.wg.gui.battle.views.minimap.BaseMinimap;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ArcadeCameraMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.personal.StrategicCameraMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ViewPointMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ViewRangeCirclesMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.vehicle.VehicleMinimapEntry;

    /**
     * Minimap coordinator: receives Python data, walks the native entries every
     * 250 ms and hands each one to the part that styles it.
     */
    public class minimapenhancementsui extends battledisplayable
    {
        private var minimap:BaseMinimap;
        private var options:Object;
        private var vehicles:Object = {};
        private var originalAlpha:Number = 1;
        private var timer:Timer = new Timer(250);
        private var remaining:int;
        private var styles:nativestyles = new nativestyles();
        private var layer:geometrylayer = new geometrylayer();
        private var scale:mapscale = new mapscale();
        private var lines:minimaplines = new minimaplines(styles, layer, scale);
        private var circles:rangecircles = new rangecircles(styles, layer, scale);
        private var icons:vehicleicons = new vehicleicons(styles);
        private var labels:vehiclelabels = new vehiclelabels(styles);
        private var mapSize:mapsizelabel = new mapsizelabel();
        private var nearby:nearbyenemies = new nearbyenemies(layer, scale);
        private var zoom:minimapzoom;
        private var artilleryAim:artilleryaim = new artilleryaim();

        override protected function onPopulate():void
        {
            super.onPopulate();
            minimap = battlePage.hasOwnProperty("minimap") ? battlePage["minimap"] as BaseMinimap : null;
            if (minimap) originalAlpha = minimap.alpha;
            zoom = new minimapzoom();
            timer.addEventListener(TimerEvent.TIMER, refresh);
        }

        public function as_minimapPresentation(value:Object):void
        {
            options = value;
            artilleryAim.configure(options && options.enabled ? options.artilleryAim : null);
            if (!minimap) return;
            restore();
            if (!options || !options.enabled)
            {
                timer.stop();
                zoom.apply(minimap, battlePage, false, options);
                minimap.alpha = originalAlpha;
                return;
            }
            scale.mapWidth = Number(options.mapWidth);
            zoom.apply(minimap, battlePage, Boolean(options.alternative && options.zoom), options);
            var background:DisplayObject = minimap.hasOwnProperty("background") ? minimap["background"] as DisplayObject : null;
            if (background) { styles.remember(background); background.alpha = Number(options.backgroundAlpha) / 100; }
            mapSize.create(minimap, options);
            minimap.alpha = Number(options.alternative ? options.alternativeAlpha : options.normalAlpha) / 100;
            timer.start();
            refresh();
        }

        public function as_minimapCamera(strategic:Boolean):void
        {
            artilleryAim.setStrategic(strategic);
        }

        public function as_minimapVehicle(value:Object):void
        {
            vehicles[value.id] = value;
        }

        public function as_minimapRanges(value:Object):void
        {
            scale.setRanges(value);
        }

        override protected function onResized():void
        {
            if (zoom) zoom.resized(minimap, battlePage, options);
        }

        private function refresh(event:TimerEvent = null):void
        {
            if (!minimap || !minimap.visible || !options || !options.enabled) return;
            labels.removeDetached();
            layer.removeDetached();
            mapSize.position(minimap, options);
            labels.begin();
            icons.begin();
            nearby.begin();
            remaining = 4000;
            scan(minimap);
            icons.order();
            nearby.end(options);
            labels.resolveOverlaps(options, minimap);
        }

        private function scan(target:DisplayObject):void
        {
            if (--remaining <= 0 || target is vehiclelabel || target == mapSize.field || target.name == geometrylayer.NAME) return;
            if (target is ViewRangeCirclesMinimapEntry)
            { circles.draw(target as ViewRangeCirclesMinimapEntry, options); return; }
            if (target is StrategicCameraMinimapEntry)
            { artilleryAim.attach(target as DisplayObjectContainer); return; }
            var entry:VehicleMinimapEntry = target as VehicleMinimapEntry;
            if (entry)
            {
                var data:Object = vehicles[entry.vehicleID];
                if (data) labels.update(entry, data, options);
                icons.update(entry, data, options);
                if (data && data.group == "enemy") nearby.candidate(entry, data);
                return;
            }
            var camera:ArcadeCameraMinimapEntry = target as ArcadeCameraMinimapEntry;
            if (camera)
            {
                lines.triangle("directionPlaceholder" in camera ? camera["directionPlaceholder"] as DisplayObject : null, options);
                lines.line(camera.directionLinePlaceholder, options, options.lines.directionColor, true, Number(options.lines.directionAlpha));
                return;
            }
            var point:ViewPointMinimapEntry = target as ViewPointMinimapEntry;
            if (point) { updateViewPoint(point); return; }
            var container:DisplayObjectContainer = target as DisplayObjectContainer;
            if (container)
                for (var i:int = 0; i < container.numChildren && remaining > 0; ++i) scan(container.getChildAt(i));
        }

        private function updateViewPoint(point:ViewPointMinimapEntry):void
        {
            nearby.own(point);
            icons.style(point.arrowPlaceholder, options.icons.selfScale, options.icons.selfAlpha);
            if (point.arrowPlaceholder)
            {
                var arrowColor:ColorTransform = new ColorTransform();
                arrowColor.color = vehiclelabel.parseColor(options.icons.selfColor);
                point.arrowPlaceholder.transform.colorTransform = arrowColor;
            }
            lines.line(point.sectorLeft, options, options.lines.sectorColor);
            lines.line(point.sectorRight, options, options.lines.sectorColor);
            lines.hull(point, options);
        }

        private function restore():void
        {
            mapSize.clear();
            labels.clear();
            layer.clear();
            styles.restore();
        }

        override protected function onDispose():void
        {
            artilleryAim.dispose();
            timer.stop();
            timer.removeEventListener(TimerEvent.TIMER, refresh);
            restore();
            if (zoom) zoom.apply(minimap, battlePage, false, options);
            if (minimap) minimap.alpha = originalAlpha;
            minimap = null;
            options = null;
            vehicles = {};
            scale.ranges = null;
            super.onDispose();
        }
    }
}
