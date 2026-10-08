package driftkings.battle.components.flight_timer
{
	import flash.events.Event;
    import driftkings.utils.Constants;
    import driftkings.utils.Align;
    import driftkings.utils.TextExt;
    import driftkings.battle.base.BattleDisplayable;

    public class FlightTimerUI extends BattleDisplayable
    {
        private var flightTime:TextExt;
        private var pendingText:String = "";
        private var alignX:String = Align.CENTER;
        private var alignY:String = Align.CENTER;

        public var getSettings:Function;

        public function FlightTimerUI()
        {
            super();
            this.tabEnabled = false;
            this.tabChildren = false;
            this.mouseEnabled = false;
            this.mouseChildren = false;
            this.buttonMode = false;
            this.addEventListener(Event.RESIZE, onResizeHandle);
        }

        override protected function onPopulate():void 
        {
            super.onPopulate();
            if (this.getSettings != null)
            {
                var settings:Object = this.getSettings();
                if (settings != null)
				{
                    this.alignX = settings.alignX || Align.CENTER;
                    this.alignY = settings.alignY || Align.CENTER;
                    this.flightTime = new TextExt(settings.x, settings.y, Constants.middleText, settings.align, this);
                    this.flightTime.htmlText = this.pendingText;
                    this.updatePosition();
                }
            }
        }

        override protected function onBeforeDispose():void 
        {
            super.onBeforeDispose();
            this.flightTime = null;
            this.pendingText = "";
            this.removeEventListener(Event.RESIZE, onResizeHandle);
        }

        private function updatePosition() : void
        {
            Align.position(this, App.appWidth, App.appHeight, this.alignX, this.alignY);
        }

        public function as_onCrosshairPositionChanged(x:Number, y:Number):void
        {
            this.x = x;
            this.y = y;
        }

        private function onResizeHandle(event:Event) : void
        {
            this.updatePosition();
        }

        public function as_flightTime(text:String):void
        {
            this.pendingText = text;
            if (this.flightTime != null)
            {
                this.flightTime.htmlText = text;
            }
        }
    }
}
