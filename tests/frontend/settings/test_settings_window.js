const assert=require('assert');
const {createEnvironment}=require('../../support/frontend/dom_fixture');
const env=createEnvironment();
const {DK,app,document,sent,callbacks,themeStyle}=env;
const option = (value, label) => ({value, label});
const defs = [
    {id: 'on', type: 'switch', label: 'Switch', default: true, description: 'Help'},
    {id: 'box', type: 'checkbox', label: 'Box', default: false},
    {id: 'mode', type: 'dropdown', label: 'Mode', options: [option('a', 'A'), option('b', 'B')], default: 'a'},
    {id: 'size', type: 'slider', label: 'Size', min: 0, max: 10, step: 0.5, default: 5},
    {id: 'count', type: 'number', label: 'Count', min: 0, max: 5, step: 1, metadata: {sourceType: 'NumericStepper'}},
    {id: 'pick', type: 'dropdown', label: 'Pick', options: [option(1, 'One'), option(2, 'Two')], metadata: {sourceType: 'RadioButtonGroup'}},
    {id: 'name', type: 'text', label: 'Name', default: '', metadata: {applyTiming: 'restart'}},
    {id: 'note', type: 'textarea', label: 'Note'},
    {id: 'secret', type: 'password', label: 'Secret'},
    {id: 'tint', type: 'color', label: 'Tint', default: '#FF0000', metadata: {allowAlpha: true, alphaKey: 'alpha', applyTiming: 'live'},
     presets: [{value: '#00FF00', label: 'Green'}]},
    {id: 'key', type: 'hotkey', label: 'Key'},
    {id: 'tags', type: 'multiselect', label: 'Tags', options: [option('x', 'X')]},
    {id: 'go', type: 'button', label: 'Go'},
    {id: 'head', type: 'section', label: 'Section'}
];
const labels = {on: 'On', off: 'Off', clearSecret: 'Clear', secretSet: 'Set', secretEmpty: 'Empty', pressKey: 'Press',
    noKey: 'None', all: 'All', profiles: 'Profiles', installed: 'Installed', close: 'Close', 'updates.title': 'Updates',
    'updates.installed': 'Installed', 'updates.channel': 'Channel', 'updates.lastCheck': 'Last', 'updates.never': 'Never',
    'updates.IDLE': 'Idle'};
const schema = {labels, mods: [
    {id: 'dk.settings', name: 'driftkings', category: 'system', icon: 'gear', controls: defs, dependencies: []},
    {id: 'other', name: 'Other', category: 'battle', icon: 'chart', controls: [], dependencies: [{id: 'x', installed: false}]}]};
const values = {on: true, box: false, mode: 'b', size: 3, count: 2, pick: 2, name: 'n', note: '', secret: '', tint: '#00FF00',
    alpha: 0.5, key: [[1, 2]], tags: ['x'], go: null};
const state = {selected: 'dk.settings', values: {'dk.settings': values}, changed: {'dk.settings': ['on']}, disabled: {},
    secrets: {}, status: {'dk.settings': {status: 'active', enabled: true}, other: {status: 'error'}}, theme: {accent: '#D98219'},
    updater: {installedVersion: '1.0', channel: 'release', lastCheck: null, status: 'IDLE'}, profiles: ['default'],
    restartRequired: [], keyNames: {'1': 'A', '2': 'B'}};

callbacks.schema(schema);callbacks.state(state);
assert(app.querySelectorAll('.dk-row').length>=12);
assert(themeStyle.textContent.includes('#D98219'));
assert(app.querySelector('.dk-updates'));
const discord=app.querySelector('.dk-community').querySelectorAll('button').find(n=>n.textContent==='DISCORD');
assert(discord);discord.fire('click');assert.strictEqual(sent[sent.length-1][0],'open_discord');
assert.strictEqual(DK.hex('0xFF8800'),null);
assert.strictEqual(DK.hex('FF8800'),null);
assert.strictEqual(DK.hex('#ff8800'),'#FF8800');
// The original spectrum is used, with cancel/apply and separate alpha conversion.
app.querySelector('.dk-swatch').fire('click');
let modal=DK.modal.top();assert(modal);assert(modal.panel.querySelector('.dk-spectrum-dark'));
assert(!modal.panel.querySelector('.dk-picker-hue'));
modal.panel.querySelector('.dk-preset').fire('click');
modal.panel.querySelector('input').value='#112233';
const pickerButtons=modal.panel.querySelector('.dk-modal-actions').querySelectorAll('button');
pickerButtons[1].fire('click');assert(!DK.modal.top());
assert.strictEqual(sent[sent.length-1][0],'set');assert.strictEqual(sent[sent.length-1][1].value,'#112233');
assert.strictEqual(DK.colorPicker.toScale(50,'normalized'),0.5);
assert.strictEqual(DK.colorPicker.toScale(100,'byte'),255);
assert.strictEqual(DK.colorPicker.fromScale(128,'byte'),128*100/255);
let chosen=0;DK.colorPicker.open({value:'#FF0000',alpha:null},()=>chosen++);
modal=DK.modal.top();modal.panel.querySelector('.dk-spectrum').fire('mousedown');
assert((document.listeners.mousemove||[]).length>0);
DK.layer.key({keyCode:27,preventDefault(){},stopPropagation(){}});
assert.strictEqual(chosen,0);assert.strictEqual((document.listeners.mousemove||[]).length,0);
// Invalid HEX cannot be applied.
DK.colorPicker.open({value:'#FF0000',alpha:null},()=>chosen++);modal=DK.modal.top();
modal.panel.querySelector('input').value='0xFFFFFF';
modal.panel.querySelector('.dk-modal-actions').querySelectorAll('button')[1].fire('click');
assert(DK.modal.top());assert.strictEqual(chosen,0);DK.modal.closeAll();
// Every normal control uses the Python action contract; disabled controls do not write.
const changes=[];
const slider=DK.controls.create({id:'x',type:'slider',label:'X',min:-4096,max:4096,step:1},{commit:(...v)=>changes.push(v)});
slider.set(0);slider.node.querySelector('.dk-slider-track').fire('keydown',{keyCode:39});
assert.strictEqual(changes[0][1],1);slider.sync({disabled:true});
slider.node.querySelector('.dk-slider-track').fire('keydown',{keyCode:39});assert.strictEqual(changes.length,1);
slider.dispose();
// Enter then blur writes once after the authoritative state synchronizes.
const text=DK.controls.create({id:'name',type:'text',label:'Name'},{commit:(...v)=>changes.push(v)});
text.set('before');const field=text.node.querySelector('input');field.value='after';field.fire('keydown',{keyCode:13});
assert.strictEqual(changes[1][1],'after');text.set('after');field.fire('blur');assert.strictEqual(changes.length,2);
// Relabel/rebuild disposes active interactions and cancels the old picker.
app.querySelector('.dk-swatch').fire('click');assert(DK.modal.top());
callbacks.schema(schema);assert(!DK.modal.top());callbacks.state(state);
const writes=[];
const ctx={commit:(...args)=>writes.push(args),capture:key=>writes.push(['capture',key]),action:key=>writes.push(['button',key])};
const dropdown=DK.controls.create({id:'mode',type:'dropdown',label:'Mode',options:[{value:'a',label:'A'},{value:'b',label:'B'}]},ctx);
dropdown.set('b');dropdown.node.querySelector('.dk-select').fire('keydown',{keyCode:36});assert.strictEqual(writes.pop()[1],'a');
dropdown.node.querySelector('.dk-select').fire('keydown',{keyCode:35});assert.strictEqual(writes.pop()[1],'b');
const stepper=DK.controls.create({id:'count',type:'number',label:'Count',min:0,max:10,step:1},ctx);stepper.set(5);
stepper.node.querySelector('input').fire('keydown',{keyCode:35});assert.strictEqual(writes.pop()[1],10);
stepper.node.querySelector('input').fire('keydown',{keyCode:36});assert.strictEqual(writes.pop()[1],0);
const secret=DK.controls.create({id:'secret',type:'password',label:'Secret'},ctx);secret.sync({secretSet:true});
assert.strictEqual(secret.node.querySelector('input').value,'');secret.node.querySelector('input').value='new-secret';
secret.node.querySelector('input').fire('keydown',{keyCode:13});assert.strictEqual(writes.pop()[1],'new-secret');
assert.strictEqual(secret.node.querySelector('input').value,'');
const hotkey=DK.controls.create({id:'key',type:'hotkey',label:'Key'},ctx);hotkey.set([]);
hotkey.node.querySelector('.dk-keys').fire('click');assert.deepStrictEqual(writes.pop(),['capture','key']);
env.flush();callbacks.resize();assert.strictEqual(env.timers.size,0,'unchanged geometry is cached');
env.window.innerWidth=1600;callbacks.resize();env.window.innerWidth=1500;callbacks.resize();
assert.strictEqual(env.timers.size,1,'layout refreshes coalesce');
DK.app.dispose();assert.strictEqual(env.timers.size,0);assert(!DK.modal.top());assert(!DK.layer.menuOpen());
console.log('Redesigned settings: controls, original spectrum, alpha, validation and lifetime passed');
