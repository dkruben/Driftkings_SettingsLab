package net.wg.gui.battle.components {
    import flash.display.MovieClip;
    // Only the engine lifecycle is stubbed; display visibility is real AIR.
    public class BattleUIDisplayable extends MovieClip {
        protected var _isCompVisible:Boolean = true;
        public function setCompVisible(value:Boolean):void {
            if (_isCompVisible != value) { _isCompVisible=value; updateVisibility(); }
        }
        protected function updateVisibility():void { visible=_isCompVisible; }
        protected function onPopulate():void {}
        protected function onDispose():void {}
    }
}
