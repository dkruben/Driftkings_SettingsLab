package driftkings.battle.base
{
	import driftkings.utils.align;

	/** Non-interactive HUD text that follows the crosshair; screen alignment applies when alignX/alignY are set. */
	public class crosshairdisplayable extends battledisplayable
	{
		protected var alignX:String = null;
		protected var alignY:String = null;

		public function crosshairdisplayable()
		{
			super();
		}

		override protected function configUI():void
		{
			super.configUI();
			this.tabEnabled = false;
			this.tabChildren = false;
			this.mouseEnabled = false;
			this.mouseChildren = false;
			this.buttonMode = false;
		}

		protected function updatePosition():void
		{
			if (this.alignX && this.alignY)
			{
				align.position(this, App.appWidth, App.appHeight, this.alignX, this.alignY);
			}
		}

		override protected function onResized():void
		{
			this.updatePosition();
		}

		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}
	}
}
