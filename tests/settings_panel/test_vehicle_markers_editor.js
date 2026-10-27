const assert=require('assert');
const {createEnvironment}=require('./dom_fixture');
const data=require('./schema_fixture');
const env=createEnvironment(), {DK,document}=env;
const mod=data.schema.mods.find(m=>m.preview&&m.preview.kind==='vehicleMarkers');assert(mod);
const values=JSON.parse(JSON.stringify(data.state.values[mod.id])),commits=[];
const empty=JSON.parse(values[mod.preview.bindings.markersDeadExtended]);empty.enemy.textFields=[];
values[mod.preview.bindings.markersDeadExtended]=JSON.stringify(empty);
const host=document.createElement('div');
const editor=DK.markers.create(host,mod,{commit:(...v)=>commits.push(v),action(){}});
editor.update(values,{disabled:[],changed:[]});
function byText(text,root=host){const n=root.querySelectorAll('button').find(n=>n.textContent===text);assert(n,text);return n;}
const choice=host.querySelectorAll('.dk-markers-choice');
choice[0].querySelectorAll('button')[1].fire('click');
byText(mod.preview.labels.textFields).fire('click');
// Native font names and Unicode remain available to the preview renderer.
const rich=document.createElement('div');DK.richText.render(rich,'<font face="XVMSymbol">&#x115;!</font>');
assert.strictEqual(rich.querySelector('span').style.fontFamily,'XVMSymbol');
// Destroyed/Alt is a separate document; adding to an empty list must work.
choice[1].querySelectorAll('button')[1].fire('click');choice[2].querySelectorAll('button')[1].fire('click');
byText(mod.preview.labels.textFields).fire('click');byText(DK.t('markers.add')).fire('click');
assert.strictEqual(commits[0][0],mod.preview.bindings.markersDeadExtended);
const draft=JSON.parse(commits[0][1]);assert.strictEqual(draft.enemy.textFields.length,1);
assert.strictEqual(JSON.parse(values[mod.preview.bindings.markersDeadExtended]).enemy.textFields.length,0,'source state was not mutated');
// Rejected/unchanged authoritative state restores the form rather than retaining a mutated draft.
editor.update(values,{disabled:[],changed:[]});
byText(DK.t('markers.json')).fire('click');const area=host.querySelector('.dk-mk-json');
area.value='{broken';byText(DK.t('markers.apply')).fire('click');assert.strictEqual(commits.length,1);
area.value=values[mod.preview.bindings.markersDeadExtended];byText(DK.t('markers.apply')).fire('click');assert.strictEqual(commits.length,2);
editor.dispose();assert.strictEqual(host.children.length,0);DK.app.dispose();
console.log('Redesigned markers: destroyed/Alt scope, empty arrays, original fonts, invalid JSON and immutable drafts passed');
