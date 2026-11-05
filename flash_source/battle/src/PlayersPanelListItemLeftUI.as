package
{
    import driftkings.battle.components.ratings.panelhook;
    import net.wg.gui.battle.random.views.stats.components.playersPanel.list.PlayersPanelListItem;

    // Same name as the client's linkage class in playersPanel.swf. Loaded first, the client's
    // row symbols bind to this class, which only reports when the client redraws the row.
    public dynamic class PlayersPanelListItemLeftUI extends PlayersPanelListItem
    {
        public var dkVehicleID:Number=NaN;

        public function PlayersPanelListItemLeftUI() { super(); panelhook.register(this); }

        override protected function draw():void { super.draw(); panelhook.changed(); }

        // Mode changes and name widths reposition the row outside draw().
        override protected function updatePositions():void { super.updatePositions(); panelhook.changed(); }
    }
}
