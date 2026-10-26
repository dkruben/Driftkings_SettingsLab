/* Vehicle marker editor: health colour bands and slider limits that must match core/vehicle_markers validation. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.resolve(__dirname, '../..');
const jsRoot = path.join(root, 'mod/res/gui/gameface/mods/driftkings/settings_window/js');
const configRoot = path.join(root, 'res/configs/driftkings/default/vehicle_markers');

// Same minimal DOM stub as test_settings_window.js.
class Node {
    constructor(tag) {
        this.tagName = String(tag).toUpperCase(); this.childNodes = []; this.parentNode = null;
        this.style = {}; this.className = ''; this.attributes = {}; this.listeners = {};
        this._text = ''; this.disabled = false; this.value = '';
    }
    get children() { return this.childNodes; }
    get firstChild() { return this.childNodes[0] || null; }
    get lastChild() { return this.childNodes[this.childNodes.length - 1] || null; }
    contains(other) { return other === this || this.childNodes.some(child => child.contains(other)); }
    remove() { if (this.parentNode) { this.parentNode.removeChild(this); } }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    get textContent() { return this._text + this.childNodes.map(child => child.textContent).join(''); }
    set textContent(value) { this._text = String(value); this.childNodes.forEach(child => { child.parentNode = null; }); this.childNodes = []; }
    get tabIndex() { return this._tabIndex === undefined ? (/^(BUTTON|INPUT|TEXTAREA)$/.test(this.tagName) ? 0 : -1) : this._tabIndex; }
    set tabIndex(value) { this._tabIndex = value; }
    appendChild(child) {
        if (child.isFragment) { child.childNodes.slice().forEach(node => this.appendChild(node)); return child; }
        if (child.parentNode) { child.parentNode.removeChild(child); }
        child.parentNode = this; this.childNodes.push(child); return child;
    }
    removeChild(child) { this.childNodes = this.childNodes.filter(node => node !== child); child.parentNode = null; return child; }
    addEventListener(type, handler) { (this.listeners[type] = this.listeners[type] || []).push(handler); }
    removeEventListener(type, handler) { this.listeners[type] = (this.listeners[type] || []).filter(h => h !== handler); }
    fire(type, extra) {
        const event = Object.assign({type, target: this, button: 0, clientX: 10, clientY: 10, preventDefault() {}, stopPropagation() {}}, extra);
        (this.listeners[type] || []).slice().forEach(handler => handler.call(this, event));
    }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
    getBoundingClientRect() { return {left: 0, top: 0, right: 100, bottom: 20, width: 100, height: 20}; }
    focus() { document.activeElement = this; }
    getContext() { return null; }
    matches(selector) {
        return selector.split(',').some(part => {
            part = part.trim();
            if (part === '[tabindex]') { return this._tabIndex !== undefined; }
            if (part[0] === '.') { return this.className.split(' ').indexOf(part.slice(1)) >= 0; }
            return this.tagName === part.toUpperCase();
        });
    }
    querySelectorAll(selector) {
        const found = [];
        const walk = node => node.childNodes.forEach(child => { if (child.matches(selector)) { found.push(child); } walk(child); });
        walk(this); return found;
    }
    get offsetWidth() { return 100; }
    get offsetHeight() { return 20; }
}

const document = {
    body: new Node('body'), documentElement: new Node('html'), activeElement: null, listeners: {},
    createElement: tag => new Node(tag),
    createDocumentFragment: () => Object.assign(new Node('fragment'), {isFragment: true}),
    getElementById: () => null,
    addEventListener() {}, removeEventListener() {}
};
const window = {innerWidth: 1920, innerHeight: 1080, addEventListener() {}, removeEventListener() {}};
const DK = window.DK = {bridge: {send() {}, scale: () => 1, clientSizeRem: () => ({width: 1920, height: 1080}), dispose() {}}};
const context = {window, document, setTimeout: () => 0, clearTimeout() {}, JSON, Math, Date, Object, Array, String, Number, isFinite, parseFloat, parseInt};
vm.createContext(context);
['colors.js', 'modal.js', 'dom.js', 'control_kit.js', 'color_picker.js', 'controls.js',
 'vehicle_markers_model.js', 'vehicle_markers_editor.js'].forEach(name => {
    vm.runInContext(fs.readFileSync(path.join(jsRoot, name), 'utf8'), context, {filename: name});
});

// Remember every control the editor builds, with the definition it was given.
const created = [];
const createControl = DK.controls.create;
DK.controls.create = function (def, handlers) {
    const api = createControl.apply(this, arguments);
    created.push({def, handlers, api});
    return api;
};

const files = {};
['markers', 'markersAliveNormal', 'markersAliveExtended', 'markersDeadNormal', 'markersDeadExtended'].forEach(key => {
    files[key] = JSON.parse(fs.readFileSync(path.join(configRoot, key + '.json'), 'utf8'));
});
const markers = Object.assign({}, files.markers.markers);
const enabled = markers.enabled;
delete markers.enabled;
const bindings = {enabled: 'enabled', markers: 'markers', markersAliveNormal: 'markersAliveNormal',
    markersAliveExtended: 'markersAliveExtended', markersDeadNormal: 'markersDeadNormal', markersDeadExtended: 'markersDeadExtended'};
const values = {enabled, markers: JSON.stringify(markers)};
Object.keys(files).filter(key => key !== 'markers').forEach(key => { values[key] = JSON.stringify(files[key]); });

const commits = [];
const parent = new Node('div');
// Without labels every caption is its own key, which keeps the lookups below simple.
const editor = DK.vehicleMarkersEditor.create(parent, {preview: {labels: {}, bindings, palettes: null, tank: 'tank.png'}},
    {labels: {}, commit: (key, value) => commits.push([key, value]), preview() {}});
editor.update(values);
const button = text => parent.querySelectorAll('button').filter(node => node.textContent === text)[0];
const property = suffix => created.filter(item => (item.api.node.getAttribute('data-property') || '').slice(-suffix.length) === suffix)[0];
const open = section => { created.length = 0; button(section).fire('click'); };

// General tab: the health colour limits can be added and removed, and they are saved in markers.json.
open('general');
assert(button('addBand'), 'the add-limit button is shown on the General tab');
button('addBand').fire('click');
let saved = commits[commits.length - 1];
assert.strictEqual(saved[0], 'markers');
let bands = JSON.parse(saved[1]).colors.hp;
assert.deepStrictEqual(bands.map(band => band.value), [25, 50, 75, 87, 100]);
button('remove').fire('click');
saved = commits[commits.length - 1];
assert.deepStrictEqual(JSON.parse(saved[1]).colors.hp.map(band => band.value), [25, 50, 75, 100]);

// Editing a limit of a list that only exists as a default stores an array, not an object keyed by index.
const fresh = DK.vehicleMarkersEditor.create(new Node('div'), {preview: {labels: {}, bindings, palettes: null, tank: 'tank.png'}},
    {labels: {}, commit: (key, value) => commits.push([key, value]), preview() {}});
fresh.update(values);
created.length = 0;
fresh.node.querySelectorAll('button').filter(node => node.textContent === 'general')[0].fire('click');
const first = property('colors.hp.0.value');
assert(first, 'the first colour limit is editable');
first.handlers.commit(first.def.id, 30);
bands = JSON.parse(commits[commits.length - 1][1]).colors.hp;
assert(Array.isArray(bands), 'colors.hp stays a list');
assert.deepStrictEqual(bands.map(band => band.value), [30, 50, 75, 100]);

// Slider limits are the ones the validators accept.
const limits = (section, suffix) => {
    open(section);
    const item = property(suffix);
    assert(item, section + ' ' + suffix);
    return [item.def.min, item.def.max, item.def.step];
};
assert.deepStrictEqual(limits('healthBar', 'healthBar.height'), [2, 100, 1]);
assert.deepStrictEqual(limits('healthBar', 'healthBar.width'), [4, 500, 1]);
assert.deepStrictEqual(limits('healthBar', 'border.size'), [0, 10, 1]);
assert.deepStrictEqual(limits('healthBar', 'damage.fade'), [0.1, 5, 0.1]);
assert.deepStrictEqual(limits('damageText', 'damageText.speed'), [0.1, 10, 0.1]);
assert.deepStrictEqual(limits('damageText', 'damageText.maxRange'), [0, 300, 1]);
// A circular template reference is reported in the error box; it must not throw out of update() or the buttons.
const broken = JSON.parse(values.markersAliveNormal);
broken.def.damageText = {$ref: {path: 'def.damageText'}};
const damaged = new Node('div');
const guarded = DK.vehicleMarkersEditor.create(damaged, {preview: {labels: {}, bindings, palettes: null, tank: 'tank.png'}},
    {labels: {}, commit() {}, preview() {}});
assert.doesNotThrow(() => guarded.update(Object.assign({}, values, {markersAliveNormal: JSON.stringify(broken)})));
assert(/circular/i.test(damaged.querySelectorAll('.dk-vm-error')[0].textContent), 'the error box explains the reference problem');
assert.doesNotThrow(() => damaged.querySelectorAll('button').filter(node => node.textContent === 'damage')[0].fire('click'));
assert.doesNotThrow(() => damaged.querySelectorAll('button').filter(node => node.textContent === 'general')[0].fire('click'));

console.log('Vehicle marker editor: colour limits, slider limits and invalid references passed');
