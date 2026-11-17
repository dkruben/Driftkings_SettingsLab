package driftkings.utils
{
    import flash.display.Loader;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.IOErrorEvent;
    import flash.events.SecurityErrorEvent;
    import flash.net.URLRequest;

    /** Owns a single local image request and all of its event listeners. */
    public class imageloadercomponent extends Sprite
    {
        protected var loader:Loader;
        private var imageDisposed:Boolean = false;

        public function imageloadercomponent()
        {
            super();
        }

        protected function loadImage(path:String, index:int = -1):void
        {
            releaseImage();
            if (imageDisposed) return;
            var requestPath:String = localImagePath(path);
            if (requestPath == null)
            {
                imageFailed(null);
                return;
            }
            loader = new Loader();
            loader.mouseEnabled = loader.mouseChildren = false;
            loader.contentLoaderInfo.addEventListener(Event.COMPLETE, loaded);
            loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, failed);
            loader.contentLoaderInfo.addEventListener(SecurityErrorEvent.SECURITY_ERROR, failed);
            if (index < 0) addChild(loader);
            else addChildAt(loader, index);
            try { loader.load(new URLRequest(requestPath)); }
            catch (error:Error) { imageFailed(null); }
        }

        /** Accept mod resources, user images and their fixed SWF-relative prefixes. */
        public static function localImagePath(path:String):String
        {
            if (!path) return null;
            if (path.indexOf("img://") == 0) path = path.substr(6);
            var root:String;
            if (path.indexOf("gui/maps/driftkings/") == 0)
            {
                path = path.substr("gui/maps/driftkings/".length);
                root = "../maps/driftkings/";
            }
            else if (path.indexOf("../maps/driftkings/") == 0)
            {
                path = path.substr("../maps/driftkings/".length);
                root = "../maps/driftkings/";
            }
            else if (path.indexOf("gui/aimingangles/") == 0)
            {
                path = path.substr("gui/aimingangles/".length);
                root = "../aimingangles/";
            }
            else if (path.indexOf("../aimingangles/") == 0)
            {
                path = path.substr("../aimingangles/".length);
                root = "../aimingangles/";
            }
            else if (path.indexOf("mods/configs/driftkings/") == 0)
            {
                path = path.substr("mods/configs/driftkings/".length);
                root = "../../../mods/configs/driftkings/";
            }
            else if (path.indexOf("../../../mods/configs/driftkings/") == 0)
            {
                path = path.substr("../../../mods/configs/driftkings/".length);
                root = "../../../mods/configs/driftkings/";
            }
            else return null;
            // Reject traversal, URL syntax and encoded separators in the tail.
            if (!validImageTail(path)) return null;
            return root + path;
        }

        public static function validImageTail(path:String):Boolean
        {
            if (!path || /[\\:%?#\x00-\x1f\x7f]/.test(path)) return false;
            for each (var part:String in path.split("/"))
                if (!part || part == "." || part == "..") return false;
            return true;
        }

        private function loaded(event:Event):void
        {
            if (loader != null && event.currentTarget === loader.contentLoaderInfo)
                imageReady(event);
        }

        private function failed(event:Event):void
        {
            if (loader != null && event.currentTarget === loader.contentLoaderInfo)
                imageFailed(event);
        }

        protected function imageReady(event:Event):void {}

        protected function imageFailed(event:Event):void
        {
            releaseImage();
        }

        protected function releaseImage():void
        {
            if (loader == null) return;
            var previous:Loader = loader;
            loader = null;
            previous.contentLoaderInfo.removeEventListener(Event.COMPLETE, loaded);
            previous.contentLoaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, failed);
            previous.contentLoaderInfo.removeEventListener(SecurityErrorEvent.SECURITY_ERROR, failed);
            utils.safeUnload(previous);
            if (previous.parent == this) removeChild(previous);
        }

        public function dispose():void
        {
            imageDisposed = true;
            releaseImage();
        }
    }
}
