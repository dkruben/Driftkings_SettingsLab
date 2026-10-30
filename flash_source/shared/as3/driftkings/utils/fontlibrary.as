package driftkings.utils
{
    import flash.text.Font;

    /** Real font resources; names and glyph maps belong to their original authors. */
    public class fontlibrary
    {
        private static var initialized:Boolean = false;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/DriftkingsFont.ttf", fontName="dkm", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face0:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/VehicleType.ttf", fontName="VehicleType", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face1:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/VehicleType.ttf", fontName="vtype", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face2:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/DynamicDefault.ttf", fontName="DynamicDefault", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face3:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/DynamicDefault.ttf", fontName="dynamic", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face4:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/DynamicOutline.ttf", fontName="DynamicOutline", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face5:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/DynamicOutline.ttf", fontName="dynamic2", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face6:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/ZurichCondMono.ttf", fontName="mono", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face7:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/ZurichCondMono.ttf", fontName="ZurichCondMono", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face8:Class;
        [Embed(source="../../../../../mod/res/gui/fonts/driftkings/DriftkingsFont.ttf", fontName="DriftkingsFont", mimeType="application/x-font", embedAsCFF="false")]
        private static const Face9:Class;

        public static function initialize():void
        {
            if (initialized) return;
            initialized = true;
            for each (var face:Class in [Face0, Face1, Face2, Face3, Face4, Face5, Face6, Face7, Face8, Face9]) Font.registerFont(face);
        }
    }
}
