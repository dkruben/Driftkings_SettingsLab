package driftkings.battle.components.ratings
{
    import flash.text.TextField;
    import flash.utils.Dictionary;

    public class LoadingClock
    {
        private var extra:ExtraFields;
        private var fields:Dictionary=new Dictionary(true);
        public function LoadingClock(e:ExtraFields) { extra=e; }

        public function draw(owner:Object,payload:Object):void
        {
            var settings:Object=payload.loadingClock;
            var anchor:TextField=owner.helpTip as TextField;
            if (!settings || !settings.enabled || !settings.format || !anchor || !anchor.visible || !anchor.parent) return;
            var text:String="", escaped:Boolean=false, format:String=String(settings.format);
            for (var i:int=0;i<format.length;++i)
            {
                var token:String=format.charAt(i);
                if (!escaped && token==String.fromCharCode(92)) { escaped=true; continue; }
                text+=!escaped && payload.time && payload.time.hasOwnProperty(token) ? payload.time[token] : token;
                escaped=false;
            }
            // Match XVM's native helpTip anchor. Never use container.width:
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
    }
}
