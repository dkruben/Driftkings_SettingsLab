package driftkings.battle.components.ratings
{
    import flash.utils.Dictionary;

    // Shared by driftkingspanels.swf, whose classes replace the client's players panel linkage
    // classes, and the ratings renderer. Both SWFs compile this class; the first one loaded
    // defines it for the battle, so the hooked rows and the renderer see the same state.
    public class panelhook
    {
        private static var rows:Dictionary=new Dictionary(true);
        // Set when the client redrew or reordered a hooked row since the last panel pass.
        public static var dirty:Boolean=true;

        public static function register(item:Object):void { rows[item]=true; dirty=true; }
        public static function changed():void { dirty=true; }
        public static function hooked(item:Object):Boolean { return Boolean(rows[item]); }
    }
}
