package
{
    import flash.display.Sprite;
    import flash.display.DisplayObjectContainer;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.filters.DropShadowFilter;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;
    import flash.events.Event;

    /** Standalone extra text fields; native marker animation and health bar remain intact. */
    public class DriftkingsVehicleMarkersFlash extends Sprite
    {
        private static var config:Object;
        private static var records:Dictionary = new Dictionary(true);
        private static var reported:Boolean = false;
        private static var colorBlind:Boolean = false;
        private static var damageRecords:Dictionary = new Dictionary(true);
        private static var animations:Dictionary = new Dictionary(true);
        private static var bars:Dictionary = new Dictionary(true);
        private static var barAnimations:Dictionary = new Dictionary(true);

        public static function configure(settings:Object):void
        {
            config = settings && settings.hasOwnProperty("__vmTest") ? settings.__vmTest : null;
            trace("[Driftkings.VehicleMarkers] Flash configuration received; custom fields=" + Boolean(config && config.enabled));
        }

        public static function setColorBlind(value:Boolean):void
        {
            colorBlind = value;
        }

        private static function clearFields(marker:Object):void
        {
            var record:Object = records[marker];
            if (!record) return;
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete records[marker];
        }

        public static function clear(marker:Object):void
        {
            clearFields(marker);
            clearDamage(marker);
            clearBar(marker);
        }

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

        public static function damageEnabled():Boolean
        {
            return Boolean(config && config.damageText && config.damageText.enabled);
        }

        public static function damage(marker:Object, model:Object, newHealth:int, flag:uint):void
        {
            try
            {
                if (!config || !config.damageText || !config.damageText.enabled || !model) return;
                var amount:int = Math.max(0, int(model.currHealth)) - Math.max(0, newHealth);
                if (int(model.maxHealth) <= 0 || amount <= 0) return;
                var options:Object = config.damageText;
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
                while (record.items.length >= options.maxCount)
                    record.holder.removeChild(record.items.shift().field);
                var field:TextField = makeField(options);
                var color:String = flag == 2 ? options.colors.player : flag == 1 ? options.colors.squad : options.colors.other;
                var template:String = String(options.format).split("{{dmg}}").join(String(amount))
                    .split("{{c:dmg}}").join(color);
                var after:Object = {currHealth:Math.max(0, newHealth), maxHealth:model.maxHealth,
                    vType:model.vType, pName:model.pName, vLevel:model.vLevel, entityName:model.entityName};
                field.htmlText = formatText(template, marker, after, newHealth <= 0);
                record.holder.addChild(field);
                record.items.push({field:field, start:getTimer(), duration:options.duration * 1000,
                    rise:options.rise, y:options.y, alpha:options.alpha / 100});
            }
            catch (error:Error)
            {
                clearDamage(marker);
                trace("[Driftkings.VehicleMarkers] Floating damage error: " + error.message);
            }
        }

        private static function animateDamage(event:Event):void
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

        private static function makeField(options:Object):TextField
        {
            var field:TextField = new TextField();
            field.mouseEnabled = field.selectable = false;
            field.width = options.width; field.height = options.height;
            field.x = options.x; field.y = options.y; field.alpha = options.alpha / 100;
            var textFormat:TextFormat = new TextFormat("$FieldFont", 13, 0xFFFFFF);
            textFormat.align = options.align;
            field.defaultTextFormat = textFormat;
            field.multiline = true; field.wordWrap = false;
            var shadow:Object = options.shadow;
            if (shadow.enabled)
                field.filters = [new DropShadowFilter(shadow.distance, shadow.angle,
                    uint(String(shadow.color).replace("#", "0x")), shadow.alpha / 100,
                    shadow.blur, shadow.blur, shadow.strength)];
            return field;
        }

        public static function clearTransient(marker:Object):void
        {
            clearDamage(marker);
            clearBar(marker);
        }

        private static function stopBarAnimation(record:Object):void
        {
            record.holder.removeEventListener(Event.ENTER_FRAME, animateBar);
            delete barAnimations[record.holder];
        }

        private static function animateBar(event:Event):void
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

        private static function clearBar(marker:Object):void
        {
            var record:Object = bars[marker];
            if (!record) return;
            stopBarAnimation(record);
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete bars[marker];
        }

        private static function rgb(value:String):uint
        {
            return uint(value.replace("#", "0x"));
        }

        private static function updateBar(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            var options:Object = config ? config.healthBar : null;
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
                if (shadow.enabled)
                    holder.filters = [new DropShadowFilter(shadow.distance, shadow.angle,
                        rgb(shadow.color), shadow.alpha / 100, shadow.blur, shadow.blur, shadow.strength)];
                DisplayObjectContainer(marker).addChild(holder);
                record = {holder:holder, options:options, ratio:-1, color:"", trail:0, from:0, start:0};
                bars[marker] = record;
            }
            record.holder.visible = !sticky;
            var maximum:int = int(model.maxHealth);
            var current:int = Math.max(0, int(model.currHealth));
            var ratio:Number = dead || maximum <= 0 ? 0 : Math.max(0, Math.min(1, current / maximum));
            var fill:String = String(options.color);
            if (fill == "{{c:hp}}") fill = hpColor(current, maximum);
            else if (fill == "{{c:team}}") fill = teamColor(marker, model, dead);
            if (record.ratio == ratio && record.color == fill) return;
            if (options.damage.enabled && record.ratio >= 0 && ratio < record.ratio)
            {
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
            record.ratio = ratio; record.color = fill;
            paintBar(record);
        }

        private static function paintBar(record:Object):void
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
                shape.graphics.beginFill(rgb(options.border.color), options.border.alpha / 100);
                shape.graphics.drawRect(0, 0, options.width, border);
                shape.graphics.drawRect(0, options.height - border, options.width, border);
                shape.graphics.drawRect(0, border, border, innerHeight);
                shape.graphics.drawRect(options.width - border, border, border, innerHeight);
                shape.graphics.endFill();
            }
            shape.graphics.beginFill(rgb(options.background.color), options.background.alpha / 100);
            shape.graphics.drawRect(border, border, innerWidth, innerHeight);
            shape.graphics.endFill();
            if (options.damage.enabled && record.trail > ratio)
            {
                shape.graphics.beginFill(rgb(options.damage.color), options.damage.alpha / 100);
                shape.graphics.drawRect(border + innerWidth * ratio, border,
                    innerWidth * (record.trail - ratio), innerHeight);
                shape.graphics.endFill();
            }
            if (ratio > 0)
            {
                shape.graphics.beginFill(rgb(fill), 1);
                shape.graphics.drawRect(border, border, innerWidth * ratio, innerHeight);
                shape.graphics.endFill();
            }
        }

        private static function escaped(value:Object):String
        {
            return String(value == null ? "" : value).split("&").join("&amp;")
                .split("<").join("&lt;").split(">").join("&gt;")
                .split('"').join("&quot;").split("'").join("&#39;");
        }

        private static function teamColor(marker:Object, model:Object, dead:Boolean):String
        {
            var teams:Object = colorBlind && config.colors.colorBlind.enabled
                ? config.colors.colorBlind.team : config.colors.team;
            if (dead) return teams.dead;
            var name:String = String(model.entityName).toLowerCase();
            if (name.indexOf("squad") >= 0) return teams.squad;
            if (name.indexOf("teamkiller") >= 0) return teams.teamKiller;
            var group:String = String(marker.entityType);
            return teams.hasOwnProperty(group) ? teams[group] : teams.unknown;
        }

        private static function hpColor(hp:int, maxHp:int):String
        {
            if (maxHp <= 0) return config.colors.team.unknown;
            var percent:Number = Math.max(0, Math.min(100, 100 * hp / maxHp));
            for each (var band:Object in config.colors.hp)
                if (percent < Number(band.value)) return String(band.color);
            return String(config.colors.hp[config.colors.hp.length - 1].color);
        }

        public static function formatText(template:String, marker:Object, model:Object, dead:Boolean):String
        {
            var hp:int = Math.max(0, int(model.currHealth));
            var maxHp:int = int(model.maxHealth);
            var values:Object = {vehicle:model.vType, name:model.pName, hp:hp,
                maxHp:maxHp > 0 ? maxHp : "--", hpPercent:maxHp > 0 ? Math.round(100 * hp / maxHp) : "--",
                level:model.vLevel};
            values["c:team"] = teamColor(marker, model, dead);
            values["c:hp"] = hpColor(hp, maxHp);
            for (var key:String in values)
                template = template.split("{{" + key + "}}").join(escaped(values[key]));
            return template;
        }

        private static function applyIcon(icon:Object, options:Object, dead:Boolean):void
        {
            if (!icon || !options) return;
            // Absolute values avoid accumulating scale or position on repeated native updates.
            if (options.x != null) icon.x = Number(options.x);
            if (options.y != null) icon.y = Number(options.y);
            icon.scaleX = icon.scaleY = Number(options.scale);
            icon.alpha = options.enabled ? Number(options.alpha) / 100 * (dead ? Number(options.deadAlpha) / 100 : 1) : 0;
        }

        private static function updateIcons(marker:Object, dead:Boolean):void
        {
            var options:Object = config ? config.icons : null;
            if (!options || !options.enabled) return;
            // Reacquire the timeline child after native state changes; never retain or reparent it.
            if (marker.marker && marker.marker.vehicleTypeIcon)
                applyIcon(marker.marker.vehicleTypeIcon, options["class"], dead);
            if (marker.levelIcon) applyIcon(marker.levelIcon, options.level, dead);
            if (marker.vehicleIcon && options.vehicle) applyIcon(marker.vehicleIcon, options.vehicle, dead);
        }

        public static function render(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            try
            {
                if (damageRecords[marker]) damageRecords[marker].holder.visible = !sticky;
                updateIcons(marker, dead);
                updateBar(marker, model, dead, sticky);
                update(marker, model, dead, sticky);
            }
            catch (error:Error)
            {
                clearFields(marker);
                clearBar(marker);
                if (!reported) { trace("[Driftkings.VehicleMarkers] Flash fields error: " + error.message); reported = true; }
            }
        }

        private static function update(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            if (!config || !config.enabled || !model) { clearFields(marker); return; }
            var group:String = dead ? "dead" : String(marker.entityType);
            var mode:String = marker.exInfo ? "extended" : "normal";
            var fields:Array = config[group] ? config[group][mode] as Array : null;
            if (!fields) { clearFields(marker); return; }
            var selection:String = group + "/" + mode;
            var record:Object = records[marker];
            if (!record || record.selection != selection || record.config !== config)
            {
                clearFields(marker);
                var holder:Sprite = new Sprite();
                holder.mouseEnabled = holder.mouseChildren = false;
                record = {holder:holder, fields:[], selection:selection, config:config};
                for each (var options:Object in fields)
                {
                    if (!options.enabled) continue;
                    var field:TextField = makeField(options);
                    holder.addChild(field);
                    record.fields.push({field:field, options:options, last:null});
                }
                DisplayObjectContainer(marker).addChild(holder);
                records[marker] = record;
            }
            record.holder.visible = !sticky;
            for each (var item:Object in record.fields)
            {
                var html:String = formatText(item.options.format, marker, model, dead);
                if (item.last !== html) { item.field.htmlText = html; item.last = html; }
            }
        }
    }
}
