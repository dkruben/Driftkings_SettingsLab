package driftkings.battle.components.minimap
{
    import flash.display.Graphics;
    import flash.display.LineScaleMode;
    public class MapGeometry
    {
        public static function stroke(g:Graphics, style:Object, color:uint, alpha:Number):void
        {
            g.lineStyle(Number(style.thickness), color, alpha / 100, false, LineScaleMode.NONE);
        }
        public static function line(g:Graphics, length:Number, style:Object):void
        {
            var dash:Number = Number(style.dash), gap:Number = Math.max(1, Number(style.gap));
            if (dash <= 0) { g.moveTo(0,0); g.lineTo(0,-length); return; }
            for (var n:Number = 0; n < length; n += dash + gap)
            { g.moveTo(0,-n); g.lineTo(0,-Math.min(length,n+dash)); }
        }
        public static function circle(g:Graphics, radius:Number, style:Object):void
        {
            if (Number(style.dash) <= 0) { g.drawCircle(0,0,radius); return; }
            var length:Number = 2 * Math.PI * radius;
            var dash:Number = Math.max(1, Number(style.dash)), gap:Number = Math.max(1,Number(style.gap));
            for (var n:Number = 0; n < length; n += dash + gap)
            {
                var end:Number = Math.min(length,n+dash);
                g.moveTo(radius*Math.cos(n/radius),radius*Math.sin(n/radius));
                for (var step:Number = n+2; step < end; step += 2)
                    g.lineTo(radius*Math.cos(step/radius),radius*Math.sin(step/radius));
                g.lineTo(radius*Math.cos(end/radius),radius*Math.sin(end/radius));
            }
        }
    }
}
