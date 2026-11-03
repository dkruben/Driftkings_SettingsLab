package driftkings.battle.components.ratings
{
    import flash.text.TextField;
    import flash.utils.Dictionary;

    public class loadingclock
    {
        private var extra:extrafields;
        private var fields:Dictionary=new Dictionary(true);
        public function loadingclock(e:extrafields) { extra=e; }

        public function draw(owner:Object,payload:Object):void
        {
            var settings:Object=payload.loadingClock;
            var anchor:TextField=owner.helpTip as TextField;
            if (!settings || !settings.enabled || !settings.format || !anchor || !anchor.visible || !anchor.parent) return;
            // Local time: Python no longer resends the roster every second for the clock.
            var now:Date=new Date();
            var time:Object={H:pad(now.getHours()),i:pad(now.getMinutes()),s:pad(now.getSeconds())};
            var text:String="", escaped:Boolean=false, format:String=String(settings.format);
            for (var i:int=0;i<format.length;++i)
            {
                var token:String=format.charAt(i);
                if (!escaped && token==String.fromCharCode(92)) { escaped=true; continue; }
                text+=!escaped && time.hasOwnProperty(token) ? time[token] : token;
                escaped=false;
            }
            // Use the native helpTip anchor. Never use container.width:
            // it includes our own overlays and can feed back into their layout.
            var cfg:Object=fields[anchor];
            if (!cfg || cfg.format!==text || cfg.x!==anchor.x || cfg.y!==anchor.y ||
                cfg.width!==anchor.width || cfg.height!==anchor.height)
            {
                cfg={format:text,x:anchor.x,y:anchor.y,width:anchor.width,height:anchor.height,
                    align:"left",textFormat:{font:"$TitleFont",size:16,color:"#FFFFFF",align:"right"}};
                fields[anchor]=cfg;
            }
            // One clock per form, independent of the two teams and row order.
            extra.draw(anchor.parent,"loadingClock",[cfg],true,0,0,0);
        }

        private static function pad(value:int):String { return value<10 ? "0"+value : String(value); }
    }
}
