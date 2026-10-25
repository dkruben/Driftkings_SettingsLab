package driftkings.battle.components.minimap
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.filters.ColorMatrixFilter;
    import flash.utils.Dictionary;
    import net.wg.gui.battle.views.minimap.components.entries.vehicle.VehicleMinimapEntry;

    /** Vehicle icon scale, opacity and lost tint, and dead < lost < alive layering. */
    public class vehicleicons
    {
        private static const ICONS:Array = ["enemyRedAnimation", "enemyPurpleAnimation", "deadAnimation",
            "deadPermanentAnimation", "squadmanYellowAnimation", "squadmanGoldAnimation",
            "teamKillerBlueAnimation", "allyGreenAnimation"];
        private static const DEAD_ICONS:Array = ["deadAnimation", "deadPermanentAnimation"];
        private var styles:nativestyles;
        // Vehicle entries seen in this refresh, with their layer rank.
        private var layered:Array = [];

        public function vehicleicons(styles:nativestyles)
        {
            this.styles = styles;
        }

        public function begin():void
        {
            layered = [];
        }

        public function update(entry:VehicleMinimapEntry, data:Object, options:Object):void
        {
            var state:String = data ? String(data.state) : "alive";
            if (data) layered.push({entry:entry, rank:rank(state)});
            var icons:Object = options.icons;
            var size:Number = Number(state == "dead" ? icons.deadScale : state == "lost" ? icons.lostScale : icons.scale);
            var tint:int = options.lostMarker.style == "tint" && data && data.lostColor ? vehiclelabel.parseColor(String(data.lostColor)) : -1;
            if (options.colorBlind && data && data.group == "enemy")
            {
                var accessible:Number = vehiclelabel.nativeColor(data);
                if (!isNaN(accessible)) tint = int(accessible);
            }
            for each (var name:String in ICONS)
            {
                var alpha:Number = DEAD_ICONS.indexOf(name) >= 0 ? Number(icons.deadAlpha) : Number(icons.alpha);
                style(entry[name] as DisplayObject, size,
                    options.showVehicleTypes ? alpha * (data ? Number(data.alpha) / 100 : 1) : 0,
                    state == "lost" ? Number(options.lostMarker.desaturate) : 0,
                    tint);
            }
        }

        // tint: RGB of a dull team colour, or -1 for plain grey.
        public function style(target:DisplayObject, scale:Number, alpha:Number, desaturate:Number = 0, tint:int = -1):void
        {
            if (!target) return;
            var saved:Object = styles.remember(target);
            saved.scaleChanged = true;
            target.scaleX = saved.sx * scale; target.scaleY = saved.sy * scale;
            target.alpha = alpha / 100;
            // Lost vehicles: fade the icon towards grey or a dull team colour, keeping the native filters.
            var amount:Number = Math.max(0, Math.min(100, desaturate)) / 100;
            if (amount > 0 || saved.filtersChanged)
            {
                saved.filtersChanged = true;
                target.filters = amount > 0 ? saved.filters.concat([recolour(amount, tint)]) : saved.filters;
            }
        }

        // Keep dead vehicles below lost ones and both below spotted vehicles, so a
        // destroyed or old marker never hides a live one at the same position.
        public function order():void
        {
            var byParent:Dictionary = new Dictionary(true);
            for each (var item:Object in layered)
            {
                var parent:DisplayObjectContainer = DisplayObject(item.entry).parent;
                if (!parent) continue;
                if (!byParent[parent]) byParent[parent] = [];
                byParent[parent].push(item);
            }
            for (var key:Object in byParent)
            {
                var container:DisplayObjectContainer = key as DisplayObjectContainer, items:Array = byParent[key];
                var slots:Array = [];
                for each (item in items) slots.push(container.getChildIndex(item.entry));
                slots.sort(Array.NUMERIC);
                // Only reorder a contiguous block of vehicles; never move them past other layers.
                if (slots.length < 2 || slots[slots.length - 1] - slots[0] != slots.length - 1) continue;
                items.sort(function(a:Object, b:Object):Number
                { return a.rank - b.rank || container.getChildIndex(a.entry) - container.getChildIndex(b.entry); });
                for (var i:int = 0; i < items.length; ++i)
                    if (container.getChildIndex(items[i].entry) != slots[0] + i) container.setChildIndex(items[i].entry, slots[0] + i);
            }
        }

        private static function rank(state:String):int
        {
            return state == "dead" ? 0 : state == "lost" ? 1 : 2;
        }

        // Blend each pixel towards its luminance, multiplied by the tint (white = grey).
        private static function recolour(amount:Number, tint:int):ColorMatrixFilter
        {
            var colour:uint = tint < 0 ? 0xFFFFFF : uint(tint);
            var cr:Number = (colour >> 16 & 0xFF) / 255, cg:Number = (colour >> 8 & 0xFF) / 255, cb:Number = (colour & 0xFF) / 255;
            var s:Number = 1 - amount, r:Number = 0.3086 * amount, g:Number = 0.6094 * amount, b:Number = 0.082 * amount;
            return new ColorMatrixFilter([s + r * cr, g * cr, b * cr, 0, 0,
                                          r * cg, s + g * cg, b * cg, 0, 0,
                                          r * cb, g * cb, s + b * cb, 0, 0,
                                          0, 0, 0, 1, 0]);
        }
    }
}
