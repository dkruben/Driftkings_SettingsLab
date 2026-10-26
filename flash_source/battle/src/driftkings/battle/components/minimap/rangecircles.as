package driftkings.battle.components.minimap
{
    import driftkings.utils.colorutils;
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ViewRangeCirclesMinimapEntry;

    /** Native and extra range circles, redrawn only when the ranges change. */
    public class rangecircles
    {
        private var styles:nativestyles;
        private var layer:geometrylayer;
        private var scale:mapscale;

        public function rangecircles(styles:nativestyles, layer:geometrylayer, scale:mapscale)
        {
            this.styles = styles; this.layer = layer; this.scale = scale;
        }

        public function draw(target:ViewRangeCirclesMinimapEntry, options:Object):void
        {
            scale.reference = target;
            var ranges:Object = scale.ranges;
            if (!ranges || Number(ranges.width) <= 0) return;
            // The shell range has no native circle: drawing it needs the custom layer.
            var custom:Boolean = options.extraCircles.length > 0 || Boolean(ranges.circles && ranges.circles.shell);
            for each (var style:Object in options.circles)
                if (style.thickness != 1 || style.dash > 0) custom = true;
            if (!custom) return;
            var stored:Object = layer.overlay(target, target);
            var shape:Sprite = stored.shape;
            for (var i:int = 0; i < target.numChildren; ++i)
            {
                var child:DisplayObject = target.getChildAt(i);
                if (child != shape) { styles.remember(child); child.alpha = 0; }
            }
            if (stored.version == scale.version) return;
            stored.version = scale.version;
            shape.graphics.clear();
            var coefficient:Number = mapscale.UNITS / Number(ranges.width);
            for (var key:String in ranges.circles)
            {
                var data:Object = ranges.circles[key];
                mapgeometry.stroke(shape.graphics, options.circles[key], uint(data.color), data.alpha);
                mapgeometry.circle(shape.graphics, Number(data.radius) * coefficient, options.circles[key]);
            }
            var vehicleClass:String = ranges.vehicleClass ? ranges.vehicleClass : options.vehicleClass;
            var names:Array = ranges.vehicleNames is Array ? ranges.vehicleNames : [];
            for each (data in options.extraCircles)
            {
                if (data.vehicleClass != "all" && data.vehicleClass != vehicleClass) continue;
                // Optional vehicle: 'germany-G04_PzVI_Tiger_I', 'G04_PzVI_Tiger_I' or 'Tiger I'.
                var vehicle:String = data.vehicle ? String(data.vehicle).toLowerCase().replace(":", "-") : "";
                if (vehicle && names.indexOf(vehicle) < 0) continue;
                mapgeometry.stroke(shape.graphics, data, colorutils.parse(data.color), data.alpha);
                mapgeometry.circle(shape.graphics, Number(data.radius) * coefficient, data);
            }
        }
    }
}
