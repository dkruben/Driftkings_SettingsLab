'use strict';
const assert = require('assert'), {spawnSync} = require('child_process');
const driver = String.raw`
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const require=createRequire(process.cwd()+'/tests/run_frontend.js');
const {Node}=require('./support/frontend/dom_fixture');
const output=console.log.bind(console);
const base='mod/res/gui/gameface/mods/driftkings/';
const entry=await import('data:text/javascript;base64,'+fs.readFileSync(base+'mono/driftkings/hangar_marks/marks_plugin.js').toString('base64'));
const clockEntry=await import('data:text/javascript;base64,'+fs.readFileSync(base+'main/clock_plugin.js').toString('base64'));
function environment(options={}) {
 const window=new Node('window'), document=new Node('document'), events=new Node('engine');
 document.body=new Node('body'); document.head=new Node('head'); document.documentElement=new Node('html');
 let elements=0;
 document.createElement=tag=>{if(options.partial && ++elements===18) throw new Error('partial DOM'); return new Node(tag);};
 document.querySelector=()=>{if(options.place) throw new Error('place callback'); return null;};
 window.getComputedStyle=node=>({fontSize:'1px',opacity:'1',display:node.style.display||'',visibility:'visible'});
 window.innerWidth=1920;window.innerHeight=1080;
 const clockConfig={visible:true,hidePrestige:true,formats:[{format:'%H:%M:%S',x:12,y:20,width:100,textFormat:{size:18}}]};
 const data={state:'data',target:{eligible:true,threshold:95},currentMark:90.63,displayMarks:2,vehicle:'one',tier:6,
  milestone:{nextMilestone:95,gap:4.37},recent:{samples:[]},labels:{current:'Current',more:'More'},config:{visible:true}};
 const clockModel={DriftkingsUI:{name:'DriftkingsHangarClock'},payload:JSON.stringify({config:clockConfig})};
 const marksModel={DriftkingsUI:{name:'DriftkingsMarksOnGunHangar'},payload:JSON.stringify(data)};
 window.subViews={ids:()=>[42,43],get:id=>({model:id===42?clockModel:marksModel})};
 const jobs=new Map(), deadlines=new Map(), intervals=new Map(), frames=new Map(), callbacks=new Map(), deferred=[];let next=0;
 const context={window,document,console:{info(){},error(){}},engine:{whenReady:Promise.resolve(),on:events.addEventListener.bind(events),off:events.removeEventListener.bind(events)},
  viewEnv:{addDataChangedCallback:(name,id)=>{if(options.subscription&&id===43)throw new Error('subscription');callbacks.set(++next,id);return next;},removeDataChangedCallback:id=>callbacks.delete(id)},
  setTimeout:(fn,delay)=>{(delay?deadlines:jobs).set(++next,fn);return next;},clearTimeout:id=>{jobs.delete(id);deadlines.delete(id);},
  setInterval:fn=>{intervals.set(++next,fn);return next;},clearInterval:id=>intervals.delete(id),
  requestAnimationFrame:fn=>{frames.set(++next,fn);return next;},cancelAnimationFrame:id=>frames.delete(id)};
 Object.assign(globalThis,context);vm.createContext(context);
 const append=document.head.appendChild.bind(document.head);
 document.head.appendChild=node=>{
  append(node);
  const url=node.src||node.href;
  const execute=()=>{
   if(options.resource && url.includes(options.resource)){node.onerror();return;}
   if(node.tagName==='SCRIPT') vm.runInContext(fs.readFileSync(base+url.split('/mods/driftkings/')[1],'utf8'),context,{filename:url});
   if(node.onload)node.onload();
  };
  if(options.defer && url.includes(options.defer))deferred.push(execute);else queueMicrotask(execute);
  return node;
 };
 async function flush(){for(let i=0;i<20;i++){await Promise.resolve();const batch=[...jobs.values()];jobs.clear();batch.forEach(fn=>fn());}}
 function clean(){assert.equal(document.body.children.length,0);assert.equal(document.head.children.length,0);assert.equal(jobs.size,0);assert.equal(deadlines.size,0);assert.equal(intervals.size,0);assert.equal(frames.size,0);assert.equal(callbacks.size,0);
  for(const target of [window,document,events])for(const list of Object.values(target.listeners))assert.equal(list.length,0);
  assert.equal(window.__dkHangarMarks,undefined);assert.equal(window.__dkHangarMarksLoad,undefined);}
 return {window,document,context,events,data,marksModel,clockModel,clockConfig,flush,clean,intervals,frames,callbacks,deferred,options,deadlines};
}
for(const order of ['clock-first','marks-first']){
 const e=environment(),clock=await clockEntry.default.plugin({}),marks=await entry.default.plugin({});
 for(const plugin of order==='clock-first'?[clock,marks]:[marks,clock]){await plugin.init();await e.flush();}
 assert.equal(marks.getState(),'ready');assert(e.window.__dkHangarClock);assert(e.window.__dkHangarMarks);
 const root=e.document.body.querySelector('.dk-moe');assert(root.textContent.includes('90.63%'));
 e.data.currentMark=92;e.data.vehicle='two';e.marksModel.payload=JSON.stringify(e.data);e.events.fire('viewEnv.onDataChanged');await e.flush();assert(root.textContent.includes('92.00%'));
 root.querySelector('.dk-moe-card').fire('click');assert.equal(e.frames.size,1);
 const late=[...e.intervals.values(),...e.frames.values()];await marks.destroy();late.forEach(fn=>fn());await marks.destroy();assert(e.window.__dkHangarClock);assert.equal(e.frames.size,0);
 e.clockConfig.hidePrestige=false;e.clockModel.payload=JSON.stringify({config:e.clockConfig});e.events.fire('viewEnv.onDataChanged');await e.flush();
 assert.equal(e.document.body.children.find(node=>node.tagName==='STYLE').textContent,'');
 const again=await entry.default.plugin({});await again.init();await e.flush();assert.equal(again.getState(),'ready');
 await clock.destroy();assert(e.window.__dkHangarMarks);await again.destroy();e.clean();
}
for(const options of [{resource:'marks.js'},{resource:'marks.css'},{partial:true},{subscription:true}]){
 const e=environment(options),clock=await clockEntry.default.plugin({});await clock.init();await e.flush();
 const plugin=await entry.default.plugin({});const pending=plugin.init();assert.equal(plugin.init(),pending);await pending;await e.flush();
 assert.equal(plugin.getState(),'failed',JSON.stringify(options));assert(plugin.getDiagnostics().length);assert(e.window.__dkHangarClock);assert.equal(e.document.body.querySelector('.dk-moe'),null);
 e.clockConfig.hidePrestige=false;e.clockModel.payload=JSON.stringify({config:e.clockConfig});e.events.fire('viewEnv.onDataChanged');await e.flush();assert.equal(e.document.body.children.find(node=>node.tagName==='STYLE').textContent,'');
 await plugin.destroy();await clock.destroy();await e.flush();e.clean();
}
for(const type of ['timer','callback','model','cleanup']){
 const e=environment(),plugin=await entry.default.plugin({});await plugin.init();await e.flush();
 if(type==='timer'){e.options.place=true;[...e.intervals.values()].forEach(fn=>fn());}
 if(type==='callback'){e.options.place=true;e.document.body.querySelector('.dk-moe-card').fire('click');}
 if(type==='model'){e.marksModel.payload='{invalid';e.events.fire('viewEnv.onDataChanged');await e.flush();}
 if(type==='cleanup'){const off=e.context.engine.off;e.context.engine.off=(...args)=>{off(...args);throw new Error('cleanup fault');};}
 if(type!=='cleanup')assert.equal(plugin.getState(),'failed');
 await plugin.destroy();if(type==='cleanup')assert(plugin.getDiagnostics().some(text=>text.includes('cleanup fault')));await e.flush();e.clean();
}
{
 const e=environment({defer:'marks.js'}),plugin=await entry.default.plugin({});const loading=plugin.init();await e.flush();
 [...e.deadlines.values()].forEach(fn=>fn());e.deadlines.clear();await loading;
 assert.equal(plugin.getState(),'failed');assert(plugin.getDiagnostics().some(text=>text.includes('Timed out')));
 e.deferred.splice(0).forEach(fn=>fn());await e.flush();await plugin.destroy();e.clean();
}
// A late classic script may still execute. It sees its cancelled generation, not a new owner.
{
 const e=environment({defer:'marks.js'}),plugin=await entry.default.plugin({});const loading=plugin.init();await e.flush();
 await plugin.destroy();await loading;assert.equal(plugin.getState(),'destroyed');assert.equal(e.deadlines.size,0);assert.equal(plugin.getPendingResources(),1);
 const blocked=await entry.default.plugin({});await blocked.init();assert.equal(blocked.getState(),'failed');
 e.deferred.splice(0).forEach(fn=>fn());await e.flush();await blocked.destroy();e.clean();
 e.options.defer=null;const next=await entry.default.plugin({});await next.init();await e.flush();await next.destroy();e.clean();
}
output('Native marks actual entrypoint/renderers: two orders, vehicle updates, CSS/script/DOM/subscription/callback/timer/model/cleanup faults, retirement, clock continuity and independent disposal passed');
`;
const run=spawnSync(process.execPath,['--input-type=module','-e',driver],{encoding:'utf8'});
assert.equal(run.status,0,run.stdout+run.stderr);console.log(run.stdout.trim());
