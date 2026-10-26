package
{
    import driftkings.vehiclemarkers.VMDamage;
    import driftkings.vehiclemarkers.VMHealthBar;
    import driftkings.vehiclemarkers.VMIcons;
    import driftkings.vehiclemarkers.VMState;
    import driftkings.vehiclemarkers.VMText;
    import flash.display.GradientType;
    import flash.geom.Matrix;
    import flash.filters.ColorMatrixFilter;
    import flash.geom.ColorTransform;
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import flash.display.DisplayObjectContainer;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.filters.DropShadowFilter;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;
    import flash.events.Event;

    /** Integrated marker layouts and cached player ratings; native game events remain in control.
     *  The patched native movie calls only these static entry points. */
    public class DriftkingsVehicleMarkersFlash extends Sprite
    {
        private static var records:Dictionary = new Dictionary(true);

        private static var reported:Boolean = false;

        private static var nativeCache:Dictionary = new Dictionary(true);

        public static function receiveStats(settings:Object):Boolean
        {
            if (!settings || !settings.hasOwnProperty("__vmRatings")) return false;
            VMState.statistics = new Dictionary();
            if (!VMState.config) return true;
            if (VMState.config)
                for each (var row:Object in settings.__vmRatings)
                    VMState.statistics[String(row.name)] = row.values;
            for (var marker:Object in records)
            {
                var record:Object = records[marker];
                if (record.model) refreshFields(marker, record, record.model, record.dead);
            }
            return true;
        }

        public static function nativeSettings(original:Object, marker:Object, dead:Boolean):Object
        {
            if (!VMState.config || !VMState.config.profiles || !original) return original;
            var selected:Object = VMState.profile(marker, dead);
            if (!selected) return original;
            var cached:Object = nativeCache[marker];
            if (cached && cached.original === original && cached.profile === selected) return cached.value;
            var result:Object = {};
            for (var name:String in original) result[name] = original[name];
            var prefix:String = marker.exInfo ? "markerAlt" : "markerBase";
            var suffixes:Object = {vehicleName:"VehicleName", playerName:"PlayerName", healthBar:"HpIndicator",
                damage:"Damage", vehicleIcon:"Icon", levelIcon:"Level"};
            for (name in selected.native)
                result[prefix + (name == "hp" ? "Hp" : suffixes[name])] = name == "hp"
                    ? ({percent:0, currentAndMax:1, current:2, hidden:3})[selected.native[name]] : selected.native[name];
            if (selected.enabled && selected.fields != null)
            {
                result[prefix + "Hp"] = 3;
                result[prefix + "VehicleName"] = result[prefix + "PlayerName"] = false;
            }
            if (selected.healthBar.enabled) result[prefix + "HpIndicator"] = false;
            if (selected.icons.enabled && !selected.icons.vehicle.enabled) result[prefix + "Icon"] = false;
            nativeCache[marker] = {original:original, profile:selected, value:result};
            return result;
        }

        public static function configure(settings:Object):void
        {
            VMState.config = settings && settings.hasOwnProperty("__vmTest") ? settings.__vmTest : null;
            VMState.statistics = new Dictionary();
            trace("[Driftkings.VehicleMarkers] Flash configuration received; custom fields=" + Boolean(VMState.config && VMState.config.enabled));
        }

        public static function setColorBlind(value:Boolean):void
        {
            VMState.colorBlind = value;
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
            VMIcons.restoreIcons(marker);
            delete nativeCache[marker];
            clearFields(marker);
            VMDamage.clearDamage(marker);
            VMHealthBar.clearBar(marker);
            delete VMDamage.damageColors[marker];
        }

        public static function clearTransient(marker:Object):void
        {
            delete VMDamage.damageColors[marker];
            VMDamage.clearDamage(marker);
            VMHealthBar.clearBar(marker);
        }

        private static function refreshFields(marker:Object, record:Object, model:Object, dead:Boolean):void
        {
            for each (var item:Object in record.fields)
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

        public static function render(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            try
            {
                if (VMDamage.damageRecords[marker]) VMDamage.damageRecords[marker].holder.visible = !sticky;
                VMIcons.updateIcons(marker, model, dead);
                VMHealthBar.updateBar(marker, model, dead, sticky);
                update(marker, model, dead, sticky);
            }
            catch (error:Error)
            {
                clearFields(marker);
                VMHealthBar.clearBar(marker);
                if (!reported) { trace("[Driftkings.VehicleMarkers] Flash fields error: " + error.message); reported = true; }
            }
        }

        private static function update(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            var selected:Object = VMState.profile(marker, dead);
            if (!selected || !selected.enabled || !model) { clearFields(marker); return; }
            var group:String = String(marker.entityType);
            var mode:String = marker.exInfo ? "extended" : "normal";
            var fields:Array = selected.fields as Array;
            if (!fields) { clearFields(marker); return; }
            var selection:String = group + "/" + (dead ? "dead" : "alive") + "/" + mode;
            var record:Object = records[marker];
            if (!record || record.selection != selection || record.config !== VMState.config)
            {
                clearFields(marker);
                var holder:Sprite = new Sprite();
                holder.mouseEnabled = holder.mouseChildren = false;
                record = {holder:holder, fields:[], selection:selection, config:VMState.config};
                for each (var options:Object in fields)
                {
                    if (!options.enabled) continue;
                    var field:TextField = VMState.makeField(options);
                    holder.addChild(field);
                    record.fields.push({field:field, options:options, last:null});
                }
                DisplayObjectContainer(marker).addChild(holder);
                records[marker] = record;
            }
            record.holder.visible = !sticky;
            record.model = model; record.dead = dead;
            refreshFields(marker, record, model, dead);
        }

        // Entry points called by the patched native movie (build_tools/vehicle_markers_patch.py).
        public static function damageEnabled(marker:Object, health:int):Boolean
        {
            return VMDamage.damageEnabled(marker, health);
        }

        public static function damage(marker:Object, model:Object, newHealth:int, flag:uint, kind:String):void
        {
            VMDamage.damage(marker, model, newHealth, flag, kind);
        }

        public static function restoreIcons(marker:Object):void
        {
            VMIcons.restoreIcons(marker);
        }
    }
}
