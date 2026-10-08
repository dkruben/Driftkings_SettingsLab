'use strict';
const assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
const folder = path.join(__dirname, '../../res/gui/gameface/mods/Driftkings/AccountManager');
const source = fs.readFileSync(path.join(folder, 'accounts.js'), 'utf8');
class Element {
    constructor(tag) { this.tag = tag; this.children = []; this.value = ''; this.style = {}; this.attributes = {}; this.scrollTop = 0; }
    set textContent(value) { this.text = value; this.children = []; }
    appendChild(child) { child.parentNode = this; this.children.push(child); }
    setAttribute(key, value) { this.attributes[key] = value; }
    focus() { this.focused = true; }
    get scrollWidth() { return parseFloat(this.style.width) * 1.25; }
    get scrollHeight() { return parseFloat(this.style.height) * 1.25; }
    all() { return this.children.flatMap(child => [child].concat(child.all())); }
}
const event = keyCode => ({keyCode, preventDefault() {}, stopPropagation() {}});
const root = new Element('div'), sent = [], sizes = [], removed = [], events = {}, engineEvents = {};
let ready, nextFrame = 0;
const frames = new Map();
const labels = Object.fromEntries(['title','close','name','email','password','keepPassword','showPassword','server','manage',
    'save','cancel','enter','delete','edit','confirmDelete','autoEnter','add','loginOnly','empty'].map(key => [key, key]));
let data = {labels, launcher: true, canLogin: true, tooltipContent: 1, tooltipDecorator: 2};
const model = {payload: JSON.stringify(data), onAction: args => sent.push(JSON.parse(args.data))};
const engine = {whenReady: {then: cb => { ready = cb; }}, on: (key, cb) => { engineEvents[key] = cb; },
    off: key => { delete engineEvents[key]; }};
const tooltips = [];
let clientSize = {width: 1920, height: 1080};
const viewEnv = {resizeViewPx: (w, h) => sizes.push([w, h]), addDataChangedCallback: () => 12,
    removeDataChangedCallback: (...args) => removed.push(args), getClientSizeRem: () => clientSize,
    setEventHandled() {}, handleViewEvent: data => tooltips.push(data)};
vm.runInNewContext(source, {document: {getElementById: () => root, createElement: tag => {
    assert(!['select','option'].includes(tag), 'Unsupported Gameface control'); return new Element(tag);
}}, window: {model, addEventListener: (key, cb) => { events[key] = cb; }, removeEventListener: key => { delete events[key]; }},
    requestAnimationFrame: cb => { frames.set(++nextFrame, cb); return nextFrame; }, cancelAnimationFrame: id => frames.delete(id),
    engine, viewEnv});
function flush() { let limit = 5; while(frames.size && limit--) { const callbacks = [...frames.values()]; frames.clear(); callbacks.forEach(cb => cb()); } assert(limit > 0); }
function render() { model.payload = JSON.stringify(data); engineEvents['viewEnv.onDataChanged'](null, null, [12]); flush(); }
function actions() { return sent.filter(x => x.action !== 'layout'); }
function control(label, role = 'button') { const found = root.all().filter(x => x.attributes.role === role && x.attributes['aria-label'] === label); assert(found.length, label); return found[found.length - 1]; }
function click(label, role) { control(label, role).onclick(event()); }
function input(label) { return root.all().find(x => x.tag === 'input' && x.attributes['aria-label'] === label); }
ready(); assert.equal(sizes.length, 0, 'Sizing must follow DOM layout'); flush();
assert.deepStrictEqual(sizes, [[52, 52]]);
assert.deepStrictEqual(sent.pop(), {x: 1052, y: 798, action: 'layout'});
const launcher = control('title'); assert(launcher.className.includes('launcher'));
launcher.onmouseenter(); launcher.onmouseleave(); assert.equal(tooltips.length, 2);
click('title'); assert.equal(actions().pop().action, 'open'); sent.length = 0;
data = {labels, launcher: false, canLogin: false, accounts: [{id: '1', title: '<script>fake</script>', server: 'EU1', available: true}]};
render(); assert.deepStrictEqual(sizes[sizes.length - 1], [525, 250]);
assert(root.all().some(x => x.text === '<script>fake</script>'));
const oneAccount = data.accounts.slice();
data.accounts = []; render(); assert.equal(root.style.height, '170rem');
data.accounts = Array.from({length: 3}, (_, i) => ({id: String(i), title: 'Synthetic ' + i, server:'EU1', available:true}));
render(); assert.equal(root.style.height, '348rem');
clientSize = {width:1280, height:768};
data.accounts = Array.from({length: 30}, (_, i) => ({id: String(i), title: 'Synthetic ' + i, server:'EU1', available:true}));
render(); assert.equal(root.style.height, '688rem');
assert(root.all().some(x => x.className === 'list' && typeof x.onwheel === 'function'));
clientSize = {width:1920, height:1080}; data.accounts = oneAccount; render();
assert(control('edit').children.some(x => x.className.includes('icon-edit')));
control('edit').onmouseenter();
assert.equal(tooltips[tooltips.length - 1].arguments[0].string, 'edit');
control('edit').onmouseleave();

assert.equal(control('enter').attributes['aria-disabled'], 'true'); click('enter'); assert.equal(actions().length, 0);
click('delete'); assert.equal(actions().length, 0); click('cancel'); assert.equal(actions().length, 0);
click('delete'); click('delete'); assert.deepStrictEqual(actions().pop(), {id: '1', confirmed: true, action: 'delete'});
sent.length = 0; data.canLogin = true; render();
click('autoEnter', 'checkbox'); assert.equal(control('autoEnter', 'checkbox').attributes['aria-checked'], 'false');
click('enter'); assert.deepStrictEqual(actions().pop(), {id:'1', autoEnter:false, action:'enter'});
data.editing = {id: '1', title: 'test', email: 'fake@example.invalid', cluster: 0};
data.servers = [{id: 0, label: 'EU1'}, {id: 1, label: 'EU2'}]; render(); sent.length = 0;
assert.equal(input('password').value, '');
click('showPassword', 'checkbox'); assert.equal(input('password').type, 'text');
const select = root.all().find(x => x.attributes.role === 'combobox');
select.onclick(event()); assert.equal(select.attributes['aria-expanded'], 'true');
click('EU2'); assert.equal(select.text, 'EU2 \u25be');
input('name').value = 'Edited'; input('name').oninput();
input('password').value = 'synthetic-secret'; click('save');
assert.equal(actions().pop().cluster, 1); assert.equal(input('password').value, '');
data.message = 'Synthetic write failure'; render();
assert.equal(input('name').value, 'Edited', 'Keep draft after a failed save');
assert.equal(input('password').value, '', 'Do not retain a submitted password');
input('email').value = 'invalid'; sent.length = 0; click('save'); assert.equal(actions().length, 0);
assert(input('email').className.includes('invalid'));
const picker = root.all().find(x => x.attributes.role === 'combobox'); picker.onclick(event());
events.keydown(event(27)); assert.equal(picker.attributes['aria-expanded'], 'false'); assert.equal(actions().length, 0);
events.keydown(event(27)); assert.equal(actions().pop().action, 'cancel');
engineEvents.clientResized(); assert(frames.size); events.unload(); flush();
assert.equal(Object.keys(engineEvents).length, 0); assert.equal(Object.keys(events).length, 0);
assert.deepStrictEqual(removed, [[12, 0]]); assert.equal(root.children.length, 0);
ready(); assert.equal(Object.keys(engineEvents).length, 0);
const css = fs.readFileSync(path.join(folder,'accounts.css'),'utf8');
assert(css.includes('@font-face') && css.includes('Warhelios-Regular.ttf'));
assert(!css.includes(':disabled') && !css.includes('font: inherit') && !css.includes('Arial'));
for (const image of ['AM_Icon_MouseOut.png','AM_Icon_MouseOver.png','enter.png','edit.png','delete.png','add.png']) {
    assert(css.includes(image)); assert(fs.existsSync(path.join(folder,'assets',image)));
}
console.log('AccountManager: layout timing, scaling, original assets, custom controls, CRUD, validation, draft preservation and cleanup passed');
