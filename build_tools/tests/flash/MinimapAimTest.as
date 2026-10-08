package {
    import flash.display.Sprite;
    import flash.display.Loader;
    import flash.display.Bitmap;
    import flash.display.BitmapData;
    import flash.text.TextField;
    import flash.events.Event;
    import flash.events.IOErrorEvent;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import flash.desktop.NativeApplication;
    import flash.filesystem.File;
    import flash.filesystem.FileStream;
    import flash.filesystem.FileMode;
    import driftkings.battle.components.minimap.ArtilleryAim;
    import driftkings.battle.components.minimap.VehicleLabel;
    import driftkings.battle.components.minimap.MapGeometry;

    public class MinimapAimTest extends Sprite {
        private var assertions:int = 0;
        private var aim:ArtilleryAim = new ArtilleryAim();
        private var png:String;
        private var variant:int = 0;
        public function MinimapAimTest() {
            png = new File(File.applicationDirectory.nativePath).resolvePath("../../res/res/gui/maps/Driftkings/Minimap/MinimapAim_0.png").url;
            aim.configure({enabled:true, scale:50, alpha:80, src:png});
            Loader(aim.getChildAt(0)).contentLoaderInfo.addEventListener(Event.COMPLETE, loaded);
            Loader(aim.getChildAt(0)).contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,
                function(e:Event):void { finish("FAIL PNG could not be loaded", 1); });
        }
        private function loaded(event:Event):void {
            try { run(); testLabels(); testVariant(); }
            catch (error:Error) { finish("FAIL " + error.getStackTrace(), 1); }
        }
        private function testVariant():void {
            if (++variant > 6) { testMissingImage(); return; }
            aim.configure({enabled:true, scale:50, alpha:100, src:png.replace("_0.png", "_" + variant + ".png")});
            aim.attach(this);
            var image:Loader = aim.getChildAt(0) as Loader;
            image.contentLoaderInfo.addEventListener(Event.COMPLETE, function(event:Event):void {
                try {
                    check(Math.abs(image.width - 25) < .01 && Math.abs(image.height - 25) < .01,
                          "high resolution variant has standard footprint");
                    check(Math.abs(image.x + 12.5) < .01 && Math.abs(image.y + 12.5) < .01,
                          "high resolution variant centered");
                    check(aim.visible && Math.abs(aim.width - 12.5) < .01, "user scale applied after normalization");
                    testVariant();
                } catch (error:Error) { finish("FAIL " + error.getStackTrace(), 1); }
            });
            image.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR,
                function(event:Event):void { finish("FAIL missing variant " + variant, 1); });
        }
        private function testMissingImage():void {
            aim.configure({enabled:true, scale:50, alpha:100, src:png + ".missing.png"});
            aim.attach(this);
            Loader(aim.getChildAt(0)).contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, function(e:Event):void {
                try {
                    check(!aim.visible && aim.numChildren == 0 && !aim.hasEventListener(Event.ENTER_FRAME),
                          "missing PNG is hidden without frame callbacks");
                    aim.dispose();
                    finish("PASS MinimapAimTest assertions=" + assertions, 0);
                } catch (error:Error) { finish("FAIL " + error.getStackTrace(), 1); }
            });
        }
        private function check(value:Boolean, message:String):void {
            ++assertions;
            if (!value) throw new Error(message);
        }
        private function testLabels():void {
            var native:TextField = new TextField(); native.textColor = 0x80D639; native.x = 12; native.y = -4;
            var label:VehicleLabel = new VehicleLabel(); addChild(label);
            var options:Object = {alternative:false, labels:{enabled:true, x:5, y:3, align:"left", shadow:true,
                fontSize:10, alpha:90, customColors:false, compactLength:8},
                health:{visibility:"key", mode:"value", fontSize:9, x:0, y:12, width:30, height:3}};
            var data:Object = {text:"VeryLongVehicle",group:"enemy",state:"alive",hp:500,percent:50,alpha:100};
            label.update(data, options, native);
            check(label.caption.text == data.text && label.x == 17 && label.y == -1,"label format and offsets");
            check(!label.hp.visible,"HP key mode hidden normally");
            check(label.caption.textColor == 0xF05050,"enemy uses color scheme rather than green native field default");
            check(label.filters.length == 1,"shadow enabled");
            label.compact(true); check(label.caption.text == "VeryLo..","compact label");
            label.compact(false); check(label.caption.text == data.text,"full label restored");
            options.alternative = true; label.update(data,options,native);
            check(label.hp.visible && label.hp.text == "500","held key reveals known HP");
            native.visible=false;label.update(data,options,native);
            check(!label.caption.visible && label.hp.visible,"native names off does not hide configured HP");
            native.visible=true;
            data = {text:"Tank",group:"enemy",state:"lost",hp:"--",percent:"--",alpha:25};
            label.update(data,options,native);
            check(label.hp.text == "--" && Math.abs(label.alpha-.25)<.01,"unknown health and fading");
            options.health.mode="bar";
            data = {text:"Tank",group:"enemy",state:"lost",hp:"--",percent:"--",alpha:25};
            label.update(data,options,native);
            check(!label.hp.visible && !label.getChildAt(2).visible,"unknown HP draws no fabricated bar");
            data = {text:"Tank",group:"enemy",state:"alive",hp:500,percent:50,alpha:100};
            label.update(data,options,native);
            check(label.getChildAt(2).visible,"known HP draws bar");
            data = {text:"Tank",group:"enemy",state:"dead",hp:0,percent:0,alpha:100};
            label.update(data,options,native);
            check(!label.hp.visible && !label.getChildAt(2).visible,"dead vehicle hides HP");
            label.dispose();check(!label.parent,"label detached on disposal");
            var shape:Sprite = new Sprite();
            var style:Object = {thickness:1,dash:5,gap:5};
            MapGeometry.stroke(shape.graphics,style,0xFFFFFF,100);
            MapGeometry.line(shape.graphics,50,style);
            var pixels:BitmapData = new BitmapData(100,100,true,0);
            var matrix:Matrix = new Matrix();matrix.translate(50,70);pixels.draw(shape,matrix);
            check(pixels.getPixel32(50,68)!=0 && pixels.getPixel32(50,62)==0,"dashed line includes gaps");
            shape.graphics.clear();MapGeometry.stroke(shape.graphics,style,0xFFFFFF,100);
            MapGeometry.circle(shape.graphics,25,style);pixels.fillRect(pixels.rect,0);pixels.draw(shape,matrix);
            check(!pixels.getColorBoundsRect(0xFF000000,0,false).isEmpty(),"dashed circle renders");
            pixels.dispose();
        }
        private function finish(message:String, code:int):void {
            var stream:FileStream = new FileStream();
            stream.open(new File(File.applicationDirectory.nativePath).resolvePath("result.txt"), FileMode.WRITE);
            stream.writeUTFBytes(message); stream.close();
            NativeApplication.nativeApplication.exit(code);
        }
        private function frame(aim:ArtilleryAim):void { aim.dispatchEvent(new Event(Event.ENTER_FRAME)); }
        private function stable(aim:ArtilleryAim, anchor:Sprite):void {
            frame(aim);
            var m:Matrix = aim.transform.concatenatedMatrix;
            check(Math.abs(m.a - .5) < .0001 && Math.abs(m.d - .5) < .0001 &&
                  Math.abs(m.b) < .0001 && Math.abs(m.c) < .0001, "screen scale and rotation");
            check(Point.distance(aim.localToGlobal(new Point()), anchor.localToGlobal(new Point())) < .001,
                  "center follows native strategic position");
        }
        private function run():void {
            var map:Sprite = new Sprite(); addChild(map);
            var anchor:Sprite = new Sprite(); map.addChild(anchor);
            var loadedImage:Loader = aim.getChildAt(0) as Loader;
            check(loadedImage.content is Bitmap, "PNG loaded as bitmap");
            check(loadedImage.x == -loadedImage.contentLoaderInfo.width / 2 &&
                  loadedImage.y == -loadedImage.contentLoaderInfo.height / 2, "PNG centered at native anchor");
            aim.configure({enabled:true, scale:50, alpha:80, src:png});
            check(aim.getChildAt(0) == loadedImage, "unchanged path reuses loaded image");
            map.scaleX = 2; map.scaleY = 3; map.rotation = 25;
            anchor.x = 120; anchor.y = 50; anchor.rotation = -70;
            aim.attach(anchor);
            check(aim.visible && aim.hasEventListener(Event.ENTER_FRAME), "attached and running");
            check(!aim.mouseEnabled && !aim.mouseChildren, "does not intercept minimap clicks");
            check(Math.abs(aim.alpha - .8) < .01 && aim.width > 0, "opacity and graphics");
            stable(aim, anchor);
            anchor.x = 350; anchor.y = -80; stable(aim, anchor);
            map.scaleX = .7; map.scaleY = .7; stable(aim, anchor);
            anchor.visible = false; frame(aim); check(!aim.visible, "camera off hides aim");
            anchor.visible = true; frame(aim); check(aim.visible, "camera on restores aim");
            map.scaleX = 0; frame(aim); check(!aim.visible, "singular transform hidden");
            map.scaleX = .7; stable(aim, anchor); check(aim.visible, "transform recovered");
            map.removeChild(anchor);
            check(!aim.hasEventListener(Event.ENTER_FRAME), "no frame callback off stage");
            map.addChild(anchor); stable(aim, anchor);
            var replacement:Sprite = new Sprite(); map.addChild(replacement);
            aim.attach(replacement);
            check(anchor.numChildren == 0 && replacement.numChildren == 1, "recreated native entry");
            aim.attach(replacement); check(replacement.numChildren == 1, "no duplicate reticle");
            aim.configure({enabled:false});
            check(!aim.parent && !aim.hasEventListener(Event.ENTER_FRAME), "disabled detaches and stops");
            check(aim.numChildren == 0, "disabled unloads PNG");
            var pending:ArtilleryAim = new ArtilleryAim();
            pending.configure({enabled:true, scale:50, alpha:100, src:png}); pending.attach(anchor);
            check(!pending.visible, "loading image stays hidden");
            pending.dispose();
            check(!pending.parent && pending.numChildren == 0 && !pending.hasEventListener(Event.ENTER_FRAME),
                  "dispose cancels pending image and callbacks");
        }
    }
}
