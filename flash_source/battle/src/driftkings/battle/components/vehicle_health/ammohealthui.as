package driftkings.battle.components.vehicle_health {
import driftkings.battle.base.battledisplayable;
import driftkings.utils.colorutils;
import flash.display.Shape;
import flash.text.TextField;
import flash.text.TextFormat;
import net.wg.gui.battle.views.consumablesPanel.ConsumablesPanel;
import net.wg.gui.battle.views.consumablesPanel.events.ConsumablesPanelEvent;
import scaleform.gfx.TextFieldEx;

// Owned and disposed by the page's DAAPI registry; visually parented to the native
// panel so its transforms, animations, visibility and UI scale are inherited.
public class ammohealthui extends battledisplayable {
    private var panel:ConsumablesPanel;
    private var art:Shape = new Shape();
    private var label:TextField = new TextField();
    private var fraction:Number = 0;
    private var tint:uint = colorutils.parse('#3FC23A');
    private var skin:int = 0;
    private var healthEnabled:Boolean = false;

    public function ammohealthui() {
        super();
        mouseEnabled = false;
        mouseChildren = false;
        addChild(art);
        addChild(label);
        label.selectable = false;
        label.mouseEnabled = false;
        label.embedFonts = false;
        label.defaultTextFormat = new TextFormat('$FieldFont', 15, colorutils.parse('#F4F8F0'), true, null, null, null, null, 'center');
        TextFieldEx.setNoTranslate(label, true);
        visible = false;
    }

    override protected function onPopulate():void {
        super.onPopulate();
        attachPanel();
    }

    private function attachPanel():void {
        if (panel != null || battlePage == null) return;
        var owner:Object = battlePage;
        panel = 'consumablesPanel' in owner ? owner.consumablesPanel as ConsumablesPanel : null;
        if (panel == null) return; // Unsupported event panel: retain native UI.
        panel.addEventListener(ConsumablesPanelEvent.UPDATE_POSITION, panelMoved);
        panel.addChild(this);
    }

    public function as_setHealth(value:Number, text:String, color:uint, style:int, shown:Boolean):void {
        fraction = isNaN(value) ? 0 : Math.max(0, Math.min(1, value));
        tint = color;
        skin = Math.max(0, Math.min(2, style));
        healthEnabled = shown;
        label.text = text;
        attachPanel();
        drawBar();
    }

    private function panelMoved(event:ConsumablesPanelEvent):void { drawBar(); }
    override protected function onResized():void { attachPanel(); drawBar(); }

    private function drawBar():void {
        var w:Number = panel == null ? 0 : panel.basePanelWidth;
        var shown:Boolean = healthEnabled && w > 0;
        visible = shown;
        // Keep geometry current even while the inherited HUD visibility is off.
        if (!shown) return;
        x = 0;
        y = -34; // 26 px frame and 8 px clearance above the native slots.
        var edge:uint = skin == 0 ? colorutils.parse('#656B70') : (skin == 1 ? colorutils.parse('#A79B77') : colorutils.parse('#D0A54A'));
        var g:Object = art.graphics;
        g.clear();
        g.lineStyle(skin == 0 ? 1 : 2, edge, 1, true);
        g.beginFill(colorutils.parse('#101315'), .96);
        if (skin == 0) {
            g.drawRect(0, 0, w, 26);
        } else {
            g.moveTo(7, 0); g.lineTo(w - 7, 0); g.lineTo(w, 7);
            g.lineTo(w, 19); g.lineTo(w - 7, 26); g.lineTo(7, 26);
            g.lineTo(0, 19); g.lineTo(0, 7); g.lineTo(7, 0);
        }
        g.endFill();
        g.lineStyle();
        g.beginFill(colorutils.parse('#24282B'), 1); g.drawRect(5, 5, Math.max(0, w - 10), 16); g.endFill();
        g.beginFill(tint, .95); g.drawRect(5, 5, Math.max(0, w - 10) * fraction, 16); g.endFill();
        if (skin != 0) {
            g.beginFill(colorutils.parse('#FFFFFF'), .12); g.drawRect(5, 5, Math.max(0, w - 10) * fraction, 7); g.endFill();
        }
        if (skin == 2) {
            g.lineStyle(2, edge, 1);
            g.moveTo(12, 2); g.lineTo(32, 2);
            g.moveTo(w - 32, 24); g.lineTo(w - 12, 24);
        }
        label.x = 5; label.y = 2;
        label.width = Math.max(0, w - 10); label.height = 24;
    }

    override protected function onDispose():void {
        if (panel != null) panel.removeEventListener(ConsumablesPanelEvent.UPDATE_POSITION, panelMoved);
        panel = null;
        // Reparent before native disposal; do not leave an orphan in the panel.
        if (battlePage != null && parent != battlePage) battlePage.addChild(this);
        super.onDispose();
    }
}
}
