package driftkings.battle.components.overlay {
import driftkings.battle.base.BattleDisplayable;
import flash.display.DisplayObjectContainer;

public class OverlayUI extends BattleDisplayable {
    public var onElementMoved:Function;
    private var nodes:Object = {};

    override protected function onPopulate():void {
        mouseEnabled = false;
        mouseChildren = true;
        super.onPopulate();
    }
    public function as_reset(items:Array):void {
        clear();
        for each (var item:Object in items) as_create(item.alias, item.kind, item.props);
    }
    public function as_create(alias:String, kind:String, props:Object):void {
        as_remove(alias);
        var node:OverlayElement = new OverlayElement(alias, kind, reportMove);
        nodes[alias] = node;
        var separator:int = alias.lastIndexOf('.');
        var owner:OverlayElement = separator < 0 ? null : nodes[alias.substr(0, separator)];
        (owner == null ? this : owner).addChild(node);
        node.apply(props, 0);
        layout();
    }
    public function as_update(alias:String, props:Object, duration:Number = 0):void {
        var node:OverlayElement = nodes[alias];
        if (node == null) return;
        node.apply(props, duration);
        layout();
    }
    public function as_remove(alias:String):void {
        var names:Array = [];
        for (var key:String in nodes) if (key == alias || key.indexOf(alias + '.') == 0) names.push(key);
        names.sort(function(a:String, b:String):Number { return b.length - a.length; });
        for each (key in names) {
            var node:OverlayElement = nodes[key];
            node.dispose();
            if (node.parent != null) node.parent.removeChild(node);
            delete nodes[key];
        }
    }
    private function reportMove(alias:String, x:Number, y:Number):void {
        if (onElementMoved != null) onElementMoved(alias, x, y);
    }
    private function layout():void {
        for (var i:int = 0; i < numChildren; i++) {
            var node:OverlayElement = getChildAt(i) as OverlayElement;
            if (node != null) node.layout(App.appWidth, App.appHeight);
        }
        OverlayElement.sortChildren(this);
    }
    override protected function onResized():void { layout(); }
    private function clear():void {
        var keys:Array = [];
        for (var key:String in nodes) keys.push(key);
        for each (key in keys) if (nodes[key] != null) as_remove(key);
    }
    override protected function onDispose():void {
        clear();
        onElementMoved = null;
        super.onDispose();
    }
}
}
