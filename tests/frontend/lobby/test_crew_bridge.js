'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const {Node}=require('../../support/frontend/dom_fixture');
const source=fs.readFileSync('mod/res/gui/gameface/mods/driftkings/crew_progression/crew.js','utf8');
function environment(){
 const window=new Node('window'),events=new Node('engine'),jobs=new Map(),callbacks=new Map(),errors=[];let next=0;
 const models=new Map();let notification=0;
 const context={window,console:{error:error=>errors.push(String(error))},Event:class {constructor(type){this.type=type;}},
  engine:{whenReady:{then:fn=>fn()},on:events.addEventListener.bind(events),off:events.removeEventListener.bind(events)},
  viewEnv:{addDataChangedCallback:(name,id)=>{callbacks.set(++next,id);return next;},removeDataChangedCallback:id=>callbacks.delete(id)},
  setTimeout:fn=>{jobs.set(++next,fn);return next;},clearTimeout:id=>jobs.delete(id)};
 window.dispatchEvent=event=>{assert.equal(event.type,'dk-carousel-config');assert.equal(event.detail,undefined);notification++;window.fire(event.type);};
 window.subViews={ids:()=>[...models.keys()],get:id=>models.get(id)};
 vm.createContext(context);
 function load(){let published=null;Object.defineProperty(window,'__dkCrewProgression',{configurable:true,get:()=>published,set:value=>{published=value;}});vm.runInContext(source,context);return published;}
 function flush(){const work=[...jobs.values()];jobs.clear();work.forEach(fn=>fn());}
 function payload(id=101,vehicleId=11){return JSON.stringify({config:{visible:true},vehicleId,rows:[{slot:0,id,lines:['XP','Battles'],kinds:['xp','battles']}]});}
 return {window,events,models,callbacks,jobs,errors,context,load,flush,payload,notifications:()=>notification};
}
// Slots can precede the API; a bare invalidation rereads current state, never an event snapshot.
for(const first of ['slots','api']){
 const e=environment();let args;
 const read=()=>{args=JSON.parse(JSON.stringify({tankman:{id:101},resId:99,dkCrewProgression:e.window.__dkCrewProgression?e.window.__dkCrewProgression.getRow(101)||undefined:undefined}));};
 if(first==='slots'){e.window.addEventListener('dk-carousel-config',read);read();assert.equal(args.dkCrewProgression,undefined);}
 e.models.set(44,{model:{DriftkingsUI:{name:'DriftkingsCrewProgression'},payload:e.payload()}});
 const api=e.load();if(first==='api'){e.window.addEventListener('dk-carousel-config',read);read();}
 assert.equal(api.getRow(101).slot,0);assert.equal(api.getRow('101'),null);assert.equal(api.getRow(0),null);assert.equal(api.getRow(-1),null);
 assert.equal(args.dkCrewProgression.lines[0],'XP');assert.equal(args.dkCrewProgression.kinds[1],'battles');
 assert.equal(JSON.stringify(args).includes('dispose'),false);
 // A known new payload cannot be served from the previous cached snapshot before its event.
 e.models.get(44).model.payload=e.payload(202,22);assert.equal(api.getRow(101),null);e.flush();
 assert.equal(api.getRow(202).id,202);assert.equal(args.dkCrewProgression,undefined);
 e.events.fire('viewEnv.onDataChanged');assert.equal(api.getRow(101),null);
 const current=e.models.get(44);e.models.delete(44);assert.equal(api.getRow(202),null);e.models.set(44,current);e.flush();assert.equal(api.getRow(202).id,202);
 current.model.payload=JSON.stringify({config:{visible:true},vehicleId:33,rows:[{slot:1,id:202,lines:['XP moved'],kinds:['xp']}]});
 assert.equal(api.getRow(202),null);e.flush();assert.equal(api.getRow(202).lines[0],'XP moved');
 e.models.get(44).model.payload=JSON.stringify({config:{visible:false},rows:[]});e.events.fire('viewEnv.onDataChanged');assert.equal(api.getRow(202),null);
 e.models.clear();e.events.fire('subViews.onRemoved');assert.equal(api.getRow(101),null);
 const count=e.notifications();api.dispose();assert.equal(e.window.__dkCrewProgression,undefined);assert.equal(api.getRow(101),null);assert(e.notifications()>count);
 e.events.fire('viewEnv.onDataChanged');assert.equal(e.callbacks.size,0);assert.equal(e.jobs.size,0);
}
// Model replacement, malformed input, partial subscriptions and cleanup exceptions stay local.
for(const fault of ['replacement','invalid','subscription','discovery','cleanup']){
 const e=environment();e.models.set(44,{model:{DriftkingsUI:{name:'DriftkingsCrewProgression'},payload:e.payload()}});
 if(fault==='subscription')e.context.viewEnv.addDataChangedCallback=()=>{throw new Error('subscribe');};
 if(fault==='discovery')e.window.subViews.ids=()=>{throw new Error('discover');};
 const api=e.load();
 if(fault==='replacement'){e.models.set(44,{model:{DriftkingsUI:{name:'DriftkingsCrewProgression'},payload:e.payload(303,33)}});assert.equal(api.getRow(101),null);e.flush();assert.equal(api.getRow(303).id,303);}
 if(fault==='invalid'){e.models.get(44).model.payload='{"config":{"visible":true},"rows":[null]}';e.events.fire('viewEnv.onDataChanged');assert.equal(api.getState(),'failed');}
 if(fault==='cleanup'){const off=e.context.engine.off;e.context.engine.off=(...args)=>{off(...args);throw new Error('off');};const remove=e.context.viewEnv.removeDataChangedCallback;e.context.viewEnv.removeDataChangedCallback=id=>{remove(id);throw new Error('unsubscribe');};}
 if(['subscription','discovery'].includes(fault))assert.equal(api.getState(),'failed');
 api.dispose();api.dispose();assert.equal(api.getRow(101),null);assert.equal(e.window.__dkCrewProgression,undefined);assert.equal(e.callbacks.size,0);
 if(fault==='cleanup')assert(e.errors.some(text=>text.includes('unsubscribe')));
}
console.log('Crew bridge actual source: strict IDs, snapshots, event orders, JSON tooltip arguments, failures and disposal passed');
