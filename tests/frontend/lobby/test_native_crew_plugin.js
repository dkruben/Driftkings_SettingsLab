'use strict';
const assert=require('assert'),{spawnSync}=require('child_process');
const driver=String.raw`
import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';import {createRequire} from 'node:module';
const require=createRequire(process.cwd()+'/tests/run_frontend.js'),{Node}=require('./support/frontend/dom_fixture');
const {NativeLoaderContract}=require('./support/frontend/native_loader_contract');
const output=console.log.bind(console),base='mod/res/gui/gameface/mods/driftkings/';
const paths=['main/clock_plugin.js','mono/driftkings/hangar_marks/marks_plugin.js','mono/driftkings/crew_progression/crew_plugin.js'];
const modules=await Promise.all(paths.map(path=>import('data:text/javascript;base64,'+fs.readFileSync(base+path).toString('base64'))));
function environment(options={}){
 const window=new Node('window'),document=new Node('document'),events=new Node('engine'),detailsHost=new Node('div');
 document.head=new Node('head');document.body=new Node('body');document.documentElement=new Node('html');document.body.appendChild(detailsHost);
 document.createElement=tag=>{if(options.create&&tag==='script'&&window.__dkCrewProgressionLoad)throw new Error('create script');return new Node(tag);};document.querySelector=selector=>selector.includes('TankmanTooltipApp')?detailsHost:null;
 window.innerWidth=1920;window.innerHeight=1080;window.getComputedStyle=node=>({fontSize:'1px',opacity:'1',display:node.style.display||'',visibility:'visible'});
 window.dispatchEvent=event=>window.fire(event.type);
 const clockConfig={visible:true,hidePrestige:true,formats:[{format:'%H:%M:%S',x:12,y:20,width:100,textFormat:{size:18}}]};
 const clock={DriftkingsUI:{name:'DriftkingsHangarClock'},payload:JSON.stringify({config:clockConfig})};
 const marks={DriftkingsUI:{name:'DriftkingsMarksOnGunHangar'},payload:JSON.stringify({config:{visible:true},state:'data',currentMark:90,displayMarks:2,target:{eligible:true},milestone:{},recent:{samples:[]}})};
 const crew={DriftkingsUI:{name:'DriftkingsCrewProgression'},payload:'{}'};
 const details={DriftkingsUI:{name:'DriftkingsCrewDetails'},payload:JSON.stringify({surface:'tooltip',config:{visible:true},lines:['detail XP'],kinds:['xp']})};
 const models=new Map([[42,{model:clock}],[43,{model:marks}],[44,{model:crew}],[45,{model:details}]]);
 window.subViews={ids:()=>[...models.keys()],get:id=>models.get(id)};
 const jobs=new Map(),deadlines=new Map(),intervals=new Map(),frames=new Map(),callbacks=new Map(),deferred=[],errors=[];let next=0,registers=0;
 const context={window,document,Event:class {constructor(type){this.type=type;}},console:{info(){},error:error=>errors.push(String(error))},
  engine:{whenReady:Promise.resolve(),on:(name,callback)=>{if(options.partial&&window.__dkCrewProgression&&++registers===2)throw new Error('partial API subscription');events.addEventListener(name,callback);},off:events.removeEventListener.bind(events)},
  viewEnv:{addDataChangedCallback:(name,id)=>{if(options.subscription&&id===44)throw new Error('crew subscription');callbacks.set(++next,id);return next;},removeDataChangedCallback:id=>callbacks.delete(id)},
  setTimeout:(fn,delay)=>{(delay?deadlines:jobs).set(++next,fn);return next;},clearTimeout:id=>{jobs.delete(id);deadlines.delete(id);},
  setInterval:fn=>{intervals.set(++next,fn);return next;},clearInterval:id=>intervals.delete(id),requestAnimationFrame:fn=>{frames.set(++next,fn);return next;},cancelAnimationFrame:id=>frames.delete(id)};
 Object.assign(globalThis,context);vm.createContext(context);
 const append=document.head.appendChild.bind(document.head);
 document.head.appendChild=node=>{append(node);const url=node.src||node.href;const execute=()=>{
  if(options.missing&&url.endsWith('/crew.js')){node.onerror();return;}
  if(node.tagName==='SCRIPT'){
   try{if(options.syntax&&url.endsWith('/crew.js'))throw new SyntaxError('renderer syntax');vm.runInContext(fs.readFileSync(base+url.split('/mods/driftkings/')[1],'utf8'),context,{filename:url});}catch(error){errors.push(String(error));}
  }
  if(node.onload)node.onload();
 };if(options.defer&&url.endsWith('/crew.js'))deferred.push(execute);else queueMicrotask(execute);return node;};
 function setCrew(id=101,vehicleId=11){crew.payload=JSON.stringify({config:{visible:true},vehicleId,rows:[{slot:0,id,lines:['XP '+id],kinds:['xp']}]});}
 setCrew();
 async function flush(){for(let i=0;i<24;i++){await Promise.resolve();const work=[...jobs.values()];jobs.clear();work.forEach(fn=>fn());}}
 function loadDetails(){vm.runInContext(fs.readFileSync(base+'crew_details/details.js','utf8'),context);}
 function clean(){assert.equal(document.head.children.length,0);assert.equal(document.body.children.length,1);assert.equal(detailsHost.children.length,0);
  for(const map of [jobs,deadlines,intervals,frames,callbacks])assert.equal(map.size,0);
  for(const target of [window,document,events])for(const handlers of Object.values(target.listeners))assert.equal(handlers.length,0);
  assert.equal(window.__dkCrewProgression,undefined);assert.equal(window.__dkCrewProgressionLoad,undefined);
 }
 return {window,document,events,context,crew,clock,clockConfig,models,callbacks,jobs,deadlines,deferred,errors,details,detailsHost,loadDetails,setCrew,flush,clean,options};
}
for(const order of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]){
 const e=environment();e.loadDetails();await e.flush();const plugins=await Promise.all(modules.map(module=>module.default.plugin({})));
 for(const index of order){const init=plugins[index].init();assert.equal(plugins[index].init(),init);await init;await e.flush();}
 assert.equal(plugins[2].getState(),'ready',JSON.stringify({order,errors:e.errors,diagnostics:plugins[2].getDiagnostics()}));assert.equal(plugins[2].getSnapshotState(),'ready');assert(e.window.__dkCrewProgression.getRow(101));
 assert(e.detailsHost.textContent.includes('detail XP'));const old=e.window.__dkCrewProgression;
 await plugins[2].destroy();await plugins[2].destroy();assert.equal(old.getRow(101),null);assert(e.window.__dkHangarClock);assert(e.window.__dkHangarMarks);assert(e.window.__dkCrewDetails);
 e.details.payload=JSON.stringify({surface:'tooltip',config:{visible:true},lines:['next detail'],kinds:['xp']});
 e.clockConfig.hidePrestige=false;e.clock.payload=JSON.stringify({config:e.clockConfig});e.events.fire('viewEnv.onDataChanged');await e.flush();
 assert(e.detailsHost.textContent.includes('next detail'));assert.equal(e.document.body.children.find(node=>node.tagName==='STYLE').textContent,'');
 const again=await modules[2].default.plugin({});await again.init();await e.flush();await plugins[0].destroy();assert(e.window.__dkCrewProgression);assert(e.window.__dkHangarMarks);
 await plugins[1].destroy();assert(e.window.__dkCrewProgression);await again.destroy();e.window.__dkCrewDetails.dispose();e.clean();
}
for(const options of [{missing:true},{syntax:true},{subscription:true},{partial:true},{create:true},{promise:true},{data:true},{getter:true}]){
 const e=environment(options);e.loadDetails();await e.flush();const clock=await modules[0].default.plugin({}),marks=await modules[1].default.plugin({});await clock.init();await marks.init();await e.flush();
 if(options.promise)e.context.engine.whenReady=Promise.reject(new Error('engine ready rejected'));
 const plugin=await modules[2].default.plugin({});await plugin.init();await e.flush();
 if(options.data){e.crew.payload='{invalid';e.events.fire('viewEnv.onDataChanged');await e.flush();}
 if(options.getter){Object.defineProperty(e.crew,'payload',{get(){throw new Error('payload getter');}});e.events.fire('viewEnv.onDataChanged');await e.flush();}
 assert.equal(plugin.getState(),'failed');assert(plugin.getDiagnostics().length);assert.equal(e.window.__dkCrewProgression,undefined);
 e.details.payload=JSON.stringify({surface:'tooltip',config:{visible:true},lines:['still active'],kinds:['xp']});e.events.fire('viewEnv.onDataChanged');await e.flush();assert(e.detailsHost.textContent.includes('still active'));assert(e.window.__dkHangarClock);assert(e.window.__dkHangarMarks);
 await plugin.destroy();await marks.destroy();await clock.destroy();e.window.__dkCrewDetails.dispose();e.clean();
}
{
 const e=environment();e.models.delete(44);const plugin=await modules[2].default.plugin({});await plugin.init();await e.flush();
 assert.equal(plugin.getState(),'ready');assert.equal(plugin.getSnapshotState(),'waiting');assert.equal(e.window.__dkCrewProgression.getRow(101),null);
 e.models.set(44,{model:e.crew});e.events.fire('subViews.onAdded');await e.flush();assert.equal(plugin.getSnapshotState(),'ready');
 await plugin.destroy();e.clean();
}
// Resources changed BEFORE the delayed renderer executes: first snapshot must be current.
{
 const e=environment({defer:true}),plugin=await modules[2].default.plugin({});const init=plugin.init();e.setCrew(202,22);e.deferred.splice(0).forEach(fn=>fn());await init;await e.flush();
 assert.equal(e.window.__dkCrewProgression.getRow(101),null);assert.equal(e.window.__dkCrewProgression.getRow(202).id,202);
 const old=e.window.__dkCrewProgression,foreign={getRow:()=>null,dispose(){throw new Error('foreign owner');}};e.window.__dkCrewProgression=foreign;old.dispose();await plugin.destroy();assert.equal(e.window.__dkCrewProgression,foreign);delete e.window.__dkCrewProgression;e.clean();
}
for(const timeout of [false,true]){
 const e=environment({defer:true}),plugin=await modules[2].default.plugin({});const init=plugin.init();
 if(timeout){[...e.deadlines.values()].forEach(fn=>fn());e.deadlines.clear();assert.equal(plugin.getState(),'failed');}else await plugin.destroy();
 await init;assert.equal(e.deadlines.size,0);assert.equal(plugin.getPendingResources(),1);
 const blocked=await modules[2].default.plugin({});await blocked.init();assert.equal(blocked.getState(),'failed');
 e.deferred.splice(0).forEach(fn=>fn());await e.flush();await plugin.destroy();await blocked.destroy();e.clean();
 e.options.defer=false;const next=await modules[2].default.plugin({});await next.init();await e.flush();await next.destroy();e.clean();
}
// Cleanup operations report faults but continue withdrawing only the crew API/resources.
{
 const e=environment(),plugin=await modules[2].default.plugin({});await plugin.init();await e.flush();
 const off=e.context.engine.off;e.context.engine.off=(...args)=>{off(...args);throw new Error('off failed');};
 const remove=e.context.viewEnv.removeDataChangedCallback;e.context.viewEnv.removeDataChangedCallback=id=>{remove(id);throw new Error('unsubscribe failed');};
 await plugin.destroy();assert(plugin.getDiagnostics().some(text=>text.includes('unsubscribe failed')));e.clean();
}
// Three real entry points through the CONTRACT model (not the real CT loader).
{
 const e=environment();const urls=paths.map(path=>'coui://gui/gameface/mods/driftkings/'+path);
 const loader=new NativeLoaderContract(async url=>modules[urls.indexOf(url)]);
 const results=await loader.reconcile(urls);await e.flush();assert.equal(loader.sdk.size,3);assert(results.every(result=>result.status==='fulfilled'));
 await loader.reconcile(urls.slice(0,2));assert(e.window.__dkHangarClock);assert(e.window.__dkHangarMarks);assert.equal(e.window.__dkCrewProgression,undefined);
 await loader.reconcile([]);e.clean();
}
output('Native crew actual entrypoints: six orders, three SDK IDs, protected CrewDetails, clock/marks continuity, failures, pending generations and cleanup passed');
`;
const run=spawnSync(process.execPath,['--input-type=module','-e',driver],{encoding:'utf8'});assert.equal(run.status,0,run.stdout+run.stderr);console.log(run.stdout.trim());
