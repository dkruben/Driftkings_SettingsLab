'use strict';
const assert = require('assert'), {spawnSync} = require('child_process');
const code = String.raw`
const assert = require('assert');
const {NativeLoaderContract} = require('./tests/support/frontend/native_loader_contract');
(async () => {
 const valid = {default: {plugin: async () => ({init: () => Promise.resolve(() => null), destroy: () => Promise.resolve()})}};
 for (const failure of ['missing-url', 'syntax', 'import', 'default', 'factory-type', 'factory', 'init', 'sync-init', 'destroy', 'rejected-destroy']) {
  const loader = new NativeLoaderContract(async url => {
   if (url === 'clock') return valid;
   if (['missing-url','syntax','import'].includes(failure)) throw new Error(failure);
   if (failure === 'default') return {};
   if (failure === 'factory-type') return {default:{plugin:7}};
   if (failure === 'factory') return {default: {plugin() {throw new Error('factory');}}};
   return {default:{plugin: async () => ({init() {if(failure==='sync-init') throw new Error('sync-init'); return failure==='init'?Promise.reject(new Error('init')):Promise.resolve(()=>null);}, destroy() {if(failure==='rejected-destroy')return Promise.reject(new Error('destroy'));throw new Error('destroy');}})}};
  });
  const url='coui://gui/gameface/mods/driftkings/mono/test/'+failure+'.js';
  const settled=await loader.reconcile(['clock',url]);
  assert.equal(settled[0].status,'fulfilled');
  assert.equal(settled[1].status,failure.includes('destroy')?'fulfilled':'rejected');
  if(!failure.includes('destroy')) assert.equal((await loader.reconcile(['clock',url]))[1].status,'rejected');
  await assert.rejects(loader.reconcile(['clock']));
  await assert.rejects(loader.reconcile(['clock',url]));
  const fresh=new NativeLoaderContract(async()=>valid); assert.equal((await fresh.reconcile([url]))[0].status,'fulfilled');
 }
 const loader=new NativeLoaderContract(async()=>valid);
 assert.equal(loader.identity('coui://gui/gameface/mods/driftkings/main/clock_plugin.js'),Symbol.for('unknown'));
 const first=await loader.load('clock'); const collision=await loader.load('another');
 assert.equal(collision,loader.sdk.get(first.id)); // distinct URLs can return the SAME raw instance.
 assert.notEqual(loader.identity('clock'),loader.identity('coui://gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js'));
 let finish; const waiting=new NativeLoaderContract(()=>new Promise(resolve=>{finish=resolve;}));
 const loading=waiting.reconcile(['pending']); await new Promise(resolve=>setImmediate(resolve));
 const removal=waiting.reconcile([]); finish(valid); await loading; await removal;
 assert.equal(Object.keys(waiting.pending).length,0);
 console.log('CT loader CONTRACT model: retained rejections, poisoned reconciliation, identity collision and pending removal demonstrated');
})().catch(error=>{console.error(error);process.exitCode=1;});`;
const run = spawnSync(process.execPath, ['-e', code], {encoding:'utf8'});
assert.equal(run.status, 0, run.stdout + run.stderr);
console.log(run.stdout.trim());
