package driftkings.battle.components.dispersion_timer
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.utils.Constants;
	import driftkings.utils.Align;
	import driftkings.utils.TextExt;
	import driftkings.battle.base.BattleDisplayable;

	public class DispersionTimerUI extends BattleDisplayable
	{
		private var dispersionTime:TextExt;
		private var alignX:String = Align.CENTER;
        private var alignY:String = Align.CENTER;
		public var getSettings:Function;

		public function DispersionTimerUI()
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
			super.onPopulate()
			if (this.getSettings != null)
			{
				var settings:Object = getSettings();
				if (settings.enabled)
				{
					this.alignX = settings.alignX || Align.CENTER;
					this.alignY = settings.alignY || Align.CENTER;
					this.x = settings.x < 0 ? parent.width + settings.x : settings.x
					this.y = settings.y < 0 ? parent.height + settings.y : settings.y
					this.dispersionTime = new TextExt(x, y, Constants.middleText, settings.align, this);
					this.updatePosition();
				}
			}
		}	

		override protected function onBeforeDispose():void 
		{
			super.onBeforeDispose();
			this.dispersionTime = null;
			this.removeEventListener(Event.RESIZE, onResizeHandle);
		}

		private function updatePosition() : void
        {
            Align.position(this, App.appWidth, App.appHeight, this.alignX, this.alignY);
        }

		private function onResizeHandle(event:Event) : void
        {
            this.updatePosition();
        }

		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}

		public function as_updateTimerText(text:String):void
		{
			this.dispersionTime.htmlText = text;
		}
	}
}