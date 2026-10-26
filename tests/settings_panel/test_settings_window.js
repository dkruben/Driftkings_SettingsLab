/* Settings window scripts load together in catalog order and every control and dialog builds. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.resolve(__dirname, '../..');
const jsRoot = path.join(root, 'mod/res/gui/gameface/mods/driftkings/settings_window/js');

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

const app = new Node('main'), themeStyle = new Node('style');
const document = {
    body: new Node('body'), documentElement: new Node('html'), activeElement: null, listeners: {},
    createElement: tag => new Node(tag),
    createDocumentFragment: () => Object.assign(new Node('fragment'), {isFragment: true}),
    getElementById: id => ({'dk-app': app, 'dk-theme': themeStyle})[id],
    addEventListener(type, handler) { (this.listeners[type] = this.listeners[type] || []).push(handler); },
    removeEventListener(type, handler) { this.listeners[type] = (this.listeners[type] || []).filter(h => h !== handler); }
};
const sent = [];
let callbacks = null;
const window = {innerWidth: 1920, innerHeight: 1080, addEventListener() {}, removeEventListener() {}};
const DK = window.DK = {bridge: {
    start: next => { callbacks = next; }, send: (action, data) => sent.push([action, data || {}]),
    scale: () => 1, clientSizeRem: () => ({width: 1920, height: 1080}), dispose() {}
}};
const context = {window, document, setTimeout: () => 0, clearTimeout() {}, JSON, Math, Date, Object, Array, String, Number, isFinite, parseFloat, parseInt};
vm.createContext(context);
// Same order as interface_catalog.py; the bridge is replaced by the stub above.
const catalog = fs.readFileSync(path.join(root, 'mod/res/scripts/client/driftkings/interface_catalog.py'), 'utf8');
const scripts = catalog.match(/settings_window\/js\/[a-z_]+\.js/g).map(name => name.split('/').pop());
assert.deepStrictEqual(scripts, ['bridge.js', 'colors.js', 'modal.js', 'dom.js', 'control_kit.js', 'color_picker.js',
    'controls.js', 'theme.js', 'updater_panel.js', 'profile_dialogs.js', 'vehicle_markers_model.js', 'vehicle_markers_editor.js', 'app.js']);
const html = fs.readFileSync(path.join(jsRoot, '..', 'window.html'), 'utf8');
assert.deepStrictEqual(html.match(/js\/[a-z_]+\.js/g).map(name => name.slice(3)), scripts);
scripts.filter(name => name !== 'bridge.js').forEach(name => {
    vm.runInContext(fs.readFileSync(path.join(jsRoot, name), 'utf8'), context, {filename: name});
});
['dom', 'layer', 'controlKit', 'controls', 'theme', 'updaterPanel', 'profileDialogs', 'app'].forEach(name => assert(DK[name], name));
assert.strictEqual(typeof DK.controlKit.color, 'function');
assert.strictEqual(DK.app.themeCss, DK.theme.css);

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

callbacks.schema(schema);
callbacks.state(state);
assert(themeStyle.textContent.indexOf('#D98219') >= 0, 'theme stylesheet');
const window_ = app.firstChild;
assert(window_.querySelectorAll('.dk-row').length >= 12, 'every value control renders a row');
assert(window_.querySelectorAll('.dk-updates').length === 1, 'updates section on the Driftkings page');
const status = window_.querySelectorAll('.dk-update-line');
assert.strictEqual(status[0].textContent, 'Installed: 1.0');

// The native alert icon marks restart-only controls and modules that need attention.
const restartBadge = window_.querySelectorAll('.dk-apply-timing--restart')[0];
assert.strictEqual(restartBadge.querySelectorAll('.dk-alert-icon').length, 1, 'restart badge has the alert icon');
assert.strictEqual(window_.querySelectorAll('.dk-apply-timing--live')[0].querySelectorAll('.dk-alert-icon').length, 0);
// Statuses: "✓ On" for the active page, "Error • Missing dependency: x" for the other module.
const alertShown = text => window_.querySelectorAll('.dk-nav-status').filter(node => node.textContent.indexOf(text) >= 0)
    .map(node => node.childNodes[0].className.indexOf('is-hidden') < 0)[0];
assert.strictEqual(alertShown('On'), false, 'an active module has no alert icon');
assert.strictEqual(alertShown('Missing dependency'), true, 'an errored module with a missing dependency shows the alert icon');
callbacks.state(Object.assign({}, state, {restartRequired: ['dk.settings']}));
assert.strictEqual(alertShown('On'), true, 'a pending restart shows the alert icon');
callbacks.state(state);

// The dropdown popup opens in the layer and a choice commits through the bridge.
const dropdown = window_.querySelectorAll('.dk-dropdown')[0];
dropdown.fire('click');
assert(DK.layer.isOpen());
DK.layer.close();
assert(!DK.layer.isOpen());
// The colour picker opens as a modal with its alpha slider and closes cleanly.
window_.querySelectorAll('.dk-color-swatch')[0].fire('click');
assert(DK.modal.isOpen());
DK.modal.close(false);
assert(!DK.modal.isOpen());
// Switch commits its new value.
window_.querySelectorAll('.dk-switch')[0].fire('click');
// Payloads come from another VM realm: compare them as JSON.
assert.strictEqual(JSON.stringify(sent.pop()), JSON.stringify(['set', {mod: 'dk.settings', key: 'on', value: false}]));

// Profile and installed dialogs open and close through the shared dialog module.
const footer = window_.querySelectorAll('.dk-btn').filter(node => node.textContent === 'Profiles')[0];
footer.fire('click');
assert(DK.profileDialogs.isOpen());
DK.profileDialogs.close();
assert(!DK.profileDialogs.isOpen());
window_.querySelectorAll('.dk-installed-button')[0].fire('click');
assert(DK.profileDialogs.isOpen());

// Integrated editor uses the same controls and sends JSON drafts through the normal session.
const markerValues = {enabled: true, debug: false};
['general','markers','fields','colors','healthbar','damage','icons'].forEach(name => {
    Object.assign(markerValues, JSON.parse(fs.readFileSync(path.join(root, 'res/configs/driftkings/default/vehicle_markers', name + '.json'), 'utf8')));
});
const markerBindings = {}, markerState = {}, markerCommits = [];
['enabled','debug','markers','customFields','colors','healthBar','damageText','icons','ratingType'].forEach(key => {
    markerBindings[key] = key;
    markerState[key] = typeof markerValues[key] === 'boolean' ? markerValues[key] : JSON.stringify(markerValues[key]);
});
markerState.ratingType=0;
const markerHost = new Node('div');
const markerEditor = DK.vehicleMarkersEditor.create(markerHost, {preview: {labels:{},bindings:markerBindings,tank:'sample.png'}}, {
    labels:{on:'On',off:'Off'},commit(key,value) { markerCommits.push([key,value]); }
});
markerEditor.update(markerState);
assert.strictEqual(markerHost.querySelector('.dk-vm-tank').src, 'sample.png');
assert(markerHost.querySelectorAll('.dk-vm-text').length > 0);
const originalFieldCount = markerHost.querySelectorAll('.dk-vm-text').length;
markerHost.querySelectorAll('button').find(node => node.textContent === 'add').fire('click');
assert.strictEqual(markerHost.querySelectorAll('.dk-vm-text').length, originalFieldCount + 1);
assert.strictEqual(markerCommits[0][0], 'customFields');
const formatInput = markerHost.querySelector('textarea');
formatInput.value = '<b>{{vehicle}} {{hp}}</b>';
formatInput.fire('input');
assert.strictEqual(markerCommits.length, 1, 'typing previews without persisting');
formatInput.fire('blur');
assert.strictEqual(JSON.parse(markerCommits[1][1]).enemy.alive.normal.slice(-1)[0].format, formatInput.value);
markerHost.querySelectorAll('button').find(node => node.textContent === 'healthBar').fire('click');
assert(markerHost.querySelectorAll('.dk-row').some(node => node.getAttribute('data-property') === 'healthBar.enemy.alive.normal.color'));
markerHost.querySelector('.dk-vm-actions').querySelectorAll('button').find(node => node.textContent === 'damage').fire('click');
assert(markerHost.querySelector('.dk-vm-damage'));
// Select a destroyed ally in ALT and change only that context's bar position.
function markerButton(text) { return markerHost.querySelectorAll('button').find(node => node.textContent === text); }
markerButton('ally').fire('click');
markerButton('alive').fire('click');
markerButton('normal').fire('click');
assert.strictEqual(markerHost.querySelector('.dk-vm-damage'), null);
const scopedX = markerHost.querySelectorAll('.dk-row').find(node => node.getAttribute('data-property') === 'healthBar.ally.dead.extended.x');
assert(scopedX);
const xInput = scopedX.querySelector('input');
xInput.value='49'; xInput.fire('blur');
const changedBar = JSON.parse(markerCommits[markerCommits.length-1][1]);
assert.strictEqual(changedBar.ally.dead.extended.x,49);
assert.deepStrictEqual(changedBar.enemy.alive.normal,markerValues.healthBar.enemy.alive.normal);
assert.strictEqual(changedBar.x,markerValues.healthBar.x);
markerButton('enemy').fire('click');
assert(markerHost.querySelectorAll('.dk-row').some(node => node.getAttribute('data-property') === 'healthBar.enemy.dead.extended.x'));
markerButton('customFields').fire('click');
markerButton('addRating').fire('click');
const ratingDraft=JSON.parse(markerCommits[markerCommits.length-1][1]);
assert.strictEqual(ratingDraft.enemy.dead.extended.slice(-1)[0].format,'{{r}}');
markerButton('extended').fire('click');
markerButton('addRating').fire('click');
markerButton('ratingType').fire('click');
assert.strictEqual(markerHost.querySelectorAll('.dk-vm-text').slice(-1)[0].style.opacity,0);
markerButton('ratingType').fire('click');
assert.strictEqual(markerHost.querySelectorAll('.dk-vm-text').slice(-1)[0].style.opacity,1);
markerButton('general').fire('click');
const ratingControl=markerHost.querySelectorAll('.dk-row').find(node => node.getAttribute('data-property')==='ratingType');
ratingControl.querySelector('.dk-dropdown').fire('keydown',{keyCode:40});
assert.deepStrictEqual(markerCommits[markerCommits.length-1],['ratingType',1]);
markerButton('damageText').fire('click');
let authorFormat=markerHost.querySelectorAll('.dk-row').find(node => node.getAttribute('data-property')==='damageText.enemy.dead.normal.sources.player.format').querySelector('textarea');
authorFormat.value='Player {{dmg}}'; authorFormat.fire('blur');
markerHost.querySelectorAll('button').find(node => node.getAttribute('data-damage-source')==='squad').fire('click');
let authorX=markerHost.querySelectorAll('.dk-row').find(node => node.getAttribute('data-property')==='damageText.enemy.dead.normal.sources.squad.x').querySelector('input');
authorX.value='55'; authorX.fire('blur');
const authorDraft=JSON.parse(markerCommits[markerCommits.length-1][1]);
assert.strictEqual(authorDraft.enemy.dead.normal.sources.player.format,'Player {{dmg}}');
assert.strictEqual(authorDraft.enemy.dead.normal.sources.squad.x,55);
assert.strictEqual(authorDraft.format,markerValues.damageText.format);
markerButton('customFields').fire('click');
markerButton('addDistance').fire('click');
assert.strictEqual(JSON.parse(markerCommits[markerCommits.length-1][1]).enemy.dead.normal.slice(-1)[0].format,'{{distance|--}} m');
markerEditor.dispose();
assert.strictEqual(markerHost.children.length, 0);

DK.app.dispose();
assert(!DK.profileDialogs.isOpen() && !DK.modal.isOpen() && !DK.layer.isOpen());
console.log('Settings window: scripts, controls, theme, updates and dialogs OK');
