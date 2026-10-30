'use strict';
const assert=require('assert'), fs=require('fs'), path=require('path'), vm=require('vm');
const {createEnvironment,root}=require('../../support/frontend/dom_fixture');
const env=createEnvironment(), {window,document,DK}=env;
const kit=window.__dkHealthBar, host=document.createElement('div'), bar=kit.create(host);
const filenames=['frame.png','bastion.png','vanguard.png','ion.png'];
filenames.forEach((name,index)=>{
    bar.render({style:index,percent:.75,color:'#12AB34',text:'1800 / 2400'});
    const frame=host.querySelector('.dk-health__frame');
    assert.strictEqual(frame.src,'coui://gui/gameface/mods/driftkings/vehicle_health/assets/'+name);
    assert(fs.existsSync(path.join(root,'mod/res/gui/gameface/mods/driftkings/vehicle_health/assets',name)));
    assert.strictEqual(host.querySelector('.dk-health__fill').style.width,'75%');
    assert.strictEqual(host.querySelector('.dk-health__fill').style.backgroundColor,'#12AB34');
    assert.strictEqual(host.querySelector('.dk-health__text').textContent,'1800 / 2400');
    assert.strictEqual(host.style.height,kit.preset(index).height+'rem');
    assert.strictEqual(host.children.length,1,'style changes reuse the same bar nodes');
});
bar.render({style:4,percent:.5,color:'#12AB34',text:'1200 / 2400'});
assert.strictEqual(host.getAttribute('data-health-style'),'minimal');
assert.strictEqual(host.style.width,'340rem');
assert.strictEqual(host.style.height,'24rem');
assert.strictEqual(host.querySelector('.dk-health__image').style.display,'none');
assert.strictEqual(host.querySelector('.dk-health__fill').style.width,'50%');
assert.strictEqual(host.querySelector('.dk-health__text').textContent,'1200 / 2400');
bar.render({style:1,percent:.5});
assert.strictEqual(host.querySelector('.dk-health__image').style.display,'');
assert.strictEqual(host.querySelector('.dk-health__frame').src.endsWith('/bastion.png'),true);
for(const value of [-1,5,1.5,'1',null,true,Infinity]){
    bar.render({style:value,percent:NaN,color:'invalid',text:''});
    assert.strictEqual(host.getAttribute('data-health-style'),'classic');
    assert.strictEqual(host.querySelector('.dk-health__fill').style.width,'0%');
    assert.strictEqual(host.querySelector('.dk-health__fill').style.backgroundColor,'#3FC23A');
}
bar.render({style:0,percent:2,text:'<font>literal</font>'});
assert.strictEqual(host.querySelector('.dk-health__fill').style.width,'100%');
assert.strictEqual(host.querySelector('.dk-health__text').textContent,'<font>literal</font>');
// The in-game bridge delegates the same payload to the renderer, retaining its drag handle.
let bridge;
window.__dkMarksKit={
    node(tag,name,parent){const node=document.createElement(tag);node.className=name;parent.appendChild(node);return node;},
    style(node,key,value){node.style[key]=value;}, number(value,fallback){return typeof value==='number'?value:fallback;},
    savedPosition(){}, position(){},
    connect(feature,owner,node,render,position){bridge={feature,owner,node,render,position};}
};
env.context.requestAnimationFrame=fn=>fn();
vm.runInContext(fs.readFileSync(path.join(root,'mod/res/gui/gameface/mods/driftkings/vehicle_health/vehicle_health.js'),'utf8'),env.context);
bridge.render({style:3,percent:.4,text:'960 / 2400',color:'#E09020',config:{draggable:true,locked:false}});
assert.strictEqual(bridge.node.getAttribute('data-health-style'),'ion');
assert.strictEqual(bridge.node.querySelector('.dk-health__fill').style.width,'40%');
assert.strictEqual(bridge.node.firstChild.style.cursor,'move');
bridge.render({style:1,percent:.1,text:'240 / 2400',config:{draggable:false,locked:false}});
assert.strictEqual(bridge.node.style.pointerEvents,'none');
// Preview reads live draft values and only changes sample HP locally.
const previewHost=document.createElement('div'), id=DK.minimapPreview.fieldId;
const preview=DK.hudPreview.create(previewHost,{id:'legacy.OwnHealth'});
const values={[id('style')]:0,[id('enabled')]:true};
preview.update(values);
assert.strictEqual(previewHost.querySelector('.dk-health__frame').src.endsWith('/assets/frame.png'),true);
preview.preview(id('style'),2);
assert.strictEqual(previewHost.querySelector('.is-current').getAttribute('data-health-style'),'vanguard');
preview.preview(id('style'),4);
assert.strictEqual(previewHost.querySelector('.is-current').getAttribute('data-health-style'),'minimal');
assert.strictEqual(previewHost.querySelector('.is-current').style.width,'340rem');
assert.strictEqual(previewHost.querySelector('.dk-health__image').style.display,'none');
preview.preview(id('style'),2);
const range=previewHost.querySelector('input'), sent=env.sent.length;
range.value=10;range.fire('input');
assert.strictEqual(previewHost.querySelector('.dk-health__fill').style.width,'10%');
const text=previewHost.querySelector('.dk-health__text').textContent;
assert(/^\d+ \/ \d+$/.test(text));
const color=previewHost.querySelector('.dk-health__fill').style.backgroundColor;
preview.preview(id('avgColor.saturation'),0);
assert.notStrictEqual(previewHost.querySelector('.dk-health__fill').style.backgroundColor,color);
range.value=0;range.fire('input');
assert.strictEqual(previewHost.querySelector('.dk-health__fill').style.width,'0%');
assert.strictEqual(env.sent.length,sent,'sample HP never saves configuration');
preview.preview(id('x'),99999);
assert.strictEqual(previewHost.querySelector('.is-current').style.left,'1440rem');
preview.preview(id('enabled'),false);
assert.strictEqual(previewHost.querySelector('.is-current'),null);
preview.dispose();assert.strictEqual(previewHost.children.length,0);
DK.app.dispose();
console.log('Health bar: five styles, shared battle/preview renderer, HP samples and live colour passed');
