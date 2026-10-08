package
{
    import flash.display.MovieClip;
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.desktop.NativeApplication;
    import flash.filters.DropShadowFilter;
    import flash.filesystem.File;
    import flash.filesystem.FileStream;
    import flash.filesystem.FileMode;
    import driftkings.battle.components.ratings.NativeState;
    import driftkings.battle.components.ratings.PanelRenderer;
    import driftkings.battle.components.ratings.PanelRow;
    import driftkings.battle.components.ratings.ExtraFields;

    public class PanelRenderTest extends Sprite
    {
        private var nativeState:NativeState=new NativeState();
        private var renderer:PanelRenderer=new PanelRenderer(nativeState);
        private var panel:MovieClip=new MovieClip();
        private var payload:Object={mode:"large",panel:{enabled:true},rows:[]};
        private var items:Array=[];
        private var assertions:int=0;
        public function PanelRenderTest()
        {
            try { run(); finish("PASS PanelRenderTest assertions="+assertions,0); }
            catch (error:Error) { finish("FAIL "+error.getStackTrace(),1); }
        }
        private function finish(message:String,code:int):void
        {
            var stream:FileStream=new FileStream();
            stream.open(new File(File.applicationDirectory.nativePath).resolvePath("result.txt"),FileMode.WRITE);
            stream.writeUTFBytes(message); stream.close();
            NativeApplication.nativeApplication.exit(code);
        }
        private function check(value:Boolean,message:String):void
        { ++assertions; if (!value) throw new Error(message); }
        private function makeItem(id:int):MovieClip
        {
            var item:MovieClip=new MovieClip(); item.holderItemID=id; item.y=(id%15)*25;
            for each (var name:String in ["playerNameFullTF","playerNameCutTF","vehicleTF","fragsTF"])
            { var text:TextField=new TextField(); text.width=80; text.height=25; item[name]=text; item.addChild(text); }
            item.playerNameFullTF.text="Player"+id; item.vehicleTF.text="Tank"+id; item.fragsTF.text="0";
            for each (name in ["vehicleIcon","vehicleLevel","badge","prestigeLevel","hit","spottedIndicator","bg","selfBg","hpBarPlayersPanelListItem"])
            { var sprite:Sprite=new Sprite(); sprite.graphics.beginFill(0); sprite.graphics.drawRect(0,0,16,16); item[name]=sprite; item.addChild(sprite); }
            return item;
        }
        private function row(id:int,hp:int=100):Object
        {
            var cfg:Object={enabled:true,standardFields:["frags","nick","vehicle"],
                nickFormatLeft:"<b>Player"+id+"</b>",nickFormatRight:"<b>Player"+id+"</b>",
                vehicleFormatLeft:"Tank"+id,vehicleFormatRight:"Tank"+id,
                fragsFormatLeft:"0",fragsFormatRight:"0",fields:[{width:hp,height:4,bgColor:"#00FF00"}],
                removeSpottedIndicator:true};
            return {id:id,ally:id<15,index:id%15,fixedIndex:id%15,name:"Player"+id,panels:{large:cfg,short:cfg}};
        }
        private function render():void
        { nativeState.begin(); renderer.begin(); renderer.draw(panel,payload); renderer.end(); nativeState.commit(); }
        private function run():void
        {
            var imageFields:ExtraFields=new ExtraFields(), imageHost:Sprite=new Sprite();
            imageFields.draw(imageHost,"hp",[{src:"hp.png",width:72,height:14,x:79,bindToIcon:true}],false,-293,0);
            var imageHolder:Sprite=imageHost.getChildAt(0) as Sprite;
            var imageText:TextField=imageHolder.getChildAt(0) as TextField;
            check(imageHolder.x==-444,"enemy bar right anchor mirrors legacy -151 offset");
            check(imageText.x==-2 && imageText.y==-2 && imageText.width==76 && imageText.height==18,"image fits without text gutter clipping");
            imageFields.draw(imageHost,"hp",[{format:"750/1500",width:72,height:25,x:79,bindToIcon:true}],false,-293,0);
            check(imageText.x==0 && imageText.y==0 && imageText.width==72,"text restores normal gutter after image");
            imageFields.dispose();
            panel.listLeft=new Sprite(); panel.listRight=new Sprite();
            panel.addChild(panel.listLeft); panel.addChild(panel.listRight); addChild(panel);
            for (var i:int=0;i<30;++i)
            { var item:MovieClip=makeItem(i); items.push(item); (i<15 ? panel.listLeft : panel.listRight).addChild(item); payload.rows.push(row(i)); }
            render(); check(renderer.drawn==30,"initial draw");
            var initialWidths:String=renderer.widths.join(",");
            check(renderer.widths[0]>0 && renderer.widths[1]>0,"both sides have measured widths");
            var count:int=items[0].numChildren, expectedX:Number=items[0].vehicleIcon.x;
            var bar:Sprite=items[17].getChildAt(items[17].numChildren-1) as Sprite;
            var idleDrawn:int=0,idleReused:int=0;
            for (i=0;i<100;++i) { render(); idleDrawn+=renderer.drawn; idleReused+=renderer.reused; }
            check(idleDrawn==0 && idleReused==3000,"100 idle cycles must reuse all 30 rows");
            check(items[0].numChildren==count && items[0].vehicleIcon.x==expectedX,"idle extras and positions survive");
            payload.rows[17]=row(17,55); render();
            check(renderer.drawn==1 && renderer.reused==29,"HP only redraws its player");
            check(items[17].getChildAt(items[17].numChildren-1)===bar && bar.getChildAt(0).width==55,"HP bar updates in place");
            payload.rows[1]=row(1);
            payload.rows[1].panels.large.nickFormatLeft="A much longer nickname changes the shared column";
            render(); check(renderer.drawn==15 && renderer.reused==15,"shared nickname width only invalidates its team");
            payload.rows[1]=row(1); render();
            items[3].vehicleTF.text="native update"; render();
            check(renderer.drawn==1 && items[3].vehicleTF.text=="Tank3","native text invalidates only its row");
            items[3].vehicleTF.x+=20; render();
            check(renderer.drawn==1,"native geometry invalidates its row");
            // A holder can be recycled without changing the list size.
            var replacement:TextField=new TextField(); replacement.text="Player4";
            items[4].removeChild(items[4].playerNameFullTF); items[4].playerNameFullTF=replacement; items[4].addChild(replacement);
            render(); check(renderer.drawn>=1 && replacement.text=="Player4","replacement native component");
            payload.rows[5]=row(50,25); payload.rows[5].ally=true;
            payload.rows[5].index=payload.rows[5].fixedIndex=5;
            items[5].holderItemID=50; items[5].playerNameFullTF.text="Player50";
            render(); check(items[5].vehicleTF.text=="Tank50" && items[5].numChildren==count,"recycled holder has new player and no old extras");
            payload.rows[5]=row(5); items[5].holderItemID=5; items[5].playerNameFullTF.text="Player5"; render();
            payload.mode="short"; render(); check(renderer.drawn==30,"mode change redraws all rows");
            render(); check(renderer.drawn==0,"new mode settles");
            for each (var data:Object in payload.rows)
                data.panels.none={enabled:true,fields:[{width:40,height:4,bgColor:"#00FF00"}],
                    extraFields:{leftPanel:{},rightPanel:{}},layout:"vertical"};
            payload.mode="none"; render();
            check(renderer.widths[0]==0 && renderer.widths[1]==0,"explicit none mode publishes valid zero widths");
            check(renderer.drawn==30 && panel.numChildren==32,"none mode moves extras to panel");
            render(); check(renderer.reused==30 && panel.numChildren==32,"none mode retains extras");
            payload.mode="short"; render(); check(panel.numChildren==2,"leaving none mode releases panel extras");
            check(renderer.widths.join(",")==initialWidths,"leaving none mode restores measured widths");
            App.appWidth=1600; render(); check(renderer.drawn==30,"viewport change redraws");
            var first:Object=payload.rows.shift(); panel.listLeft.removeChild(items[0]); render();
            check(items[0].numChildren==count-1 && items[0].vehicleIcon.x==0,"removed holder is restored");
            payload.rows.unshift(first); panel.listLeft.addChild(items[0]); render();
            check(renderer.matched==30,"respawn/reinsert rebinds");
            var beforeHide:String=renderer.widths.join(",");
            nativeState.begin(); renderer.begin(); renderer.end(); nativeState.commit();
            check(renderer.widths.join(",")==beforeHide,"TAB hiding preserves last measured widths");
            check(items[0].numChildren==count-1 && items[0].playerNameCutTF.visible,"hidden panel releases extras and overrides");
            render(); check(renderer.drawn==30 && items[0].numChildren==count,"reopen reconstructs once");
            check(renderer.widths.join(",")==beforeHide,"reopening unchanged panel does not change macro widths");
            // Missing resolved profiles during the visibility handshake are not zero-width measurements.
            var savedRows:Array=payload.rows; payload.rows=[]; render();
            check(renderer.widths.join(",")==beforeHide,"temporarily unbound rows preserve widths");
            payload.rows=savedRows;
            for each (data in payload.rows) { data.panels.short.nickMinWidth=180; data.panels.short.nickMaxWidth=180; }
            App.appWidth=1280; render();
            check(renderer.widths[0]>Number(beforeHide.split(",")[0]),"new layout after hidden interval updates width");
            for each (data in payload.rows) { data.panels.short.nickMinWidth=46; data.panels.short.nickMaxWidth=158; }
            // Use new configs to invalidate rows after in-place fixture edits.
            for (i=0;i<30;++i) payload.rows[i]=row(i);
            render(); check(renderer.widths.join(",")==beforeHide,"width can shrink after layout change");
            payload.panel.enabled=false; render(); check(items[0].numChildren==count-1,"disabled panel cleans up");
            payload.panel.enabled=true; render(); renderer.restore(); nativeState.restore();
            check(renderer.widths[0]==0 && renderer.widths[1]==0,"restore clears measurements for disposed view");
            check(items[0].vehicleIcon.x==0 && items[0].playerNameFullTF.text=="Player0","dispose restores native fields");

            // Exercise staggered audits with deterministic time rather than sleep.
            var cached:PanelRow=new PanelRow(0,0), value:Object=row(0);
            item=makeItem(0);
            cached.update(item,value,"large","layout",0); cached.prepare(item,value.panels.large,"Left"); cached.commit(item);
            check(!cached.update(item,value,"large","layout",50),"clean row before audit");
            item.playerNameFullTF.filters=[new DropShadowFilter(3)];
            check(cached.update(item,value,"large","layout",100),"audit catches native filter changes");
            cached.prepare(item,value.panels.large,"Left"); cached.commit(item);
            check(!cached.update(item,value,"large","layout",1100),"unchanged filter copies do not invalidate");
            item.spottedIndicator=new Sprite();
            check(cached.update(item,value,"large","layout",1150),"replaced spotted component invalidates without audit delay");
            cached.prepare(item,value.panels.large,"Left");
            cached.extra.draw(item,"hp",value.panels.large.fields,true,0,0); cached.commit(item);
            var overlay:Sprite=item.getChildAt(item.numChildren-1) as Sprite;
            item.removeChild(overlay);
            check(cached.update(item,value,"large","layout",2100),"audit detects detached extras");
            cached.prepare(item,value.panels.large,"Left");
            cached.extra.draw(item,"hp",value.panels.large.fields,true,0,0); cached.commit(item);
            check(overlay.parent===item,"native removal is repaired with same overlay");
            cached.dispose(); check(item.playerNameFullTF.filters.length==1,"restore keeps newer native filter");
        }
    }
}
