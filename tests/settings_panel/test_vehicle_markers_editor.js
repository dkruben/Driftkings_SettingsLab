const assert=require('assert');
const {createEnvironment}=require('./dom_fixture');
const data=require('./schema_fixture');
const env=createEnvironment(), {DK,document}=env;
const mod=data.schema.mods.find(m=>m.preview&&m.preview.kind==='vehicleMarkers');assert(mod);
const values=JSON.parse(JSON.stringify(data.state.values[mod.id])),commits=[];
const empty=JSON.parse(values[mod.preview.bindings.markersDeadExtended]);empty.enemy.textFields=[];
values[mod.preview.bindings.markersDeadExtended]=JSON.stringify(empty);
const alive=JSON.parse(values[mod.preview.bindings.markersAliveNormal]);
alive.ally.textFields=[{enabled:true,format:'{{hp}}',x:5,y:7,width:88,height:30,align:'right',valign:'bottom',
    textFormat:{size:15,color:'#123456'},shadow:{enabled:true,angle:0,distance:2,blur:3,color:'#000000',alpha:50}}];
values[mod.preview.bindings.markersAliveNormal]=JSON.stringify(alive);
const host=document.createElement('div');
const editor=DK.markers.create(host,mod,{commit:(...v)=>commits.push(v),action(){}});
editor.update(values,{disabled:[],changed:[]});
let sampleText=host.querySelector('.dk-mk-text');
assert.strictEqual(sampleText.style.width,'88rem');
assert.strictEqual(sampleText.style.marginLeft,'-88rem');
assert.strictEqual(sampleText.style.top,'-23rem');
assert.strictEqual(sampleText.style.color,'#123456');
assert.strictEqual(sampleText.style.textShadow,'2rem 0rem 3rem rgba(0,0,0,0.5)');
const off=Object.assign({},values,{[mod.preview.bindings.enabled]:false});
editor.update(off,{disabled:[],changed:[]});
assert.strictEqual(host.querySelector('.dk-markers-anchor').children.length,0,'general enable changes redraw the preview');
editor.update(values,{disabled:[],changed:[]});
assert(host.querySelector('.dk-markers-anchor').children.length>0);
function byText(text,root=host){const n=root.querySelectorAll('button').find(n=>n.textContent===text);assert(n,text);return n;}
const choice=host.querySelectorAll('.dk-markers-choice');
choice[0].querySelectorAll('button')[1].fire('click');
byText(mod.preview.labels.textFields).fire('click');
// Native font names and Unicode remain available to the preview renderer.
const rich=document.createElement('div');DK.richText.render(rich,'<font face="XVMSymbol">&#x115;!</font>');
assert.strictEqual(rich.querySelector('span').style.fontFamily,'XVMSymbol');
assert.strictEqual(rich.textContent,'\u0115!');
DK.richText.render(rich,'A&#39;B &lt;b&gt; &amp; &#128512;');
assert.strictEqual(rich.textContent,"A'B <b> & \uD83D\uDE00");
assert.strictEqual(rich.querySelector('b'),null,'decoded markup stays text');
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
editor.dispose();assert.strictEqual(host.children.length,0);
const shared=DK.markers.create(host,mod,{commit:(...v)=>commits.push(v),action(){}});
shared.update(data.state.values[mod.id],{disabled:[],changed:[]});
byText(mod.preview.labels.textFields).fire('click');
const reference=host.querySelector('.is-reference');assert(reference,'string references have a dedicated wrapping row');
assert.strictEqual(reference.style.display,'block');
assert.strictEqual(reference.querySelector('.dk-mk-input').style.display,'block');
assert.strictEqual(reference.querySelector('.dk-mk-input').style.width,'100%');
reference.querySelector('button').fire('click');
assert(host.querySelector('.dk-mk-title').textContent.includes('def'));
const formatRow=host.querySelectorAll('[data-property]').find(n=>/def\.tankName\.format$/.test(n.getAttribute('data-property')));
assert(formatRow,'shared model properties are directly editable');
formatRow.querySelector('input').value='Updated {{vehicle}}';formatRow.querySelector('input').fire('keydown',{keyCode:13});
const saved=JSON.parse(commits[commits.length-1][1]);
assert.strictEqual(saved.def.tankName.format,'Updated {{vehicle}}');
assert.strictEqual(saved.ally.textFields[0], '${def.tankName}', 'editing shared properties preserves the reference');
byText(mod.preview.labels.ratingType,host.querySelector('.dk-markers-list')).fire('click');
assert(host.querySelector('.dk-mk-title').textContent.includes('rating'));
for(const property of ['enabled','x','y','alpha','format']) {
    assert(host.querySelectorAll('[data-property]').some(n=>n.getAttribute('data-property').endsWith('def.rating.'+property)),property);
}
const ratingOn=host.querySelectorAll('[data-property]').find(n=>n.getAttribute('data-property').endsWith('def.rating.enabled'));
ratingOn.querySelector('.dk-switch').fire('click');
const ratingSaved=JSON.parse(commits[commits.length-1][1]);
assert.strictEqual(ratingSaved.def.rating.enabled,false);
assert.strictEqual(commits[commits.length-1][0],mod.preview.bindings.markersAliveNormal);
assert.strictEqual(ratingSaved.ally.textFields[3],'${def.rating}');
shared.dispose();DK.app.dispose();
console.log('Redesigned markers: destroyed/Alt scope, empty arrays, original fonts, invalid JSON and immutable drafts passed');
