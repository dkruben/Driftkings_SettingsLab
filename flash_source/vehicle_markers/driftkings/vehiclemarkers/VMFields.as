package driftkings.vehiclemarkers
{
    import flash.display.DisplayObjectContainer;
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;

    /** Per-marker, per-state text layers. Layout semantics follow the reference marker components.
     *  Reference: XVM Contributors, GPL-3.0-or-later, TextFieldsComponent / ExtraFields. */
    public class VMFields
    {
        private static var records:Dictionary = new Dictionary(true);

        public static function clear(marker:Object):void
        {
            var record:Object = records[marker];
            if (!record) return;
            for each (var state:Object in record.states)
                if (state.holder.parent) state.holder.parent.removeChild(state.holder);
            delete records[marker];
        }

        public static function statisticsChanged():void
        {
            for (var marker:Object in records)
            {
                var record:Object = records[marker];
                if (record.active && record.model) refresh(marker, record.active, record.model, record.dead);
            }
        }

        private static function refresh(marker:Object, state:Object, model:Object, dead:Boolean):void
        {
            for each (var item:Object in state.fields)
            {
                var html:String = VMText.formatText(item.options.format, marker, model, dead);
                var alpha:Number = Number(VMText.formatText(String(item.options.alpha), marker, model, dead));
                item.field.alpha = isFinite(alpha) ? Math.max(0, Math.min(100, alpha)) / 100 : 0;
                var shadow:Object = item.options.shadow;
                if (shadow && shadow.enabled && String(shadow.color).indexOf("{{") >= 0)
                {
                    var shadowColor:String = VMText.formatText(String(shadow.color), marker, model, dead);
                    if (item.shadowColor !== shadowColor)
                    {
                        item.field.filters = VMState.shadowFilters(shadow, shadowColor);
                        item.shadowColor = shadowColor;
                    }
                }
                var style:Object = item.options.textFormat;
                var color:String = style && style.color != null ? VMText.formatText(String(style.color), marker, model, dead) : VMText.teamColor(marker, model, dead);
                if (item.last !== html || item.color !== color)
                {
                    var textFormat:TextFormat = item.field.defaultTextFormat;
                    textFormat.color = VMState.rgb(color);
                    item.field.defaultTextFormat = textFormat;
                    item.field.htmlText = html;
                    item.last = html; item.color = color;
                }
            }
        }

        public static function render(marker:Object, selected:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            var fields:Array = selected && selected.enabled ? selected.fields as Array : null;
            if (!fields || !model) { clear(marker); return; }
            var record:Object = records[marker];
            if (!record || record.config !== VMState.config)
            {
                clear(marker);
                record = {states:{}, active:null, config:VMState.config};
                records[marker] = record;
            }
            var selection:String = String(marker.entityType) + "/" + (dead ? "dead" : "alive") + "/" + (marker.exInfo ? "extended" : "normal");
            var state:Object = record.states[selection];
            if (!state)
            {
                var holder:Sprite = new Sprite();
                holder.mouseEnabled = holder.mouseChildren = false;
                state = {holder:holder, fields:[]};
                record.states[selection] = state;
                for each (var options:Object in fields)
                {
                    if (!options.enabled) continue;
                    var field:TextField = VMState.makeField(options);
                    holder.addChild(field);
                    state.fields.push({field:field, options:options, last:null});
                }
                DisplayObjectContainer(marker).addChild(holder);
            }
            if (record.active && record.active !== state) record.active.holder.visible = false;
            record.active = state; record.model = model; record.dead = dead;
            state.holder.visible = !sticky;
            var container:DisplayObjectContainer = DisplayObjectContainer(marker);
            if (state.holder.parent !== container) container.addChild(state.holder);
            var top:int = container.numChildren - 1;
            var damage:Object = VMDamage.damageRecords[marker];
            // Keep an existing damage layer above text without swapping both on every update.
            if (damage && damage.holder.parent === container && container.getChildIndex(damage.holder) == top) top--;
            if (container.getChildIndex(state.holder) != top) container.setChildIndex(state.holder, top);
            refresh(marker, state, model, dead);
        }
    }
}
