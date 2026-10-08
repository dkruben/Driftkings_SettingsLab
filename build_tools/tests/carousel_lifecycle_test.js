'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');
let queue = [], mutations, mounts = 0, cleanups = 0, queries = 0, requests = 0;
const events = {}, windowEvents = {};
const body = {};
function card(id) {
    return {
        id, clientWidth:160, clientHeight:100, className:'vehicle-card', parentNode:body,
        getAttribute: () => 'vehicleCard-' + id,
        getBoundingClientRect: () => ({width:160,height:100,left:0,right:160,top:0,bottom:100}),
        querySelector(selector) { return selector === '.dk-carousel-stats' && this.layer ? {} : null; },
        matches: () => true,
        contains(node) { return node.parentNode === this; }
    };
}
let cards = [card(1), card(2)];
const payload = {config:{visible:true},vehicles:{1:{normal:{value:1}},2:{normal:{value:2}}}};
const model = {DriftkingsUI:{name:'DriftkingsCarouselStats'}, payload:JSON.stringify(payload),
    onRequestVehicles: () => requests++};
function Observer(fn) { mutations=fn; this.disconnect=()=>{}; this.observe=()=>{}; }
const window = {
    innerWidth:1920, innerHeight:1080, MutationObserver:Observer,
    subViews:{ids:()=>[1],get:()=>({model})},
    DKCarouselLayout:{profileName:()=> 'normal', mount(node) {
        mounts++; node.layer=true; return () => { cleanups++; node.layer=false; };
    }},
    addEventListener:(name,fn)=>windowEvents[name]=fn, removeEventListener:()=>{}
};
const document = {body, querySelectorAll:()=>{queries++;return cards;},
    addEventListener:()=>{},removeEventListener:()=>{}};
const context = {window, document, MutationObserver:Observer,
    viewEnv:{addDataChangedCallback:()=>1,removeDataChangedCallback:()=>{}},
    engine:{on:(name,fn)=>events[name]=fn,off:()=>{},whenReady:{then:fn=>fn()}},
    setTimeout:fn=>{queue.push(fn);return queue.length;},clearTimeout:()=>{queue=[];}};
function flush() { const tasks=queue;queue=[];tasks.forEach(fn=>fn()); }
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../res/gui/gameface/mods/Driftkings/CarouselStats/carousel.js'),'utf8'),context);
flush(); assert.equal(mounts,2); assert.equal(requests,1);
// Clock/mission notifications and unrelated DOM updates do no carousel work.
const other={parentNode:body,matches:()=>false};
for(let i=0;i<1000;i++) { events['viewEnv.onDataChanged'](); mutations([{target:other}]); flush(); }
assert.equal(queries,1); assert.equal(mounts,2); assert.equal(cleanups,0);
// A model update remounts only the changed card.
payload.vehicles[1].normal.value=3; model.payload=JSON.stringify(payload);
events['viewEnv.onDataChanged']();flush();assert.equal(mounts,3);assert.equal(cleanups,1);
// Position-only resize retains fields; geometry change rebuilds that card.
windowEvents.resize();flush();assert.equal(mounts,3);
cards[1].clientWidth=200;windowEvents.resize();flush();assert.equal(mounts,4);
// Native replacement of fields refreshes that card even if payload is unchanged.
mutations([{target:cards[0],addedNodes:[{}]}]);flush();assert.equal(mounts,5);
const own={parentNode:cards[0],classList:{contains:()=>true}};
mutations([{target:own}]);assert.equal(queue.length,0);
// Virtualized/recycled cards and hidden hangar release all owned fields.
cards=[cards[1]];mutations([{target:body,removedNodes:[{querySelector:()=>({})}]}]);flush();
assert.equal(requests,2);assert.equal(cleanups,4);
payload.config.visible=false;model.payload=JSON.stringify(payload);
events['viewEnv.onDataChanged']();flush();assert.equal(cleanups,5);
payload.config.visible=true;model.payload=JSON.stringify(payload);
events['viewEnv.onDataChanged']();flush();assert.equal(mounts,6);
window.__dkCarouselStats.dispose();assert.equal(cleanups,6);
console.log('Carousel lifecycle: unrelated updates, selective remount, resize, virtualization and disposal passed.');
