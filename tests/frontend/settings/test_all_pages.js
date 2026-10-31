/* Every live backend schema opens in the redesigned frontend. */
const assert=require('assert');
const data=require('../../support/frontend/schema_fixture');
const {createEnvironment}=require('../../support/frontend/dom_fixture');
const env=createEnvironment(), {DK,app,callbacks}=env;
callbacks.schema(data.schema);
let count=0;
for(const mod of data.schema.mods){
    assert.notStrictEqual(data.state.status[mod.id].status,'configError',mod.id);
    const state=Object.assign({},data.state,{selected:mod.id});
    callbacks.state(state);callbacks.state(state);env.flush();
    assert(app.querySelector('.dk-title').textContent.includes(mod.name),mod.id);
    assert(app.querySelectorAll('.dk-row').length || mod.preview || (mod.controls.length===1&&app.querySelector('.dk-power').style.display!=='none'),mod.id);
    count+=mod.controls.length;
}
assert(data.schema.mods.length>=35);assert(count>=1100);
// Clan collection keeps its original owner/action contract but is shown under general settings.
const main=data.schema.mods.find(m=>m.id==='legacy.main');
const clan=data.schema.mods.find(m=>m.id==='legacy.AutoClaimClan');
assert(main&&clan);
callbacks.state(Object.assign({},data.state,{selected:main.id}));env.flush();
assert(!app.querySelectorAll('.dk-nav-name').some(n=>n.textContent===clan.name));
const clanRow=app.querySelectorAll('.dk-row').find(n=>n.querySelector('.dk-row-label')&&n.querySelector('.dk-row-label').textContent===clan.name);
assert(clanRow);clanRow.querySelector('.dk-switch').fire('click');
assert.strictEqual(env.sent[env.sent.length-1][1].mod,clan.id);
// Full settings schema stays interactive through the core command routes.
callbacks.state(Object.assign({},data.state,{selected:'dk.settings'}));
const labels=data.schema.labels;
assert.strictEqual(app.querySelector('.dk-construction').textContent,labels.constructionNotice);
function button(text,root=app){const found=root.querySelectorAll('button').find(n=>n.textContent===text);assert(found,text);return found;}
button(labels.profiles).fire('click');assert(DK.modal.top());
button(labels.profileExport,DK.modal.top().panel).fire('click');
assert.strictEqual(env.sent[env.sent.length-1][0],'profile');assert.strictEqual(env.sent[env.sent.length-1][1].operation,'export');
DK.modal.closeAll();
button(labels.saveApply).fire('click');assert.strictEqual(env.sent[env.sent.length-1][0],'save');
const core=Object.assign({},data.state,{selected:'dk.settings',profiles:['default','test'],unsaved:false});
callbacks.state(core);button(labels.profiles).fire('click');
let panel=DK.modal.top().panel;
const beforeDelete=env.sent.length;button(labels.profileDelete,panel).fire('click');
assert.strictEqual(env.sent.length,beforeDelete,'deletion requires the second click');
button(labels.confirmDelete,panel).fire('click');assert.strictEqual(env.sent[env.sent.length-1][1].operation,'delete');
DK.modal.closeAll();
callbacks.state(Object.assign({},core,{confirm:true}));button(labels.confirmStay,DK.modal.top().panel).fire('click');
assert.deepStrictEqual(JSON.parse(JSON.stringify(env.sent[env.sent.length-1])),['confirm',{choice:'stay'}]);
callbacks.state(Object.assign({},core,{restartPrompt:true,inBattle:true}));
let restart=button(labels.restartNow,DK.modal.top().panel);assert(restart.disabled);
const blocked=env.sent.length;restart.fire('click');assert.strictEqual(env.sent.length,blocked);
callbacks.state(Object.assign({},core,{restartPrompt:true}));button(labels.restartNow,DK.modal.top().panel).fire('click');
assert.deepStrictEqual(JSON.parse(JSON.stringify(env.sent[env.sent.length-1])),['restart',{choice:'now'}]);callbacks.state(core);
const update={installedVersion:'test',channel:'beta',lastCheck:null,changelog:[],compatible:true};
for(const [fields,label,action] of [
    [{status:'AVAILABLE',canDownload:true},'updates.download','download_update'],
    [{status:'DOWNLOADING',canCancel:true},'updates.cancelDownload','cancel_update_download'],
    [{status:'READY',canInstall:true},'updates.install','schedule_update'],
    [{status:'RESTART_REQUIRED',installScheduled:true,canRestart:true},'restartNow','restart_update']]){
    callbacks.state(Object.assign({},core,{updater:Object.assign({},update,fields)}));
    const control=button(labels[label],app.querySelector('.dk-updates'));assert(!control.disabled);
    control.fire('click');assert.strictEqual(env.sent[env.sent.length-1][0],action);
}
callbacks.state(Object.assign({},core,{updater:Object.assign({},update,{status:'ERROR',canDownload:true,compatible:false})}));
assert(button(labels['updates.download'],app.querySelector('.dk-updates')).disabled);
DK.app.dispose();
console.log(`All ${data.schema.mods.length} real pages / ${count} controls render; profile and save contracts passed`);
