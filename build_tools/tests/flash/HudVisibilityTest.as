package {
    import flash.display.Sprite;
    import flash.display.BitmapData;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import flash.events.Event;
    import driftkings.battle.components.distance_marker.DistanceMarkerUI;
    import net.wg.gui.battle.views.BaseBattlePage;
    import flash.text.TextField;
    import flash.desktop.NativeApplication;
    import flash.filesystem.File;
    import flash.filesystem.FileStream;
    import flash.filesystem.FileMode;
    import driftkings.battle.base.BattleDisplayable;
    import driftkings.battle.components.overlay.OverlayElement;

    public class HudVisibilityTest extends Sprite {
        private var assertions:int = 0;
        public function HudVisibilityTest() {
            try { run(); finish("PASS HudVisibilityTest assertions=" + assertions, 0); }
            catch (error:Error) { finish("FAIL " + error.getStackTrace(), 1); }
        }
        private function check(value:Boolean, message:String):void {
            ++assertions;
            if (!value) throw new Error(message);
        }
        private function finish(message:String, code:int):void {
            var stream:FileStream = new FileStream();
            stream.open(new File(File.applicationDirectory.nativePath).resolvePath("result.txt"), FileMode.WRITE);
            stream.writeUTFBytes(message); stream.close();
            NativeApplication.nativeApplication.exit(code);
        }
        private function run():void {
            var page:BaseBattlePage = new BaseBattlePage();
            page.x=175; page.y=92; page.scaleX=page.scaleY=1.25;
            addChild(page);
            var distance:DistanceProbe = new DistanceProbe();
            page.addChild(distance);
            distance.battlePage=page;
            distance.as_applyConfig({decimalPrecision:0, textSize:16, textColor:0xFFFFFF,
                                     textAlpha:1, drawTextShadow:false});
            var requests:int=0;
            distance.py_requestFrameData=function():Object {
                ++requests;
                return {screenWidth:2560, screenHeight:1440,
                    observedVehicles:[{id:"7", x:400, y:250, currentDistance:125, isVisible:true}]};
            };
            distance.start();
            distance.dispatchEvent(new Event(Event.ENTER_FRAME));
            check(distance.numChildren==1, "shared distance component creates marker");
            var marker:Sprite=distance.getChildAt(0) as Sprite;
            var projected:Point=marker.localToGlobal(new Point());
            // Flash display positions are quantized to 1/20 pixel (twips).
            check(Math.abs(projected.x-400*stage.stageWidth/2560)<0.06 &&
                  Math.abs(projected.y-250*stage.stageHeight/1440)<0.06,
                  "distance coordinates follow physical screen despite page scale: " + projected + " expected=" + (400*stage.stageWidth/2560) + "," + (250*stage.stageHeight/1440));
            var label:TextField=marker.getChildAt(0) as TextField;
            var centre:Point=label.localToGlobal(new Point(label.width/2,label.height/2));
            var px:Number=centre.x*2560/stage.stageWidth, py:Number=centre.y*1440/stage.stageHeight;
            check(distance.as_isPointInMarker(px,py), "drag hit test uses physical pixel coordinates");
            marker.visible=false;
            check(!distance.as_isPointInMarker(px,py), "hidden marker cannot be dragged");
            distance.disposeProbe();
            distance.dispatchEvent(new Event(Event.ENTER_FRAME));
            check(requests==1 && distance.numChildren==0 && distance.py_requestFrameData==null,
                  "component disposal releases markers and stops frame callbacks");
            var hud:BattleDisplayable = new BattleDisplayable();
            addChild(hud);
            check(hud.visible, "initial visibility");
            hud.as_setBattleHudVisible(false);
            check(!hud.visible, "TAB hides active module");
            hud.visible = true;
            check(!hud.visible, "module update cannot reveal HUD over TAB");
            hud.as_setBattleHudVisible(true);
            check(hud.visible, "TAB close restores active module");
            hud.visible = false;
            hud.as_setBattleHudVisible(false);
            hud.as_setBattleHudVisible(true);
            check(!hud.visible, "disabled module stays hidden on close");
            hud.visible = true;
            hud.as_setBattleHudVisible(false);
            hud.visible = false;
            hud.as_setBattleHudVisible(true);
            check(!hud.visible, "timer expiry during TAB stays hidden");
            hud.visible = true;
            hud.setCompVisible(false);
            check(!hud.visible, "native loading hides component");
            hud.visible = false;
            hud.setCompVisible(true);
            check(!hud.visible, "native restoration preserves expired timer");
            hud.visible = true;
            check(hud.visible, "module can show again after native restoration");

            var box:OverlayElement = new OverlayElement("box", "panel", function(...args):void {});
            addChild(box);
            box.apply({width:80, height:25, drag:true, border:true,
                customBackground:{border:true, borderColor:0xFFFFFF, fill:false}}, 0);
            var pixels:BitmapData = new BitmapData(84, 29, true, 0);
            var transform:Matrix = new Matrix(); transform.translate(2, 2);
            pixels.draw(box, transform);
            check(pixels.getColorBoundsRect(0xFF000000, 0, false).isEmpty(), "old border flags draw no outline");
            check(box.mouseEnabled && box.hitTestPoint(20, 10), "invisible box still supports dragging");
            box.apply({customBackground:{border:true, fill:true, alpha:0.5, color:0x000000}}, 0);
            pixels.fillRect(pixels.rect, 0); pixels.draw(box, transform);
            check((pixels.getPixel32(20,10) >>> 24) > 0, "configured background fill is preserved");
            check(pixels.getPixel32(2,10) == pixels.getPixel32(20,10), "filled box has no brighter border");
            pixels.dispose();

            var info:OverlayElement = new OverlayElement("info", "label", function(...args):void {});
            addChild(info);
            info.apply({width:250, height:250, multiline:true,
                text:"<textformat leading='0'><font face='Arial' size='14' color='#FCFCFC'><p align='left'>" +
                     "<b>Vehicle</b><br>Reload 7.5 s<br><textformat tabstops='[95]'>Weight: 45 t\tView: 390 m</textformat>" +
                     "<br><textformat tabstops='[65,105,145]'>Hull:\t120\t80\t40</textformat>" +
                     "<br><textformat tabstops='[65,105,145]'>Turret:\t200\t120\t80</textformat>" +
                     "</p></font></textformat>"}, 0);
            var field:TextField = info.getChildAt(0) as TextField;
            check(field.numLines >= 5, "InfoPanel BR tags produce separate lines");
            for (var line:int = 1; line < 5; ++line) {
                var previous:int = field.getLineOffset(line - 1), current:int = field.getLineOffset(line);
                check(field.getCharBoundaries(current).y >= field.getCharBoundaries(previous).bottom - 1,
                      "InfoPanel text lines do not overlap: " + line);
            }
            var marks:OverlayElement=new OverlayElement('MarksOnGunBattle','label',function(...args):void{});
            var marksData:Object={mode:'detailed',scale:1,marks:'★★☆',percent:'86.43%',currentPercent:'86.35%',progress:.8643,
                delta:{text:'▲ +0.08%',direction:'positive'},combined:'2840',target:'3120',damage:'2500',assist:'340',labels:{},
                targets:[{percent:65,text:'1900'},{percent:85,text:'2600'},{percent:95,text:'3120'}],
                tokens:{background:0x121518,border:0xffffff,text:0xe8e4da,muted:0x969ba3,positive:0x67c56a,negative:0xe05454,accent:0xd98219,backgroundAlpha:.75,borderAlpha:.1}};
            marks.apply({width:300,height:185,text:'legacy custom',marks:marksData,background:false},0);
            check(!marks.getChildAt(0).visible,'modern card hides legacy label');
            var capture:BitmapData=new BitmapData(300,185,true,0);capture.draw(marks);
            var captureFile:FileStream=new FileStream();captureFile.open(new File(File.applicationDirectory.nativePath).resolvePath('marks-battle.argb'),FileMode.WRITE);
            captureFile.writeInt(300);captureFile.writeInt(185);captureFile.writeBytes(capture.getPixels(capture.rect));captureFile.close();capture.dispose();
            for each(var screen:Array in [[1920,1080],[2560,1440],[3440,1440],[3840,2160]]) {
                marks.apply({x:20,y:-20,alignX:'left',alignY:'bottom'},0);marks.layout(screen[0],screen[1]);
                check(marks.x==20 && marks.y==screen[1]-205,'Marks anchor respects viewport '+screen[0]);
            }
            marksData.scale=1.5;marks.apply({width:450,height:277.5,marks:marksData},0);
            check(Math.abs(marks.getChildAt(1).scaleX-1.5)<.001,'Marks respects existing percentage scale');
            marksData.scale=1;marks.apply({width:300,height:185,marks:marksData},0);

            var marksFields:* = marks.getChildAt(1);
            check(marksFields.numChildren >= 7,'detailed card fields render');
            var children:int=marksFields.numChildren;
            marksData.percent='95.00%';marksData.progress=.95;marksData.delta={text:'— 0.00%',direction:'zero'};
            marks.apply({marks:marksData},0);check(marksFields.numChildren==children,'modern update reuses text fields');
            marks.apply({marks:null},0);check(marks.getChildAt(0).visible,'legacy format remains available');
            check(TextField(marks.getChildAt(0)).text=='legacy custom','legacy custom format preserved');
            marks.dispose();

            var hull:int = field.text.indexOf("120");
            check(field.getCharBoundaries(hull).x >= 65, "InfoPanel armor first column uses tabstop");
            check(field.getCharBoundaries(hull + 4).x >= 105, "InfoPanel armor second column uses tabstop");
        }
    }
}
import driftkings.battle.components.distance_marker.DistanceMarkerUI;
internal class DistanceProbe extends DistanceMarkerUI {
        public function start():void { onPopulate(); }
        public function disposeProbe():void { onDispose(); }
    }
