package driftkings.utils
{
	
	import flash.display.DisplayObject;

	public final class Align
	{
		public static const NONE:String = "none";
		public static const LEFT:String = "left";
		public static const RIGHT:String = "right";
		public static const CENTER:String = "center";
		public static const TOP:String = "top";
		public static const BOTTOM:String = "bottom";
		
		private static const ZERO:Number = 0;
		private static const HALF:Number = .5;
		private static const FULL:Number = 1;
		
        public static function position(target:DisplayObject, width:Number, height:Number,
                                        horizontal:String, vertical:String):void
        {
            target.x = horizontal == LEFT ? 0 : horizontal == RIGHT ? width : width >> 1;
            target.y = vertical == TOP ? 0 : vertical == BOTTOM ? height : height >> 1;
        }

		public static function isValid(align:String):Boolean
		{
			return align == LEFT || align == RIGHT || align == CENTER || align == TOP || align == BOTTOM;
		}
		
		public static function isValidX(align:String):Boolean
		{
			return align == LEFT || align == CENTER || align == RIGHT;
		}
		
		public static function isValidY(align:String):Boolean
		{
			return align == TOP || align == CENTER || align == BOTTOM;
		}
		
		public static function getFactor(align:String):Number
		{
			switch (align)
			{
				case LEFT:
					return ZERO;
				case RIGHT:
					return FULL;
				case CENTER:
					return HALF;
				case TOP:
					return ZERO;
				case BOTTOM:
					return FULL;
				default:
					return ZERO;
			}
		}
		
		public static function isValidAutoSize(align:String):Boolean
		{
			return align == LEFT || align == RIGHT || align == CENTER || align == NONE;
		}
	}
}