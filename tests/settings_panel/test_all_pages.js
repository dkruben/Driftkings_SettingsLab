/* Every live backend schema opens in the redesigned frontend. */
const assert=require('assert');
const data=require('./schema_fixture');
const {createEnvironment}=require('./dom_fixture');
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
// Full settings schema stays interactive through the core command routes.
callbacks.state(Object.assign({},data.state,{selected:'dk.settings'}));
const labels=data.schema.labels;
function button(text,root=app){const found=root.querySelectorAll('button').find(n=>n.textContent===text);assert(found,text);return found;}
button(labels.profiles).fire('click');assert(DK.modal.top());
button(labels.profileExport,DK.modal.top().panel).fire('click');
assert.strictEqual(env.sent[env.sent.length-1][0],'profile');assert.strictEqual(env.sent[env.sent.length-1][1].operation,'export');
DK.modal.closeAll();
button(labels.saveApply).fire('click');assert.strictEqual(env.sent[env.sent.length-1][0],'save');
DK.app.dispose();
console.log(`All ${data.schema.mods.length} real pages / ${count} controls render; profile and save contracts passed`);
