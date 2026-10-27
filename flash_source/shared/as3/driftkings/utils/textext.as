package driftkings.utils
{
	import flash.filters.GlowFilter;
	import flash.text.*;
	import driftkings.utils.constants;
	
	public class textext extends TextField
	{
		public function textext(x:Number, y:Number, style:TextFormat, align:String, ui:*, enabled:Boolean = true)
		{
			super();
			// Allow shared client fonts, device fonts and embedded symbol fonts.
			this.embedFonts = false;
			if (style == null)
			{
				style = constants.normalText;
			}
			this.x = x;
			this.y = y;
			this.width = 1;
			this.defaultTextFormat = style;
			this.antiAliasType = AntiAliasType.ADVANCED;
			this.autoSize = align;
			this.filters = [new GlowFilter(0, 0.55, 2, 2, 4)];
			this.selectable = false;
			this.multiline = true;
			this.visible = enabled;
			this.htmlText = "";
			ui.addChild(this);
		}
	}
}
