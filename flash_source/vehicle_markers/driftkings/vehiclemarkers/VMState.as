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

    /** Shared marker configuration, per-vehicle statistics and text field helpers. */
    public class VMState
    {
        public static var config:Object;

        public static var statistics:Dictionary = new Dictionary();

        public static var colorBlind:Boolean = false;

        public static function profile(marker:Object, dead:Boolean):Object
        {
            if (!config || !config.profiles) return config;
            var team:String = String(marker.entityType);
            var state:String = dead ? "dead" : "alive";
            var mode:String = marker.exInfo ? "extended" : "normal";
            return config.profiles[team] ? config.profiles[team][state][mode] : null;
        }

        public static function rgb(value:String):uint
        {
            return uint(value.replace("#", "0x"));
        }

        public static function shadowFilters(shadow:Object, color:String):Array
        {
            return shadow && shadow.enabled ? [new DropShadowFilter(shadow.distance, shadow.angle, rgb(color),
                shadow.alpha / 100, shadow.blur, shadow.blur, shadow.strength)] : [];
        }

        public static function makeField(options:Object):TextField
        {
            var field:TextField = new TextField();
            field.mouseEnabled = field.selectable = false;
            field.width = options.width; field.height = options.height;
            field.x = options.x; field.y = options.y;
            var style:Object = options.textFormat;
            var textFormat:TextFormat = style ? new TextFormat(style.font, style.size, 0xFFFFFF, style.bold, style.italic)
                                             : new TextFormat("$FieldFont", 13, 0xFFFFFF);
            textFormat.align = options.align;
            field.defaultTextFormat = textFormat;
            field.multiline = true; field.wordWrap = false;
            // Macro shadow colours ({{c:system}}) are applied per vehicle in refreshFields.
            var shadow:Object = options.shadow;
            if (shadow.enabled && String(shadow.color).indexOf("{{") < 0)
                field.filters = shadowFilters(shadow, String(shadow.color));
            return field;
        }
    }
}
