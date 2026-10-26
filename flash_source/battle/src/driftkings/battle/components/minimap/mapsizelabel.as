package driftkings.battle.components.minimap
{
    import driftkings.utils.colorutils;
    import driftkings.utils.shadowutils;
    import flash.geom.Point;
    import flash.geom.Rectangle;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import net.wg.gui.battle.views.minimap.BaseMinimap;

    /** Map size caption inside the native minimap frame. */
    public class mapsizelabel
    {
        public var field:TextField;

        public function create(minimap:BaseMinimap, options:Object):void
        {
            clear();
            var size:Object = options.mapSize;
            if (!size.enabled) return;
            field = new TextField();
            field.embedFonts = true;
            field.mouseEnabled = field.selectable = false;
            field.width = Number(size.width);
            field.height = Number(size.height);
            field.alpha = Number(size.alpha) / 100;
            field.defaultTextFormat = new TextFormat("$FieldFont", 10, colorutils.parse("#FFCC66"));
            var shadow:Object = size.shadow;
            if (shadow.enabled) field.filters = shadowutils.filters(shadow);
            // The minimap grid is 10 x 10: {{cellsize}} is the side of one cell in metres.
            field.htmlText = String(size.format).split("{{width}}").join(options.mapWidth).split("{{height}}").join(options.mapHeight)
                .split("{{cellsize}}").join(Math.round(Number(options.mapWidth) / 10));
            minimap.addChild(field);
            position(minimap, options);
        }

        public function position(minimap:BaseMinimap, options:Object):void
        {
            if (!field || !minimap) return;
            // The native minimap has an inset origin that changes with +/- size.
            var origin:Point = minimap.currentTopLeftPoint;
            var bounds:Rectangle = minimap.getMinimapRectBySizeIndex(minimap.currentSizeIndex);
            if (!origin || bounds.width <= 0 || bounds.height <= 0) return;
            field.x = origin.x + Number(options.mapSize.offsetX);
            field.y = origin.y + Number(options.mapSize.offsetY);
        }

        public function clear():void
        {
            if (field && field.parent) field.parent.removeChild(field);
            field = null;
        }
    }
}
