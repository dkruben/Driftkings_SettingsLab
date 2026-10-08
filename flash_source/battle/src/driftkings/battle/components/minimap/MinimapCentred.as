package driftkings.battle.components.minimap
{
    import driftkings.battle.base.BattleDisplayable;
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import flash.geom.Rectangle;
    import flash.geom.Point;
    import flash.text.TextFieldAutoSize;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ViewRangeCirclesMinimapEntry;
    import flash.display.DisplayObjectContainer;
    import flash.events.TimerEvent;
    import flash.geom.ColorTransform;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    import flash.utils.Timer;
    import net.wg.gui.battle.views.minimap.BaseMinimap;
    import net.wg.infrastructure.events.LifeCycleEvent;
    import net.wg.gui.battle.views.minimap.components.entries.vehicle.VehicleMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ArcadeCameraMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ViewPointMinimapEntry;
    import net.wg.gui.battle.views.minimap.components.entries.personal.StrategicCameraMinimapEntry;

    public class MinimapCentred extends BattleDisplayable
    {
        private var minimap:BaseMinimap;
        private var options:Object;
        private var vehicles:Object = {};
        private var labels:Dictionary = new Dictionary(true);
        private var geometry:Dictionary = new Dictionary(true);
        private var rangeData:Object;
        private var rangeVersion:int = 0;
        private var sizeLabel:TextField;
        private var visibleLabels:Array;
        private var zoomed:Boolean = false;
        private var original:Object;
        private var originalAlpha:Number = 1;
        private var lastWidth:Number = 0;
        private var lastHeight:Number = 0;
        private var styles:Dictionary = new Dictionary(true);
        private var timer:Timer = new Timer(250);
        private var remaining:int;
        private var artilleryAim:ArtilleryAim = new ArtilleryAim();

        override protected function onPopulate():void
        {
            super.onPopulate();
            minimap = battlePage.hasOwnProperty("minimap") ? battlePage["minimap"] as BaseMinimap : null;
            if (minimap) originalAlpha = minimap.alpha;
            lastWidth = App.appWidth;
            lastHeight = App.appHeight;
            timer.addEventListener(TimerEvent.TIMER, refresh);
        }

        public function as_minimapPresentation(value:Object):void
        {
            options = value;
            artilleryAim.configure(options && options.enabled ? options.artilleryAim : null);
            if (!minimap) return;
            restoreStyles();
            if (!options || !options.enabled)
            {
                timer.stop();
                updateZoom(false);
                minimap.alpha = originalAlpha;
                return;
            }
            updateZoom(Boolean(options.alternative && options.zoom));
            var background:DisplayObject = minimap.hasOwnProperty("background") ? minimap["background"] as DisplayObject : null;
            if (background) { remember(background); background.alpha = Number(options.backgroundAlpha) / 100; }
            updateMapSize();
            minimap.alpha = Number(options.alternative ? options.alternativeAlpha : options.normalAlpha) / 100;
            timer.start();
            refresh();
        }

        private function updateZoom(active:Boolean):void
        {
            if (!minimap) return;
            if (active)
            {
                if (!zoomed)
                    original = {x:minimap.x, y:minimap.y, sx:minimap.scaleX, sy:minimap.scaleY,
                                size:minimap.currentSizeIndex, index:battlePage.getChildIndex(minimap)};
                zoomed = true;
                minimap.setAllowedSizeIndex(Number(options.sizeIndex));
                var scale:Number = Math.max(1, Math.min(3, Number(options.scale)));
                // Keep the full map on screen even on smaller resolutions.
                scale = Math.min(scale, App.appWidth / Math.max(1, minimap.currentWidth),
                                App.appHeight / Math.max(1, minimap.currentHeight));
                minimap.scaleX = minimap.scaleY = scale;
                if (options.center)
                {
                    minimap.x = (App.appWidth - minimap.currentWidth * scale) * .5;
                    minimap.y = (App.appHeight - minimap.currentHeight * scale) * .5;
                }
                else
                {
                    minimap.x = App.appWidth - minimap.currentWidth * scale;
                    minimap.y = App.appHeight - minimap.currentHeight * scale;
                }
                battlePage.setChildIndex(minimap, battlePage.numChildren - 1);
            }
            else if (zoomed)
            {
                zoomed = false;
                minimap.scaleX = original.sx;
                minimap.scaleY = original.sy;
                minimap.setAllowedSizeIndex(original.size);
                minimap.x = original.x;
                minimap.y = original.y;
                battlePage.setChildIndex(minimap, Math.min(original.index, battlePage.numChildren - 1));
                original = null;
            }
            minimap.dispatchEvent(new LifeCycleEvent(LifeCycleEvent.ON_GRAPHICS_RECTANGLES_UPDATE));
        }

        override protected function onResized():void
        {
            if (zoomed)
            {
                original.x += App.appWidth - lastWidth;
                original.y += App.appHeight - lastHeight;
                updateZoom(true);
            }
            lastWidth = App.appWidth;
            lastHeight = App.appHeight;
        }

        private function remember(target:DisplayObject):Object
        {
            if (!styles[target])
                styles[target] = {alpha:target.alpha, color:target.transform.colorTransform,
                    sx:target.scaleX, sy:target.scaleY, size:target is TextField ? TextField(target).defaultTextFormat.size : null};
            return styles[target];
        }

        public function as_minimapVehicle(value:Object):void
        {
            vehicles[value.id] = value;
        }

        public function as_minimapRanges(value:Object):void
        {
            rangeData = value;
            ++rangeVersion;
        }

        private function updateMapSize():void
        {
            if (!options.mapSize.enabled) return;
            sizeLabel = new TextField();
            sizeLabel.mouseEnabled = sizeLabel.selectable = false;
            sizeLabel.autoSize = TextFieldAutoSize.LEFT;
            sizeLabel.defaultTextFormat = new TextFormat("$FieldFont", options.mapSize.fontSize,
                VehicleLabel.parseColor(options.mapSize.color));
            sizeLabel.text = String(options.mapSize.format).split("{{width}}").join(options.mapWidth).split("{{height}}").join(options.mapHeight);
            minimap.addChild(sizeLabel);
            positionMapSize();
        }

        private function positionMapSize():void
        {
            if (!sizeLabel || !minimap) return;
            // The native minimap has an inset origin that changes with +/- size.
            var origin:Point = minimap.currentTopLeftPoint;
            var bounds:Rectangle = minimap.getMinimapRectBySizeIndex(minimap.currentSizeIndex);
            if (!origin || bounds.width <= 0 || bounds.height <= 0) return;
            sizeLabel.x = origin.x + Math.max(0, Math.min(bounds.width - sizeLabel.width, Number(options.mapSize.x)));
            sizeLabel.y = origin.y + Math.max(0, Math.min(bounds.height - sizeLabel.height, Number(options.mapSize.y)));
        }

        private function iconStyle(target:DisplayObject, scale:Number, alpha:Number):void
        {
            if (!target) return;
            var saved:Object = remember(target);
            saved.scaleChanged = true;
            target.scaleX = saved.sx * scale; target.scaleY = saved.sy * scale;
            target.alpha = alpha / 100;
        }

        private function line(target:DisplayObject, color:String):void
        {
            if (!target || !options.lines.customStyle) return;
            remember(target);
            if (options.lines.geometry && target.parent)
            {
                var shape:Sprite = geometry[target] as Sprite;
                if (!shape)
                {
                    shape = new Sprite(); shape.mouseEnabled = shape.mouseChildren = false;
                    shape.name = "dkMinimapGeometry";
                    geometry[target] = shape;
                    target.parent.addChild(shape);
                    MapGeometry.stroke(shape.graphics, options.lines, VehicleLabel.parseColor(color), options.lines.alpha);
                    MapGeometry.line(shape.graphics, options.lines.length, options.lines);
                }
                shape.transform.matrix = target.transform.matrix;
                shape.visible = target.visible;
                target.alpha = 0;
            }
            else
            {
                var transform:ColorTransform = new ColorTransform();
                transform.color = VehicleLabel.parseColor(color);
                target.transform.colorTransform = transform;
                target.alpha = Number(options.lines.alpha) / 100;
            }
        }

        private function circles(target:ViewRangeCirclesMinimapEntry):void
        {
            if (!rangeData || Number(rangeData.width) <= 0) return;
            var custom:Boolean = options.extraCircles.length > 0;
            for each (var style:Object in options.circles)
                if (style.thickness != 1 || style.dash > 0) custom = true;
            if (!custom) return;
            var stored:Object = geometry[target];
            if (!stored)
            {
                var shape:Sprite = new Sprite(); shape.mouseEnabled = shape.mouseChildren = false;
                target.addChild(shape);
                stored = geometry[target] = {shape:shape, version:-1};
            }
            shape = stored.shape;
            for (var i:int = 0; i < target.numChildren; ++i)
            {
                var child:DisplayObject = target.getChildAt(i);
                if (child != shape) { remember(child); child.alpha = 0; }
            }
            if (stored.version == rangeVersion) return;
            stored.version = rangeVersion;
            shape.graphics.clear();
            var coefficient:Number = 210 / Number(rangeData.width);
            for (var key:String in rangeData.circles)
            {
                var data:Object = rangeData.circles[key];
                MapGeometry.stroke(shape.graphics, options.circles[key], uint(data.color), data.alpha);
                MapGeometry.circle(shape.graphics, Number(data.radius) * coefficient, options.circles[key]);
            }
            for each (data in options.extraCircles)
            {
                if (data.vehicleClass != "all" && data.vehicleClass != (rangeData.vehicleClass ? rangeData.vehicleClass : options.vehicleClass)) continue;
                MapGeometry.stroke(shape.graphics, data, VehicleLabel.parseColor(data.color), data.alpha);
                MapGeometry.circle(shape.graphics, Number(data.radius) * coefficient, data);
            }
        }

        private function scan(target:DisplayObject):void
        {
            if (--remaining <= 0 || target is VehicleLabel || target == sizeLabel || target.name == "dkMinimapGeometry") return;
            if (target is ViewRangeCirclesMinimapEntry)
            { circles(target as ViewRangeCirclesMinimapEntry); return; }
            if (target is StrategicCameraMinimapEntry)
            {
                artilleryAim.attach(target as DisplayObjectContainer);
                return;
            }
            var entry:VehicleMinimapEntry = target as VehicleMinimapEntry;
            if (entry)
            {
                var data:Object = vehicles[entry.vehicleID];
                if (data)
                {
                    var owned:VehicleLabel = labels[entry] as VehicleLabel;
                    if (!owned) { owned = new VehicleLabel(); labels[entry] = owned; entry.addChild(owned); }
                    var native:TextField = entry.vehicleNameTextFieldAlt.visible ? entry.vehicleNameTextFieldAlt : entry.vehicleNameTextFieldClassic;
                    remember(entry.vehicleNameTextFieldAlt); remember(entry.vehicleNameTextFieldClassic);
                    entry.vehicleNameTextFieldAlt.alpha = entry.vehicleNameTextFieldClassic.alpha = 0;
                    owned.update(data, options, native);
                    if (entry.visible && owned.caption.visible) visibleLabels.push(owned);
                }
                for each (var name:String in ["enemyRedAnimation", "enemyPurpleAnimation", "deadAnimation",
                    "deadPermanentAnimation", "squadmanYellowAnimation", "squadmanGoldAnimation",
                    "teamKillerBlueAnimation", "allyGreenAnimation"])
                    iconStyle(entry[name] as DisplayObject, options.icons.scale,
                        options.showVehicleTypes ? Number(options.icons.alpha) * (data ? Number(data.alpha)/100 : 1) : 0);
                return;
            }
            var camera:ArcadeCameraMinimapEntry = target as ArcadeCameraMinimapEntry;
            if (camera) { line(camera.directionLinePlaceholder, options.lines.directionColor); return; }
            var point:ViewPointMinimapEntry = target as ViewPointMinimapEntry;
            if (point)
            {
                iconStyle(point.arrowPlaceholder, options.icons.selfScale, options.icons.selfAlpha);
                if (point.arrowPlaceholder)
                {
                    var arrowColor:ColorTransform = new ColorTransform();
                    arrowColor.color = VehicleLabel.parseColor(options.icons.selfColor);
                    point.arrowPlaceholder.transform.colorTransform = arrowColor;
                }
                line(point.sectorLeft, options.lines.sectorColor);
                line(point.sectorRight, options.lines.sectorColor);
                return;
            }
            var container:DisplayObjectContainer = target as DisplayObjectContainer;
            if (container)
                for (var i:int = 0; i < container.numChildren && remaining > 0; ++i) scan(container.getChildAt(i));
        }

        private function refresh(event:TimerEvent = null):void
        {
            if (!minimap || !minimap.visible || !options || !options.enabled) return;
            for (var key:Object in labels)
                if (!DisplayObject(key).stage) { VehicleLabel(labels[key]).dispose(); delete labels[key]; }
            for (key in geometry)
                if (!DisplayObject(key).stage)
                {
                    var old:Sprite = geometry[key] is Sprite ? geometry[key] as Sprite : geometry[key].shape;
                    if (old.parent) old.parent.removeChild(old);
                    delete geometry[key];
                }
            positionMapSize();
            visibleLabels = [];
            remaining = 4000;
            scan(minimap);
            if (options.labels.avoidOverlap && !options.alternative)
            {
                visibleLabels.sortOn("priority", Array.DESCENDING | Array.NUMERIC);
                var occupied:Array = [];
                for each (var label:VehicleLabel in visibleLabels)
                {
                    var bounds:Rectangle = label.caption.getBounds(minimap);
                    var collision:Boolean = intersects(bounds, occupied);
                    if (collision) { label.compact(true); bounds = label.caption.getBounds(minimap); }
                    if (collision && intersects(bounds, occupied)) label.caption.visible = false;
                    else occupied.push(bounds);
                }
            }
        }

        private function intersects(bounds:Rectangle, occupied:Array):Boolean
        {
            for each (var rect:Rectangle in occupied) if (bounds.intersects(rect)) return true;
            return false;
        }

        private function restoreStyles():void
        {
            if (sizeLabel && sizeLabel.parent) sizeLabel.parent.removeChild(sizeLabel);
            sizeLabel = null;
            for each (var label:VehicleLabel in labels) label.dispose();
            labels = new Dictionary(true);
            for each (var node:Object in geometry)
            {
                var shape:Sprite = node is Sprite ? node as Sprite : node.shape;
                if (shape.parent) shape.parent.removeChild(shape);
            }
            geometry = new Dictionary(true);
            for (var key:Object in styles)
            {
                var target:DisplayObject = key as DisplayObject;
                var saved:Object = styles[key];
                target.alpha = saved.alpha;
                if (saved.scaleChanged) { target.scaleX = saved.sx; target.scaleY = saved.sy; }
                target.transform.colorTransform = saved.color;
                if (target is TextField && saved.size != null)
                {
                    var field:TextField = target as TextField;
                    var format:TextFormat = field.getTextFormat();
                    format.size = saved.size;
                    field.setTextFormat(format);
                    field.defaultTextFormat = format;
                }
            }
            styles = new Dictionary(true);
        }

        override protected function onDispose():void
        {
            artilleryAim.dispose();
            timer.stop();
            timer.removeEventListener(TimerEvent.TIMER, refresh);
            restoreStyles();
            updateZoom(false);
            if (minimap) minimap.alpha = originalAlpha;
            minimap = null;
            options = null;
            vehicles = {}; rangeData = null; visibleLabels = null;
            super.onDispose();
        }
    }
}
