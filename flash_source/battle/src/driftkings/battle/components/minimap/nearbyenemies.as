package driftkings.battle.components.minimap
{
    import driftkings.utils.colorutils;
    import flash.display.DisplayObject;
    import flash.display.Graphics;
    import flash.display.Sprite;
    import flash.geom.Point;
    import net.wg.gui.battle.views.minimap.components.entries.vehicle.VehicleMinimapEntry;

    /** Ring around spotted enemies within the view range, the shell range or a fixed distance. */
    public class nearbyenemies
    {
        private static const ORIGIN:Point = new Point(0, 0);
        private var layer:geometrylayer;
        private var scale:mapscale;
        // Own vehicle position, taken from the view point entry during the scan.
        private var self:DisplayObject;
        private var enemies:Array = [];

        public function nearbyenemies(layer:geometrylayer, scale:mapscale)
        {
            this.layer = layer; this.scale = scale;
        }

        public function begin():void
        {
            self = null;
            enemies = [];
        }

        public function own(point:DisplayObject):void
        {
            if (point.visible) self = point;
        }

        public function candidate(entry:VehicleMinimapEntry, data:Object):void
        {
            enemies.push({entry:entry, data:data});
        }

        // Drawn after the scan, once the own position and every enemy are known.
        public function end(options:Object):void
        {
            var nearby:Object = options.nearby;
            var limit:Number = range(nearby);
            var perMetre:Number = globalPerMetre();
            for each (var item:Object in enemies)
            {
                var data:Object = item.data, entry:VehicleMinimapEntry = item.entry;
                var close:Boolean = nearby.enabled && self && limit > 0 && perMetre > 0 && entry.visible &&
                    data && data.group == "enemy" && data.state == "alive" &&
                    distance(entry, self) / perMetre <= limit;
                var stored:Object = layer.overlay(entry, entry, 0);
                var shape:Sprite = stored.shape;
                shape.visible = close;
                if (!close) continue;
                var radius:Number = 6 / Math.max(0.0001, mapscale.scaleOf(shape));
                var key:String = [Math.round(radius * 100), nearby.color, nearby.alpha].join(":");
                if (stored.key == key) continue;
                stored.key = key;
                var g:Graphics = shape.graphics;
                g.clear();
                g.lineStyle(1.5, colorutils.parse(nearby.color), Number(nearby.alpha) / 100, false, "none");
                g.drawCircle(0, 0, radius);
            }
        }

        private function range(nearby:Object):Number
        {
            var circles:Object = scale.ranges && scale.ranges.circles ? scale.ranges.circles : {};
            if (nearby.range == "view" && circles.view) return Number(circles.view.radius);
            if (nearby.range == "shell" && circles.shell) return Number(circles.shell.radius);
            return Number(nearby.distance);
        }

        // Screen pixels per metre, measured on the native circles entry (210 units per map width).
        private function globalPerMetre():Number
        {
            if (!scale.reference || !scale.reference.stage || !(scale.width > 0)) return 0;
            return mapscale.scaleOf(scale.reference) * mapscale.UNITS / scale.width;
        }

        private static function distance(a:DisplayObject, b:DisplayObject):Number
        {
            return Point.distance(a.localToGlobal(ORIGIN), b.localToGlobal(ORIGIN));
        }
    }
}
