package driftkings.battle.factory
{
    import flash.display.DisplayObject;
    import driftkings.battle.base.BattleDisplayable;
    import net.wg.gui.battle.views.BaseBattlePage;

    public class ComponentFactory
    {
        public static function create(host:Object, aliases:Array, surface:String):void
        {
            if (aliases == null || (surface == "battle" && !(host is BaseBattlePage))) return;
            var classes:Object = ComponentCatalog.classes(surface);
            for each (var alias:String in aliases)
            {
                if (host.isFlashComponentRegisteredS(alias)) continue;
                var type:Class = classes[alias] as Class;
                if (type == null) continue;
                var component:DisplayObject = new type() as DisplayObject;
                var hud:BattleDisplayable = component as BattleDisplayable;
                if (hud) hud.battlePage = host as BaseBattlePage;
                host.addChild(component);
                // Preserve the client's verified public DAAPI registration contract.
                host.registerFlashComponentS(component, alias);
            }
        }
    }
}
