package driftkings.battle.components.ratings
{
    import flash.utils.Dictionary;
    import flash.utils.getQualifiedClassName;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.filters.DropShadowFilter;
    public class NativeState
    {
        private var changes:Dictionary = new Dictionary(true);
        private var texts:Dictionary = new Dictionary(true);
        private function remember(target:Object,key:String):void
        {
            if (!changes[target]) changes[target] = {};
            var record:Object=changes[target][key];
            if (!record) changes[target][key]=record={before:target[key],after:target[key]};
            else if (!equal(target[key],record.after)) record.before=target[key];
            record.used=true;
        }
        public function base(target:Object,key:String):*
        {
            if (!target) return null;
            var record:Object=changes[target] && changes[target][key];
            return record && equal(target[key],record.after) ? record.before : target[key];
        }
        public function setValue(target:Object, key:String, value:*):void
        {
            if (!target || !(key in target)) return;
            remember(target,key);
            var record:Object = changes[target];
            if (!record.hasOwnProperty(key)) record[key] = {before:target[key]};
            if (!equal(target[key],value)) target[key] = value;
            record[key].after = target[key];
        }
        private function restoreGeometry():void
        {
            for (var target:Object in changes)
            {
                var pending:Object = {};
                for (var key:String in changes[target])
                {
                    var value:Object = changes[target][key];
                    // Respect updates made by the client after our last render.
                    if (equal(target[key], value.after)) pending[key] = value.before;
                }
                // Re-enable autoSize before restoring geometry: right/center
                // sizing can move x and must not run after the final position.
                if (pending.hasOwnProperty("htmlText")) target.htmlText = pending.htmlText;
                if (pending.hasOwnProperty("autoSize")) target.autoSize = pending.autoSize;
                for (key in pending)
                    if (["htmlText","autoSize","width","height","x","y"].indexOf(key)<0) target[key] = pending[key];
                for each (key in ["width","height","x","y"])
                    if (pending.hasOwnProperty(key)) target[key] = pending[key];
            }
            changes = new Dictionary(true);
        }
        public function begin():void
        {
            for each (var group:Object in changes)
                for each (var property:Object in group) property.used=false;
            for each (var record:Object in texts) record.used=false;
        }
        private function restoreText(field:TextField,record:Object):void
        {
            var x:Number=field.x,y:Number=field.y,w:Number=field.width,h:Number=field.height;
            for each (var key:String in ["htmlText","autoSize","filters"])
                if (equal(field[key],record.after[key]) && !equal(field[key],record.before[key])) field[key]=record.before[key];
            field.width=w; field.height=h; field.x=x; field.y=y;
        }
        public function restore():void
        {
            restoreGeometry();
            for (var target:Object in texts) restoreText(target as TextField,texts[target]);
            texts=new Dictionary(true);
        }
        public function originalText(field:TextField):String
        {
            var record:Object=texts[field];
            var plain:String=field.text;
            return record && plain===record.renderedPlain ? record.plain : plain;
        }
        public function changed():Boolean
        {
            for (var target:Object in changes)
                for (var key:String in changes[target])
                    if (!equal(target[key],changes[target][key].after)) return true;
            for (var field:Object in texts)
                for each (key in ["htmlText","autoSize","filters"])
                    if (!equal(field[key],texts[field].after[key])) return true;
            return false;
        }
        public function commit():void
        {
            for (var target:Object in changes)
                for (var key:String in changes[target]) if (!changes[target][key].used)
                {
                    var property:Object=changes[target][key];
                    if (equal(target[key],property.after) && !equal(target[key],property.before)) target[key]=property.before;
                    delete changes[target][key];
                }
            for (var field:Object in texts) if (!texts[field].used)
            { restoreText(field as TextField,texts[field]); delete texts[field]; }
            // Coupled setters (HTML/width/autoSize) may change other properties.
            for (target in changes)
                for (key in changes[target]) changes[target][key].after = target[key];
        }
        private function equal(a:*,b:*):Boolean
        {
            if (a === b) return true;
            // DisplayObject.filters returns fresh copies on every read.
            if (!(a is Array) || !(b is Array) || a.length != b.length) return false;
            for (var i:int=0;i<a.length;++i)
            {
                if (getQualifiedClassName(a[i]) != getQualifiedClassName(b[i])) return false;
                for each (var key:String in ["distance","angle","color","alpha","blurX","blurY","strength","quality","inner","knockout","hideObject"])
                    if (key in a[i] && a[i][key] !== b[i][key]) return false;
            }
            return true;
        }
        public function text(field:TextField, value:*, shadow:Object = null):void
        {
            if (!field || value === null || value === undefined) return;
            var record:Object=texts[field];
            if (!record)
            {
                record={before:{htmlText:field.htmlText,autoSize:field.autoSize,filters:field.filters},after:{},plain:field.text};
                texts[field]=record;
            }
            else
            {
                // A native update wins over our previous output, including a
                // holder reused for a different player after a death/respawn.
                for each (var property:String in ["htmlText","autoSize","filters"])
                    if (!equal(field[property],record.after[property]))
                    {
                        record.before[property]=field[property];
                        if (property=="htmlText") record.plain=field.text;
                    }
            }
            record.used=true;
            for each (var key:String in ["x","y","width","height"]) remember(field,key);
            if (field.autoSize!=="none") field.autoSize="none";
            if (record.input!==String(value) || field.htmlText!==record.after.htmlText) field.htmlText=String(value);
            var shadowKey:String="";
            if (shadow) for each (key in ["enabled","distance","angle","color","alpha","blurX","blurY","blur","strength"])
                shadowKey+=key+":"+shadow[key]+";";
            if (record.shadowKey!==shadowKey || !equal(field.filters,record.after.filters)) field.filters=filters(shadow);
            record.input=String(value); record.shadowKey=shadowKey;
            record.after={htmlText:field.htmlText,autoSize:field.autoSize,filters:field.filters};
            record.renderedPlain=field.text;
        }
        public static function number(value:*, fallback:Number = 0):Number
        { var n:Number = Number(value); return value === null || value === undefined || !isFinite(n) ? fallback : n; }
        public static function flag(value:*):Boolean
        { return !(value === false || value === null || value === undefined || value === "false" || value === "" || value === 0 || value === "0"); }
        public static function color(value:*, fallback:uint = 0):uint
        { var s:String = String(value).replace("#", "0x"); var n:Number = Number(s); return isNaN(n) ? fallback : uint(n); }
        public static function filters(config:Object):Array
        {
            if (!config || config.enabled === false) return [];
            return [new DropShadowFilter(number(config.distance), number(config.angle), color(config.color),
                number(config.alpha,100)/100, number(config.blurX,number(config.blur,4)),
                number(config.blurY,number(config.blur,4)), number(config.strength,1), 2)];
        }
    }
}
