'use strict';
// Exercise the production shared lifecycle and renderer with a minimal DOM.
var assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
function target() {
    return {handlers: {}, addEventListener: function (name, fn) {
        (this.handlers[name] || (this.handlers[name] = [])).push(fn);
    }, removeEventListener: function (name, fn) {
        this.handlers[name] = (this.handlers[name] || []).filter(function (item) { return item !== fn; });
    }, fire: function (name, event) {
        (this.handlers[name] || []).slice().forEach(function (fn) { fn(event); });
    }};
}
function element(tag) {
    var node = target();
    node.tagName = tag; node.style = {}; node.children = [];
    node.appendChild = function (child) { child.parentNode = node; node.children.push(child); };
    node.removeChild = function (child) { node.children.splice(node.children.indexOf(child), 1); child.parentNode = null; };
    Object.defineProperty(node, 'firstChild', {get: function () { return node.children[0]; }});
    node.getBoundingClientRect = function () {
        var match = /scale\(([^)]+)\)/.exec(node.style.transform || '');
        var scale = match ? parseFloat(match[1]) : 1;
        return {left: parseFloat(node.style.left) || 0, top: parseFloat(node.style.top) || 0,
            width: (parseFloat(node.style.width) || 290) * scale, height: 84 * scale};
    };
    return node;
}
var document = target();
document.body = element('body'); document.documentElement = element('html'); document.createElement = element;
var window = target();
window.innerWidth = 1920; window.innerHeight = 1080;
window.getComputedStyle = function () { return {fontSize: '1px'}; };
var saved = [], queue = [], registered = 0;
var model = {payload: '{}', DriftkingsUI: {name: 'DriftkingsMainGun'}, onSavePosition: function (value) { saved.push(value); }};
window.subViews = {ids: function () { return [42]; }, get: function () { return {model: model}; }};
var engine = target();
engine.whenReady = {then: function (fn) { fn(); }}; engine.on = engine.addEventListener; engine.off = engine.removeEventListener;
var context = vm.createContext({window: window, document: document, engine: engine,
    viewEnv: {addDataChangedCallback: function () { registered++; return 7; }, removeDataChangedCallback: function () { registered--; }},
    setTimeout: function (fn) { queue.push(fn); return queue.length; }, clearTimeout: function () { queue = []; }});
var base = path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings');
function load(relative) { vm.runInContext(fs.readFileSync(path.join(base, relative), 'utf8'), context); }
function flush() { while (queue.length) { queue.shift()(); } }
load('shared/marks_panel.js'); load('high_caliber_gameface/main_gun.js'); flush();
var root = document.body.firstChild;
assert.strictEqual(root.style.display, 'none');
var data = {visible: true, state: 'progress', progress: 25, primaryText: '3,000 HP',
    secondaryText: 'remaining for High Caliber', progressText: '25%', progressLabel: 'Progress',
    config: {visible: true, locked: false, draggable: false, scale: 1, x: 200, y: 200}};
function update() { model.payload = JSON.stringify(data); engine.fire('viewEnv.onDataChanged'); flush(); }
function find(cls, parent) {
    parent = parent || root;
    if (parent.className === cls) { return parent; }
    for (var i = 0; i < parent.children.length; i++) { var found = find(cls, parent.children[i]); if (found) { return found; } }
    return null;
}
update();
assert.strictEqual(root.style.display, 'block');
assert.strictEqual(find('dk-main-gun__fill').style.width, '25%');
assert.strictEqual(find('dk-main-gun__value').textContent, '3,000 HP');
assert.strictEqual(find('dk-main-gun__medal').src, 'coui://gui/maps/icons/achievement/32x32/mainGun.png');
assert.strictEqual(root.style.pointerEvents, 'none');
data.state = 'achieved'; data.progress = 100; data.primaryText = '4,000 HP'; update();
assert.strictEqual(find('dk-main-gun__fill').style.backgroundColor, '#7DCEA0');
data.state = 'progress'; data.progress = 80; update();
assert.strictEqual(find('dk-main-gun__fill').style.width, '80%');
data.state = 'unavailable'; data.primaryText = '<b>UNAVAILABLE</b>'; update();
assert.strictEqual(find('dk-main-gun__fill').style.backgroundColor, '#D77D7D');
assert.strictEqual(find('dk-main-gun__value').textContent, '<b>UNAVAILABLE</b>');
data.config.showProgress = false; data.config.showPercentage = false; data.config.showSecondary = false; update();
assert.strictEqual(find('dk-main-gun__footer').style.display, 'none');
assert.strictEqual(find('dk-main-gun__secondary').style.display, 'none');
data.config.draggable = true; update();
assert.strictEqual(root.style.pointerEvents, 'auto');
var event = {target: find('dk-main-gun__value'), button: 0, clientX: 210, clientY: 210,
    preventDefault: function () {}, stopPropagation: function () {}};
document.fire('mousedown', event); event.clientX = 230; event.clientY = 240;
// While dragging, a full-screen layer keeps input flowing after the cursor leaves the panel.
var shield = document.body.children[1];
assert.strictEqual(shield.className, 'dk-drag-shield'); assert.strictEqual(shield.style.pointerEvents, 'auto');
event.target = shield;
document.fire('mousemove', event); document.fire('mouseup', event);
assert.strictEqual(document.body.children.length, 1); assert.strictEqual(shield.parentNode, null);
assert.strictEqual(saved.length, 1); assert.strictEqual(saved[0].x, 220); assert.strictEqual(saved[0].y, 230);
assert.strictEqual(saved[0].alignX, 'left'); assert.strictEqual(saved[0].alignY, 'top');
// Dropped near the bottom-right corner, the position is stored relative to that corner.
event.target = find('dk-main-gun__value'); event.clientX = 230; event.clientY = 240;
document.fire('mousedown', event); event.clientX = 2000; event.clientY = 2000;
document.fire('mousemove', event); document.fire('mouseup', event);
assert.strictEqual(saved.length, 2);
assert.strictEqual(JSON.stringify(saved[1]), JSON.stringify({x: 0, y: 0, alignX: 'right', alignY: 'bottom'}));
saved.pop();
window.innerWidth = 320; window.innerHeight = 100; data.config.scale = 3; update();
var bounds = root.getBoundingClientRect(); assert(bounds.width <= 320 && bounds.height <= 100);
data.config.locked = true; update(); document.fire('mousedown', event); document.fire('mouseup', event);
assert.strictEqual(saved.length, 1);
data.config.visible = false; update(); assert.strictEqual(root.style.display, 'none');
load('high_caliber_gameface/main_gun.js'); flush();
assert.strictEqual(document.body.children.length, 1); assert.strictEqual(registered, 1);
window.__dkMainGun.dispose();
assert.strictEqual(registered, 0); assert.strictEqual(document.body.children.length, 0);
assert.strictEqual(document.handlers.mousedown.length, 0);
assert.strictEqual(engine.handlers['viewEnv.onDataChanged'].length, 0);
console.log('MainGun Gameface lifecycle, states, drag and responsive sizing: OK');
