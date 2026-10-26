package driftkings.battle.components.dispersion_timer
{
	import driftkings.utils.constants;
	import driftkings.utils.align;
	import driftkings.utils.textext;
	import driftkings.battle.base.crosshairdisplayable;

	public class dispersiontimerui extends crosshairdisplayable
	{
		private var dispersionTime:textext;
		public var getSettings:Function;

		public function dispersiontimerui()
		{
			super();
		}

		override protected function onPopulate():void
		{
			super.onPopulate()
			if (this.getSettings != null)
			{
				var settings:Object = getSettings();
				if (settings.enabled)
				{
					this.alignX = settings.alignX || align.CENTER;
					this.alignY = settings.alignY || align.CENTER;
					this.x = settings.x < 0 ? parent.width + settings.x : settings.x
					this.y = settings.y < 0 ? parent.height + settings.y : settings.y
					this.dispersionTime = new textext(x, y, constants.middleText, settings.align, this);
					this.updatePosition();
				}
			}
		}

		override protected function onBeforeDispose():void
		{
			super.onBeforeDispose();
			this.dispersionTime = null;
		}

		public function as_updateTimerText(text:String):void
		{
			this.dispersionTime.htmlText = text;
		}
	}
}
