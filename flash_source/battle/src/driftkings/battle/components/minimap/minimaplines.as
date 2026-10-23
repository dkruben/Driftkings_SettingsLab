package driftkings.battle.components.minimap
{
    import flash.display.DisplayObject;
    import flash.display.Graphics;
    import flash.display.Sprite;
    import flash.geom.ColorTransform;
    import flash.geom.Matrix;
    import net.wg.gui.battle.views.minimap.components.entries.personal.ViewPointMinimapEntry;

    /** Camera, sector and hull lines, measured in metres. */
    public class minimaplines
    {
        private var styles:nativestyles;
        private var layer:geometrylayer;
        private var scale:mapscale;

        public function minimaplines(styles:nativestyles, layer:geometrylayer, scale:mapscale)
        {
            this.styles = styles; this.layer = layer; this.scale = scale;
        }

        // The camera's direction triangle has its own opacity.
        public function triangle(target:DisplayObject, options:Object):void
        {
            if (!target) return;
            styles.remember(target);
            target.alpha = Number(options.lines.triangleAlpha) / 100;
        }

        // opacity: extra factor in 0..100 (the camera line's own opacity).
        public function line(target:DisplayObject, options:Object, color:String, withMarks:Boolean = false, opacity:Number = 100):void
        {
            if (!target) return;
            var lines:Object = options.lines;
            var custom:Boolean = Boolean(lines.customStyle);
            var drawn:Boolean = custom && Boolean(lines.geometry);
            var marks:Boolean = withMarks && Number(lines.marks) > 0;
            var alpha:Number = Number(lines.alpha) * opacity / 100;
            if (!custom && !marks && opacity >= 100) return;
            var saved:Object = styles.remember(target);
            // Native style: only scale the client's own opacity.
            if (!custom) target.alpha = saved.alpha * opacity / 100;
            if ((drawn || marks) && target.parent)
            {
                var stored:Object = layer.overlay(target, target.parent);
                var shape:Sprite = stored.shape;
                // Copy position and rotation only: a scaled native placeholder
                // must not stretch a line measured in metres.
                var m:Matrix = target.transform.matrix, angle:Number = Math.atan2(m.b, m.a);
                shape.transform.matrix = new Matrix(Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle), m.tx, m.ty);
                shape.visible = target.visible;
                var length:Number = scale.metres(shape, Number(lines.length));
                var step:Number = marks ? scale.metres(shape, Number(lines.marks)) : 0;
                var key:String = [Math.round(length * 10), Math.round(step * 10), drawn, color, alpha].join(":");
                if (stored.key != key)
                {
                    stored.key = key;
                    draw(shape, lines, vehiclelabel.parseColor(color), alpha, length, step, drawn);
                }
                if (drawn) target.alpha = 0;
            }
            if (custom && !drawn)
            {
                var transform:ColorTransform = new ColorTransform();
                transform.color = vehiclelabel.parseColor(color);
                target.transform.colorTransform = transform;
                target.alpha = alpha / 100;
            }
        }

        private static function draw(shape:Sprite, lines:Object, tint:uint, alpha:Number, length:Number, step:Number, stroke:Boolean):void
        {
            var g:Graphics = shape.graphics;
            g.clear();
            if (stroke)
            {
                mapgeometry.stroke(g, lines, tint, alpha);
                mapgeometry.line(g, length, lines);
            }
            if (step > 0) mapgeometry.marks(g, length, step, tint, alpha, 1.5 / Math.max(0.0001, mapscale.scaleOf(shape)));
        }

        // The view point entry is rotated with the hull: local -y is forward. The line spans
        // the map diagonal, so the native entries mask cuts it at the minimap edge.
        public function hull(point:ViewPointMinimapEntry, options:Object):void
        {
            var lines:Object = options.lines;
            if (!lines.hull || !point.visible) return;
            var stored:Object = layer.overlay(point, point, 0);
            var shape:Sprite = stored.shape;
            var length:Number = scale.metres(shape, scale.width * Math.SQRT2);
            var step:Number = Number(lines.marks) > 0 ? scale.metres(shape, Number(lines.marks)) : 0;
            var key:String = [Math.round(length * 10), Math.round(step * 10)].join(":");
            if (stored.key == key) return;
            stored.key = key;
            draw(shape, lines, vehiclelabel.parseColor(lines.hullColor), Number(lines.alpha), length, step, true);
        }
    }
}
