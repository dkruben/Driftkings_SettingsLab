package driftkings.battle.components.health
{
   import driftkings.utils.constants;
   import driftkings.battle.components.health.progressbar;
   import driftkings.utils.align;
   import flash.text.TextFieldAutoSize;
   import driftkings.battle.base.crosshairdisplayable;
   
   public class ownhealthui extends crosshairdisplayable
   {
      private var own_health:progressbar;
      public var getAVGColor:Function;
      public var getSettings:Function;
      
      public function ownhealthui()
      {
         super();
         this.alignX = align.CENTER;
         this.alignY = align.BOTTOM;
      }
      
      override protected function onPopulate() : void
      {
         super.onPopulate();
         this.applySettings();
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

         this.alignX = settings.alignX || align.CENTER;
         this.alignY = settings.alignY || align.BOTTOM;

         if(this.own_health == null)
         {
            this.own_health = new progressbar(0, 0, 180, 22, this.getAVGColor(), settings.colors.bgColor, 0.2);
            this.own_health.setOutline(180, 22);
            this.own_health.addTextField(90, -3, TextFieldAutoSize.CENTER, constants.middleText);
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
   }
}
