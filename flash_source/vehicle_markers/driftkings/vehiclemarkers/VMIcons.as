package driftkings.vehiclemarkers
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.display.GradientType;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.filters.ColorMatrixFilter;
    import flash.filters.DropShadowFilter;
    import flash.geom.ColorTransform;
    import flash.geom.Matrix;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;

    /** Native icon and indicator placement (XVM positions); originals are restored before native updates. */
    public class VMIcons
    {
        public static var iconOriginals:Dictionary = new Dictionary(true);

        public static function applyIcon(icon:Object, options:Object, dead:Boolean, visible:Boolean = false):void
        {
            if (!icon || !options) return;
            if (!iconOriginals[icon]) iconOriginals[icon] = {x:icon.x, y:icon.y, scaleX:icon.scaleX, scaleY:icon.scaleY, alpha:icon.alpha};
            // Absolute values avoid accumulating scale or position on repeated native updates.
            if (options.x != null) icon.x = Number(options.x);
            if (options.y != null) icon.y = Number(options.y);
            icon.scaleX = icon.scaleY = Number(options.scale);
            icon.alpha = options.enabled || visible ? Number(options.alpha) / 100 * (dead ? Number(options.deadAlpha) / 100 : 1) : 0;
        }

        // XVM moves the class icon container (marker.marker) rather than the icon itself.
        public static function applyContainer(container:Object, options:Object):void
        {
            if (!container || !options || options.containerX == null && options.containerY == null) return;
            if (!iconOriginals[container]) iconOriginals[container] = {x:container.x, y:container.y};
            if (options.containerX != null) container.x = Number(options.containerX);
            if (options.containerY != null) container.y = Number(options.containerY);
        }

        // XVM GraphicsUtil.tint: blend the contour icon towards a colour by amount (0..100).
        public static function applyTint(icon:Object, tint:Object, color:String):void
        {
            if (!icon || !tint || !(Number(tint.amount) > 0)) return;
            var original:Object = iconOriginals[icon];
            if (original && !original.hasOwnProperty("colorTransform")) original.colorTransform = icon.transform.colorTransform;
            var amount:Number = Math.min(100, Number(tint.amount)) / 100;
            var value:uint = VMState.rgb(color);
            icon.transform.colorTransform = new ColorTransform(1 - amount, 1 - amount, 1 - amount, 1,
                ((value >> 16) & 0xFF) * amount, ((value >> 8) & 0xFF) * amount, (value & 0xFF) * amount, 0);
        }

        // The hover marker glow is its first child, as XVM uses it.
        public static function applyGlow(hover:Object, glow:Object):void
        {
            if (!hover || !glow || !(hover is DisplayObjectContainer) || DisplayObjectContainer(hover).numChildren < 1) return;
            var child:DisplayObject = DisplayObjectContainer(hover).getChildAt(0);
            if (!iconOriginals[child]) iconOriginals[child] = {x:child.x, y:child.y, alpha:child.alpha, visible:child.visible};
            child.visible = Boolean(glow.enabled);
            if (glow.x != null) child.x = Number(glow.x);
            if (glow.y != null) child.y = Number(glow.y);
            child.alpha = Number(glow.alpha) / 100;
        }

        public static function applyIndicator(icon:Object, options:Object, dead:Boolean):void
        {
            if (!icon || !options) return;
            if (!iconOriginals[icon]) iconOriginals[icon] = {x:icon.x, y:icon.y, scaleX:icon.scaleX, scaleY:icon.scaleY, filters:icon.filters};
            var original:Object = iconOriginals[icon];
            if (options.x != null) icon.x = Number(options.x);
            if (options.y != null) icon.y = Number(options.y);
            icon.scaleX = original.scaleX * options.scale; icon.scaleY = original.scaleY * options.scale;
            var alpha:Number = options.enabled ? options.alpha / 100 * (dead ? options.deadAlpha / 100 : 1) : 0;
            var filters:Array = original.filters.concat();
            filters.push(new ColorMatrixFilter([1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,alpha,0]));
            icon.filters = filters;
        }

        public static function indicators():Object
        {
            return {actionMarker:"actionMarker", hoverMarker:"vehicleMarkerHoverMC", vehicleStatusMarker:"statusContainer",
                damageIndicator:"criticalHit", damageIndicatorText:"criticalHitLabel", hitExplosion:"hitExplosion"};
        }

        public static function restoreIcon(icon:Object):void
        {
            if (!icon || !iconOriginals[icon]) return;
            var original:Object = iconOriginals[icon];
            for (var key:String in original)
            {
                // The contour tint lives on the transform, not on the icon itself.
                if (key == "colorTransform") icon.transform.colorTransform = original[key];
                else icon[key] = original[key];
            }
            delete iconOriginals[icon];
        }

        public static function restoreIcons(marker:Object):void
        {
            if (marker.vehicleMarkerHoverMC && marker.vehicleMarkerHoverMC.numChildren > 0)
                restoreIcon(marker.vehicleMarkerHoverMC.getChildAt(0));
            restoreIcon(marker.marker);
            if (marker.marker) restoreIcon(marker.marker.vehicleTypeIcon);
            restoreIcon(marker.levelIcon);
            restoreIcon(marker.vehicleIcon);
            var names:Object = indicators();
            for (var key:String in names) restoreIcon(marker[names[key]]);
        }

        public static function updateIcons(marker:Object, model:Object, dead:Boolean):void
        {
            var selected:Object = VMState.profile(marker, dead);
            var options:Object = selected ? selected.icons : null;
            if (!options || !options.enabled) return;
            var names:Object = indicators();
            for (var key:String in names) applyIndicator(marker[names[key]], options[key], dead);
            if (options.hoverMarker) applyGlow(marker.vehicleMarkerHoverMC, options.hoverMarker.glow);
            // Reacquire the timeline child after native state changes; never retain or reparent it.
            var type:Object = options["class"];
            if (marker.marker) applyContainer(marker.marker, type);
            if (marker.marker && marker.marker.vehicleTypeIcon)
            {
                // showSpeaker keeps the speaking icon visible even when the class icon is hidden.
                var speaking:Boolean = !dead && type && type.showSpeaker && ("isSpeaking" in marker) && marker.isSpeaking();
                applyIcon(marker.marker.vehicleTypeIcon, type, dead, speaking);
            }
            if (marker.levelIcon) applyIcon(marker.levelIcon, options.level, dead);
            if (marker.vehicleIcon && options.vehicle)
            {
                applyIcon(marker.vehicleIcon, options.vehicle, dead);
                if (options.vehicle.tint && model)
                    applyTint(marker.vehicleIcon, options.vehicle.tint, VMText.formatText(String(options.vehicle.tint.color), marker, model, dead));
            }
        }
    }
}
