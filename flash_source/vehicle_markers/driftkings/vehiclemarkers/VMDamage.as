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

    /** Floating damage per author; the colour of the last hit also feeds the health bar trail. */
    public class VMDamage
    {
        public static var damageRecords:Dictionary = new Dictionary(true);

        public static var animations:Dictionary = new Dictionary(true);

        public static var damageColors:Dictionary = new Dictionary(true);

        public static function clearDamage(marker:Object):void
        {
            var record:Object = damageRecords[marker];
            if (!record) return;
            record.holder.removeEventListener(Event.ENTER_FRAME, animateDamage);
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete animations[record.holder];
            record.items = [];
            delete damageRecords[marker];
        }

        public static function damageEnabled(marker:Object, health:int):Boolean
        {
            // updateHealth updates HP before the separate destroyed-state event arrives.
            var selected:Object = VMState.profile(marker, health <= 0);
            if (!selected) return false;
            if (selected.native && selected.native.damage === false) return true;
            if (!selected.damageText) return false;
            for each (var source:Object in selected.damageText.sources) if (source.enabled) return true;
            return Boolean(selected.damageText.enabled);
        }

        public static function damage(marker:Object, model:Object, newHealth:int, flag:uint, kind:String):void
        {
            try
            {
                var selected:Object = VMState.profile(marker, newHealth <= 0);
                if (!selected || !selected.damageText || !model) return;
                var source:String = flag == 2 ? "player" : flag == 1 ? "squad" : "other";
                var options:Object = selected.damageText.sources[source];
                if (!options) return;
                var amount:int = Math.max(0, int(model.currHealth)) - Math.max(0, newHealth);
                if (int(model.maxHealth) <= 0 || amount <= 0) return;
                damageColors[marker] = options.colors[source];
                if (!options.enabled || (selected.native && selected.native.damage === false)) return;
                var record:Object = damageRecords[marker];
                if (!record)
                {
                    var holder:Sprite = new Sprite();
                    holder.mouseEnabled = holder.mouseChildren = false;
                    record = {holder:holder, items:[], marker:marker};
                    DisplayObjectContainer(marker).addChild(holder);
                    damageRecords[marker] = record;
                    animations[holder] = record;
                    holder.addEventListener(Event.ENTER_FRAME, animateDamage);
                }
                var count:int = 0;
                for each (var existing:Object in record.items) if (existing.source == source) count++;
                while (count >= options.maxCount)
                {
                    for (var index:int = 0; index < record.items.length; index++)
                        if (record.items[index].source == source)
                        {
                            record.holder.removeChild(record.items[index].field);
                            record.items.splice(index, 1); count--; break;
                        }
                }
                var field:TextField = VMState.makeField(options);
                var color:String = options.colors[source];
                var explosion:Boolean = newHealth < 0 || kind == "explosion";
                var event:Object = {dmg:amount, "c:dmg":color, "dmg-ratio":Math.round(100 * amount / model.maxHealth),
                    "dmg-kind":explosion ? "explosion" : kind, "dmg-source":source};
                var template:String = String(explosion ? options.blowupMessage : options.format);
                var after:Object = {currHealth:Math.max(0, newHealth), maxHealth:model.maxHealth,
                    vType:model.vType, vClass:model.vClass, pName:model.pName, pClan:model.pClan, vLevel:model.vLevel, entityName:model.entityName};
                var damageFormat:TextFormat = field.defaultTextFormat;
                damageFormat.color = options.textFormat && options.textFormat.color != null
                    ? VMState.rgb(VMText.formatText(String(options.textFormat.color), marker, after, newHealth <= 0, event)) : VMState.rgb(color);
                field.defaultTextFormat = damageFormat;
                var opacity:Number = Number(VMText.formatText(String(options.alpha), marker, after, newHealth <= 0, event));
                opacity = isFinite(opacity) ? Math.max(0, Math.min(100, opacity)) / 100 : 0;
                field.alpha = opacity;
                field.htmlText = VMText.formatText(template, marker, after, newHealth <= 0, event);
                record.holder.addChild(field);
                record.items.push({field:field, start:getTimer(), duration:options.duration * 1000,
                    rise:options.rise, y:options.y, alpha:opacity, source:source});
            }
            catch (error:Error)
            {
                clearDamage(marker);
                trace("[Driftkings.VehicleMarkers] Floating damage error: " + error.message);
            }
        }

        public static function animateDamage(event:Event):void
        {
            var record:Object = animations[event.currentTarget];
            if (!record) return;
            var now:int = getTimer();
            for (var i:int = record.items.length - 1; i >= 0; --i)
            {
                var item:Object = record.items[i];
                var progress:Number = (now - item.start) / item.duration;
                if (progress >= 1)
                {
                    record.holder.removeChild(item.field);
                    record.items.splice(i, 1);
                }
                else
                {
                    item.field.y = item.y - item.rise * progress;
                    item.field.alpha = item.alpha * Math.min(1, (1 - progress) * 2);
                }
            }
            if (!record.items.length) clearDamage(record.marker);
        }
    }
}
