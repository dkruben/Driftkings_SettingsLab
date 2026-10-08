package driftkings.battle.components.minimap
{
    import flash.display.Sprite;
    import net.wg.gui.battle.views.minimap.components.entries.constants.VehicleMinimapEntryConst;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.filters.DropShadowFilter;

    /** Owned fields attached to the existing native vehicle entry. */
    public class VehicleLabel extends Sprite
    {
        public var caption:TextField = new TextField();
        public var hp:TextField = new TextField();
        private var bar:Sprite = new Sprite();
        private var previous:Object;
        private var settings:Object;
        private var previousColor:uint;
        private var fullText:String = "";
        private var compactText:String = "";
        private var aligned:String = "left";
        public var priority:int = 0;

        public function VehicleLabel()
        {
            mouseEnabled = mouseChildren = false;
            for each (var field:TextField in [caption, hp])
            {
                field.mouseEnabled = field.selectable = false;
                field.autoSize = TextFieldAutoSize.LEFT;
                addChild(field);
            }
            addChild(bar);
        }

        public static function parseColor(value:String):uint
        {
            return uint(parseInt(value.replace(/^#|^0x/i, ""), 16));
        }

        public function update(data:Object, options:Object, native:TextField):void
        {
            if (!data || !native) { visible = false; return; }
            visible = true;
            var labels:Object = options.labels;
            var health:Object = options.health;
            var color:uint = labels.customColors ? parseColor(labels[(data.state == "dead" ? "dead" : data.group) + "Color"]) : App.colorSchemeMgr.getRGB(VehicleMinimapEntryConst.TEXT_COLOR_SCHEME_PREFIX +
                    String(data.guiLabel ? data.guiLabel : (data.group == "squad" ? "squadman" : data.group)) +
                    VehicleMinimapEntryConst.TEXT_COLOR_SCHEME_POSTFIX);
            if (previous != data || settings != options || previousColor != color)
            {
                previous = data; settings = options; previousColor = color;
                priority = data.group == "squad" ? 2 : data.group == "enemy" ? 1 : 0;
                aligned = labels.align;
                fullText = String(data.text);
                compactText = fullText.length > int(labels.compactLength) ? fullText.substr(0, int(labels.compactLength)-2) + ".." : fullText;
                caption.defaultTextFormat = new TextFormat("$FieldFont", labels.fontSize, color);
                caption.text = fullText;
                caption.alpha = Number(labels.alpha) / 100;
                hp.defaultTextFormat = new TextFormat("$FieldFont", health.fontSize, color);
                hp.text = health.mode == "percent" ? String(data.percent) + "%" : String(data.hp);
                if (data.hp == "--") hp.text = "--";
                filters = labels.shadow ? [new DropShadowFilter(0, 0, 0, 1, 2, 2, 2)] : [];
                alpha = Number(data.alpha) / 100;
                bar.graphics.clear();
                if (data.hp != "--")
                {
                    bar.graphics.beginFill(0, .65);
                    bar.graphics.drawRect(0, 0, health.width, health.height);
                    bar.graphics.endFill();
                    bar.graphics.beginFill(color);
                    bar.graphics.drawRect(0, 0, Number(health.width) * Number(data.percent) / 100, health.height);
                    bar.graphics.endFill();
                }
            }
            x = native.x + Number(labels.x); y = native.y + Number(labels.y);
            scaleX = native.scaleX; scaleY = native.scaleY;
            caption.visible = labels.enabled && native.visible && fullText.length > 0;
            var showHP:Boolean = data.state != "dead" && (health.visibility == "always" || health.visibility == "key" && options.alternative);
            hp.visible = showHP && health.mode != "bar";
            bar.visible = showHP && health.mode == "bar" && data.hp != "--";
            hp.x = bar.x = Number(health.x); hp.y = bar.y = Number(health.y);
            compact(false);
        }

        public function compact(value:Boolean):void
        {
            var text:String = value ? compactText : fullText;
            if (caption.text != text) caption.text = text;
            caption.x = aligned == "right" ? -caption.width : aligned == "center" ? -caption.width / 2 : 0;
        }

        public function dispose():void
        {
            if (parent) parent.removeChild(this);
            previous = settings = null;
        }
    }
}
