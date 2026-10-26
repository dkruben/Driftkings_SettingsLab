package driftkings.vehiclemarkers
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.display.GradientType;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.filters.ColorMatrixFilter;
    import flash.filters.DropShadowFilter;
    import flash.geom.ColorTransform;
    import flash.geom.Matrix;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;

    /** Custom health bar with an animated damage trail. */
    public class VMHealthBar
    {
        public static var bars:Dictionary = new Dictionary(true);

        public static var barAnimations:Dictionary = new Dictionary(true);

        public static function stopBarAnimation(record:Object):void
        {
            record.holder.removeEventListener(Event.ENTER_FRAME, animateBar);
            delete barAnimations[record.holder];
        }

        public static function animateBar(event:Event):void
        {
            var record:Object = barAnimations[event.currentTarget];
            if (!record) return;
            var progress:Number = (getTimer() - record.start) / (record.options.damage.duration * 1000);
            if (progress < 0) return;
            progress = Math.min(1, progress);
            record.trail = record.from + (record.ratio - record.from) * progress;
            paintBar(record);
            if (progress >= 1) stopBarAnimation(record);
        }

        public static function clearBar(marker:Object):void
        {
            var record:Object = bars[marker];
            if (!record) return;
            stopBarAnimation(record);
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete bars[marker];
        }

        public static function updateBar(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            var selected:Object = VMState.profile(marker, dead);
            var options:Object = selected ? selected.healthBar : null;
            if (!options || !options.enabled || !model || (dead && !options.showOnDead))
            { clearBar(marker); return; }
            var record:Object = bars[marker];
            if (!record || record.options !== options)
            {
                clearBar(marker);
                var holder:Sprite = new Sprite();
                holder.mouseEnabled = holder.mouseChildren = false;
                holder.x = options.x; holder.y = options.y; holder.alpha = options.alpha / 100;
                var shadow:Object = options.shadow;
                holder.filters = VMState.shadowFilters(shadow, String(shadow.color));
                DisplayObjectContainer(marker).addChild(holder);
                record = {holder:holder, options:options, ratio:-1, color:"", trailColor:"#FFFFFF", trail:0, from:0, start:0};
                bars[marker] = record;
            }
            record.holder.visible = !sticky;
            var maximum:int = int(model.maxHealth);
            var current:int = Math.max(0, int(model.currHealth));
            var ratio:Number = dead || maximum <= 0 ? 0 : Math.max(0, Math.min(1, current / maximum));
            var fill:String = String(options.color);
            if (fill == "{{c:hp}}") fill = VMText.hpColor(current, maximum);
            else if (fill == "{{c:team}}") fill = VMText.teamColor(marker, model, dead);
            var gradientColor:String = VMText.formatText(String(options.gradient.color), marker, model, dead);
            if (record.ratio == ratio && record.color == fill && record.gradientColor == gradientColor) return;
            if (options.damage.enabled && record.ratio >= 0 && ratio < record.ratio)
            {
                record.trailColor = options.damage.color == "{{c:dmg}}" ? (VMDamage.damageColors[marker] || "#FFFFFF") : options.damage.color;
                record.from = Math.max(record.trail, record.ratio);
                record.trail = record.from;
                record.start = getTimer() + options.damage.delay * 1000;
                barAnimations[record.holder] = record;
                record.holder.addEventListener(Event.ENTER_FRAME, animateBar);
            }
            else if (!options.damage.enabled || record.ratio < 0 || ratio >= record.trail)
            {
                stopBarAnimation(record);
                record.trail = ratio;
            }
            record.gradientColor = gradientColor;
            record.ratio = ratio; record.color = fill;
            paintBar(record);
        }

        public static function paintBar(record:Object):void
        {
            var options:Object = record.options;
            var ratio:Number = record.ratio;
            var fill:String = record.color;
            var border:Number = options.border.width;
            var innerWidth:Number = options.width - 2 * border;
            var innerHeight:Number = options.height - 2 * border;
            var shape:Sprite = record.holder;
            shape.graphics.clear();
            // Draw the border as an outer rectangle, keeping all dimensions inside the configured size.
            if (border > 0)
            {
                shape.graphics.beginFill(VMState.rgb(options.border.color), options.border.alpha / 100);
                shape.graphics.drawRect(0, 0, options.width, border);
                shape.graphics.drawRect(0, options.height - border, options.width, border);
                shape.graphics.drawRect(0, border, border, innerHeight);
                shape.graphics.drawRect(options.width - border, border, border, innerHeight);
                shape.graphics.endFill();
            }
            shape.graphics.beginFill(VMState.rgb(options.background.color), options.background.alpha / 100);
            shape.graphics.drawRect(border, border, innerWidth, innerHeight);
            shape.graphics.endFill();
            if (options.damage.enabled && record.trail > ratio)
            {
                shape.graphics.beginFill(VMState.rgb(record.trailColor), options.damage.alpha / 100);
                shape.graphics.drawRect(border + innerWidth * ratio, border,
                    innerWidth * (record.trail - ratio), innerHeight);
                shape.graphics.endFill();
            }
            if (ratio > 0)
            {
                if (options.gradient.enabled)
                {
                    var matrix:Matrix = new Matrix();
                    matrix.createGradientBox(innerWidth * ratio, innerHeight, options.gradient.angle * Math.PI / 180, border, border);
                    shape.graphics.beginGradientFill(GradientType.LINEAR, [VMState.rgb(fill), VMState.rgb(record.gradientColor)],
                        [options.fill.alpha / 100, options.fill.alpha / 100], [0, 255], matrix);
                }
                else shape.graphics.beginFill(VMState.rgb(fill), options.fill.alpha / 100);
                shape.graphics.drawRect(border, border, innerWidth * ratio, innerHeight);
                shape.graphics.endFill();
            }
        }
    }
}
