package driftkings.battle.components.minimap
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import driftkings.utils.imageloadercomponent;
    import flash.display.Bitmap;
    import flash.events.Event;
    import flash.geom.Point;

    /**
     * A fixed-size reticle at the centre of the client's strategic camera area (the green frame).
     * It is a sibling of the native entry, not a child: the entry is scaled to the camera area,
     * and inheriting that transform made the reticle huge and offset.
     */
    public class artilleryaim extends imageloadercomponent
    {
        private var active:Boolean = false;
        // The native entry is only deactivated outside strategic/artillery modes: it keeps its
        // last position and camera-area scale and stays visible to AS3, so Python sends the mode.
        private var strategic:Boolean = false;
        private var size:Number = .5;
        private var entry:DisplayObject;
        private var source:String;
        private var ready:Boolean = false;

        public function artilleryaim()
        {
            mouseEnabled = mouseChildren = false;
            addEventListener(Event.ADDED_TO_STAGE, added);
            addEventListener(Event.REMOVED_FROM_STAGE, removed);
        }

        public function configure(settings:Object):void
        {
            active = settings != null && settings.enabled;
            if (!active) { detach(); releaseImage(); source = null; return; }
            size = Number(settings.scale) / 100;
            alpha = Number(settings.alpha) / 100;
            var path:String = String(settings.src);
            if (path != source)
            {
                source = path;
                loadImage(path);
            }
            update();
        }

        override protected function imageReady(event:Event):void
        {
            if (loader.content is Bitmap) Bitmap(loader.content).smoothing = true;
            // All PNG variants share one 60px footprint (30px at the default 50%), centred on the origin.
            // Scaleform reports zero contentLoaderInfo sizes; the content holds the real ones.
            var width:Number = loader.content && loader.content.width > 0 ? loader.content.width : 25;
            var height:Number = loader.content && loader.content.height > 0 ? loader.content.height : 25;
            var factor:Number = 60 / Math.max(1, width, height);
            loader.scaleX = loader.scaleY = factor;
            loader.x = -width * factor / 2;
            loader.y = -height * factor / 2;
            ready = true;
            if (stage) addEventListener(Event.ENTER_FRAME, update);
            update();
        }

        override protected function imageFailed(event:Event):void
        {
            releaseImage();
            visible = false;
        }

        override protected function releaseImage():void
        {
            ready = false;
            removeEventListener(Event.ENTER_FRAME, update);
            super.releaseImage();
        }

        public function setStrategic(value:Boolean):void
        {
            strategic = value;
            update();
        }

        public function attach(anchor:DisplayObjectContainer):void
        {
            if (!active || !anchor || !anchor.parent) return;
            if (entry == anchor && parent == anchor.parent) return;
            detach();
            entry = anchor;
            anchor.parent.addChild(this);
            update();
        }

        private function added(event:Event):void
        {
            if (ready) addEventListener(Event.ENTER_FRAME, update);
        }

        private function removed(event:Event):void
        {
            removeEventListener(Event.ENTER_FRAME, update);
        }

        private function update(event:Event = null):void
        {
            visible = active && strategic && ready && entry != null && parent != null &&
                entry.parent == parent && entry.visible && parent.visible;
            if (!visible) return;
            // The entry's origin is the camera centre. The container's own scale is
            // small and its ancestors enlarge it, so the scale is measured on the stage instead.
            var origin:Point = parent.localToGlobal(new Point(0, 0));
            var sx:Number = Point.distance(parent.localToGlobal(new Point(1, 0)), origin);
            var sy:Number = Point.distance(parent.localToGlobal(new Point(0, 1)), origin);
            if (!isFinite(entry.x) || !isFinite(entry.y) || !(sx > .000001) || !(sy > .000001) ||
                !isFinite(sx) || !isFinite(sy))
            {
                visible = false;
                return;
            }
            x = entry.x;
            y = entry.y;
            scaleX = size / sx;
            scaleY = size / sy;
        }

        public function detach():void
        {
            removeEventListener(Event.ENTER_FRAME, update);
            if (parent) parent.removeChild(this);
            entry = null;
            visible = false;
        }

        override public function dispose():void
        {
            detach();
            super.dispose();
            source = null;
            active = false;
            removeEventListener(Event.ADDED_TO_STAGE, added);
            removeEventListener(Event.REMOVED_FROM_STAGE, removed);
        }
    }
}
