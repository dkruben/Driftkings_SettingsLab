package driftkings.battle.components.sixth_sense
{
    import driftkings.utils.colorutils;
	import flash.display.*;
	import flash.events.Event;
	import flash.events.IOErrorEvent;
	import flash.events.SecurityErrorEvent;
	import driftkings.utils.imageloadercomponent;
	import flash.net.URLRequest;
	import flash.text.TextFieldAutoSize;
	import flash.text.TextFormat;
	import flash.utils.clearInterval;
	import flash.utils.clearTimeout;
	import flash.utils.setInterval;
	import flash.utils.setTimeout;
	import driftkings.battle.base.battledisplayable;
	import net.wg.data.constants.generated.BATTLE_VIEW_ALIASES;
	import net.wg.gui.battle.views.BaseBattlePage;
	import driftkings.utils.constants;
	import driftkings.utils.textext;
	import driftkings.utils.tween.tween;
	import driftkings.battle.components.sixth_sense.radialprogressbar;
	import driftkings.utils.utils;

	public class sixthsenseui extends battledisplayable
	{
		private var loader:Loader;
		private var imageDisposed:Boolean = false;
		private var params:Object;
		private var timer:textext;
		private var _container:Sprite;
		private var hideAnimation:tween;
		private var showAnimation:tween;
		private var hideAnimation2:tween;
		private var POSITION_Y:Number;
		private var _image:Bitmap;
		private var radial_progress:radialprogressbar;
		private var timerId:Number;
		private var timeoutID:Number;
		private var progress:Number    = 10000;
		private var show_time:Number   = 10000;
		private var is_visible:Boolean = false;
		public var getSettings:Function;
		public var playSound:Function;
        public var onIconReady:Function;
		public var getTimerString:Function;
		[Embed(source = "error.png")]
		private var DefaultIcon:Class;

		public function sixthsenseui()
		{
			super();
			this.loader = new Loader();
			this.loader.contentLoaderInfo.addEventListener(Event.COMPLETE, this.imageLoaded);
			this.loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, this.onLoadError);
			this.loader.contentLoaderInfo.addEventListener(SecurityErrorEvent.SECURITY_ERROR, this.onLoadError);
		}

		override protected function onPopulate():void
		{
			super.onPopulate();
			this.params = this.getSettings();
			this.x = App.appWidth >> 1;
			this._container = new Sprite()
			this.addChild(this._container);
            var path:String;
            if (this.params.defaultIcon)
            {
                var name:String = String(this.params.defaultIconName);
                if (imageloadercomponent.validImageTail(name) && name.indexOf("/") < 0)
                    path = '../../gui/maps/icons/sixthsense/' + name + '.png';
            }
            else
            {
                path = imageloadercomponent.localImagePath(String(this.params.userIcon));
            }
            if (path == null)
            {
                this.onLoadError(null);
                return;
            }
            try { this.loader.load(new URLRequest(path)); }
            catch (error:Error) { this.onLoadError(null); }
		}

		override protected function onBeforeDispose():void
		{
			this.imageDisposed = true;
			super.onBeforeDispose();
			this.clearTimers();
			this.loader.contentLoaderInfo.removeEventListener(Event.COMPLETE, this.imageLoaded);
			this.loader.contentLoaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, this.onLoadError);
			this.loader.contentLoaderInfo.removeEventListener(SecurityErrorEvent.SECURITY_ERROR, this.onLoadError);
			utils.safeUnload(this.loader);
			this.loader = null;
			if (this.hideAnimation)
			{
				this.hideAnimation.dispose();
			}
			if (this.hideAnimation2)
			{
				this.hideAnimation2.dispose();
			}
			if (this.showAnimation)
			{
				this.showAnimation.dispose();
			}
			this.hideAnimation = null;
			this.hideAnimation2 = null;
			this.showAnimation = null;
			if (this._container)
			{
				this._container.removeChildren();
			}
			this.timer = null;
			this._container = null;
			App.utils.data.cleanupDynamicObject(this.params);
		}

		private function addAnimations(finish:Number):void
		{
			this.hideAnimation = new tween(this._container, "y", this.POSITION_Y, -finish, 0.5);
			this.hideAnimation2 = new tween(this._container, "alpha", 1.0, 0, 0.5);
			this.showAnimation = new tween(this._container, "alpha", 0, 1.0, 0.1);
			this._container.alpha = 0;
		}

		private function updateParams():void
		{
			var size:Number = this.params.iconSize || 90.0;
			var scale:Number = App.appHeight / 1080.0;
			var afterScaleWH:Number = Math.min(180.0, Math.ceil(size * scale));
			if (afterScaleWH % 2 != 0)
			{
				afterScaleWH += 1;
			}
			var half_size:Number = afterScaleWH >> 1;
			this.POSITION_Y = Math.ceil(App.appHeight / 7 + half_size);
			this._image.width = afterScaleWH;
			this._image.height = afterScaleWH;
			this._image.smoothing = true;
			this._image.x = -half_size;
			this._container.addChild(this._image);
			if (this.params.showTimer)
			{
				if (this.timer)
				{
					this._container.removeChild(this.timer);
					this.timer = null;
				}
				var textformat:TextFormat = new TextFormat("$TitleFont", Math.ceil(16 * scale), colorutils.parse("#FFFFFF"));
				var _y:Number = afterScaleWH - (this.params.showTimerGraphics ? -2 : 2);
				this.timer = new textext(0, _y, textformat, TextFieldAutoSize.CENTER, this._container);
			}
			if (!this.hideAnimation)
			{
				this.addAnimations(afterScaleWH);
			}
			else
			{
				// finish derives change from begin, so begin must be set first.
				this.hideAnimation.begin = this.POSITION_Y;
				this.hideAnimation.finish = -afterScaleWH;
			}
			
			if (!this.radial_progress)
			{
				this.radial_progress = this._container.addChild(new radialprogressbar()) as radialprogressbar;
			}
			var radius:Number = Math.round(this.params.showTimerGraphicsRadius * scale) || half_size;
			this.radial_progress.setParams(0, half_size, radius, scale, utils.colorConvert(this.params.showTimerGraphicsColor));
		}

		public function as_show(seconds:Number):void
		{
			if (!this._container || !this._image)
			{
				return;
			}
			if (this.hideAnimation && this.hideAnimation.isPlaying)
			{
				this.hideAnimation.stop();
				this.hideAnimation.rewind();
				if (this.hideAnimation2)
				{
					this.hideAnimation2.stop();
					this.hideAnimation2.rewind();
				}
			}
			if (seconds)
			{
				this.clearTimers();
				this.progress = this.show_time = seconds * 1000;
				if (this.params.showTimer)
				{
					this.timer.htmlText = this.getTimerString(seconds);
				}
				if (this.params.showTimerGraphics)
				{
					this.radial_progress.updateProgressBar(this.progress / this.show_time);
					this.timerId = setInterval(this.updateProgress, 100);
					
				}
				else
				{
					this.timeoutID = setTimeout(as_hide, this.show_time)
					if (this.params.playTickSound)
					{
						this.timerId = setInterval(this.playSound, 1000);
					}
				}
			}
			this._container.y = this.POSITION_Y;
			this.showAnimation.start();
			this.is_visible = true;
		}

		private function clearTimers():void
		{
			if (this.timerId)
			{
				clearInterval(this.timerId);
				this.timerId = 0;
			}
			if (this.timeoutID)
			{
				clearTimeout(this.timeoutID);
				this.timeoutID = 0;
			}
		}

		public function as_hide():void
		{
			this.clearTimers();
			if (this.is_visible && this.hideAnimation && this.hideAnimation2)
			{
				this.hideAnimation.start();
				this.hideAnimation2.start();
				this.is_visible = false;
			}
		}

		private function updateProgress():void
		{
			this.progress -= 100;
			this.radial_progress.updateProgressBar(this.progress / this.show_time);
			if (this.params.showTimer)
			{
				this.timer.htmlText = this.getTimerString(this.progress / 1000);
			}
			if (this.params.playTickSound && this.progress >= 1000 && this.progress % 1000 == 0)
			{
				this.playSound();
			}
			if (this.progress == 0)
			{
				this.as_hide();
			}
		}

		private function onLoadError(e:Event):void
		{
			if (this.imageDisposed || !this.loader) return;
			utils.safeUnload(this.loader);
			this._image = new DefaultIcon() as Bitmap;
			this.updateParams();
		}

		private function imageLoaded(e:Event):void
		{
			if (this.imageDisposed || !this.loader) return;
			this._image = this.loader.content as Bitmap;
			this.updateParams();
            if (this.onIconReady != null) this.onIconReady();
			this.loader.unload();
		}

		override protected function onResized():void
		{
			this.onResizeHandle(null);
		}

		public function onResizeHandle(event:Event):void
		{
			this.x = App.appWidth >> 1;
			if (this._image)
			{
				this.updateParams();
			}
		}
	}
}
