package {
import flash.display.DisplayObject;
import driftkings.battle.base.BattleDisplayable;
import driftkings.battle.components.overlay.OverlayUI;
import driftkings.battle.components.health.OwnHealthUI;
import driftkings.battle.components.flight_timer.FlightTimerUI;
import driftkings.battle.components.dispersion_timer.DispersionTimerUI;
import driftkings.battle.components.armor_calculator.ArmorCalculatorUI;
import driftkings.battle.components.minimap.MinimapCentred;
import driftkings.battle.components.sixth_sense.SixthSenseUI;
import driftkings.battle.components.distance_marker.DistanceMarkerUI;
import driftkings.battle.components.ratings.RatingScreens;
import net.wg.gui.battle.views.BaseBattlePage;
import net.wg.infrastructure.base.AbstractView;

// Required battle library, not a window: the native page owns every component.
public class DriftkingsBattle extends AbstractView {
    public function DriftkingsBattle() {
        super();
        AbstractView.prototype.as_DriftkingsCreate = function(aliases:Array):void {
            var classes:Object = {
                DriftkingsOverlay:OverlayUI, OwnHealthView:OwnHealthUI,
                FlightTimerView:FlightTimerUI, DispersionTimerView:DispersionTimerUI,
                ArmorCalculatorView:ArmorCalculatorUI, MinimapCentredView:MinimapCentred,
                SixthSenseView:SixthSenseUI, DistanceMarkerView:DistanceMarkerUI,
                DriftkingsRatingScreens:RatingScreens
            };
            for each (var alias:String in aliases) {
                if (this.isFlashComponentRegisteredS(alias)) continue;
                var type:Class = classes[alias] as Class;
                if (type == null || (!(this is BaseBattlePage) && alias != "DriftkingsRatingScreens")) continue;
                var component:DisplayObject = new type() as DisplayObject;
                var hud:BattleDisplayable = component as BattleDisplayable;
                if (hud) hud.battlePage = this as BaseBattlePage;
                this.addChild(component);
                if (this is BaseBattlePage) this.registerComponent(component, alias);
                else this.registerFlashComponentS(component, alias);
            }
            if (this is BaseBattlePage) this.updateStage(App.appWidth, App.appHeight);
        };
    }
}
}
