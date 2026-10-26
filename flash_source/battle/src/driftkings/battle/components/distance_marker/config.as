package driftkings.battle.components.distance_marker 
{
    import driftkings.utils.colorutils;
	import driftkings.battle.components.distance_marker.disposable;

	public class config implements disposable
	{
		private var _decimalPrecision:int= 0;
		private var _textSize:int = 11;
		private var _textColor:int = colorutils.parse("#FFFFFF");
		private var _textAlpha:Number = 1.0;
		private var _drawTextShadow:Boolean = true;

		public function config() 
		{
			super()
		}

		public function deserialize(serializedConfig:Object) : void
		{
            this._decimalPrecision = serializedConfig["decimalPrecision"];
            this._textSize = serializedConfig["textSize"];
            this._textColor = colorutils.parse(serializedConfig["textColor"]);
            this._textAlpha = serializedConfig["textAlpha"];
            this._drawTextShadow = serializedConfig["drawTextShadow"];
        }

		public function disposeState() : void
		{}

		public function get decimalPrecision() : int
		{
			return this._decimalPrecision;
		}

		public function get textSize() : int
		{
			return this._textSize;
		}

		public function get textColor() : int
		{
			return this._textColor;
		}

		public function get textAlpha() : Number
		{
			return this._textAlpha;
		}

		public function get drawTextShadow() : Boolean
		{
			return this._drawTextShadow;
		}
	}
}
