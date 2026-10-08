'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function harness(script, feature, initial) {
    let writes=0, created=0, nextId=1, subscriptions=0, intervalStarts=0, observer;
    const events={}, windowEvents={}, timeouts=new Map(), intervals=new Map();
    class Node {
        constructor() {
            created++; this.childNodes=[]; this.attributes={}; this.className=''; this.value='';
            this.style=new Proxy({}, {set:(obj,key,value)=>{writes++;obj[key]=value;return true;}});
            this.offsetWidth=300;this.offsetHeight=120;
            this.classList={contains:name=>this.className.split(' ').includes(name)};
        }
        get textContent() { return this.value; }
        set textContent(value) { writes++;this.value=value; }
        get firstChild() { return this.childNodes[0]; }
        appendChild(node) { writes++;node.parentNode=this;this.childNodes.push(node);return node; }
        removeChild(node) { writes++;this.childNodes.splice(this.childNodes.indexOf(node),1);node.parentNode=null; }
        setAttribute(key,value) { this.attributes[key]=value; }
        getAttribute(key) { return this.attributes[key]; }
        addEventListener() {}
        matches(selector) {
            return selector[0]==='.' ? this.classList.contains(selector.slice(1)) :
                selector.includes('data-test-id') ? /-content$/.test(this.attributes['data-test-id']||'') :
                this.className.includes('VehicleNode_name_');
        }
        querySelectorAll(selector) {
            return this.childNodes.flatMap(n=>(n.matches(selector)?[n]:[]).concat(n.querySelectorAll(selector)));
        }
        querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    }
    const body=new Node(), document={body,documentElement:{},createElement:()=>new Node(),
        addEventListener:()=>{},removeEventListener:()=>{},querySelectorAll:s=>body.querySelectorAll(s)};
    const model={DriftkingsUI:{name:feature},payload:JSON.stringify(initial)};
    let present=true, now=new Date(2026,9,6,23,59,58);
    function TestDate() { return new Date(now); }
    function Observer(fn) { observer=fn;this.disconnect=()=>{};this.observe=()=>{}; }
    const window={innerWidth:1920,innerHeight:1080,MutationObserver:Observer,
        getComputedStyle:()=>({fontSize:'1'}),
        subViews:{ids:()=>present?[1]:[],get:()=>({model})},
        addEventListener:(k,fn)=>windowEvents[k]=fn,removeEventListener:k=>delete windowEvents[k]};
    const context={window,document,Date:TestDate,MutationObserver:Observer,getComputedStyle:window.getComputedStyle,
        viewEnv:{addDataChangedCallback:()=>++subscriptions,removeDataChangedCallback:()=>subscriptions--},
        engine:{whenReady:{then:fn=>fn()},on:(k,fn)=>events[k]=fn,off:k=>delete events[k]},
        setTimeout:fn=>{const id=nextId++;timeouts.set(id,fn);return id;},clearTimeout:id=>timeouts.delete(id),
        setInterval:fn=>{intervalStarts++;const id=nextId++;intervals.set(id,fn);return id;},clearInterval:id=>intervals.delete(id)};
    function flush() { const pending=[...timeouts.values()];timeouts.clear();pending.forEach(fn=>fn()); }
    vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../res/gui/gameface/mods/Driftkings',script),'utf8'),context);
    flush();
    return {window,body,model,events,Node,intervals,
        flush, mutate:r=>{observer(r);flush();},stats:()=>({writes,created,intervalStarts,subscriptions}),
        notify:()=>{events['viewEnv.onDataChanged']();flush();},
        update:data=>{model.payload=JSON.stringify(data);events['viewEnv.onDataChanged']();flush();},
        show:value=>{present=value;events[value?'subViews.onAdded':'subViews.onRemoved']();flush();},
        tick:()=>{now=new Date(+now+1000);[...intervals.values()].forEach(fn=>fn());},
        resize:()=>windowEvents.resize()};
}
for (const [script,feature,globalName] of [
    ['HangarEfficiency/efficiency.js','DriftkingsHangarEfficiency','__dkHangarEfficiency'],
    ['MarksOnGunHangar/marks.js','DriftkingsMarksOnGunHangar','__dkHangarMarks'],
    ['HangarClock/clock.js','DriftkingsHangarClock','__dkHangarClock']
]) {
    const late=harness(script,null,{config:{visible:true},rows:[{value:1}]});
    late.model.DriftkingsUI.name=feature;late.notify();
    assert.notEqual(late.body.childNodes[0].style.display,'none', 'Late model discovery');
    late.window[globalName].dispose();
    const data={config:{visible:true},vehicle:'Tank',rows:[{label:'Damage',value:1200}]};
    const h=harness(script,feature,data), before=h.stats();
    for(let i=0;i<1000;i++) h.notify();
    assert.deepStrictEqual(h.stats(),before,script+': unrelated model updates must do no DOM/timer work');
    h.resize();assert(h.stats().writes>before.writes);
    data.config.visible=false;h.update(data);
    assert.equal(h.body.childNodes[0].style.display,'none');assert.equal(h.intervals.size,0);
    data.config.visible=true;h.update(data);assert.notEqual(h.body.childNodes[0].style.display,'none');
    if(script.includes('Clock')) {
        assert.equal(h.intervals.size,1);
        const starts=h.stats().intervalStarts;
        h.tick();h.tick(); // Midnight changes both the time and date.
        assert.equal(h.body.querySelector('.dk-clock__digit').textContent,'00');
        assert.equal(h.stats().intervalStarts,starts);
        data.config.clockStyle=2;h.update(data);h.tick();
        assert(h.body.querySelector('.hour').style.transform.startsWith('rotate('));
    }
    h.show(false);assert.equal(h.stats().subscriptions,0);assert.equal(h.intervals.size,0);
    assert.equal(h.body.childNodes[0].style.display,'none');
    h.show(true);assert.equal(h.stats().subscriptions,1);assert.notEqual(h.body.childNodes[0].style.display,'none');
    h.window[globalName].dispose();assert.equal(h.stats().subscriptions,0);assert.equal(h.body.childNodes.length,0);
}
const tree=harness('MarksOnGunTechTree/marks.js','DriftkingsMarksOnGunTechTree',
    {enabled:true,showPercent:true,colorName:true,vehicles:{1:{tier:8,percent:85,color:'#ABCDEF'}}});
const card=new tree.Node();card.setAttribute('data-test-id','1-content');
const name=new tree.Node();name.className='VehicleNode_name_test';name.style.color='white';card.appendChild(name);
tree.body.appendChild(card);tree.mutate([{target:tree.body,addedNodes:[card]}]);
assert.equal(tree.body.querySelectorAll('.dk-tech-marks').length,1);assert.equal(name.style.color,'#ABCDEF');
const before=tree.stats();
for(let i=0;i<1000;i++) { tree.notify();tree.mutate([{target:tree.body,addedNodes:[]}]); }
assert.deepStrictEqual(tree.stats(),before);
tree.mutate([{target:card,addedNodes:[name]}]);assert.equal(tree.body.querySelectorAll('.dk-tech-marks').length,1);
tree.show(false);assert.equal(tree.body.querySelectorAll('.dk-tech-marks').length,0);assert.equal(name.style.color,'white');
tree.show(true);assert.equal(tree.body.querySelectorAll('.dk-tech-marks').length,1);
tree.window.__dkTechMarks.dispose();assert.equal(name.style.color,'white');assert.equal(tree.stats().subscriptions,0);
console.log('Hangar updates: 4 interfaces, 1000 unrelated notifications each, visibility, resize, midnight and cleanup OK.');
