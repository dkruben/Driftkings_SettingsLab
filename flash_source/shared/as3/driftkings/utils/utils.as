package driftkings.utils
{
    import flash.display.DisplayObject;
    import flash.display.Loader;
    import flash.geom.ColorTransform;

    public class utils
    {
        public static function safeUnload(loader:Loader):void
        {
            if (loader == null) return;
            try
            {
                loader.close();
            }
            catch (closeError:Error)
            {
                // close() may fail when loading has already completed or stopped.
                // Still attempt unload() so completed content is released.
            }
            try
            {
                loader.unload();
            }
            catch (unloadError:Error)
            {
                // Cleanup is best effort for failed or already-unloaded content.
            }
        }

        public static function colorConvert(color:String):uint
        {
            return colorutils.parse(color);
        }

        public static function updateColor(object:DisplayObject, hpColor:String):void
        {
            var colorInfo:ColorTransform = object.transform.colorTransform;
            colorInfo.color = colorConvert(hpColor);
            object.transform.colorTransform = colorInfo;
        }
    }
}
