package
{
    import driftkings.vehiclemarkers.VMDamage;
    import driftkings.vehiclemarkers.VMHealthBar;
    import driftkings.vehiclemarkers.VMFields;
    import driftkings.vehiclemarkers.VMIcons;
    import driftkings.vehiclemarkers.VMState;
    import flash.display.Sprite;
    import flash.utils.Dictionary;

    /** Integrated marker layouts and cached player ratings; native game events remain in control.
     *  The patched native movie calls only these static entry points. */
    public class DriftkingsVehicleMarkersFlash extends Sprite
    {
        private static var markers:Dictionary = new Dictionary(true);

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
            VMFields.statisticsChanged();
            return true;
        }

        public static function nativeSettings(original:Object, marker:Object, dead:Boolean):Object
        {
            if (!VMState.config || !VMState.config.enabled || !VMState.config.profiles || !original) return original;
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
            var previous:Array = [];
            for (var marker:Object in markers) previous.push(marker);
            for each (marker in previous) clear(marker);
            nativeCache = new Dictionary(true);
            VMState.config = settings && settings.hasOwnProperty("__vmTest") ? settings.__vmTest : null;
            VMState.statistics = new Dictionary();
            trace("[Driftkings.VehicleMarkers] Flash configuration received; custom fields=" + Boolean(VMState.config && VMState.config.enabled));
        }

        public static function setColorBlind(value:Boolean):void
        {
            VMState.colorBlind = value;
        }

        public static function clear(marker:Object):void
        {
            VMIcons.restoreIcons(marker);
            delete nativeCache[marker];
            delete markers[marker];
            VMFields.clear(marker);
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

        public static function render(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            try
            {
                var selected:Object = VMState.profile(marker, dead);
                if (!VMState.config || !VMState.config.enabled || !selected) { clear(marker); return; }
                markers[marker] = true;
                if (VMDamage.damageRecords[marker]) VMDamage.damageRecords[marker].holder.visible = !sticky;
                VMIcons.updateIcons(marker, model, dead);
                VMHealthBar.updateBar(marker, model, dead, sticky);
                VMFields.render(marker, selected, model, dead, sticky);
                // A recreated bar must stay below cached text; floating damage is the top layer.
                if (VMDamage.damageRecords[marker]) addTop(marker, VMDamage.damageRecords[marker].holder);
            }
            catch (error:Error)
            {
                clear(marker);
                if (!reported) { trace("[Driftkings.VehicleMarkers] Flash fields error: " + error.message); reported = true; }
            }
        }

        private static function addTop(marker:Object, child:Sprite):void
        {
            if (child.parent === marker && marker.getChildIndex(child) != marker.numChildren - 1)
                marker.setChildIndex(child, marker.numChildren - 1);
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
