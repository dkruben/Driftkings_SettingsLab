package driftkings.utils
{
    /** Colours from settings: "#RRGGBB", "0xRRGGBB", "RRGGBB" or a number. */
    public final class colorutils
    {
        public static function parse(value:*, fallback:uint = 0):uint
        {
            if (value is Number) return uint(value);
            var text:String = String(value == null ? "" : value).replace(/^#|^0x/i, "");
            return /^[0-9A-Fa-f]{1,8}$/.test(text) ? uint(parseInt(text, 16)) : fallback;
        }
    }
}
