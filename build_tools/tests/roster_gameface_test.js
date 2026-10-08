'use strict';
const assert = require('assert'), fs = require('fs'), vm = require('vm'), path = require('path');
let geometryReads=0, styleWrites=0, markupWrites=0, rosterSearches=0, fragmentCommits=0;
class Element {
    constructor(name='', text='') { this.className=name; this.text=text; this.style=new Proxy({visibility:'',transform:'',opacity:''},{set(target,key,value){styleWrites++;target[key]=value;return true;}}); this.children=[]; this.nodeType=1; this.tagName='DIV'; this.attrs={}; }
    appendChild(child) {
        if(child.nodeType===11) {
            fragmentCommits++;
            while(child.firstChild) this.appendChild(child.firstChild);
        } else {
            if(child.parentNode) child.parentNode.removeChild(child);
            child.parentNode=this; this.children.push(child);
        }
        return child;
    }
    removeChild(child) { this.children.splice(this.children.indexOf(child),1); child.parentNode=null; }
    contains(child) { return this===child || this.children.some(c=>c.contains && c.contains(child)); }
    get firstChild() { return this.children[0]; }
    get childNodes() { return this.children; }
    get textContent() { return this.text; }
    set textContent(value) { this.text=value; }
    getAttribute(name) { return this.attrs[name] === undefined ? null : this.attrs[name]; }
    set innerHTML(value) {
        markupWrites++;
        // Minimal DOM fixture parser: formatting tags and text nodes, including
        // nested font tags (the old fixture treated all HTML as plain text).
        this.children=[]; const stack=[this];
        for(const part of value.split(/(<[^>]+>)/g)) {
            if(!part) continue;
            if(part.startsWith('</')) { stack.pop(); continue; }
            if(part.startsWith('<')) {
                const node=new Element(); node.tagName=part.match(/^<(\w+)/)[1].toUpperCase();
                for(const match of part.matchAll(/([\w-]+)=['"]([^'"]*)['"]/g)) node.attrs[match[1]]=match[2];
                stack[stack.length-1].appendChild(node); if(!['IMG','BR'].includes(node.tagName)) stack.push(node);
            } else stack[stack.length-1].appendChild({nodeType:3,nodeValue:part});
        }
    }
    querySelector(selector) { const token=selector.match(/\*="([^"]+)/)[1]; return this.children.find(c=>(c.className||'').includes(token)) || this.children.map(c=>c.querySelector && c.querySelector(selector)).find(Boolean) || null; }
    getBoundingClientRect() { geometryReads++; this.geometryReads=(this.geometryReads||0)+1; return this.rect || {left:100,top:50,width:80,height:20}; }
}
const body=new Element(), root=new Element(); body.appendChild(root);
const elements=[];
function player(right,name) {
    const outer=new Element(right?'Player_right_ab123':''), row=new Element('Player_base_fe348');
    root.appendChild(outer); outer.appendChild(row); elements.push(row);
    const nick=new Element('UserInfo_userNameWrapper_ddc08',name), vehicle=new Element('Player_vehicleName_aa673','Tank');
    const column=new Element('UserInfo_nickname_wrapper_af103'), icon=new Element('Player_vehicleContour_image_a35ee');
    column.rect={left:100,top:50,width:127,height:20};
    ['UserInfo_clanTag_','Player_kills_','Player_vehicleContour_level_','Player_vehicleType_',
     'Player_prestigeGrade_','Player_prestigeLevel_','Player_platoon_wrapper_','UserInfo_badge_',
     'Player_playerStatus_'].forEach(token=>row.appendChild(new Element(token+'ab123')));
    row.appendChild(column); column.appendChild(nick); row.appendChild(vehicle); row.appendChild(icon); return {row,nick,vehicle,column,icon};
}
const ally=player(false,'Ally'), enemy=player(true,'Enemy');
const cfg=side=>({enabled:true,['format'+side+'Nick']:side+' rating',['format'+side+'Vehicle']:'Tank statistics'});
let data={screen:'tab',enabled:true,order:{left:[1],right:[2]},rows:[
    {id:1,ally:true,aliases:['Ally'],cfg:cfg('Left')},{id:2,ally:false,aliases:['Enemy'],cfg:cfg('Right')} ]};
const model={DriftkingsUI:{name:'DriftkingsRatingPlayers'},payload:JSON.stringify(data)};
let clockNow=0;
const performanceReports=[];
model.onPerformance=sample=>performanceReports.push(sample);
let refresh; const events={};
let nextFrameId=0; const scheduledFrames=new Map();
function scheduleFrame(callback){const id=++nextFrameId;scheduledFrames.set(id,callback);return id;}
function runFrame(){const entry=scheduledFrames.entries().next().value;assert(entry);scheduledFrames.delete(entry[0]);clockNow+=16;entry[1]();}
const context={document:{body,documentElement:root,createElement:()=>new Element(),createTextNode:text=>({nodeType:3,nodeValue:text}),querySelectorAll:()=>{rosterSearches++;return elements;}},
    getComputedStyle:source=>new Proxy(Object.assign({fontSize:source===root?'1px':'13px',fontFamily:'WarHeliosCondC',fontWeight:'400',fontStyle:'normal',lineHeight:'16px',color:'#ffffff',textAlign:'left',opacity:'1',display:'block',visibility:'visible',transform:'none'},Object.fromEntries(Object.entries(source.style).filter(([,v])=>v!==''))),{get(target,key){source.styleReads=source.styleReads||{};source.styleReads[key]=(source.styleReads[key]||0)+1;return target[key];}}),
    engine:{whenReady:{then:fn=>fn()},on(name,fn){events[name]=fn;},off(name){delete events[name];}},viewEnv:{addDataChangedCallback:()=>1,removeDataChangedCallback(){}},
    setInterval:fn=>{refresh=fn;return 1;},clearInterval(){},
    setTimeout:fn=>scheduleFrame(fn),clearTimeout:id=>scheduledFrames.delete(id)};
if(!process.argv.includes('--no-fragment')) context.document.createDocumentFragment=()=>{const fragment=new Element();fragment.nodeType=11;return fragment;};
context.window={subViews:{ids:()=>[1],get:()=>({model})},addEventListener(){},removeEventListener(){}};
context.window.performance={now:()=>clockNow+=0.25};
if(!process.argv.includes('--timer-only')) {
    context.window.requestAnimationFrame=scheduleFrame;
    context.window.cancelAnimationFrame=id=>scheduledFrames.delete(id);
}
let mutations, observerDisconnected=false;
const useObserver=!process.argv.includes('--poll-only');
if(useObserver) context.window.MutationObserver=class {
    constructor(callback){mutations=callback;}
    observe(target,options){assert.equal(target,body); assert.deepEqual(options.attributeFilter,['class']);}
    disconnect(){observerDisconnected=true;}
};
function notifyNative(records) { if(useObserver) mutations(records); else clockNow+=1001; }
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../res/gui/gameface/mods/Driftkings/RatingPlayers/ratings.js'),'utf8'),context);
const overlays=()=>body.children.filter(c=>c.className==='dk-tab-roster-field');
assert.equal(ally.nick.style.visibility,'hidden'); assert.equal(enemy.nick.style.visibility,'hidden');
assert(overlays().some(n=>n.children.some(c=>c.textContent==='Right rating')));
assert.equal(ally.nick.textContent,'Ally'); // Native identity remains intact.
assert.equal(fragmentCommits,context.document.createDocumentFragment?1:0);
assert.equal(markupWrites,0); // Plain text never invokes the HTML parser.
const count=overlays().length; refresh(); assert.equal(overlays().length,count); // Reuse, no duplicate overlays.
const reads=geometryReads;
for(let i=0;i<100;i++) events['viewEnv.onDataChanged']();
assert.equal(geometryReads,reads); // Unrelated native events perform no layout reads/writes.
refresh(); assert(geometryReads>reads); // Periodic layout poll still follows native changes.
const idleWrites=styleWrites, idleMarkup=markupWrites, idleSearches=rosterSearches;
for(let i=0;i<100;i++) refresh();
assert.equal(styleWrites,idleWrites); assert.equal(markupWrites,idleMarkup); assert.equal(rosterSearches,idleSearches);
// Stable polling reads only rendered text geometry. Hidden clan, absent frags
// and unmodified icons do not need fonts or rectangles; ancestors need visibility.
assert.equal(geometryReads-reads,404); // 101 polls * two text anchors * two players.
assert.equal(ally.icon.geometryReads,undefined); assert.equal(ally.icon.styleReads,undefined);
assert.equal(ally.row.styleReads.fontFamily,undefined);
assert.equal(ally.row.parentNode.styleReads.fontSize,undefined);
const clan=ally.row.querySelector('[class*="UserInfo_clanTag_"]');
assert.equal(clan.geometryReads,undefined); assert.equal(clan.styleReads,undefined);
assert.equal(clan.style.visibility,'hidden');
// A changed payload with identical enemy settings must not reapply the enemy.
const enemyOverlay=overlays().find(n=>n.children.some(c=>c.textContent==='Right rating'));
const oldEnemyStyle=enemyOverlay.style;
let enemyWrites=0;
enemyOverlay.style=new Proxy(oldEnemyStyle,{set(target,key,value){enemyWrites++;target[key]=value;return true;}});
data.rows[0].cfg.formatLeftVehicle='Changed ally'; model.payload=JSON.stringify(data); refresh();
assert.equal(enemyWrites,0);
// The actual nested formats must be flat runs on one line, with inherited font
// size, alpha and colors. No native HTML or username is overwritten.
data.rows[0].cfg.formatLeftVehicle="Tank<font face='$FieldFont' size='13'> <font color='#FFFF00'>15k</font> <font color='#00FF00'><b>2165</b></font> 54%</font><font size='0'>hidden</font>";
data.rows[1].cfg.formatRightNick="<font alpha='#A0'>[CLAN]</font> Enemy";
data.rows[1].cfg.nameFieldWidthRight=200;
data.rows[0].cfg.vehicleIconOffsetXLeft=31;
data.rows[1].cfg.vehicleIconOffsetXRight=27;
enemy.icon.style.transform='scaleX(-1)';
model.payload=JSON.stringify(data); refresh();
const rich=overlays().find(n=>n.children.some(c=>c.textContent==='2165'));
assert(rich); assert.equal(rich.children.map(c=>c.textContent).join(''),'Tank 15k 2165 54%');
assert(rich.children.every(c=>c.children.length===0 && c.style.flexShrink==='0'));
const rating=rich.children.find(c=>c.textContent==='2165');
assert.equal(rating.style.color,'#00FF00'); assert.equal(rating.style.fontSize,'13rem');
assert.equal(rating.style.fontWeight,'bold'); assert.equal(rating.style.fontFamily,undefined);
assert.equal(rich.style.fontFamily,'WarHeliosCondC');
const rightName=overlays().find(n=>n.children.some(c=>c.textContent==='[CLAN]'));
assert.equal(rightName.children.map(c=>c.textContent).join(''),'[CLAN] Enemy');
assert.equal(rightName.children[0].style.opacity,160/255);
assert.equal(rightName.style.left,'27px'); assert.equal(rightName.style.justifyContent,'flex-end');
enemy.nick.rect={left:150,top:50,width:23,height:20}; refresh();
assert.equal(rightName.style.left,'27px'); // Short names/clans do not change column anchor.
assert.equal(ally.icon.style.transform,'translateX(31rem) ');
assert.equal(enemy.icon.style.transform,'translateX(-27rem) scaleX(-1)');
refresh(); assert.equal(enemy.icon.style.transform,'translateX(-27rem) scaleX(-1)');
const stableIconReads=JSON.stringify(enemy.icon.styleReads);
refresh(); assert.equal(JSON.stringify(enemy.icon.styleReads),stableIconReads);
// Styles changing without an observer notification are still found on a poll.
ally.vehicle.style.color='#112233'; refresh(); assert.equal(rich.style.color,'#112233');
ally.vehicle.style.fontSize='15px'; refresh(); assert.equal(rich.style.fontSize,'15px');
root.style.opacity='0'; refresh(); assert.equal(rich.style.opacity,0);
root.style.opacity='1'; refresh(); assert.equal(rich.style.opacity,1);
// Extra fields share the resolved Flash configuration: bar, text and local icon.
data.rows[0].cfg.fields=[{id:'hpBar',x:-10,y:2,width:70,height:8,bindToIcon:true,bgColor:'#00FF00',alpha:80},
    {format:"<b>500</b><font color='#FF0000'>/1000</font>",width:70,height:20}];
data.rows[1].cfg.fields=[{src:'img://gui/maps/Driftkings/PlayerPanelPro/spotted/dot-spotted.png',width:22,height:22,x:10}];
model.payload=JSON.stringify(data); refresh();
const extras=()=>body.children.filter(c=>c.className==='dk-tab-extra');
assert.equal(extras().length,3);
const bar=extras().find(n=>n.style.backgroundColor==='#00FF00');
assert.equal(bar.style.width,'70px'); assert.equal(bar.style.left,'90px'); assert.equal(bar.style.opacity,.8);
const extraText=extras().find(n=>n.children.some(c=>c.textContent==='500'));
assert.equal(extraText.children.map(c=>c.textContent).join(''),'500/1000');
ally.row.style.fontFamily='ChangedFont'; refresh(); assert.equal(extraText.style.fontFamily,'ChangedFont');
const spotted=extras().find(n=>n.children.some(c=>c.src));
assert.equal(spotted.style.left,'148px'); assert(spotted.children[0].src.startsWith('coui://gui/'));
data.rows[0].cfg.fields[0].width=35; model.payload=JSON.stringify(data); refresh();
assert.equal(bar.style.width,'35px'); assert.equal(extras().length,3);
// Geometry is still followed, while native component replacement invalidates
// cached references immediately through the observer.
const leftName=overlays().find(n=>n.children.some(c=>c.textContent==='Left rating'));
ally.column.rect.left+=17; refresh(); assert.equal(leftName.style.left,'117px');
const oldNick=ally.nick;
ally.column.removeChild(oldNick); ally.nick=new Element('UserInfo_userNameWrapper_new','Ally'); ally.column.appendChild(ally.nick);
notifyNative([{type:'childList',target:ally.column,addedNodes:[ally.nick],removedNodes:[oldNick]}]); refresh();
assert.equal(oldNick.style.visibility,''); assert.equal(ally.nick.style.visibility,'hidden');
const newLeftName=overlays().find(n=>n.children.some(c=>c.textContent==='Left rating'));
body.removeChild(newLeftName); refresh(); assert.equal(newLeftName.parentNode,body);
const searchesBeforeOwn=rosterSearches;
if(useObserver) mutations([{type:'childList',target:body,addedNodes:[newLeftName],removedNodes:[]}]); refresh();
assert.equal(rosterSearches,searchesBeforeOwn); // Our overlays do not invalidate native discovery.
root.style.fontSize='2px'; refresh(); assert.equal(bar.style.width,'70px');
root.style.fontSize='1px'; refresh(); assert.equal(bar.style.width,'35px');
ally.icon.style.transform='scaleX(-1)'; refresh();
assert.equal(ally.icon.style.transform,'translateX(31rem) scaleX(-1)');
root.style.visibility='hidden'; refresh(); assert.equal(extras().length,0); assert.equal(overlays().length,0);
root.style.visibility='visible'; refresh(); assert.equal(extras().length,3);
data.rows[1].cfg.fields[0].src='https://example.com/icon.png'; model.payload=JSON.stringify(data); refresh();
assert(extras().every(n=>n.children.every(c=>!c.src || c.src.startsWith('coui://gui/'))));
data.rows[1].cfg.enabled=false; model.payload=JSON.stringify(data); refresh();
assert.equal(enemy.nick.style.visibility,''); assert.equal(ally.nick.style.visibility,'hidden');
assert.equal(enemy.icon.style.transform,'scaleX(-1)');
// Use the production model command without a browser console.
assert.equal(performanceReports.length,0);
data.diagnostics=true; model.payload=JSON.stringify(data); refresh();
assert.equal(performanceReports.length,0);
clockNow+=5100; refresh();
assert.equal(performanceReports.length,1);
let sample=performanceReports[0];
assert.equal(sample.reason,'interval'); assert.equal(sample.calls,2); assert.equal(sample.rows,2);
assert(sample.totalMs>0 && sample.maxMs<=sample.totalMs && sample.windowMs>=5000);
assert.equal(sample.rowsDrawn,0); assert.equal(sample.rowsReused,2);
for(let i=0;i<100;i++) events['viewEnv.onDataChanged']();
assert.equal(performanceReports.length,1);
refresh();
data.enabled=false; model.payload=JSON.stringify(data); refresh();
assert.equal(performanceReports.length,2);
assert.equal(performanceReports[1].reason,'hidden'); assert.equal(performanceReports[1].calls,1);
clockNow+=10000; refresh(); assert.equal(performanceReports.length,2);
assert.equal(ally.nick.style.visibility,''); assert.equal(overlays().length,0);
assert.equal(ally.icon.style.transform,'scaleX(-1)'); // Preserve the newer native transform.
assert.equal(extras().length,0);
data.enabled=true; model.payload=JSON.stringify(data); refresh();
data.diagnostics=false; model.payload=JSON.stringify(data); refresh();
clockNow+=6000; refresh(); assert.equal(performanceReports.length,2);
// Closing detaches overlays but retains the parsed runs for the same native row.
const warmNodes=overlays().concat(extras()), warmMarkup=markupWrites;
data.enabled=false; model.payload=JSON.stringify(data); refresh();
assert(warmNodes.every(n=>!n.parentNode));
ally.nick.style.visibility='hidden'; // Client changes visibility while TAB is closed.
refresh(); assert.equal(ally.nick.style.visibility,'hidden');
data.enabled=true; model.payload=JSON.stringify(data); refresh();
assert(warmNodes.every(n=>n.parentNode===body));
assert.equal(markupWrites,warmMarkup);
data.enabled=false; model.payload=JSON.stringify(data); refresh();
assert.equal(ally.nick.style.visibility,'hidden'); // Reopening captured the new native value.
ally.nick.style.visibility='';
data.enabled=true; model.payload=JSON.stringify(data); refresh();
// Empty formats hide the native field without creating a replacement element.
const vehicleNode=overlays().find(n=>n.children.some(c=>c.textContent==='2165'));
data.rows[0].cfg.formatLeftVehicle=''; model.payload=JSON.stringify(data); refresh();
assert.equal(ally.vehicle.style.visibility,'hidden'); assert.equal(vehicleNode.parentNode,null);
const emptyCount=overlays().length;
refresh(); assert.equal(overlays().length,emptyCount);
data.rows[0].cfg.formatLeftVehicle='Fresh vehicle'; model.payload=JSON.stringify(data); refresh();
assert.equal(vehicleNode.parentNode,body); assert.equal(vehicleNode.children[0].textContent,'Fresh vehicle');
data.enabled=false; model.payload=JSON.stringify(data); refresh();
data.rows[0].cfg.formatLeftVehicle='Changed while closed';
data.enabled=true; model.payload=JSON.stringify(data); refresh();
assert.equal(vehicleNode.children[0].textContent,'Changed while closed');
const holder=ally.row.parentNode;
root.removeChild(holder); notifyNative([{type:'childList',target:root,addedNodes:[],removedNodes:[holder]}]); refresh();
assert.equal(ally.nick.style.visibility,''); assert.equal(overlays().length,0); assert.equal(extras().length,0);
root.appendChild(holder); notifyNative([{type:'childList',target:root,addedNodes:[holder],removedNodes:[]}]); refresh();
assert.equal(ally.nick.style.visibility,'hidden'); assert(overlays().length>0);
data.diagnostics=true; model.payload=JSON.stringify(data); refresh();
// Large rosters are constructed over frames, keeping pending native names visible.
const newcomers=[];
for(let i=0;i<24;i++) {
    const right=!!(i%2), name='New'+i, item=player(right,name), id=100+i;
    newcomers.push(item);
    data.order[right?'right':'left'].push(id);
    data.rows.push({id,ally:!right,aliases:[name],cfg:cfg(right?'Right':'Left')});
}
notifyNative([{type:'childList',target:root,addedNodes:newcomers.map(p=>p.row.parentNode),removedNodes:[]}]);
model.payload=JSON.stringify(data); refresh();
const readyNew=()=>newcomers.filter(p=>p.nick.style.visibility==='hidden').length;
assert.equal(readyNew(),6); assert.equal(scheduledFrames.size,1);
assert(newcomers.slice(6).every(p=>p.nick.style.visibility===''));
data.enabled=false; model.payload=JSON.stringify(data); refresh();
assert.equal(scheduledFrames.size,0); assert.equal(readyNew(),0);
data.enabled=true; model.payload=JSON.stringify(data); refresh();
assert.equal(readyNew(),12); assert.equal(scheduledFrames.size,1);
data.rows[data.rows.length-1].cfg.formatRightVehicle='Latest deferred vehicle';
model.payload=JSON.stringify(data); events['viewEnv.onDataChanged']();
assert.equal(readyNew(),18); assert.equal(scheduledFrames.size,1);
const last=newcomers[newcomers.length-1], oldPendingName=last.nick;
last.column.removeChild(oldPendingName); last.nick=new Element('UserInfo_userNameWrapper_replaced','New23'); last.column.appendChild(last.nick);
notifyNative([{type:'childList',target:last.column,addedNodes:[last.nick],removedNodes:[oldPendingName]}]);
runFrame(); assert.equal(readyNew(),24); assert.equal(scheduledFrames.size,0);
assert.equal(oldPendingName.style.visibility,'');
assert(overlays().some(n=>n.children.some(c=>c.textContent==='Latest deferred vehicle')));
const cachedLargeMarkup=markupWrites;
data.enabled=false; model.payload=JSON.stringify(data); refresh();
data.enabled=true; model.payload=JSON.stringify(data); refresh();
assert.equal(readyNew(),24); assert.equal(scheduledFrames.size,0); assert.equal(markupWrites,cachedLargeMarkup);
// Losing the model clears the roster; disposal cancels a fresh pending opening.
context.window.subViews.ids=()=>[]; refresh();
assert.equal(readyNew(),0); assert.equal(overlays().length,0);
context.window.subViews.ids=()=>[1]; refresh();
assert.equal(scheduledFrames.size,1);
context.window.__dkPlayerRatings.dispose();
assert.equal(scheduledFrames.size,0); assert.equal(overlays().length,0); assert.equal(readyNew(),0);
// Recreate the bridge to retain the diagnostic command failure coverage.
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../res/gui/gameface/mods/Driftkings/RatingPlayers/ratings.js'),'utf8'),context);
while(scheduledFrames.size) runFrame();
model.onPerformance=()=>{throw new Error('native view already finalized');};
data.enabled=false; model.payload=JSON.stringify(data); refresh();
ally.nick.style.visibility='hidden';
context.window.__dkPlayerRatings.dispose();
assert.equal(overlays().length,0); assert.equal(extras().length,0);
assert.equal(ally.nick.style.visibility,'hidden'); // Disposal must not restore an already released field.
assert.equal(observerDisconnected,useObserver);
console.log('Gameface roster: formatting, incremental rows, native layout/replacement, restoration and diagnostics OK ('+(useObserver?'observer':'poll fallback')+')');
