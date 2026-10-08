package driftkings.battle.components.minimap
{
    import flash.display.DisplayObjectContainer;
    import flash.display.Sprite;
    import flash.display.Loader;
    import flash.display.Bitmap;
    import flash.events.Event;
    import flash.events.IOErrorEvent;
    import flash.events.SecurityErrorEvent;
    import flash.geom.Matrix;
    import flash.net.URLRequest;

    /** A screen-sized reticle anchored to the client's strategic camera entry. */
    public class ArtilleryAim extends Sprite
    {
        private var active:Boolean = false;
        private var size:Number = .5;
        private var previous:Matrix;
        private var loader:Loader;
        private var source:String;
        private var ready:Boolean = false;

        public function ArtilleryAim()
        {
            mouseEnabled = mouseChildren = false;
            addEventListener(Event.ADDED_TO_STAGE, added);
            addEventListener(Event.REMOVED_FROM_STAGE, removed);
        }

        public function configure(settings:Object):void
        {
            active = settings != null && settings.enabled;
            previous = null;
            if (!active) { detach(); releaseImage(); source = null; return; }
            size = Number(settings.scale) / 100;
            alpha = Number(settings.alpha) / 100;
            var path:String = String(settings.src);
            if (path != source)
            {
                releaseImage();
                source = path;
                loader = new Loader();
                loader.mouseEnabled = loader.mouseChildren = false;
                loader.contentLoaderInfo.addEventListener(Event.COMPLETE, imageReady);
                loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, imageFailed);
                loader.contentLoaderInfo.addEventListener(SecurityErrorEvent.SECURITY_ERROR, imageFailed);
                addChild(loader);
                // WoT resources are relative to gui/flash; AIR tests use a file URL.
                if (path.indexOf("img://") == 0) path = path.substr(6);
                if (path.indexOf("gui/") == 0) path = "../../" + path;
                try { loader.load(new URLRequest(path)); }
                catch (error:Error) { imageFailed(null); }
            }
            update();
        }

        private function imageReady(event:Event):void
        {
            if (event.currentTarget != loader.contentLoaderInfo) return;
            if (loader.content is Bitmap) Bitmap(loader.content).smoothing = true;
            // All PNG variants share the original 25px footprint, regardless of resolution.
            var width:Number = loader.contentLoaderInfo.width;
            var height:Number = loader.contentLoaderInfo.height;
            var factor:Number = 25 / Math.max(1, width, height);
            loader.scaleX = loader.scaleY = factor;
            loader.x = -width * factor / 2;
            loader.y = -height * factor / 2;
            ready = true;
            if (stage) addEventListener(Event.ENTER_FRAME, update);
            update();
        }

        private function imageFailed(event:Event):void
        {
            trace("[Driftkings.Minimap] Cannot load artillery aim: " + source);
            releaseImage();
            visible = false;
        }

        private function releaseImage():void
        {
            ready = false;
            removeEventListener(Event.ENTER_FRAME, update);
            if (!loader) return;
            loader.contentLoaderInfo.removeEventListener(Event.COMPLETE, imageReady);
            loader.contentLoaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, imageFailed);
            loader.contentLoaderInfo.removeEventListener(SecurityErrorEvent.SECURITY_ERROR, imageFailed);
            try { loader.close(); } catch (error:Error) {}
            try { loader.unload(); } catch (ignored:Error) {}
            if (loader.parent == this) removeChild(loader);
            loader = null;
        }

        public function attach(anchor:DisplayObjectContainer):void
        {
            if (!active || !anchor || parent == anchor) return;
            detach();
            anchor.addChild(this);
            previous = null;
            update();
        }

        private function added(event:Event):void
        {
            if (ready) addEventListener(Event.ENTER_FRAME, update);
        }

        private function removed(event:Event):void
        {
            removeEventListener(Event.ENTER_FRAME, update);
            previous = null;
        }

        private function update(event:Event = null):void
        {
            visible = active && ready && parent != null && parent.visible;
            if (!visible) return;
            var matrix:Matrix = parent.transform.concatenatedMatrix;
            if (!isFinite(matrix.a) || !isFinite(matrix.b) || !isFinite(matrix.c) || !isFinite(matrix.d) ||
                Math.abs(matrix.a * matrix.d - matrix.b * matrix.c) < .000001)
            {
                visible = false;
                return;
            }
            if (previous && previous.a == matrix.a && previous.b == matrix.b &&
                previous.c == matrix.c && previous.d == matrix.d) return;
            previous = matrix.clone();
            matrix.invert();
            matrix.a *= size; matrix.b *= size; matrix.c *= size; matrix.d *= size;
            matrix.tx = matrix.ty = 0;
            transform.matrix = matrix;
        }

        public function detach():void
        {
            removeEventListener(Event.ENTER_FRAME, update);
            if (parent) parent.removeChild(this);
            previous = null;
            visible = false;
        }

        public function dispose():void
        {
            detach();
            releaseImage();
            source = null;
            active = false;
            removeEventListener(Event.ADDED_TO_STAGE, added);
            removeEventListener(Event.REMOVED_FROM_STAGE, removed);
        }
    }
}
