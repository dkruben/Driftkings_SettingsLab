package driftkings.battle.components.overlay {
import flash.display.Sprite;
import flash.text.TextField;
import flash.text.TextFormat;

/** Displays only Python-supplied strings/ratios; no MoE estimations here. */
public class MarksCard extends Sprite {
    private var fields:Object = {};
    public function MarksCard() { mouseEnabled = false; mouseChildren = false; }
    private function put(key:String, text:String, x:Number, y:Number, width:Number, size:Number, color:uint, bold:Boolean=false):void {
        var field:TextField = fields[key];
        if (field == null) { field = new TextField(); field.selectable=false; field.mouseEnabled=false; fields[key]=field; addChild(field); }
        field.visible=true; field.x=x; field.y=y; field.width=width; field.height=size+8;
        field.defaultTextFormat=new TextFormat('$FieldFont',size,color,bold);
        field.text=text;
    }
    public function render(data:Object, width:Number, height:Number):void {
        for each (var old:TextField in fields) old.visible=false;
        graphics.clear();
        var tokens:Object=data.tokens, scale:Number=Number(data.scale || 1);
        scaleX=scaleY=scale;
        width/=scale; height/=scale;
        if(data.background !== false) {
            graphics.lineStyle(1,uint(tokens.border),Number(tokens.borderAlpha));
            graphics.beginFill(uint(tokens.background),Number(tokens.backgroundAlpha));
            graphics.drawRoundRect(0,0,width,height,8,8);graphics.endFill();
        }
        var y:Number=8;
        if(data.showMarks !== false) { put('marks',String(data.marks),12,y,width-24,17,uint(tokens.accent),true);y+=23; }
        put('percent',String(data.percent),12,y,width*.52,22,uint(tokens.text),true);
        if(data.showDelta !== false) {
            var direction:String=data.delta.direction;
            var deltaColor:uint=direction=='positive'?uint(tokens.positive):direction=='negative'?uint(tokens.negative):uint(tokens.muted);
            put('delta',String(data.delta.text),width*.53,y+4,width*.47-12,13,deltaColor);
        }
        y+=30;
        if(data.showProgress !== false) {
            graphics.lineStyle();graphics.beginFill(uint(tokens.border),.12);graphics.drawRect(12,y,width-24,4);graphics.endFill();
            graphics.beginFill(uint(tokens.accent));graphics.drawRect(12,y,(width-24)*Number(data.progress),4);graphics.endFill();
            graphics.beginFill(uint(tokens.text));graphics.drawCircle(12+(width-24)*Number(data.progress),y+2,3);graphics.endFill();
            graphics.lineStyle(1,uint(tokens.muted),.75);
            for each(var limit:Number in [65,85,95]) { var tick:Number=12+(width-24)*limit/100;graphics.moveTo(tick,y-2);graphics.lineTo(tick,y+7);put('milestone'+limit,String(limit),tick-9,y+7,24,8,uint(tokens.muted)); }
            graphics.lineStyle();y+=23;
        }
        if(data.showDamage !== false || data.showTargets !== false) {
            var damage:String=data.showDamage !== false?String(data.combined):'';
            if(data.showTargets !== false) damage+=(damage?' / ':'')+String(data.target);
            var caption:String=data.mode=='compact'?'':String(data.labels.combined || 'Combined')+'  ';
            put('combined',caption+damage,12,y,width-24,13,uint(tokens.text));y+=23;
        }
        if(data.mode=='detailed') {
            put('current',String(data.labels.current || 'Current MoE')+' '+data.currentPercent,12,y,width-24,11,uint(tokens.muted));y+=21;
            if(data.showDamage !== false) { put('details',String(data.labels.damage || 'Damage')+' '+data.damage+'  '+String(data.labels.assist || 'Assist')+' '+data.assist,12,y,width-24,11,uint(tokens.muted));y+=21; }
            if(data.showTargets !== false) {
                var targets:String='';
                for each(var target:Object in data.targets) targets+=(targets?'   ':'')+target.percent+'% '+target.text;
                put('targets',targets,12,y,width-24,11,uint(tokens.muted));
            }
        }
    }
}
}
