'use strict';
var assert = require('assert'), fs = require('fs'), vm = require('vm'), path = require('path');
var Node = require('../../support/frontend/dom_fixture').Node;
function boot(launcher, editing, delayed) {
    var events = {}, listeners = {}, jobs = [], sent = [], resized = [], removed = 0;
    var document = {activeElement: null};
    function element(tag) {
        var node = new Node(tag || 'div'); node.ownerDocument = document; return node;
    }
    var root = element(), body = element();
    var data = {launcher: launcher, labels: {title: 'Accounts'}, accounts: [], servers: [], canLogin: true, editing: editing};
    var model = {payload: delayed ? '{}' : JSON.stringify(data),
        onAction: function (data) { sent.push(JSON.parse(data.data)); }};
    document.body = body; document.getElementById = function () { return root; }; document.createElement = element;
    var window = {model: model, addEventListener: function (name, fn, capture) { listeners[name] = {fn: fn, capture: capture}; },
        removeEventListener: function (name) { delete listeners[name]; }};
    var context = {window: window, document: document,
        engine: {whenReady: {then: function (fn) { fn(); }}, on: function (name, fn) { events[name] = fn; },
            off: function (name) { delete events[name]; }},
        viewEnv: {getClientSizeRem: function () { return {width: 1920, height: 1080}; },
            addDataChangedCallback: function () { return 1; }, removeDataChangedCallback: function () { removed++; },
            resizeViewPx: function (w, h) { resized.push([w, h]); }, setEventHandled: function () {}, handleViewEvent: function () {}},
        requestAnimationFrame: function (fn) { jobs.push(fn); return jobs.length; }, cancelAnimationFrame: function (id) { jobs[id - 1] = null; }};
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings/account_manager/accounts.js'), 'utf8'), context);
    function flush() { var count = 0; while (jobs.length) { if (++count > 100) { throw new Error('Unbounded animation frames'); } var fn = jobs.shift(); if (fn) { fn(); } } }
    flush();
    return {root: root, body: body, resized: resized, sent: sent, events: events, listeners: listeners,
        focused: function () { return document.activeElement; }, flush: flush, removed: function () { return removed; },
        update: function (change) { Object.assign(data, change); model.payload = JSON.stringify(data); events['viewEnv.onDataChanged'](null, null, [1]); flush(); }};
}
var modal = boot(false);
assert.strictEqual(modal.body.className, 'modal');
assert.strictEqual(modal.focused(), modal.root);
modal.events.clientResized(); modal.events['self.onLoaded'](); modal.flush();
assert.strictEqual(modal.resized.length, 0, 'Modal must retain the native fullscreen viewport after load/resize');
assert.strictEqual(modal.listeners.keydown.capture, true);
modal.listeners.keydown.fn({keyCode: 27, preventDefault: function () {}, stopPropagation: function () {}});
assert.strictEqual(modal.sent.pop().action, 'close');
modal.listeners.unload.fn();
assert.strictEqual(modal.listeners.keydown, undefined);
var launcher = boot(true);
assert.strictEqual(launcher.body.className, '');
assert.strictEqual(launcher.resized.length, 1, 'Launcher must remain a small native view');
assert.strictEqual(launcher.sent.pop().action, 'layout');
console.log('Account manager modal sizing and Escape: passed');

function descendants(node) {
    return node.children.reduce(function (all, child) { return all.concat([child], descendants(child)); }, []);
}
function editControls(editing) {
    var view = boot(false, editing), nodes = descendants(view.root);
    view.inputs = nodes.filter(function (node) { return node.tagName === 'INPUT'; });
    view.toggle = nodes.filter(function (node) { return node.attributes.role === 'checkbox'; })[0];
    return view;
}
var saved = {id: 'example', title: 'Example', email: 'test@example.com', cluster: 0};
function inputsOf(view) {
    return descendants(view.root).filter(function (node) { return node.tagName === 'INPUT'; });
}
var editor = editControls(saved), fields = inputsOf(editor);
assert.strictEqual(fields.length, 2, 'Profile editor holds only title and e-mail');
assert.ok(fields.every(function (input) { return input.type !== 'password'; }), 'No password input in the profile editor');
assert.strictEqual(editor.toggle, undefined, 'No show-password control in the profile editor');
editor.listeners.keydown.fn({keyCode: 13, preventDefault: function () {}, stopPropagation: function () {}});
var submitted = editor.sent.pop();
assert.strictEqual(submitted.action, 'save');
assert.ok(!('password' in submitted), 'A save never carries a password field');
assert.deepStrictEqual(Object.keys(submitted).sort(), ['action', 'cluster', 'email', 'id', 'title']);
assert.strictEqual(editor.sent.length, 0, 'Saving must not request any stored secret');
console.log('Account profile editor has no password field and sends no secret: passed');

var changing = boot(false, null, true);
assert.strictEqual(changing.root.children.length, 0);
changing.update({editing: saved});
assert.strictEqual(inputsOf(changing).length, 2);
changing.update({editing: Object.assign({}, saved, {title: 'Changed'})});
assert.strictEqual(changing.root.children.length, 1);
assert.strictEqual(inputsOf(changing).length, 2);
changing.listeners.keydown.fn({keyCode: 27, preventDefault: function () {}, stopPropagation: function () {}});
assert.strictEqual(changing.sent.pop().action, 'cancel');
changing.update({editing: null});
assert.strictEqual(inputsOf(changing).length, 0);
changing.listeners.unload.fn();
assert.strictEqual(changing.removed(), 1);
assert.strictEqual(changing.root.children.length, 0);
assert.strictEqual(Object.keys(changing.events).length, 0);
console.log('Account profile delayed model, cancellation and disposal: passed');
