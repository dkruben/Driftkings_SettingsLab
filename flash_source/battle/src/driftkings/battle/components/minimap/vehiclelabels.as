package driftkings.battle.components.minimap
{
    import flash.display.DisplayObject;
    import flash.geom.Rectangle;
    import flash.text.TextField;
    import flash.utils.Dictionary;
    import net.wg.gui.battle.views.minimap.components.entries.vehicle.VehicleMinimapEntry;

    /** Owned vehicle captions replacing the native names, with overlap avoidance. */
    public class vehiclelabels
    {
        private var styles:nativestyles;
        private var labels:Dictionary = new Dictionary(true);
        private var visible:Array = [];

        public function vehiclelabels(styles:nativestyles)
        {
            this.styles = styles;
        }

        public function begin():void
        {
            visible.length = 0;
        }

        public function update(entry:VehicleMinimapEntry, data:Object, options:Object):void
        {
            var owned:vehiclelabel = labels[entry] as vehiclelabel;
            if (!owned) { owned = new vehiclelabel(); labels[entry] = owned; entry.addChild(owned); }
            var native:TextField = entry.vehicleNameTextFieldAlt.visible ? entry.vehicleNameTextFieldAlt : entry.vehicleNameTextFieldClassic;
            styles.remember(entry.vehicleNameTextFieldAlt); styles.remember(entry.vehicleNameTextFieldClassic);
            entry.vehicleNameTextFieldAlt.alpha = entry.vehicleNameTextFieldClassic.alpha = 0;
            owned.update(data, options, native);
            if (entry.visible && owned.caption.visible) visible.push(owned);
        }

        public function resolveOverlaps(options:Object, space:DisplayObject):void
        {
            if (!options.labels.avoidOverlap || options.alternative) return;
            visible.sortOn("priority", Array.DESCENDING | Array.NUMERIC);
            var occupied:Array = [];
            for each (var label:vehiclelabel in visible)
            {
                var bounds:Rectangle = label.caption.getBounds(space);
                var collision:Boolean = intersects(bounds, occupied);
                if (collision) { label.compact(true); bounds = label.caption.getBounds(space); }
                if (collision && intersects(bounds, occupied)) label.caption.visible = false;
                else occupied.push(bounds);
            }
        }

        public function removeDetached():void
        {
            for (var key:Object in labels)
                if (!DisplayObject(key).stage) { vehiclelabel(labels[key]).dispose(); delete labels[key]; }
        }

        public function clear():void
        {
            for each (var label:vehiclelabel in labels) label.dispose();
            labels = new Dictionary(true);
            visible = [];
        }

        private static function intersects(bounds:Rectangle, occupied:Array):Boolean
        {
            for each (var rect:Rectangle in occupied) if (bounds.intersects(rect)) return true;
            return false;
        }
    }
}
