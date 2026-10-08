'use strict';
/* Integrated settings Gameface window with a minimal DOM. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.join(__dirname, '../../res/gui/gameface/mods/Driftkings/DKModSettings');
const read = name => fs.readFileSync(path.join(ROOT, name), 'utf8');

class Element {
    constructor(tag) {
        this.tagName = tag.toUpperCase(); this.children = []; this.parentNode = null; this.listeners = {};
        this.style = {}; this.className = ''; this.ownText = ''; this.value = ''; this.disabled = false;
        this.tabIndex = ['BUTTON','INPUT','TEXTAREA','SELECT'].includes(this.tagName) ? 0 : -1; this.scrollTop = 0; this.type = ''; this.placeholder = ''; this.title = '';
    }
    set textContent(value) { this.ownText = String(value); this.children.forEach(c => { c.parentNode = null; }); this.children = []; }
    get textContent() { return this.ownText + this.children.map(c => c.textContent).join(''); }
    appendChild(child) { if (child.parentNode) { child.parentNode.removeChild(child); } child.parentNode = this; this.children.push(child); return child; }
    removeChild(child) { const i = this.children.indexOf(child); if (i >= 0) { this.children.splice(i, 1); } child.parentNode = null; return child; }
    setAttribute(name,value) { this[name] = value; }
    click() { this.fire('click'); }
    focus() { if (!this.disabled) { this.ownerDocument.activeElement = this; } }
    querySelectorAll(selector) { return this.all().slice(1).filter(n => selector.split(',').some(s => s[0] === '.' ? n.has(s.slice(1)) : s === '[tabindex]' ? n.tabIndex >= 0 || n._dkTab !== undefined : n.tagName.toLowerCase() === s)); }
    get firstChild() { return this.children[0] || null; }
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
    removeEventListener(type, fn) { const list = this.listeners[type] || []; const i = list.indexOf(fn); if (i >= 0) { list.splice(i, 1); } }
    fire(type, event) { event = Object.assign({target: this}, event || {}); (this.listeners[type] || []).slice().forEach(fn => fn.call(this, event)); }
    getBoundingClientRect() { return {left: 100, top: 100, right: 300, bottom: 124, width: 200, height: 24}; }
    get offsetHeight() { return 20; }
    get offsetWidth() { return 100; }
    all() { return [this].concat(...this.children.map(c => c.all())); }
    find(cls) { return this.all().filter(n => n.className.split(' ').indexOf(cls) >= 0); }
    has(cls) { return this.className.split(' ').indexOf(cls) >= 0; }
}

function context(extra) {
    const nodes = {'dk-app': new Element('main'), 'dk-theme': new Element('style')};
    const body = new Element('body');
    const documentListeners = new Element('document');
    const document = {
        body, activeElement: null,
        getElementById: id => nodes[id],
        createElement: tag => { const n = new Element(tag); n.ownerDocument = document; return n; },
        documentElement: new Element('html'),
        addEventListener: (t, f) => documentListeners.addEventListener(t, f),
        removeEventListener: (t, f) => documentListeners.removeEventListener(t, f)
    };
    const windowListeners = {};
    const sandbox = Object.assign({
        document, nodes, documentListeners, console, setTimeout: () => 1, clearTimeout: () => {}, JSON, Math, isFinite, parseFloat,
        parseInt, Number, String, Object, getComputedStyle: () => ({fontSize: '1px'}), innerWidth: 1920, innerHeight: 1080,
        addEventListener: (t, f) => { windowListeners[t] = f; }, removeEventListener: t => { delete windowListeners[t]; },
        windowListeners
    }, extra);
    sandbox.window = sandbox;
    return vm.createContext(sandbox);
}

// ---------------------------------------------------------------- window
const sent = [], resized = [], removed = [];
let ready = null, changed = null;
const model = {schema: '{}', state: '{}', onAction: args => sent.push(JSON.parse(args.data))};
const ctx = context({
    model,
    engine: {whenReady: {then: cb => { ready = cb; }}, on: (e, cb) => { changed = cb; }, off: () => { changed = null; }},
    viewEnv: {
        addDataChangedCallback: () => 7, removeDataChangedCallback: (...args) => removed.push(args),
        getClientSizeRem: () => ({width: 1600, height: 900}), remToPx: () => 1.5, resizeViewRem: (w, h) => resized.push([w, h])
    }
});
['js/bridge.js', 'js/colors.js', 'js/modal.js', 'js/controls.js', 'js/app.js'].forEach(name => vm.runInContext(read(name), ctx, {filename: name}));
const app = ctx.nodes['dk-app'];
const labels = {title: 'DK MOD SETTINGS', apply: 'Apply', cancel: 'Cancel', reset: 'Reset', saveApply: 'Save & Apply',
    unsaved: 'Unsaved', on: 'ON', off: 'OFF', secretSet: 'Saved (hidden)', secretEmpty: 'Not set', clearSecret: 'Clear',
    search: 'Search', undo: 'Undo', profiles: 'Profiles', profileCreate: 'Create', profileLoad: 'Load', profileRename: 'Rename', profileDelete: 'Delete profile', profileExport: 'Export JSON', profileImport: 'Import JSON', close: 'Close', installed: 'Installed mods', noKey: 'No key', pressKey: 'Press a key',
    presets: 'Presets', confirmSave: 'Save', confirmDiscard: 'Discard', confirmStay: 'Stay',
    restartTitle: 'Restart needed', restartText: 'Saved changes need restart', restartNow: 'Restart now', restartLater: 'Later'};
const schema = {language: 'en', labels, mods: [{
    id: 'dk.demo', name: '<b>Demo</b>', version: '1.0.0', author: 'DK', description: 'desc', icon: 'evil"icon', controls: [
        {id: 'section_1', type: 'section', label: 'General'},
        {id: 'enabled', type: 'switch', label: 'Enable', default: true, description: 'tip'},
        {id: 'lang', type: 'dropdown', label: 'Language', default: 'en', options: [{value: 'en', label: 'English'}, {value: 'pt', label: 'Português'}]},
        {id: 'volume', type: 'slider', label: 'Volume', default: 80, min: 0, max: 100, step: 5, unit: '%'},
        {id: 'size', type: 'number', label: 'Size', default: 3, min: 0, max: 10, step: 1},
        {id: 'name', type: 'text', label: 'Name', default: 'abc', maxLength: 20},
        {id: 'apiKey', type: 'password', label: 'API key', maxLength: 64},
        {id: 'accent', type: 'color', label: 'Accent', default: '#D98219', presets: [{value: '#3D8FD9', label: 'Blue'}]},
        {id: 'test', type: 'button', label: 'Test', text: 'Run'}
    ]}, {id: 'dk.settings', name: 'DK Mod Settings', version: '0.1.0', author: 'DK', description: '', icon: 'gear', controls: []}]};
const values = {enabled: true, lang: 'en', volume: 80, size: 3, name: 'abc', apiKey: '', accent: '#D98219'};
function state(extra) {
    return Object.assign({selected: 'dk.demo', values: {'dk.demo': Object.assign({}, values), 'dk.settings': {}},
        secrets: {}, changed: {'dk.demo': []}, disabled: {'dk.demo': []}, status: {'dk.demo': {status: 'active'}},
        pending: false, unsaved: false, confirm: false, message: null, theme: {accent: '#D98219'}}, extra || {});
}
function push(nextSchema, nextState) {
    if (nextSchema) { model.schema = JSON.stringify(nextSchema); }
    if (nextState) { model.state = JSON.stringify(nextState); }
    changed(null, null, [7]);
}
function rows() { return app.find('dk-row'); }
function row(label) { const r = rows().find(n => n.find('dk-label')[0].textContent === label); assert(r, label); return r; }
function button(text) { const b = app.all().find(n => n.tagName === 'BUTTON' && n.textContent === text); assert(b, text); return b; }

ready();
model.schema = JSON.stringify(schema); model.state = JSON.stringify(state());
changed(null, null, [7]);
// Fullscreen view: the panel is sized in UI units by CSS; the view itself is never resized.
assert.deepStrictEqual(resized, []);
assert.strictEqual(sent.length, 0);
assert.strictEqual(ctx.document.documentElement.style.fontSize, '1.5px');
const panel = app.find('dk-window')[0];
assert.strictEqual(panel.style.width, '1280rem');
assert.strictEqual(panel.style.height, '740rem');
ctx.viewEnv.getClientSizeRem = () => ({width: 1000, height: 600});
ctx.windowListeners.resize();
assert.strictEqual(panel.style.width, '840rem');
assert.strictEqual(panel.style.height, '480rem');
assert.strictEqual(app.find('dk-nav-item').length, 2);
assert(app.all().some(n => n.textContent === '<b>Demo</b>' && n.has('dk-mod-name')), 'names are text, not HTML');
assert(app.find('dk-nav-icon')[0].src.endsWith('/puzzle.svg'), 'unknown icons fall back to the puzzle');
assert.strictEqual(rows().length, 8);
assert.strictEqual(app.find('dk-section')[0].textContent, 'General');
assert(ctx.nodes['dk-theme'].textContent.indexOf('#D98219') >= 0);
assert.strictEqual(button('Apply').disabled, true);

// Gameface wheel direction, UI-scaled speed and containment at both boundaries.
function checkScroll(node) {
    node.scrollHeight = 1200; node.clientHeight = 400; node.scrollTop = 300;
    let prevented = 0, stopped = 0;
    const wheel = deltaY => node.fire('wheel', {deltaY,
        preventDefault: () => prevented++, stopPropagation: () => stopped++});
    wheel(-1);
    assert.strictEqual(node.scrollTop, 408, 'wheel down moves 72 UI units at 1.5 scale');
    wheel(120);
    assert.strictEqual(node.scrollTop, 300, 'wheel up uses the same step regardless of native delta magnitude');
    node.scrollTop = 795; wheel(-120);
    assert.strictEqual(node.scrollTop, 800);
    wheel(-120);
    node.scrollTop = 5; wheel(1);
    assert.strictEqual(node.scrollTop, 0);
    wheel(1);
    assert.strictEqual(prevented, 6, 'native scrolling is prevented even at boundaries');
    assert.strictEqual(stopped, 6, 'nested scroll does not move the parent');
    wheel(0);
    assert.strictEqual(prevented, 6, 'horizontal-only events are ignored');
}
checkScroll(app.find('dk-controls')[0]);
checkScroll(app.find('dk-sidebar')[0]);
checkScroll(ctx.DK.dom.el('textarea', 'dk-profile-json'));
checkScroll(ctx.DK.dom.el('div', 'dk-dialog dk-profile-dialog'));

// Switch: sends the new value; state patches keep the same nodes.
const enabledRow = row('Enable');
enabledRow.find('dk-switch')[0].fire('click');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'enabled', value: false, action: 'set'});
push(null, state({values: {'dk.demo': Object.assign({}, values, {enabled: false})}, changed: {'dk.demo': ['enabled']},
    disabled: {'dk.demo': ['lang']}, pending: true, unsaved: true}));
assert.strictEqual(row('Enable'), enabledRow, 'state changes patch the DOM instead of rebuilding');
assert(enabledRow.has('is-changed'));
assert(row('Language').has('is-disabled'));
assert(app.find('dk-nav-item')[0].has('is-changed'));
assert.strictEqual(button('Apply').disabled, false);
assert(app.find('dk-unsaved')[0].has('is-visible'));
row('Language').find('dk-dropdown')[0].fire('click');
assert.strictEqual(sent.length, 0, 'disabled controls do not send');

// Dropdown through the popup layer.
push(null, state());
row('Language').find('dk-dropdown')[0].fire('click');
const options = ctx.document.body.find('dk-option');
assert.strictEqual(options.length, 2);
checkScroll(ctx.document.body.find('dk-popup')[0]);
options[1].fire('click');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'lang', value: 'pt', action: 'set'});
assert.strictEqual(ctx.document.body.find('dk-popup').length, 0);

// Slider: drag from the middle to the end, commit once on release with the snapped value.
const track = row('Volume').find('dk-slider-track')[0];
track.fire('mousedown', {clientX: 201});
assert.strictEqual(row('Volume').find('dk-slider-value')[0].value, '50');
ctx.documentListeners.fire('mouseup', {clientX: 400});
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'volume', value: 100, action: 'set'});
assert.strictEqual(sent.length, 0);

// Legacy numeric definitions also render sliders, with precise input and no stepper.
const numberRow = row('Size'), numberInput = numberRow.all().find(n => n.tagName === 'INPUT');
assert.strictEqual(numberRow.find('dk-step').length, 2);
numberInput.fire('keydown', {keyCode: 38});
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'size', value: 4, action: 'set'});
numberInput.value = '99'; numberInput.fire('keydown', {keyCode: 13});
assert.strictEqual(sent.length, 0);
assert(numberInput.has('is-invalid'));

// Text commits on Enter; focused input is not overwritten by a state patch.
const textInput = row('Name').all().find(n => n.tagName === 'INPUT');
textInput.value = 'typed'; ctx.document.activeElement = textInput;
push(null, state());
assert.strictEqual(textInput.value, 'typed');
textInput.fire('keydown', {keyCode: 13});
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'name', value: 'typed', action: 'set'});
ctx.document.activeElement = null;

// Password: never displayed, submitted once, input cleared.
const secretRow = row('API key'), secretInput = secretRow.all().find(n => n.tagName === 'INPUT');
assert.strictEqual(secretInput.type, 'password');
assert.strictEqual(secretInput.placeholder, 'Not set');
secretInput.value = 'synthetic-secret'; secretInput.fire('blur');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'apiKey', value: 'synthetic-secret', action: 'set'});
assert.strictEqual(secretInput.value, '');
push(null, state({secrets: {'dk.demo': ['apiKey']}}));
assert.strictEqual(secretInput.placeholder, 'Saved (hidden)');
assert.strictEqual(secretInput.value, '');

// Color: hex normalization, invalid hex rejected, presets in the popup.
const colorRow = row('Accent'), hex = colorRow.all().find(n => n.tagName === 'INPUT');
hex.value = '3d8fd9'; hex.fire('keydown', {keyCode: 13});
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'accent', value: '#3D8FD9', action: 'set'});
hex.value = '#zz'; hex.fire('keydown', {keyCode: 13});
assert.strictEqual(sent.length, 0);
push(null, state());
colorRow.find('dk-color-swatch')[0].fire('click');
assert.strictEqual(ctx.document.body.find('dk-spectrum').length, 1);
ctx.document.body.find('dk-preset')[0].fire('click');
assert.strictEqual(sent.length, 0, 'preset edits only the local draft');
ctx.document.body.find('dk-modal-actions')[0].children[1].fire('click');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'accent', value: '#3D8FD9', action: 'set'});
ctx.documentListeners.fire('mousedown', {target: app});
assert.strictEqual(ctx.document.body.find('dk-popup').length, 0, 'outside click closes popups');

// Button, footer, dialog, toast, theme.
button('Run').fire('click');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', key: 'test', action: 'button'});
button('Reset').fire('click');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.demo', action: 'reset'});
button('Save & Apply').fire('click');
assert.strictEqual(sent.pop().action, 'save');
push(null, state({confirm: true, message: {id: 4, kind: 'error', text: 'Oops'}, theme: {accent: '#5DB346'}}));
assert(app.find('dk-overlay')[0].has('is-visible'));
assert(app.find('dk-toast')[0].has('is-visible') && app.find('dk-toast')[0].has('is-error'));
assert(ctx.nodes['dk-theme'].textContent.indexOf('#5DB346') >= 0);
ctx.documentListeners.fire('keydown', {keyCode: 27});
assert.deepStrictEqual(sent.pop(), {choice: 'stay', action: 'confirm'});
button('Discard').fire('click');
assert.deepStrictEqual(sent.pop(), {choice: 'discard', action: 'confirm'});

// Search finds options and hides unrelated controls, without reconstructing their DOM.
push(null, state({restartPrompt: true, inBattle: false}));
assert(app.find('dk-overlay')[0].has('is-visible'));
button('Restart now').fire('click');
assert.deepStrictEqual(sent.pop(), {action: 'restart', choice: 'now'});
push(null, state({restartPrompt: true, inBattle: true}));
assert(button('Restart now').disabled);
ctx.documentListeners.fire('keydown', {keyCode: 27});
assert.deepStrictEqual(sent.pop(), {action: 'restart', choice: 'later'});

// Scrollbars support dragging and release their document listeners.
{
const scrollNode = new Element('div'), scrollHost = new Element('div');
scrollNode.clientHeight = 100; scrollNode.scrollHeight = 500;
const updateScroll = ctx.DK.dom.scrollbar(scrollNode, scrollHost);
const track = scrollHost.find('dk-scroll-track')[0], thumb = scrollHost.find('dk-scroll-thumb')[0];
track.clientHeight = 100;
track.getBoundingClientRect = () => ({top: 0, height: 100});
thumb.getBoundingClientRect = () => ({top: 0, height: 24});
updateScroll();
assert.strictEqual(track.style.display, 'block');
track.fire('mousedown', {target: thumb, clientY: 5, button: 0});
ctx.documentListeners.fire('mousemove', {clientY: 81});
assert.strictEqual(scrollNode.scrollTop, 400);
ctx.documentListeners.fire('mouseup');
assert.strictEqual((ctx.documentListeners.listeners.mousemove || []).length, 0);
scrollNode.scrollHeight = 80; updateScroll();
assert.strictEqual(track.style.display, 'none');
}

push(null, state({canUndo: true, profiles: ['Default']}));
const searchInput = app.find('dk-search')[0];
searchInput.value = 'volume'; searchInput.fire('input');
assert.strictEqual(row('Volume').style.display, '');
assert.strictEqual(row('Name').style.display, 'none');
assert.strictEqual(app.find('dk-nav-item')[1].style.display, 'none');
searchInput.value = ''; searchInput.fire('input');
button('Undo').fire('click'); assert.strictEqual(sent.pop().action, 'undo');
button('Profiles').fire('click');
button('Export JSON').fire('click'); assert.deepStrictEqual(sent.pop(), {action: 'profile', operation: 'export'});
push(null, state({profileText: '{"example":true}'}));
assert.strictEqual(app.find('dk-profile-json')[0].value, '{"example":true}');
button('Import JSON').fire('click'); assert.deepStrictEqual(sent.pop(), {action: 'profile', operation: 'import', text: '{"example":true}'});
button('Close').fire('click');
button('Installed mods').fire('click'); assert.strictEqual(app.find('dk-installed-row').length, 2);
button('Close').fire('click');

// Advanced controls and column mapping use the same schema, with native hotkey codes.
const advanced = JSON.parse(JSON.stringify(schema));
advanced.mods[0].controls = [
    {id: 'hotkey', type: 'hotkey', label: 'Shortcut', default: [[68]], column: 0},
    {id: 'channels', type: 'multiselect', label: 'Channels', default: ['team'], column: 1, options: [{value:'team',label:'Team'},{value:'clan',label:'Clan'}]},
    {id: 'notes', type: 'textarea', label: 'Notes', default: '', column: 0}
];
push(advanced, state({values: {'dk.demo': {hotkey: [[68]], channels: ['team'], notes: 'text'}}, keyNames: {'68': 'F10'}}));
assert.strictEqual(app.find('dk-column').length, 2);
button('F10').fire('click'); assert.deepStrictEqual(sent.pop(), {action:'capture', mod:'dk.demo', key:'hotkey'});
row('Channels').find('dk-option')[1].fire('click'); assert.deepStrictEqual(sent.pop(), {action:'set', mod:'dk.demo', key:'channels', value:['team','clan']});
const notes = row('Notes').all().find(node => node.tagName === 'TEXTAREA'); notes.value = 'edited'; notes.fire('blur');
assert.deepStrictEqual(sent.pop(), {action:'set', mod:'dk.demo', key:'notes', value:'edited'});
push(schema, state());

// Media previews use draft state, recover from missing images, and dispatch audio actions.
const mediaSchema = JSON.parse(JSON.stringify(schema));
mediaSchema.labels['sound.play'] = 'Play'; mediaSchema.labels['sound.stop'] = 'Stop';
mediaSchema.labels['image.unavailable'] = 'Image unavailable';
mediaSchema.mods[0].controls = [
    {id:'image',type:'dropdown',label:'Icon',column:0,options:[{value:0,label:'First'},{value:1,label:'Second'}],
     preview:{kind:'image',images:['coui://gui/first.png','coui://gui/second.png']}},
    {id:'sound',type:'dropdown',label:'Sound',column:1,options:[{value:0,label:'Sound 01'}],
     preview:{kind:'audio',play:'soundPreview',stop:'soundStop'}},
    {id:'precision',type:'slider',label:'Precision',column:1,min:0,max:5,step:0.1}
];
push(mediaSchema,state({values:{'dk.demo':{image:0,sound:0,precision:1.1}},previews:{image:'coui://gui/first.png'}}));
const picture = row('Icon').find('dk-preview-image')[0];
assert.strictEqual(picture.src,'coui://gui/first.png');
picture.fire('load'); assert.strictEqual(picture.style.display,'block');
row('Icon').find('dk-dropdown')[0].fire('click');
assert.strictEqual(ctx.document.body.find('dk-option-image').length,2);
ctx.document.body.find('dk-option')[1].fire('click');
assert.deepStrictEqual(sent.pop(),{mod:'dk.demo',key:'image',value:1,action:'set'});
push(null,state({values:{'dk.demo':{image:1,sound:0,precision:1.1}},previews:{image:'coui://gui/second.png'}}));
assert.strictEqual(picture.src,'coui://gui/second.png');
picture.fire('error'); assert.strictEqual(picture.style.display,'none');
assert.strictEqual(row('Icon').find('dk-preview-missing')[0].style.display,'block');
button('Play').fire('click'); assert.deepStrictEqual(sent.pop(),{mod:'dk.demo',key:'soundPreview',action:'button'});
button('Stop').fire('click'); assert.deepStrictEqual(sent.pop(),{mod:'dk.demo',key:'soundStop',action:'button'});
push(null,state({values:{'dk.demo':{image:1,sound:0,precision:1.1}},disabled:{'dk.demo':['sound']}}));
button('Play').fire('click'); assert.deepStrictEqual(sent.pop(),{mod:'dk.demo',key:'soundPreview',action:'button'});
button('Stop').fire('click'); assert.deepStrictEqual(sent.pop(),{mod:'dk.demo',key:'soundStop',action:'button'});
push(null,state({values:{'dk.demo':{image:1,sound:0,precision:1.1}}}));
const precise = row('Precision').find('dk-slider-value')[0];
precise.value='2,3'; precise.fire('blur');
assert.deepStrictEqual(sent.pop(),{mod:'dk.demo',key:'precision',value:2.3,action:'set'});
push(schema,state());


// Pure color boundaries, prefixes and all alpha scales.
['#D98219','D98219','0xD98219','0xd98219','#d98219'].forEach(c=>assert.strictEqual(ctx.DK.colors.normalizeColor(c),'#D98219'));
['',null,'#12345','0xZZZZZZ','#D9821900'].forEach(c=>assert.strictEqual(ctx.DK.colors.parseColor(c),null));
assert.strictEqual(ctx.DK.colors.formatColor('#123456','0xD98219'),'0x123456');
assert.strictEqual(ctx.DK.colors.formatColor('#123456','D98219'),'123456');
assert.strictEqual(ctx.DK.colors.rgbToHex(ctx.DK.colors.hexToRgb('#D98219')),'#D98219');
['percent','normalized','byte'].forEach(scale=>[0,50,85,100].forEach(ui=>{
 const physical=ctx.DK.colors.alphaFromUi(ui,scale), roundtrip=ctx.DK.colors.alphaToUi(physical,scale);
 assert(Math.abs(roundtrip-ui)<0.2); assert(physical>=0);
}));
assert.strictEqual(ctx.DK.colors.alphaFromUi(NaN,'byte'),null);
assert.strictEqual(ctx.DK.colors.alphaFromUi(50,'byte'),128);

// A legacy color picker keeps all edits local until Apply; Escape restores focus.
push(schema,state()); sent.length=0;
let origin=row('Accent').find('dk-color-swatch')[0];origin.focus();origin.fire('click');
let spectrum=ctx.document.body.find('dk-spectrum')[0];
let hexDraft=ctx.document.body.find('dk-color-picker')[0].all().find(n=>n.tagName==='INPUT');
assert.strictEqual(ctx.document.body.find('dk-spectrum-canvas')[0].style.display,'none', 'CSS fallback without Canvas');
assert.strictEqual(ctx.document.activeElement,spectrum);
ctx.documentListeners.fire('keydown',{keyCode:9});assert.strictEqual(ctx.document.activeElement,hexDraft);
ctx.documentListeners.fire('keydown',{keyCode:9,shiftKey:true});assert.strictEqual(ctx.document.activeElement,spectrum);
const initialDraft=hexDraft.value;
spectrum.fire('keydown',{keyCode:40}); const smallDraft=hexDraft.value;
assert.notStrictEqual(smallDraft,initialDraft); spectrum.fire('keydown',{keyCode:40,shiftKey:true});assert.notStrictEqual(hexDraft.value,smallDraft);
assert.strictEqual(sent.length,0);
ctx.documentListeners.fire('keydown',{keyCode:27});assert.strictEqual(ctx.DK.modal.isOpen(),false);assert.strictEqual(ctx.document.activeElement,origin);assert.strictEqual(sent.length,0);
origin.fire('click');ctx.document.body.find('dk-modal-actions')[0].children[0].fire('click');assert.strictEqual(sent.length,0);
const createElement=ctx.document.createElement; let draws=0;
ctx.document.createElement=tag=>{const n=createElement(tag);if(tag==='canvas'){n.getContext=()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:()=>draws++});}return n;};
origin.fire('click');spectrum=ctx.document.body.find('dk-spectrum')[0];
assert.strictEqual(draws,1);spectrum.fire('mousedown',{clientX:180,clientY:112});ctx.documentListeners.fire('mousemove',{clientX:200,clientY:115});ctx.documentListeners.fire('mouseup',{});
assert.strictEqual(draws,1,'drag never redraws spectrum');assert.strictEqual(sent.length,0);
ctx.DK.modal.close(false);ctx.document.createElement=createElement;
assert.strictEqual((ctx.documentListeners.listeners.mousemove || []).length,0);
// Alpha is explicit and sent with color in a single bridge action.
const alphaSchema=JSON.parse(JSON.stringify(schema));
alphaSchema.mods[0].controls.find(c=>c.id==='accent').metadata={allowAlpha:true,alphaScale:'normalized',alphaKey:'opacity'};
alphaSchema.mods[0].controls.push({id:'opacity',type:'number',label:'Opacity',default:0.5,min:0,max:1,step:0.01});
alphaSchema.mods[0].controls.push({id:'mode',type:'dropdown',label:'Mode',metadata:{sourceType:'RadioButtonGroup'},options:[{value:0,label:'A'},{value:1,label:'B'}]});
push(alphaSchema,state({values:{'dk.demo':Object.assign({},values,{opacity:0.5,mode:0})}}));sent.length=0;
origin=row('Accent').find('dk-color-swatch')[0];origin.fire('click');
let picker=ctx.document.body.find('dk-color-picker')[0],alphaTrack=picker.find('dk-slider-track')[0];
alphaTrack.fire('keydown',{keyCode:39,shiftKey:true});assert.strictEqual(picker.find('dk-alpha-value')[0].textContent,'55%');assert.strictEqual(sent.length,0);
assert.strictEqual(picker.find('dk-preview-fill')[1].style.opacity,0.55);
picker.find('dk-modal-actions')[0].children[1].fire('click');assert.deepStrictEqual(sent.pop(),{action:'set',mod:'dk.demo',key:'accent',value:'#D98219',alpha:0.55});
// Widget navigation stays local; native text cursor keys are untouched.
row('Volume').find('dk-slider-track')[0].fire('keydown',{keyCode:37,shiftKey:true});assert.strictEqual(sent.pop().value,55);
row('Volume').find('dk-slider-track')[0].fire('keydown',{keyCode:36});assert.strictEqual(sent.pop().value,0);
row('Volume').find('dk-slider-track')[0].fire('keydown',{keyCode:33});assert.strictEqual(sent.pop().value,50);
row('Size').all().find(n=>n.tagName==='INPUT').fire('keydown',{keyCode:38,shiftKey:true});assert.strictEqual(sent.pop().value,10);
row('Language').find('dk-dropdown')[0].fire('keydown',{keyCode:35});assert.strictEqual(sent.pop().value,'pt');
row('Mode').find('dk-radio')[0].fire('keydown',{keyCode:39});assert.strictEqual(sent.pop().value,1);
let prevented=0;[37,39,35,36].forEach(keyCode=>row('Name').all().find(n=>n.tagName==='INPUT').fire('keydown',{keyCode,preventDefault:()=>prevented++}));assert.strictEqual(prevented,0);
push(null,state({disabled:{'dk.demo':['enabled','volume','accent','size','mode']}}));
['Enable','Volume','Accent','Size','Mode'].forEach(label=>row(label).all().filter(n=>n.disabled).forEach(n=>assert.strictEqual(n.tabIndex,-1)));
row('Volume').find('dk-slider-track')[0].fire('keydown',{keyCode:39});assert.strictEqual(sent.length,0);
push(schema,state());

// External warnings patch the header without becoming dependencies or disabled state.
push(schema,state());sent.length=0;
const warningRow=row('Volume');
push(null,state({compatibilityWarnings:{'dk.demo':[{code:'external.XVM.PlayerPanelPro',level:'warning',text:'<b>XVM</b> may overlap.'}]}}));
assert.strictEqual(app.find('dk-compatibility-warnings')[0].textContent,'⚠ <b>XVM</b> may overlap.');
assert.strictEqual(row('Volume'),warningRow);
assert.strictEqual(row('Volume').find('dk-slider-track')[0].tabIndex,0);
assert.strictEqual(sent.length,0);
push(null,state());assert.strictEqual(app.find('dk-compatibility-warnings')[0].style.display,'none');

// Selecting another mod rebuilds the content area.
// Optional metadata and category grouping remain presentation-only.
const categorized = JSON.parse(JSON.stringify(schema));
categorized.labels['category.battle'] = 'Battle';
categorized.labels['category.system'] = 'System';
categorized.labels['timing.battle'] = 'Next battle';
categorized.labels['status.disabled'] = 'Off';
categorized.mods[0].category = 'battle';
categorized.mods[1].category = 'system';
categorized.mods[0].dependencies = [{id: 'available', installed: true}, {id: 'missing', installed: false}];
categorized.mods[0].controls.find(c => c.id === 'volume').metadata = {sourceType: 'NumericStepper', applyTiming: 'battle'};
push(categorized, state({status: {'dk.demo': {status:'active', enabled:false, restartRequired:true}}}));
assert.deepStrictEqual(app.find('dk-nav-category').map(n => n.textContent), ['Battle', 'System']);
assert(app.find('dk-nav-status')[0].textContent.includes('Off'));
assert(app.find('dk-nav-status')[0].textContent.includes('Restart required'));
assert(app.find('dk-nav-status')[0].textContent.includes('missing'));
assert(app.find('dk-mod-dependencies')[0].textContent.includes('available'));
assert(row('Volume').find('dk-apply-timing')[0].textContent.includes('Next battle'));
const beforeNav = app.find('dk-nav-item')[0], beforeRow = row('Volume');
push(null, state({values: {'dk.demo': Object.assign({}, values, {volume:35})}, status:{'dk.demo':{status:'configError',enabled:true}}}));
assert.strictEqual(app.find('dk-nav-item')[0], beforeNav);
assert.strictEqual(row('Volume'), beforeRow);
assert(beforeNav.has('is-error'));
searchInput.value = 'volume'; searchInput.fire('input');
assert.strictEqual(app.find('dk-nav-group')[1].style.display, 'none');
searchInput.value = 'battle'; searchInput.fire('input');
assert.strictEqual(app.find('dk-nav-item')[0].style.display, 'flex');
searchInput.value = ''; searchInput.fire('input');
const custom = JSON.parse(JSON.stringify(categorized));
custom.mods[0].category = 'Tools'; delete custom.mods[1].category;
push(custom,state());
assert.deepStrictEqual(app.find('dk-nav-category').map(n=>n.textContent), ['General','Tools']);
// Return to the unextended schema: no badge and all original controls still render.
push(schema,state());
assert.strictEqual(app.find('dk-apply-timing').length,0);
assert.strictEqual(rows().length,8);
app.find('dk-nav-item')[1].fire('click');
assert.deepStrictEqual(sent.pop(), {mod: 'dk.settings', action: 'select'});
push(null, state({selected: 'dk.settings'}));
assert.strictEqual(rows().length, 0);
assert(app.find('dk-nav-item')[1].has('is-selected'));

// Disposal releases the model subscription and listeners.
ctx.windowListeners.unload();
assert.strictEqual(changed, null);
assert.deepStrictEqual(removed, [[7, 0]]);
assert.strictEqual((ctx.documentListeners.listeners.keydown || []).length, 0);

console.log('Integrated settings Gameface controls and disposal passed');
