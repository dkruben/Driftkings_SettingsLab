package driftkings.battle.base
{
	import flash.events.Event;
	import net.wg.gui.battle.components.BattleUIDisplayable;
	import net.wg.gui.battle.views.BaseBattlePage;

	public class BattleDisplayable extends BattleUIDisplayable
	{
		public var battlePage:BaseBattlePage;

		private var hudVisible:Boolean = true;
		private var requestedVisible:Boolean = true;
		private var nativeVisible:Boolean = true;

		// Keep each module's visibility while TAB suppresses the shared HUD.
		override public function get visible():Boolean
		{
			return super.visible;
		}

		override public function set visible(value:Boolean):void
		{
			requestedVisible = value;
			super.visible = value && hudVisible && nativeVisible;
		}

		public function as_setBattleHudVisible(value:Boolean):void
		{
			hudVisible = value;
			super.visible = requestedVisible && hudVisible && nativeVisible;
		}

		override public function setCompVisible(value:Boolean):void
		{
			nativeVisible = value;
			_isCompVisible = value;
			updateVisibility();
		}

		override protected function updateVisibility():void
		{
			// Native loading/FUI visibility must not overwrite a module's own
			// state (for example a timer that expires while the HUD is hidden).
			super.visible = requestedVisible && hudVisible && nativeVisible;
		}

		public function BattleDisplayable()
		{
			super();
		}

		override protected function onPopulate() : void
		{
			super.onPopulate();
			this.battlePage.addEventListener(Event.RESIZE,this._handleResize);
		}

		override protected function onDispose() : void
		{
			if (this.battlePage) this.battlePage.removeEventListener(Event.RESIZE,this._handleResize);
			this.battlePage = null;
			super.onDispose();
		}

		private function _handleResize(param1:Event) : void
		{
			this.onResized();
		}

		protected function onResized() : void
		{}
	}
}
