package driftkings.battle.components.ratings
{
    import flash.display.DisplayObjectContainer;
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    public class ExtraFields
    {
        private var holders:Dictionary = new Dictionary(true);
        private var textIDs:Dictionary = new Dictionary(true);
        private var nextTextID:uint=0;
        public function drawText(source:TextField,html:String,x:Number,width:Number,border:Boolean):void
        {
            var parent:DisplayObjectContainer=source.parent;
            if (!parent) return;
            if (!textIDs[source]) textIDs[source]="nativeText:"+(++nextTextID);
            if (!holders[parent]) holders[parent]={};
            var group:Object=holders[parent], key:String=textIDs[source];
            if (!group[key])
            {
                var holder:Sprite=new Sprite(); holder.mouseEnabled=holder.mouseChildren=false;
                var field:TextField=new TextField(); field.mouseEnabled=false;
                holder.addChild(field); parent.addChild(holder);
                group[key]={sprite:holder,text:field};
            }
            var record:Object=group[key]; record.used=true;
            holder=record.sprite; field=record.text;
            if (holder.parent!==parent) parent.addChild(holder);
            // Keep the native text and its layout untouched. Client auto-sizing
            // must never measure our longer statistics string on the next draw.
            field.defaultTextFormat=source.getTextFormat();
            field.embedFonts=source.embedFonts;
            field.antiAliasType=source.antiAliasType;
            field.multiline=source.multiline; field.wordWrap=source.wordWrap;
            field.autoSize="none"; field.width=width; field.height=source.height;
            field.border=border;
            if (record.html!==html) { field.htmlText=html; record.html=html; }
            holder.x=x; holder.y=source.y; holder.alpha=source.alpha;
            holder.filters=source.filters;
        }
        public function begin():void
        { for each (var group:Object in holders) for each (var field:Object in group) field.used = false; }
        public function changed():Boolean
        {
            for (var parent:Object in holders)
                for each (var record:Object in holders[parent]) if (record.sprite.parent!==parent) return true;
            return false;
        }
        public function draw(parent:DisplayObjectContainer, key:String, fields:Array, left:Boolean, edge:Number, rowY:Number, screenEdge:Number = 0):void
        {
            if (!parent || !fields) return;
            if (!holders[parent]) holders[parent] = {};
            var group:Object = holders[parent];
            for (var i:int = 0; i < fields.length; ++i)
            {
                var cfg:Object = fields[i], id:String = key + ":" + i;
                if (!group[id])
                {
                    var sprite:Sprite = new Sprite(); sprite.mouseEnabled = sprite.mouseChildren = false;
                    var text:TextField = new TextField(); text.mouseEnabled = false; text.embedFonts = true;
                    sprite.addChild(text); parent.addChild(sprite);
                    group[id] = {sprite:sprite, text:text};
                }
                var record:Object = group[id]; record.used = true;
                sprite = record.sprite; text = record.text;
                if (sprite.parent!==parent) parent.addChild(sprite);
                var width:Number = Math.max(0,NativeState.number(cfg.width,350));
                var height:Number = Math.max(0,NativeState.number(cfg.height,25));
                // Payload objects are immutable until the next Python update.
                // Keep graphics, text formatting and filters between native polls.
                if (record.config !== cfg)
                {
                var style:Object = cfg.textFormat || {};
                text.defaultTextFormat = new TextFormat(style.font || "$FieldFont", NativeState.number(style.size,13),
                    NativeState.color(style.color,0xD9D9D9), NativeState.flag(style.bold),
                    NativeState.flag(style.italic), NativeState.flag(style.underline), null, null, style.align || "left");
                // HTML images have a two-pixel TextField gutter. Compensate it
                // for src so a full-width texture is neither clipped nor shifted.
                text.x = text.y = cfg.src ? -2 : 0;
                text.width = width + (cfg.src ? 4 : 0);
                text.height = height + (cfg.src ? 4 : 0);
                text.multiline = NativeState.flag(cfg.multiline); text.wordWrap = NativeState.flag(cfg.wordWrap);
                var html:String = cfg.format === undefined ? "" : String(cfg.format);
                if (cfg.src) html = "<img src='" + String(cfg.src).replace(/'/g,"&apos;") + "' width='" + width + "' height='" + height + "'>";
                // Flash normalizes htmlText, so comparing its getter to the input
                // would reparse the same HTML and reload images on every draw.
                if (record.html !== html) { text.htmlText = html; record.html = html; }
                sprite.graphics.clear();
                if (cfg.borderColor !== undefined && cfg.borderColor !== null) sprite.graphics.lineStyle(1,NativeState.color(cfg.borderColor));
                if (cfg.bgColor !== undefined && cfg.bgColor !== null) sprite.graphics.beginFill(NativeState.color(cfg.bgColor));
                if (cfg.bgColor !== undefined || cfg.borderColor !== undefined) sprite.graphics.drawRect(0,0,width,height);
                sprite.graphics.endFill();
                sprite.alpha = Math.max(0,Math.min(1,NativeState.number(cfg.alpha,100)/100));
                sprite.rotation = NativeState.number(cfg.rotation);
                sprite.scaleX = NativeState.number(cfg.scaleX,1); sprite.scaleY = NativeState.number(cfg.scaleY,1);
                sprite.filters = NativeState.filters(cfg.shadow);
                sprite.visible = cfg.visible === undefined || NativeState.flag(cfg.visible);
                record.config = cfg;
                }
                var x:Number = NativeState.number(cfg.x), y:Number = rowY + NativeState.number(cfg.y);
                // XVM mirrors the default, but honors an explicitly set align.
                var align:String = cfg.align || (left ? "left" : "right");
                sprite.x = (NativeState.flag(cfg.bindToIcon) ? edge : screenEdge) + (left ? x : -x) - (align == "right" ? width : align == "center" ? width/2 : 0);
                sprite.y = y - (cfg.valign == "bottom" ? height : cfg.valign == "center" ? height/2 : 0);
            }
        }
        public function end():void
        {
            for (var parent:Object in holders)
            {
                var group:Object = holders[parent];
                for (var id:String in group) if (!group[id].used)
                {
                    var sprite:Sprite = group[id].sprite;
                    if (sprite.parent) sprite.parent.removeChild(sprite);
                    delete group[id];
                }
            }
        }
        public function dispose():void { begin(); end(); holders = new Dictionary(true); textIDs = new Dictionary(true); }
    }
}
