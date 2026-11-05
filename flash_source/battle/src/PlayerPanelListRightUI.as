package
{
    import driftkings.battle.components.ratings.panelhook;
    import net.wg.data.VO.daapi.DAAPIVehicleInfoVO;
    import net.wg.gui.battle.random.views.stats.components.playersPanel.interfaces.IPlayersPanelListItemHolder;
    import net.wg.gui.battle.random.views.stats.components.playersPanel.list.PlayersPanelListRight;

    // See PlayerPanelListLeftUI.
    public dynamic class PlayerPanelListRightUI extends PlayersPanelListRight
    {
        public function PlayerPanelListRightUI() { super(); }

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

        override public function updateOrder(order:Vector.<Number>):void { super.updateOrder(order); panelhook.changed(); }
    }
}
