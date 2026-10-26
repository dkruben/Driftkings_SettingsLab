package driftkings.battle.components.flight_timer
{
    import driftkings.utils.constants;
    import driftkings.utils.align;
    import driftkings.utils.textext;
    import driftkings.battle.base.crosshairdisplayable;

    public class flighttimerui extends crosshairdisplayable
    {
        private var flightTime:textext;
        private var pendingText:String = "";

        public var getSettings:Function;

        public function flighttimerui()
        {
            super();
        }

        override protected function onPopulate():void
        {
            super.onPopulate();
            if (this.getSettings != null)
            {
                var settings:Object = this.getSettings();
                if (settings != null)
                {
                    this.alignX = settings.alignX || align.CENTER;
                    this.alignY = settings.alignY || align.CENTER;
                    this.flightTime = new textext(settings.x, settings.y, constants.middleText, settings.align, this);
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
