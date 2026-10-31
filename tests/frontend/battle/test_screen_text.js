'use strict';
// Texts at a fixed place on the screen: settings position and style, Flash runs, dragged with Ctrl.
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
var model = {payload: '{}', DriftkingsUI: {name: 'DriftkingsBattleEfficiency'}, onSavePosition: function (value) { saved.push(value); }};
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
load('shared/marks_panel.js'); load('shared/flash_lines.js'); load('shared/screen_text.js'); load('battle_performance_hud/battle_performance_hud.js'); flush();
var root = document.body.firstChild, content = root.children[0];
assert.strictEqual(root.className, 'dk-screen-text dk-screen-text--efficiency');
var shadow = {alpha: 0.8, angle: 90, blurX: 2, blurY: 2, color: '#000000', distance: 0, enabled: true, strength: 100};
var data = {text: "WN8: <font color='#FF0000'>1500</font><br><font face='$FieldFont' alpha='#80'>EFF: <font face='Arial'>900</font></font>",
    style: {font: '$TitleFont', size: 16, color: '#FFFFFF', align: 'center'},
    config: {visible: true, draggable: false, locked: false, x: 125, y: 36, alpha: 1, shadow: shadow}};
function update() { model.payload = JSON.stringify(data); engine.fire('viewEnv.onDataChanged'); flush(); }
update();
assert.strictEqual(root.style.display, 'block');
// Without an anchor the position is a top-left offset in interface units (2px each here), as in Flash.
assert.strictEqual(root.style.left, '250px');
assert.strictEqual(root.style.top, '72px');
// Base style from textStyle: $TitleFont is the client font in bold.
assert.strictEqual(root.style.fontFamily, 'Warhelios'); assert.strictEqual(root.style.fontWeight, '700');
assert.strictEqual(root.style.fontSize, '16rem'); assert.strictEqual(root.style.color, '#FFFFFF');
assert.strictEqual(content.style.alignItems, 'center');
assert.strictEqual(root.style.textShadow, '0.00rem 0.00rem 2rem rgba(0,0,0,0.8)');
// One row per line; inline runs keep colour, face and alpha, unknown faces are ignored.
assert.strictEqual(content.children.length, 2);
var first = content.children[0].children, second = content.children[1].children;
assert.strictEqual(first[1].textContent, '1500'); assert.strictEqual(first[1].style.color, '#FF0000');
assert.strictEqual(second[0].style.fontWeight, '400'); assert.strictEqual(second[0].style.opacity, String(128 / 255));
assert.strictEqual(second[1].textContent, '900'); assert.strictEqual(second[1].style.fontFamily, 'Warhelios');
assert.strictEqual(root.style.pointerEvents, 'none');
// The team strength shape: anchored to the right edge, bold/italic base, faint Flash strength fades the shadow.
data.style = {font: '$FieldFont', size: 14, color: '#DBD7D2', bold: true, italic: true};
data.config.alignX = 'right'; data.config.x = -58; data.config.y = 2; data.config.alpha = 0.5;
data.config.shadow = {alpha: 100, angle: 0, distance: 1, blurX: 1, blurY: 3, color: '#102030', strength: 2};
update();
assert.strictEqual(root.style.left, (1920 - 120 - 116) + 'px');
assert.strictEqual(root.style.fontWeight, '700'); assert.strictEqual(root.style.fontStyle, 'italic');
assert.strictEqual(root.style.opacity, '0.5');
assert.strictEqual(root.style.textShadow, '1.00rem 0.00rem 3rem rgba(16,32,48,0.02)');
data.config.shadow.enabled = false; update();
assert.strictEqual(root.style.textShadow, 'none');
// Ctrl: an unlocked text can be dragged; the position is saved anchored to the nearest edge.
data.config.draggable = true; update();
assert.strictEqual(root.style.pointerEvents, 'auto');
var event = {target: first[0], button: 0, clientX: 1700, clientY: 20, preventDefault: function () {}, stopPropagation: function () {}};
document.fire('mousedown', event);
event.clientX = 1000; event.clientY = 1000; document.fire('mousemove', event);
document.fire('mouseup', event);
assert.strictEqual(saved.length, 1);
assert.deepStrictEqual(JSON.parse(JSON.stringify(saved[0])), {x: 42, y: -28, alignX: 'center', alignY: 'bottom'});
// A locked text cannot be dragged even with the cursor.
data.config.locked = true; update();
assert.strictEqual(root.style.pointerEvents, 'none');
window.__dkBattleEfficiencyHud.dispose();
console.log('Screen texts keep the Flash position, style and shadow and save dragged positions: passed');
