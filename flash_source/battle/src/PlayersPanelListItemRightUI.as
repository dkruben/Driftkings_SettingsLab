package
{
    import driftkings.battle.components.ratings.panelhook;
    import net.wg.gui.battle.random.views.stats.components.playersPanel.list.PlayersPanelListItem;

    // See PlayersPanelListItemLeftUI.
    public dynamic class PlayersPanelListItemRightUI extends PlayersPanelListItem
    {
        public var dkVehicleID:Number=NaN;

        public function PlayersPanelListItemRightUI() { super(); panelhook.register(this); }

        override protected function draw():void { super.draw(); panelhook.changed(); }

        override protected function updatePositions():void { super.updatePositions(); panelhook.changed(); }
    }
}
