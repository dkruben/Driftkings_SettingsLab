package {
import driftkings.battle.factory.componentfactory;
import driftkings.utils.fontlibrary;
import net.wg.gui.battle.views.BaseBattlePage;
import net.wg.infrastructure.base.AbstractView;

// One library, with a separate factory contract for each root surface.
public class driftkingsbattle extends AbstractView {
    private static function registerCreators():void {
        BaseBattlePage.prototype.as_DriftkingsCreate = function(aliases:Array):void {
            componentfactory.create(this, aliases, "battle");
            this.updateStage(App.appWidth, App.appHeight);
        };
        AbstractView.prototype.as_DriftkingsCreateRatings = function(aliases:Array):void {
            componentfactory.create(this, aliases, "ratings");
        };
    }

    { fontlibrary.initialize(); registerCreators(); }

    public function driftkingsbattle() {
        super();
        registerCreators();
    }
}
}
