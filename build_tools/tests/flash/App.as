package
{
    // Only the viewport used by PanelRenderer; no game client classes needed.
    public class App
    {
        public static var appWidth:Number=1920;
        public static var appHeight:Number=1080;
        public static var colorSchemeMgr:Object = {getRGB:function(name:String):uint {
            return name.indexOf("enemy") >= 0 ? 0xF05050 : 0x80D639;
        }};
    }
}
