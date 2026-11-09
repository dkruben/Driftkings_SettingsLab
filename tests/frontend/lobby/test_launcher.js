'use strict';
var assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
function target() {
    return {events: {}, addEventListener: function (name, fn) {
        (this.events[name] || (this.events[name] = [])).push(fn);
    }, removeEventListener: function (name, fn) {
        this.events[name] = (this.events[name] || []).filter(function (item) { return item !== fn; });
    }, fire: function (name) { (this.events[name] || []).slice().forEach(function (fn) { fn(); }); }};
}
function element() {
    var node = target(); node.children = [];
    node.setAttribute = function (name, value) { node[name] = value; };
    node.appendChild = function (child) { node.children.push(child); child.parentNode = node; };
    node.removeChild = function (child) { node.children.splice(node.children.indexOf(child), 1); child.parentNode = null; };
    node.insertBefore = function (child, before) {
        if (child.parentNode) { child.parentNode.removeChild(child); }
        node.children.splice(node.children.indexOf(before), 0, child); child.parentNode = node;
    };
    return node;
}
var document = {body: element(), createElement: element}, window = target(), engine = target();
var section, menu, observer, queue = [], calls = 0, callbacks = 0, present = true;
var model = {DriftkingsUI: {name: 'DriftkingsFooterLauncher'},
    payload: JSON.stringify({visible: true, title: 'Configurações Driftkings'}), onOpen: function () { calls++; }};
window.subViews = {ids: function () { return present ? [42] : []; }, get: function () { return {model: model}; }};
function footer() {
    section = element(); section.className = 'Footer_section_9d3d3a12'; menu = element();
    section.appendChild(menu); document.body.appendChild(section);
}
footer(); document.querySelector = function () { return menu; };
window.MutationObserver = function (fn) { observer = this; this.fn = fn; this.connected = false;
    this.observe = function () { this.connected = true; }; this.disconnect = function () { this.connected = false; }; };
engine.whenReady = {then: function (fn) { fn(); }}; engine.on = engine.addEventListener; engine.off = engine.removeEventListener;
var context = vm.createContext({window: window, document: document, engine: engine, console: console,
    viewEnv: {addDataChangedCallback: function () { callbacks++; return 7; }, removeDataChangedCallback: function () { callbacks--; }},
    setTimeout: function (fn) { queue.push(fn); return queue.length; }, clearTimeout: function () { queue = []; }});
var base = path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings/launcher');
function load() { vm.runInContext(fs.readFileSync(path.join(base, 'launcher.js'), 'utf8'), context); }
function flush() { while (queue.length) { queue.shift()(); } }
load(); flush();
var button = section.children[0];
assert.strictEqual(button.className, 'driftkings-launcher'); assert.strictEqual(button.parentNode, section);
assert.strictEqual(button.title, 'Configurações Driftkings'); button.fire('click'); assert.strictEqual(calls, 1);
observer.fn(); observer.fn(); flush(); assert.strictEqual(section.children.length, 2);
engine.fire('self.onScaleUpdated'); assert.strictEqual(section.children[0], button);
footer(); observer.fn(); flush(); assert.strictEqual(button.parentNode, section);
model.payload = JSON.stringify({visible: false}); engine.fire('viewEnv.onDataChanged'); flush();
assert.strictEqual(section.children.length, 1); button.fire('click'); assert.strictEqual(calls, 1);
model.payload = JSON.stringify({visible: true}); engine.fire('viewEnv.onDataChanged'); flush();
load(); flush(); assert.strictEqual(callbacks, 1); assert.strictEqual(section.children.length, 2);
present = false; engine.fire('subViews.onRemoved'); flush(); assert.strictEqual(callbacks, 0);
assert.strictEqual(section.children.length, 1);
present = true; engine.fire('subViews.onAdded'); flush(); assert.strictEqual(section.children.length, 2);
menu = null; observer.fn(); flush(); assert.strictEqual(section.children.length, 1);
window.__dkFooterLauncher.dispose(); assert.strictEqual(callbacks, 0); assert.strictEqual(observer.connected, false);
Object.keys(engine.events).forEach(function (name) { assert.strictEqual(engine.events[name].length, 0); });
assert.strictEqual(queue.length, 0);
var css = fs.readFileSync(path.join(base, 'launcher.css'), 'utf8');
css.split('}').filter(function (part) { return part.trim(); }).forEach(function (part) {
    assert(/^\s*\.driftkings-launcher/.test(part));
});
assert(css.indexOf(':hover') >= 0 && css.indexOf(':active') >= 0 && css.indexOf('rem') >= 0);
console.log('Footer launcher: ownership, click, anchor replacement, model changes, recreation and cleanup passed');
