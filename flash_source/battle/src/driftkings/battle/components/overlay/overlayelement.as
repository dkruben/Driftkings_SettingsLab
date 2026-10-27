package driftkings.battle.components.overlay {
import driftkings.utils.colorutils;
import driftkings.utils.imageloadercomponent;
import driftkings.utils.shadowutils;
import flash.display.Stage;
import flash.display.DisplayObjectContainer;
import flash.events.Event;
import flash.events.MouseEvent;
import flash.text.TextField;
import flash.text.TextFormat;
import flash.utils.getTimer;

public class overlayelement extends imageloadercomponent {
    public var alias:String;
    public var props:Object = {x:0, y:0, alignX:'left', alignY:'top', alpha:1, visible:true};
    private var kind:String;
    private var moved:Function;
    private var label:TextField;
    private var imagePath:String = '';
    private var fallback:Boolean = false;
    private var boxWidth:Number = 0;
    private var boxHeight:Number = 0;
    private var areaWidth:Number = 0;
    private var areaHeight:Number = 0;
    private var dragging:Boolean = false;
    private var dragStage:Stage;
    private var dragX:Number;
    private var dragY:Number;
    private var tweens:Object = {};
    private var dead:Boolean = false;

    public function overlayelement(id:String, type:String, callback:Function) {
        alias = id; kind = type; moved = callback;
        mouseChildren = true;
        if (kind == 'label') {
            label = new TextField();
            label.embedFonts = false;
            label.defaultTextFormat = new TextFormat('$FieldFont', 14, colorutils.parse("#FFFFFF"));
            label.selectable = false; label.mouseEnabled = false;
            addChild(label);
        }
        addEventListener(MouseEvent.MOUSE_DOWN, beginDrag);
    }
    public function apply(delta:Object, duration:Number):void {
        for (var key:String in delta) {
            if (duration > 0 && (key == 'x' || key == 'y' || key == 'alpha' || key == 'rotation')) {
                tweens[key] = {from:Number(props[key] || 0), to:Number(delta[key]), start:getTimer(), ms:duration * 1000};
            } else {
                delete tweens[key];
                props[key] = delta[key];
            }
        }
        if (duration > 0) addEventListener(Event.ENTER_FRAME, tick);
        if (!props.drag && dragging) finishDrag();
        render();
    }
    private function tick(event:Event):void {
        var remaining:Boolean = false;
        for (var key:String in tweens) {
            var t:Object = tweens[key];
            var ratio:Number = Math.min(1, (getTimer() - t.start) / t.ms);
            props[key] = t.from + (t.to - t.from) * ratio;
            if (ratio == 1) delete tweens[key]; else remaining = true;
        }
        render(); layout(areaWidth, areaHeight);
        if (!remaining) removeEventListener(Event.ENTER_FRAME, tick);
    }
    private function render():void {
        mouseEnabled = Boolean(props.drag);
        visible = props.visible !== false;
        alpha = Math.max(0, Math.min(1, Number(props.alpha)));
        rotation = Number(props.rotation || 0);
        if (label != null) {
            label.multiline = props.multiline !== false;
            label.wordWrap = Boolean(props.wordWrap);
            label.htmlText = props.text == null ? '' : String(props.text);
            label.width = props.width != null ? Number(props.width) : label.textWidth + 5;
            label.height = props.height != null ? Number(props.height) : label.textHeight + 5;
            boxWidth = label.width; boxHeight = label.height;
        } else {
            boxWidth = props.width != null ? Number(props.width) : (loader && loader.content ? loader.content.width : 0);
            boxHeight = props.height != null ? Number(props.height) : (loader && loader.content ? loader.content.height : 0);
        }
        if (kind == 'image') {
            var path:String = props.image == null ? '' : String(props.image);
            if (path != imagePath) {
                imagePath = path; fallback = false;
                loadImage(path, 0);
            }
            if (loader != null && loader.content != null) {
                loader.width = boxWidth; loader.height = boxHeight;
            }
        }
        var shadow:Object = props.shadow;
        if (shadow != null && shadow.enabled !== false) {
            // Overlays accept opacity and strength as 0..1 or 0..100.
            var opacity:Number = shadow.alpha == null ? 1 : Number(shadow.alpha);
            var strength:Number = shadow.strength == null ? 1 : Number(shadow.strength);
            filters = shadowutils.filters({distance:shadow.distance, angle:shadow.angle, color:shadow.color,
                alpha:(opacity > 1 ? opacity / 100 : opacity) * 100, blurX:shadow.blurX || 0, blurY:shadow.blurY || 0,
                strength:strength > 1 ? strength / 100 : strength, quality:shadow.quality || 1});
        } else filters = [];
        drawBackground();
    }
    private function drawBackground():void {
        graphics.clear();
        var bg:Object = props.customBackground;
        var margin:Number = bg == null ? 0 : Number(bg.margin || 0);
        var fill:Number = props.background ? 0.5 : 0;
        if (bg != null) fill = bg.fill === false ? 0 : Number(bg.alpha || 0);
        // Drag hit areas remain available without drawing their box outlines.
        // Also suppress outlines from older saved configurations.
        graphics.beginFill(bg == null ? colorutils.parse("#000000") : colorutils.parse(bg.color), fill);
        var w:Number = boxWidth, h:Number = boxHeight;
        // A zero-size parent can still be dragged using its children's visible bounds.
        if (kind == 'panel' && w == 0 && h == 0 && numChildren > 0) {
            var bounds:* = getBounds(this);
            graphics.drawRect(bounds.x, bounds.y, bounds.width, bounds.height);
        } else graphics.drawRoundRect(-margin, -margin, Math.max(1, w + margin * 2), Math.max(1, h + margin * 2), bg == null ? 0 : Number(bg.ellipseWidth || 0));
        graphics.endFill();
    }
    override protected function imageReady(event:Event):void {
        if (dead) return;
        render(); layout(areaWidth, areaHeight);
    }
    override protected function imageFailed(event:Event):void {
        if (!fallback && props.imageAlt && props.imageAlt != imagePath) {
            fallback = true; loadImage(String(props.imageAlt), 0);
        } else releaseImage();
    }
    private function anchor(align:String, area:Number, size:Number):Number {
        return align == 'center' ? (area - size) / 2 : (align == 'right' || align == 'bottom' ? area - size : 0);
    }
    public function layout(w:Number, h:Number):void {
        areaWidth = w; areaHeight = h;
        if (!dragging) {
            x = Number(props.x) + anchor(props.alignX, w, boxWidth);
            y = Number(props.y) + anchor(props.alignY, h, boxHeight);
            if (props.limit && !(parent is overlayelement)) {
                x = Math.max(0, Math.min(Math.max(0, w - boxWidth), x));
                y = Math.max(0, Math.min(Math.max(0, h - boxHeight), y));
            }
        }
        for (var i:int = 0; i < numChildren; i++) {
            var node:overlayelement = getChildAt(i) as overlayelement;
            if (node != null) node.layout(boxWidth, boxHeight);
        }
        sortChildren(this);
        if (kind == 'panel') drawBackground();
    }
    public static function sortChildren(container:DisplayObjectContainer):void {
        var elements:Array = [];
        for (var i:int = 0; i < container.numChildren; i++) {
            var node:overlayelement = container.getChildAt(i) as overlayelement;
            if (node != null) elements.push({node:node, index:Number(node.props.index || 0), order:i});
        }
        elements.sortOn(['index', 'order'], [Array.NUMERIC, Array.NUMERIC]);
        for each (var item:Object in elements) container.setChildIndex(item.node, container.numChildren - 1);
    }
    private function beginDrag(event:MouseEvent):void {
        if (!props.drag || stage == null) return;
        event.stopPropagation();
        dragX = x; dragY = y; dragging = true;
        delete tweens.x; delete tweens.y;
        startDrag();
        dragStage = stage;
        dragStage.addEventListener(MouseEvent.MOUSE_UP, endDrag);
        dragStage.addEventListener(Event.MOUSE_LEAVE, endDrag);
    }
    private function endDrag(event:Event):void { finishDrag(); }
    private function finishDrag():void {
        if (!dragging) return;
        stopDrag(); dragging = false;
        if (dragStage != null) {
            dragStage.removeEventListener(MouseEvent.MOUSE_UP, endDrag);
            dragStage.removeEventListener(Event.MOUSE_LEAVE, endDrag);
            dragStage = null;
        }
        props.x = Number(props.x) + x - dragX;
        props.y = Number(props.y) + y - dragY;
        layout(areaWidth, areaHeight);
        props.x = x - anchor(props.alignX, areaWidth, boxWidth);
        props.y = y - anchor(props.alignY, areaHeight, boxHeight);
        if (!dead && moved != null) moved(alias, props.x, props.y);
    }
    override public function dispose():void {
        dead = true; finishDrag();
        removeEventListener(MouseEvent.MOUSE_DOWN, beginDrag);
        removeEventListener(Event.ENTER_FRAME, tick);
        super.dispose();
        tweens = {}; moved = null; filters = [];
    }
}
}
