package driftkings.utils
{
    /** Hash-prefixed setting colours; numeric values come from native APIs. */
    public final class colorutils
    {
        public static function parse(value:*, fallback:uint = 0):uint
        {
            if (value is Number) return uint(value);
            var text:String = String(value == null ? "" : value);
            return /^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$/.test(text) ? uint(parseInt(text.substr(1), 16)) : fallback;
        }
    }
}
