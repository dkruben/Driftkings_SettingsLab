package {
    import flash.desktop.NativeApplication;
    import flash.display.Sprite;
    import flash.filesystem.File;
    import flash.filesystem.FileMode;
    import flash.filesystem.FileStream;
    import flash.text.TextFormat;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import driftkings.utils.ScreenTransform;
    import driftkings.utils.Align;
    import driftkings.utils.TextExt;
    import driftkings.utils.Utils;
    import driftkings.utils.tween.Tween;
    import driftkings.utils.tween.TweenEvent;

    public class SharedUtilsTest extends Sprite {
        public function SharedUtilsTest() {
            try { run(); finish("PASS SharedUtilsTest", 0); }
            catch (error:Error) { finish(error.getStackTrace(), 1); }
        }
        private function check(value:Boolean, message:String):void {
            if (!value) throw new Error(message);
        }
        private function run():void {
            var parentGlobal:Matrix = new Matrix(1.25, 0, 0, 1.25, 175, 92);
            var physical:Point = new Point(1920, 1080);
            var local:Matrix = ScreenTransform.pixelsToParent(parentGlobal, 0.8, 0.8);
            var global:Point = parentGlobal.transformPoint(local.transformPoint(physical));
            check(Math.abs(global.x-1536)<0.001 && Math.abs(global.y-864)<0.001,
                  "distance marker projection cancels parent translation and UI scale");
            local = ScreenTransform.pixelsToParent(new Matrix(), 1, 1);
            global = local.transformPoint(physical);
            check(global.equals(physical), "unscaled screen retains physical coordinates");
            var target:Sprite = new Sprite();
            Align.position(target, 901, 601, Align.CENTER, Align.CENTER);
            check(target.x == 450 && target.y == 300, "odd dimensions preserve integer center");
            Align.position(target, 901, 601, Align.LEFT, Align.TOP);
            check(target.x == 0 && target.y == 0, "top left anchor");
            Align.position(target, 901, 601, Align.RIGHT, Align.BOTTOM);
            check(target.x == 901 && target.y == 601, "bottom right anchor");
            Align.position(target, 901, 601, "unknown", "unknown");
            check(target.x == 450 && target.y == 300, "unknown alignment keeps legacy center fallback");
            check(Utils.colorConvert("#Ab1234") == 0xAB1234 && Utils.colorConvert("Ab1234") == 0xAB1234,
                  "hex colors with and without prefix");
            Utils.updateColor(target, "#123456");
            check(target.transform.colorTransform.color == 0x123456, "display color applied");
            var first:TextExt = new TextExt(0, 0, null, Align.LEFT, this);
            var second:TextExt = new TextExt(0, 0, null, Align.LEFT, this);
            first.htmlText = "<font color='#FF0000'>HP</font><br>100";
            check(first.numLines == 2 && first.text.indexOf("100") >= 0, "HTML line breaks preserved");
            var originalSize:Object = second.defaultTextFormat.size;
            var custom:TextFormat = first.defaultTextFormat;
            custom.size = 30;
            first.defaultTextFormat = custom;
            check(second.defaultTextFormat.size == originalSize, "text styles remain independent");
            var a:Object = {value:0};
            var b:Object = {value:0};
            var one:Tween = new Tween(a, "value", 0, 100, 10);
            var two:Tween = new Tween(b, "value", 10, 20, 10);
            one.time = 5;
            check(a.value == 50 && b.value == 10, "animation targets independent");
            two.time = 5;
            check(b.value == 15 && a.value == 50, "second animation independent");
            var event:TweenEvent = new TweenEvent(TweenEvent.MOTION_CHANGE, 5, 50, true, true);
            var clone:TweenEvent = event.clone() as TweenEvent;
            check(clone != event && clone.time == 5 && clone.position == 50 && clone.bubbles && clone.cancelable,
                  "animation event clone retains payload");
            one.stop(); two.stop();
            check(!one.isPlaying && !two.isPlaying, "animations stop");
        }
        private function finish(message:String, code:int):void {
            var stream:FileStream = new FileStream();
            stream.open(new File(File.applicationDirectory.nativePath).resolvePath("result.txt"), FileMode.WRITE);
            stream.writeUTFBytes(message); stream.close();
            NativeApplication.nativeApplication.exit(code);
        }
    }
}
