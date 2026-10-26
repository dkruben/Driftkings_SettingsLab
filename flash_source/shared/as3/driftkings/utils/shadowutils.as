package driftkings.utils
{
    import flash.filters.DropShadowFilter;

    /** Drop shadow from settings: enabled, distance, angle, color, alpha (0..100), blur or blurX/blurY, strength, quality. */
    public final class shadowutils
    {
        public static function filters(config:Object, blur:Number = 4, quality:int = 1):Array
        {
            if (!config || config.enabled === false) return [];
            return [new DropShadowFilter(number(config.distance, 0), number(config.angle, 0), colorutils.parse(config.color),
                number(config.alpha, 100) / 100, number(config.blurX, number(config.blur, blur)),
                number(config.blurY, number(config.blur, blur)), number(config.strength, 1), int(number(config.quality, quality)))];
        }

        private static function number(value:*, fallback:Number):Number
        {
            var result:Number = Number(value);
            return value === null || value === undefined || !isFinite(result) ? fallback : result;
        }
    }
}
