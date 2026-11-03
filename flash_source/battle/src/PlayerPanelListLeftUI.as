package
{
    import driftkings.battle.components.ratings.panelhook;
    import net.wg.data.VO.daapi.DAAPIVehicleInfoVO;
    import net.wg.gui.battle.random.views.stats.components.playersPanel.interfaces.IPlayersPanelListItemHolder;
    import net.wg.gui.battle.random.views.stats.components.playersPanel.list.PlayersPanelListLeft;

    // Same name as the client's linkage class. Tags each row with its vehicle, so the ratings
    // renderer finds a row's data by ID instead of matching player names.
    public dynamic class PlayerPanelListLeftUI extends PlayersPanelListLeft
    {
        public function PlayerPanelListLeftUI() { super(); }

        override public function setVehicleData(data:Vector.<DAAPIVehicleInfoVO>):void
        {
            super.setVehicleData(data);
            for each (var vo:DAAPIVehicleInfoVO in data)
            {
                var holder:IPlayersPanelListItemHolder=getHolderByVehicleID(vo.vehicleID);
                var item:Object=holder ? holder.getListItem() : null;
                if (item && "dkVehicleID" in item) item.dkVehicleID=vo.vehicleID;
            }
            panelhook.changed();
        }

        // Reordering moves rows without redrawing them.
        override public function updateOrder(order:Vector.<Number>):void { super.updateOrder(order); panelhook.changed(); }
    }
}
