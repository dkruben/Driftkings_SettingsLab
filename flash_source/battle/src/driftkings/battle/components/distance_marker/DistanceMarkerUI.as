package driftkings.battle.components.distance_marker
{
	import driftkings.battle.components.distance_marker.Config;
	import driftkings.battle.components.distance_marker.DistanceMarker;
	import driftkings.battle.base.BattleDisplayable;
	import flash.geom.Matrix;
	import driftkings.utils.ScreenTransform;
	import flash.events.Event;
	import flash.utils.getTimer;

	public class DistanceMarkerUI extends BattleDisplayable 
	{
		private static const REFRESH_DISTANCE_INTERVAL_MS:int = 100;
		private static const SORT_BY_DISTANCE_INTERVAL_MS:int = 500;

		public var py_requestFrameData:Function;
		private var _config:Config = new Config();
		private var _lastRefreshDistanceTimestamp:int = 0;
		private var _lastSortByDistanceTimestamp:int = 0;

		public function DistanceMarkerUI() 
		{
			super();
		}

		override protected function onPopulate() : void
		{
			super.onPopulate();
			mouseEnabled = mouseChildren = false;
			this.addEventListener(Event.ENTER_FRAME, this.onEnterFrame);
		}

		override protected function onDispose() : void
		{
			this.removeEventListener(Event.ENTER_FRAME, this.onEnterFrame);
			
			for (var i:int = 0; i < numChildren; ++i)
			{
				var marker:DistanceMarker = getMarkerAt(i);
				marker.disposeState();
			}
			this.removeChildren();
			this._config.disposeState();
			this._config = null;
			this.py_requestFrameData = null;
			super.onDispose();
		}

		private function onEnterFrame(event:Event) : void
		{
			if (!visible || this.py_requestFrameData == null)
			{
				return;
			}
			var serializedFrameData:Object = this.py_requestFrameData();
			this.updateAppPosition(serializedFrameData);
			this.updateMarkers(serializedFrameData);
			var observedVehicles:Array = serializedFrameData["observedVehicles"];
			observedVehicles.splice(0, observedVehicles.length);
		}

		public function as_applyConfig(serializedConfig:Object) : void
		{
			while (numChildren > 0) {
                var marker:DistanceMarker = getMarkerAt(0);
                removeChild(marker);
                marker.disposeState();
            }
            this._config.deserialize(serializedConfig);
		}

		public function as_isPointInMarker(mouseX:Number, mouseY:Number) : Boolean
		{
            if (!visible) return false;
			// hitTestPoint takes global stage coordinates, not component coordinates.
			mouseX *= _stagePerPixelX;
			mouseY *= _stagePerPixelY;
			for (var i:int = 0; i < this.numChildren; ++i)
			{
				var marker:DistanceMarker = this.getMarkerAt(i);
				
				if (marker.visible && marker.isInBounds(mouseX, mouseY))
				{
					return true;
				}
			}
			return false;
		}

        private var _stagePerPixelX:Number = 1;
        private var _stagePerPixelY:Number = 1;
        private function updateAppPosition(frame:Object):void
        {
            if (!parent || !stage || frame.screenWidth <= 0 || frame.screenHeight <= 0) return;
            _stagePerPixelX = stage.stageWidth / frame.screenWidth;
            _stagePerPixelY = stage.stageHeight / frame.screenHeight;
            transform.matrix = ScreenTransform.pixelsToParent(parent.transform.concatenatedMatrix,
                _stagePerPixelX, _stagePerPixelY);
        }

		private function updateMarkers(serializedFrameData:Object) : void
		{
			var observedVehicles:Array = serializedFrameData["observedVehicles"];
			if (this.numChildren == 0 && observedVehicles.length == 0)
			{
				return;
			}
			this.destroyInvalidMarkers(observedVehicles);
			this.createOrUpdateMarkers(observedVehicles);
			var currentTime:int = getTimer();
			if ((currentTime - this._lastSortByDistanceTimestamp) >= SORT_BY_DISTANCE_INTERVAL_MS)
			{
				this._lastSortByDistanceTimestamp = currentTime;
				this.sortMarkersByDistance();
			}
		}

		private function destroyInvalidMarkers(observedVehicles:Array) : void
		{			
			nextMarkerLabel:
			for (var i:int = 0; i < this.numChildren;)
			{
				var marker:DistanceMarker = this.getMarkerAt(i);
				
				for (var j:int = 0; j < observedVehicles.length; ++j)
				{
					if (marker.name == observedVehicles[j]["id"])
					{
						i += 1;
						continue nextMarkerLabel;
					}
				}
				this.removeChildAt(i);
				marker.disposeState();
			}
		}

		private function createOrUpdateMarkers(observedVehicles:Array) : void
		{
			var shouldRefreshDistance:Boolean = false;
			var currentTime:int = getTimer();
			if ((currentTime - this._lastRefreshDistanceTimestamp) >= REFRESH_DISTANCE_INTERVAL_MS)
			{
				this._lastRefreshDistanceTimestamp = currentTime;
				shouldRefreshDistance = true;
			}
			for (var i:int = 0; i < observedVehicles.length; ++i)
			{
				var observedVehicle:Object = observedVehicles[i];
				var marker:DistanceMarker = this.getOrCreateMarkerById(observedVehicle["id"]);
				var currentDistance:Number = observedVehicle["currentDistance"];
				var x:Number = observedVehicle["x"];
				var y:Number = observedVehicle["y"];
				var isVisible:Boolean = observedVehicle["isVisible"];
				if (shouldRefreshDistance || marker.currentDistance < 0.0)
				{
					marker.currentDistance = currentDistance;
				}
				marker.x = x;
				marker.y = y;
				if (marker.visible != isVisible)
				{
					marker.visible = isVisible;
				}
			}
		}

		private function sortMarkersByDistance() : void
		{
			for(var i:int = 1; i < this.numChildren; i++)
			{
				var j:int = i;
				while (j > 0 && getMarkerAt(j - 1).currentDistance < getMarkerAt(j).currentDistance)
				{
					this.swapChildrenAt( j - 1, j );
					--j;
				}
			}
		}

		private function getMarkerAt(index:int) : DistanceMarker
		{
			return this.getChildAt(index) as DistanceMarker;
		}

		private function getOrCreateMarkerById(vehicleID:String) : DistanceMarker
		{
			var marker:DistanceMarker = this.getChildByName(vehicleID) as DistanceMarker;
			if (marker != null)
			{
				return marker;
			}
			marker = new DistanceMarker(this);
			marker.name = vehicleID;
			this.addChild(marker);
			this._lastSortByDistanceTimestamp = 0;
			return marker;
		}

		public function get config() : Config
		{
			return this._config;
		}
	}
}