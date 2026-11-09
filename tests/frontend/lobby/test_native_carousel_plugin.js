'use strict';
const assert=require('assert'),{spawnSync}=require('child_process');
const driver=String.raw`
import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';import {createRequire} from 'node:module';
const require=createRequire(process.cwd()+'/tests/run_frontend.js'),{Node}=require('./support/frontend/dom_fixture');
const {NativeLoaderContract}=require('./support/frontend/native_loader_contract');
const output=console.log.bind(console),base='mod/res/gui/gameface/mods/driftkings/';
const paths=['main/clock_plugin.js','mono/driftkings/hangar_marks/marks_plugin.js','mono/driftkings/crew_progression/crew_plugin.js','mono/driftkings/vehicle_carousel/carousel_plugin.js'];
const modules=await Promise.all(paths.map(path=>import('data:text/javascript;base64,'+fs.readFileSync(base+path).toString('base64'))));
function environment(options={}){
 const window=new Node('window'),document=new Node('document'),events=new Node('engine'),detailsHost=new Node('div');
 const card=new Node('div'),field=new Node('span');card.className='vehicle-card';card.setAttribute('data-test-id','vehicleCard-123');card.clientWidth=200;card.clientHeight=100;field.className='native-name';field.style.visibility='visible';card.appendChild(field);
 document.head=new Node('head');document.body=new Node('body');document.documentElement=new Node('html');document.body.appendChild(detailsHost);document.body.appendChild(card);
 document.querySelectorAll=selector=>selector.includes('vehicle-card')?[card]:document.body.querySelectorAll(selector);
 const nativeMatches=card.matches.bind(card);card.matches=selector=>selector.includes('vehicle-card')?true:nativeMatches(selector);
 const nativeQuery=card.querySelectorAll.bind(card);card.querySelectorAll=selector=>selector.includes('Information_truncatedText_')?[field]:nativeQuery(selector);
 document.createElement=tag=>{if(options.create&&tag==='script'&&window.__dkCrewProgressionLoad)throw new Error('create script');return new Node(tag);};document.querySelector=selector=>selector.includes('TankmanTooltipApp')?detailsHost:null;
 window.innerWidth=1920;window.innerHeight=1080;window.getComputedStyle=node=>({fontSize:'1px',opacity:'1',display:node.style.display||'',visibility:'visible'});
 window.dispatchEvent=event=>window.fire(event.type);
 const clockConfig={visible:true,hidePrestige:true,formats:[{format:'%H:%M:%S',x:12,y:20,width:100,textFormat:{size:18}}]};
 const clock={DriftkingsUI:{name:'DriftkingsHangarClock'},payload:JSON.stringify({config:clockConfig})};
 const marks={DriftkingsUI:{name:'DriftkingsMarksOnGunHangar'},payload:JSON.stringify({config:{visible:true},state:'data',currentMark:90,displayMarks:2,target:{eligible:true},milestone:{},recent:{samples:[]}})};
 const crew={DriftkingsUI:{name:'DriftkingsCrewProgression'},payload:'{}'};
 const details={DriftkingsUI:{name:'DriftkingsCrewDetails'},payload:JSON.stringify({surface:'tooltip',config:{visible:true},lines:['detail XP'],kinds:['xp']})};
 const requests=[],loaded=[],observers=[];const profile={width:200,height:100,fields:{tankName:{enabled:false,alpha:100,dx:0,dy:0,scale:1}},extraFields:[]};
 const carousel={DriftkingsUI:{name:'DriftkingsCarouselStats'},payload:JSON.stringify({config:{visible:true,cellType:'normal',effectiveRows:1,normal:{width:200,height:100,gap:0},small:{width:100,height:50,gap:0},filters:{params:{enabled:true}},filtersPadding:{horizontal:0,vertical:0},sorting_criteria:[]},vehicles:{'123':{normal:profile,small:profile}},sortValues:{},images:{}}),onRequestVehicles:args=>requests.push(args)};
 const models=new Map([[46,{model:carousel}],[42,{model:clock}],[43,{model:marks}],[44,{model:crew}],[45,{model:details}]]);
 window.subViews={ids:()=>[...models.keys()],get:id=>models.get(id)};
 const jobs=new Map(),deadlines=new Map(),intervals=new Map(),frames=new Map(),callbacks=new Map(),deferred=[],errors=[];let next=0,registers=0;
 class Observer {constructor(fn){this.fn=fn;this.connected=false;observers.push(this);}observe(){this.connected=true;}disconnect(){this.connected=false;}}
 window.MutationObserver=Observer;
 const context={window,document,MutationObserver:Observer,getComputedStyle:node=>({position:'static',transform:'none'}),Event:class {constructor(type){this.type=type;}},console:{info(){},error:error=>errors.push(String(error))},
  engine:{whenReady:Promise.resolve(),on:(name,callback)=>{if(options.partial&&window.__dkCrewProgression&&++registers===2)throw new Error('partial API subscription');events.addEventListener(name,callback);},off:events.removeEventListener.bind(events)},
  viewEnv:{addDataChangedCallback:(name,id)=>{if(options.subscription&&id===44)throw new Error('crew subscription');callbacks.set(++next,id);return next;},removeDataChangedCallback:id=>callbacks.delete(id)},
  setTimeout:(fn,delay)=>{(delay>40?deadlines:jobs).set(++next,fn);return next;},clearTimeout:id=>{jobs.delete(id);deadlines.delete(id);},
  setInterval:fn=>{intervals.set(++next,fn);return next;},clearInterval:id=>intervals.delete(id),requestAnimationFrame:fn=>{frames.set(++next,fn);return next;},cancelAnimationFrame:id=>frames.delete(id)};
 Object.assign(window,{document,Event:context.Event});Object.assign(globalThis,context);vm.createContext(context);
 const append=document.head.appendChild.bind(document.head);
 document.head.appendChild=node=>{append(node);const url=node.src||node.href;if(!url)return node;const execute=()=>{
  loaded.push(url);if(options.failSuffix&&url.endsWith(options.failSuffix)){node.onerror();return;}
  if(options.syntaxSuffix&&url.endsWith(options.syntaxSuffix)){node.onload();return;}
  if(options.missing&&url.endsWith('/crew.js')){node.onerror();return;}
  if(node.tagName==='SCRIPT'){
   try{if(options.syntax&&url.endsWith('/crew.js'))throw new SyntaxError('renderer syntax');vm.runInContext(fs.readFileSync(base+url.split('/mods/driftkings/')[1],'utf8'),context,{filename:url});}catch(error){errors.push(String(error));}
  }
  if(node.onload)node.onload();
 };if((options.deferURL&&url.endsWith(options.deferURL))||(options.defer&&url.endsWith('/crew.js')))deferred.push(execute);else queueMicrotask(execute);return node;};
 function setCrew(id=101,vehicleId=11){crew.payload=JSON.stringify({config:{visible:true},vehicleId,rows:[{slot:0,id,lines:['XP '+id],kinds:['xp']}]});}
 setCrew();
 async function flush(){for(let i=0;i<24;i++){await Promise.resolve();const work=[...jobs.values()];jobs.clear();work.forEach(fn=>fn());}}
 function loadDetails(){vm.runInContext(fs.readFileSync(base+'crew_details/details.js','utf8'),context);}
 function clean(){assert.equal(document.head.children.length,0);assert.equal(document.body.children.length,2);assert.equal(detailsHost.children.length,0);
  for(const map of [jobs,deadlines,intervals,frames,callbacks])assert.equal(map.size,0);
  for(const target of [window,document,events])for(const handlers of Object.values(target.listeners))assert.equal(handlers.length,0);
  assert.equal(window.__dkCrewProgression,undefined);assert.equal(window.__dkCrewProgressionLoad,undefined);for(const key of ['__dkCarouselStats','__dkCarouselLoad','DKCarouselNative','DKCarouselLayout'])assert.equal(window[key],undefined,key);assert(observers.every(o=>!o.connected));assert.equal(card.querySelectorAll('.dk-carousel-stats').length,0);assert.equal(field.style.visibility,'visible');
 }
 return {card,field,requests,loaded,observers,carousel,profile,window,document,events,context,crew,clock,clockConfig,models,callbacks,jobs,deadlines,deferred,errors,details,detailsHost,loadDetails,setCrew,flush,clean,options};
}

function permutations(a){return a.length?a.flatMap((x,i)=>permutations(a.filter((_,j)=>i!==j)).map(t=>[x,...t])):[[]];}
for(const order of permutations([0,1,2,3])){
 const e=environment();e.loadDetails();await e.flush();const plugins=await Promise.all(modules.map(m=>m.default.plugin({})));
 for(const index of order){const init=plugins[index].init();assert.equal(plugins[index].init(),init);await init;await e.flush();}
 assert.equal(plugins[3].getState(),'ready',e.errors.join('\n'));assert.equal(plugins[3].getModelState(),'bound');
 assert.equal(e.requests[0].ids,'123');assert.equal(e.field.style.visibility,'hidden');assert.equal(e.card.querySelectorAll('.dk-carousel-stats').length,2);
 const scripts=e.loaded.filter(u=>u.includes('/vehicle_carousel/')&&u.endsWith('.js'));assert.deepEqual(scripts.map(x=>x.split('/').pop()),['carousel_native.js','carousel_layout.js','carousel.js']);
 const crew=e.window.__dkCrewProgression;await plugins[3].destroy();await plugins[3].destroy();assert.equal(crew.getRow(101).id,101);assert(e.window.__dkHangarClock&&e.window.__dkHangarMarks&&e.window.__dkCrewDetails);
 const again=await modules[3].default.plugin({});await again.init();await e.flush();await plugins[2].destroy();assert.equal(again.getState(),'ready');
 await again.destroy();await plugins[0].destroy();await plugins[1].destroy();e.window.__dkCrewDetails.dispose();e.clean();
}
for(const failSuffix of ['carousel_native.js','carousel_layout.js','carousel.js','carousel.css','fonts.css']){
 const e=environment({failSuffix});const crew=await modules[2].default.plugin({});await crew.init();await e.flush();const p=await modules[3].default.plugin({});await p.init();await e.flush();
 assert.equal(p.getState(),'failed');assert(p.getDiagnostics().length);assert(e.window.__dkCrewProgression.getRow(101));await p.destroy();await crew.destroy();e.clean();
}
for(const suffix of ['carousel_native.js','carousel_layout.js','carousel.js']){
 const e=environment({syntaxSuffix:suffix}),p=await modules[3].default.plugin({});await p.init();await e.flush();assert.equal(p.getState(),'failed');await p.destroy();e.clean();
}
for(const suffix of ['carousel_native.js','carousel_layout.js','carousel.js'])for(const timeout of [false,true]){
 const e=environment({deferURL:suffix}),p=await modules[3].default.plugin({});const init=p.init();await e.flush();
 if(timeout){[...e.deadlines.values()].forEach(f=>f());e.deadlines.clear();assert.equal(p.getState(),'failed');}else await p.destroy();
 await init;const blocked=await modules[3].default.plugin({});await blocked.init();assert.equal(blocked.getState(),'failed');
 e.deferred.splice(0).forEach(f=>f());await e.flush();await p.destroy();await blocked.destroy();e.clean();
 e.options.deferURL=null;const next=await modules[3].default.plugin({});await next.init();await e.flush();await next.destroy();e.clean();
}
{
 const e=environment();e.models.delete(46);const p=await modules[3].default.plugin({});await p.init();await e.flush();assert.equal(p.getState(),'ready');assert.equal(p.getModelState(),'waiting');assert.equal(e.requests.length,0);
 e.models.set(46,{model:e.carousel});e.events.fire('subViews.onAdded');await e.flush();assert.equal(e.requests.length,1);
 const old=e.carousel;e.models.set(46,{model:{...old,onRequestVehicles:args=>e.requests.push({replacement:args.ids})}});e.events.fire('subViews.onAdded');await e.flush();assert(e.requests.some(a=>a.replacement==='123'));
 const callback=e.observers.find(o=>o.connected).fn;const count=e.requests.length;await p.destroy();callback([{target:e.card,addedNodes:[],removedNodes:[]}]);e.events.fire('viewEnv.onDataChanged');await e.flush();assert.equal(e.requests.length,count);e.clean();
}
{
 const e=environment(),p=await modules[3].default.plugin({});await p.init();await e.flush();
 // A replaced field inside the same card needs remount; restoring an externally changed style is forbidden.
 e.field.style.visibility='collapse';e.observers.find(o=>o.connected).fn([{target:e.card,addedNodes:[],removedNodes:[]}]);await e.flush();
 assert.equal(e.card.querySelectorAll('.dk-carousel-stats').length,2);await p.destroy();assert.equal(e.field.style.visibility,'collapse');e.field.style.visibility='visible';e.clean();
}
{
 const e=environment(),p=await modules[3].default.plugin({});await p.init();await e.flush();
 const off=e.context.engine.off;e.context.engine.off=(...args)=>{off(...args);throw new Error('off failed');};
 const remove=e.context.viewEnv.removeDataChangedCallback;e.context.viewEnv.removeDataChangedCallback=id=>{remove(id);throw new Error('unsubscribe failed');};
 await p.destroy();assert(p.getDiagnostics().some(x=>x.includes('unsubscribe failed')));e.clean();
}
{
 const e=environment(),p=await modules[3].default.plugin({});await p.init();await e.flush();const foreign={generation:{},dispose(){throw new Error('foreign owner');}};e.window.DKCarouselNative=foreign;
 await p.destroy();assert.equal(e.window.DKCarouselNative,foreign);delete e.window.DKCarouselNative;e.clean();
}
{
 const e=environment();e.loadDetails();await e.flush();const p=await modules[3].default.plugin({});await p.init();await e.flush();
 e.context.engine.whenReady=Promise.reject(new Error('crew unavailable'));const crew=await modules[2].default.plugin({});await crew.init();await e.flush();assert.equal(crew.getState(),'failed');assert.equal(p.getState(),'ready');await crew.destroy();await p.destroy();e.window.__dkCrewDetails.dispose();e.clean();
}

for(const fault of ['engine','subscription','observer','request','getter','create','append','mount']){
 const e=environment();
 if(fault==='engine')e.context.engine.whenReady=Promise.reject(new Error('engine failure'));
 if(fault==='subscription')e.context.viewEnv.addDataChangedCallback=()=>{throw new Error('subscribe failure');};
 if(fault==='observer'){class Broken{constructor(){throw new Error('observer failure');}}e.context.MutationObserver=e.window.MutationObserver=Broken;}
 if(fault==='request')e.carousel.onRequestVehicles=()=>{throw new Error('command failure');};
 if(fault==='getter')Object.defineProperty(e.carousel,'payload',{get(){throw new Error('payload failure');}});
 if(fault==='create'){const create=e.document.createElement;e.document.createElement=tag=>{if(tag==='script')throw new Error('create failure');return create(tag);};}
 if(fault==='mount'){const create=e.document.createElement;e.document.createElement=tag=>{if(tag==='div'&&e.window.__dkCarouselStats)throw new Error('mount failure');return create(tag);};}
 if(fault==='append'){const append=e.document.head.appendChild;e.document.head.appendChild=node=>{if(node.tagName==='SCRIPT')throw new Error('append failure');return append(node);};}
 const p=await modules[3].default.plugin({});await p.init();await e.flush();assert.equal(p.getState(),'failed',fault);assert(p.getDiagnostics().length);await p.destroy();e.clean();
}
{
 const e=environment(),p=await modules[3].default.plugin({});await p.init();await e.flush();const foreign={generation:{}};e.window.__dkCarouselStats=foreign;
 await p.destroy();assert.equal(e.window.__dkCarouselStats,foreign);delete e.window.__dkCarouselStats;e.clean();
}
{
 const e=environment();let bareEvents=0;e.window.addEventListener('dk-carousel-config',ev=>{bareEvents++;assert.equal(ev.detail,undefined);});
 const p=await modules[3].default.plugin({});await p.init();await e.flush();assert(bareEvents>0);const before=bareEvents;await p.destroy();assert(bareEvents>before);
 // This listener belongs to the document, so the plugin must preserve it.
 assert.equal(e.window.listeners['dk-carousel-config'].length,1);e.window.listeners['dk-carousel-config']=[];e.clean();
}

{
 const e=environment(),p=await modules[3].default.plugin({});await p.init();await e.flush();
 e.document.body.removeChild(e.card);e.document.querySelectorAll=()=>[];e.observers.find(o=>o.connected).fn([{target:e.document.body,addedNodes:[],removedNodes:[e.card]}]);await e.flush();
 assert.equal(e.requests[e.requests.length-1].ids,'');assert.equal(e.card.querySelectorAll('.dk-carousel-stats').length,0);
 e.document.body.appendChild(e.card);await p.destroy();e.clean();
}
{
 const e=environment({deferURL:'carousel.js'}),p=await modules[3].default.plugin({});const init=p.init();await e.flush();
 const changed={...e.carousel,payload:JSON.stringify({...JSON.parse(e.carousel.payload),vehicles:{}}),onRequestVehicles:args=>e.requests.push({late:args.ids})};
 e.models.set(46,{model:changed});e.deferred.splice(0).forEach(f=>f());await init;await e.flush();assert(e.requests.some(x=>x.late==='123'));await p.destroy();e.clean();
}

{
 const e=environment(),p=await modules[3].default.plugin({});let old;e.carousel.onRequestVehicles=()=>{old=e.window.__dkCarouselStats;return p.destroy();};
 await p.init();await e.flush();assert.equal(p.getState(),'destroyed');assert.equal(old.getState(),'destroyed');e.clean();
}

{
 const e=environment(),urls=paths.map(path=>'coui://gui/gameface/mods/driftkings/'+path);
 const loader=new NativeLoaderContract(async url=>modules[urls.indexOf(url)]);const results=await loader.reconcile(urls);await e.flush();
 assert.equal(loader.sdk.size,4);assert(results.every(x=>x.status==='fulfilled'));
 await loader.reconcile(urls.slice(0,3));assert.equal(e.window.__dkCarouselStats,undefined);assert(e.window.__dkCrewProgression.getRow(101));await loader.reconcile([]);e.clean();
}
{
 const e=environment(),urls=paths.map(path=>'coui://gui/gameface/mods/driftkings/'+path);
 const loader=new NativeLoaderContract(async url=>{if(url===urls[3])throw new Error('carousel entrypoint import failed');return modules[urls.indexOf(url)];});
 const results=await loader.reconcile(urls);await e.flush();assert.equal(results[3].status,'rejected');assert.equal(loader.sdk.size,3);assert(e.window.__dkCrewProgression.getRow(101));
 // Expected CT-contract limitation: failed import is retained and removal rejects.
 await assert.rejects(loader.reconcile(urls.slice(0,3)));
 // Harness-only teardown of successful owners; this is NOT loader recovery.
 for(const owner of loader.sdk.values())await owner.destroy();e.clean();
}
output('Native carousel actual sources: 24 orders; four SDK identities and retained import rejection CONTRACT; Wulf command arguments; sequential helpers/CSS; models/recycling; isolated failures/late generations; selective cleanup and crew continuity passed');
`;
const run=spawnSync(process.execPath,['--input-type=module','-e',driver],{encoding:'utf8'});assert.equal(run.status,0,run.stdout+run.stderr);console.log(run.stdout.trim());
