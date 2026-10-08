package net.wg.gui.battle.views {
    import flash.display.MovieClip;
    public class BaseBattlePage extends MovieClip {
        public function isFlashComponentRegisteredS(alias:String):Boolean { return false; }
        public function registerFlashComponentS(component:*, alias:String):void {}
        public function unregisterFlashComponentS(alias:String):void {}
    }
}
