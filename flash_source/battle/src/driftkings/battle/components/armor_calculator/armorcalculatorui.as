package driftkings.battle.components.armor_calculator
{
	import flash.text.TextFieldAutoSize;
	import driftkings.utils.constants;
	import driftkings.utils.textext;
	import driftkings.battle.base.crosshairdisplayable;

	public class armorcalculatorui extends crosshairdisplayable
	{
		private var armorCalc:textext;
		public var getSettings:Function;

		public function armorcalculatorui()
		{
			super();
		}

		override protected function onPopulate():void 
		{
			super.onPopulate();
			var settings:Object = this.getSettings();
			if (settings.enabled)
			{
				this.x = settings.position.x < 0 ? parent.width + settings.position.x : settings.position.x
				this.y = settings.position.y < 0 ? parent.height + settings.position.y : settings.position.y
				this.armorCalc = new textext(settings.position.x, settings.position.y, constants.largeText, TextFieldAutoSize.CENTER, this);
			}
		}

		override protected function onBeforeDispose():void 
		{
			super.onBeforeDispose();
			this.armorCalc = null;
		}

		public function as_armorCalculator(text:String):void
		{
			if (armorCalc)
			{
				this.armorCalc.htmlText = text;
			}
		}
	}
}