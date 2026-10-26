package driftkings.utils
{
	import flash.text.TextFormat;

	public class constants
	{
		public static const tite16:TextFormat       = new TextFormat("$TitleFont", 16, colorutils.parse("#FFFFFF"));
		public static const middleText:TextFormat   = new TextFormat("$TitleFont", 18, colorutils.parse("#FFFFFF"));
		public static const diff:TextFormat         = new TextFormat("$TitleFont", 14, colorutils.parse("#FFFFFF"));
		public static const largeText:TextFormat    = new TextFormat("$TitleFont", 20, colorutils.parse("#FFFFFF"));
		public static const normalText:TextFormat   = new TextFormat("$FieldFont", 16, colorutils.parse("#FFFFFF"));
		public static const normalText15:TextFormat = new TextFormat("$FieldFont", 15, colorutils.parse("#FFFFFF"));
		public static const scoreformat:TextFormat  = new TextFormat("$TitleFont", 24, colorutils.parse("#FFFFFF"), true);

		public static const ALPHA:Number            = 0.6;
		public static const BG_ALPHA:Number         = 0.3;
		public static const HUNDREDTH:Number        = 0.01;

		public function constants()
		{
			super();
		}
	}
}