package driftkings.battle.components.health
{
   import driftkings.utils.Constants;
   import driftkings.battle.components.health.ProgressBar;
   import driftkings.utils.Align;
   import flash.text.TextFieldAutoSize;
   import driftkings.battle.base.BattleDisplayable;
   
   public class OwnHealthUI extends BattleDisplayable
   {
      private var own_health:ProgressBar;
      public var getAVGColor:Function;
      public var getSettings:Function;
	  
      private var alignX:String = Align.CENTER;
      private var alignY:String = Align.BOTTOM;
      
      public function OwnHealthUI()
      {
         super();
      }
      
      override protected function configUI() : void
      {
         super.configUI();
         this.tabEnabled = false;
         this.tabChildren = false;
         this.mouseEnabled = false;
         this.mouseChildren = false;
         this.buttonMode = false;
      }
      
      override protected function onPopulate() : void
      {
         super.onPopulate();
         this.applySettings();
      }
      
      private function updatePosition() : void
      {
         Align.position(this, App.appWidth, App.appHeight, this.alignX, this.alignY);
      }

      private function applySettings() : void
      {
         if(this.getSettings == null)
         {
            return;
         }

         var settings:Object = this.getSettings();
         if(settings == null)
         {
            return;
         }

         this.alignX = settings.alignX || Align.CENTER;
         this.alignY = settings.alignY || Align.BOTTOM;

         if(this.own_health == null)
         {
            this.own_health = new ProgressBar(0, 0, 180, 22, this.getAVGColor(), settings.colors.bgColor, 0.2);
            this.own_health.setOutline(180, 22);
            this.own_health.addTextField(90, -3, TextFieldAutoSize.CENTER, Constants.middleText);
            this.addChild(this.own_health);
         }
         else
         {
            this.own_health.updateColor(this.getAVGColor());
         }

         this.own_health.x = Number(settings.x) - 90;
         this.own_health.y = Number(settings.y);
         this.updatePosition();
      }

      override protected function onResized() : void
      {
         this.updatePosition();
      }
      
      override protected function onBeforeDispose() : void
      {
         super.onBeforeDispose();
         if(this.own_health)
         {
            this.own_health.remove();
            this.own_health = null;
         }
      }
      
      public function as_setOwnHealth(scale:Number, text:String, color:String) : void
      {
         if (this.own_health)
         {
            this.own_health.setNewScale(scale);
            this.own_health.setText(text);
            this.own_health.updateColor(color);
         }
      }
      
      public function as_BarVisible(isVisible:Boolean) : void
      {
         if(this.own_health)
         {
            this.own_health.visible = isVisible;
         }
      }

      public function as_updateSettings() : void
      {
         this.applySettings();
      }
      
      public function as_onCrosshairPositionChanged(x:Number, y:Number) : void
      {
         this.x = x;
         this.y = y;
      }
   }
}
