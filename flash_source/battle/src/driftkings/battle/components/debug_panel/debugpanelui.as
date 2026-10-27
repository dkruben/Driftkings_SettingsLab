package driftkings.battle.components.debug_panel {
import driftkings.battle.base.battledisplayable;
import flash.display.DisplayObject;
import flash.display.DisplayObjectContainer;
import flash.text.TextField;
import flash.text.TextFieldAutoSize;
import scaleform.gfx.TextFieldEx;

// A separate DAAPI component; the native FPS/ping panel owns the clock field.
public class debugpanelui extends battledisplayable {
    private var clock:TextField = new TextField();
    private var clockEnabled:Boolean = false;

    public function debugpanelui() {
        super();
        clock.mouseEnabled = false;
        clock.selectable = false;
        clock.visible = false;
        TextFieldEx.setNoTranslate(clock, true);
    }

    public function as_setClock(text:String, enabled:Boolean):void {
        clockEnabled = enabled;
        // Accept existing HTML formats, then replace their style with WG's.
        clock.htmlText = text;
        clock.text = clock.text;
        layoutClock();
    }

    private function layoutClock():void {
        var page:Object = battlePage;
        var panel:DisplayObjectContainer = page && 'debugPanel' in page ? page.debugPanel as DisplayObjectContainer : null;
        var owner:Object = panel;
        var source:TextField = panel && 'pingTF' in owner ? owner.pingTF as TextField : null;
        if (source == null) { clock.visible = false; return; }
        if (clock.parent != panel) panel.addChild(clock);
        clock.defaultTextFormat = source.getTextFormat();
        clock.setTextFormat(source.getTextFormat());
        clock.autoSize = TextFieldAutoSize.LEFT;
        clock.multiline = false;
        clock.wordWrap = false;
        clock.embedFonts = source.embedFonts;
        clock.antiAliasType = source.antiAliasType;
        clock.filters = source.filters;
        clock.transform.colorTransform = source.transform.colorTransform;
        var right:Number = source.x + source.width;
        for each (var key:String in ['fpsTF', 'lagOnlineSpr', 'lagOfflineSpr']) {
            var item:DisplayObject = key in owner ? owner[key] as DisplayObject : null;
            if (item != null) right = Math.max(right, item.x + item.width);
        }
        clock.x = right + 8;
        clock.y = source.y;
        clock.alpha = source.alpha;
        clock.visible = clockEnabled && source.visible;
    }

    override protected function onResized():void { layoutClock(); }

    override protected function onDispose():void {
        if (clock.parent != null) clock.parent.removeChild(clock);
        clock = null;
        super.onDispose();
    }
}
}
