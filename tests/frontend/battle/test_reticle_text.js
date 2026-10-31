'use strict';
// Texts beside the crosshair: placed at crosshair + offset, one row per line, dragged with Ctrl.
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
// A tiny parser for the Flash subset used by the templates.
function parse(node, html) {
    var stack = [node], re = /<(\/?)(\w+)([^>]*)>|([^<]+)/g, match;
    while ((match = re.exec(html))) {
        var top = stack[stack.length - 1];
        if (match[4]) { var text = element('#text'); text.nodeType = 3; text.nodeValue = match[4]; top.appendChild(text); continue; }
        if (match[1]) { stack.pop(); continue; }
        var child = element(match[2]), attrs = /(\w+)='([^']*)'/g, attr;
        while ((attr = attrs.exec(match[3]))) { child.setAttribute(attr[1], attr[2]); }
        top.appendChild(child);
        if (match[2].toLowerCase() !== 'br') { stack.push(child); }
    }
}
function element(tag) {
    var node = target(), attributes = {};
    node.tagName = tag; node.nodeType = 1; node.style = {}; node.children = []; node.childNodes = node.children;
    node.appendChild = function (child) { child.parentNode = node; node.children.push(child); };
    node.removeChild = function (child) { node.children.splice(node.children.indexOf(child), 1); child.parentNode = null; };
    node.getAttribute = function (name) { return attributes[name]; };
    node.setAttribute = function (name, value) { attributes[name] = value; };
    Object.defineProperty(node, 'firstChild', {get: function () { return node.children[0]; }});
    Object.defineProperty(node, 'innerHTML', {set: function (html) { node.children.length = 0; parse(node, html); }});
    node.getBoundingClientRect = function () {
        return {left: parseFloat(node.style.left) || 0, top: parseFloat(node.style.top) || 0, width: 120, height: 40};
    };
    return node;
}
var document = target();
document.body = element('body'); document.documentElement = element('html'); document.createElement = element;
var window = target();
window.innerWidth = 1920; window.innerHeight = 1080;
window.getComputedStyle = function () { return {fontSize: '2px'}; };
var queue = [], saved = [];
var model = {payload: '{}', DriftkingsUI: {name: 'DriftkingsPenetration'}, onSavePosition: function (value) { saved.push(value); }};
window.subViews = {ids: function () { return [42]; }, get: function () { return {model: model}; }};
var engine = target();
engine.whenReady = {then: function (fn) { fn(); }}; engine.on = engine.addEventListener; engine.off = engine.removeEventListener;
var context = vm.createContext({window: window, document: document, engine: engine, Date: Date,
    viewEnv: {addDataChangedCallback: function () { return 7; }, removeDataChangedCallback: function () {}},
    setTimeout: function (fn) { queue.push(fn); return queue.length; }, clearTimeout: function () { queue = []; },
    requestAnimationFrame: function (fn) { queue.push(fn); return queue.length; }});
var base = path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings');
function load(relative) { vm.runInContext(fs.readFileSync(path.join(base, relative), 'utf8'), context); }
function flush() { while (queue.length) { queue.shift()(); } }
load('shared/marks_panel.js'); load('shared/flash_lines.js'); load('shared/reticle_text.js'); load('penetration_indicator/penetration_indicator.js'); flush();
var root = document.body.firstChild, content = root.children[0];
assert.strictEqual(root.className, 'dk-reticle-text dk-reticle-text--penetration');
var data = {text: "RICOCHET<br><font color='#66FF33' size='22'>80 | <b>120</b></font>", anchorX: 0.5, anchorY: 0.5,
    config: {visible: true, draggable: false, locked: false, x: 10, y: 40, align: 'center'}};
function update() { model.payload = JSON.stringify(data); engine.fire('viewEnv.onDataChanged'); flush(); }
update();
assert.strictEqual(root.style.display, 'block');
// Centre of the 120px box on crosshair + offset (2px per interface unit).
assert.strictEqual(root.style.left, (960 + 20 - 60) + 'px');
assert.strictEqual(root.style.top, (540 + 80) + 'px');
assert.strictEqual(content.style.alignItems, 'center');
// One row per line; inline runs keep their own colour, size and weight.
assert.strictEqual(content.children.length, 2);
assert.strictEqual(content.children[0].children[0].textContent, 'RICOCHET');
var runs = content.children[1].children;
assert.strictEqual(runs[0].textContent, '80 | ');
assert.strictEqual(runs[0].style.color, '#66FF33'); assert.strictEqual(runs[0].style.fontSize, '22rem');
assert.strictEqual(runs[1].textContent, '120'); assert.strictEqual(runs[1].style.fontWeight, 'bold');
assert.strictEqual(root.style.pointerEvents, 'none');
// The crosshair moves: the text follows it.
data.anchorY = 0.6; update();
assert.strictEqual(root.style.top, (648 + 80) + 'px');
// Ctrl: the text can be dragged and the new offset is reported relative to the crosshair.
data.config.draggable = true; update();
assert.strictEqual(root.style.pointerEvents, 'auto');
var event = {target: runs[0], button: 0, clientX: 960, clientY: 730, preventDefault: function () {}, stopPropagation: function () {}};
document.fire('mousedown', event);
event.clientX = 1000; event.clientY = 750; document.fire('mousemove', event);
// A new text while dragging does not snap it back.
data.text = '81 | 120'; update();
assert.strictEqual(root.style.left, (920 + 40) + 'px');
document.fire('mouseup', event);
assert.deepStrictEqual(JSON.parse(JSON.stringify(saved)), [{x: 30, y: 50}]);
// Until the saved offset comes back the dropped position is kept; then it is placed from it.
update();
assert.strictEqual(root.style.left, (920 + 40) + 'px');
data.config.x = 30; data.config.y = 50; update();
assert.strictEqual(root.style.left, (960 + 60 - 60) + 'px');
assert.strictEqual(root.style.top, (648 + 100) + 'px');
window.__dkPenetration.dispose();
assert.strictEqual((document.handlers.mousedown || []).length, 0);
console.log('Reticle texts follow the crosshair, keep Flash runs and save dragged offsets: passed');
