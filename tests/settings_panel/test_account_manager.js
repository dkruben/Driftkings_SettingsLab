'use strict';
var assert = require('assert'), fs = require('fs'), vm = require('vm'), path = require('path');
function boot(launcher, editing) {
    var events = {}, listeners = {}, jobs = [], sent = [], resized = [], focused = null;
    function element(tag) {
        return {tag: tag, attributes: {}, style: {}, children: [], appendChild: function (child) { this.children.push(child); },
            setAttribute: function (name, value) { this.attributes[name] = value; }, focus: function () { focused = this; }};
    }
    var root = element(), body = element();
    var model = {payload: JSON.stringify({launcher: launcher, labels: {title: 'Accounts'},
        accounts: [], servers: [], canLogin: true, editing: editing}), onAction: function (data) { sent.push(JSON.parse(data.data)); }};
    var window = {model: model, addEventListener: function (name, fn, capture) { listeners[name] = {fn: fn, capture: capture}; },
        removeEventListener: function (name) { delete listeners[name]; }};
    var context = {window: window, document: {body: body, getElementById: function () { return root; }, createElement: element},
        engine: {whenReady: {then: function (fn) { fn(); }}, on: function (name, fn) { events[name] = fn; },
            off: function (name) { delete events[name]; }},
        viewEnv: {getClientSizeRem: function () { return {width: 1920, height: 1080}; },
            addDataChangedCallback: function () { return 1; }, removeDataChangedCallback: function () {},
            resizeViewPx: function (w, h) { resized.push([w, h]); }, setEventHandled: function () {}, handleViewEvent: function () {}},
        requestAnimationFrame: function (fn) { jobs.push(fn); return jobs.length; }, cancelAnimationFrame: function () {}};
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../mod/res/gui/gameface/mods/driftkings/account_manager/accounts.js'), 'utf8'), context);
    function flush() { while (jobs.length) { jobs.shift()(); } }
    flush();
    return {root: root, body: body, resized: resized, sent: sent, events: events, listeners: listeners,
        focused: function () { return focused; }, flush: flush};
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
    view.inputs = nodes.filter(function (node) { return node.tag === 'input'; });
    view.toggle = nodes.filter(function (node) { return node.attributes.role === 'checkbox'; })[0];
    return view;
}
var saved = {id: 'example', title: 'Example', email: 'test@example.com', cluster: 0};
var editor = editControls(saved), password = editor.inputs[2];
assert.strictEqual(password.placeholder, '********');
assert.strictEqual(password.value, '', 'Mask must never be submitted as a replacement password');
editor.toggle.onclick();
assert.strictEqual(editor.sent.pop().action, 'revealPassword');
editor.listeners.keydown.fn({keyCode: 13, preventDefault: function () {}, stopPropagation: function () {}});
assert.strictEqual(editor.sent.pop().password, '', 'Saving untouched masked field preserves stored password');
var visible = editControls(Object.assign({}, saved, {password: 'fictional-password'}));
assert.strictEqual(visible.inputs[2].value, 'fictional-password');
assert.strictEqual(visible.inputs[2].type, 'text');
assert.strictEqual(visible.toggle.children[0].className, 'check-box checked');
assert.strictEqual(visible.toggle.attributes['aria-checked'], 'true');
visible.toggle.onclick();
assert.strictEqual(visible.inputs[2].type, 'password');
assert.strictEqual(visible.toggle.children[0].className, 'check-box');
assert.strictEqual(visible.toggle.attributes['aria-checked'], 'false');
assert.strictEqual(visible.sent.length, 0);
var replacement = editControls(saved);
replacement.inputs[2].value = 'replacement'; replacement.toggle.onclick();
assert.strictEqual(replacement.inputs[2].type, 'text');
assert.strictEqual(replacement.sent.length, 0, 'Typed replacement must not trigger retrieval of stored password');
console.log('Account manager saved password mask and explicit reveal: passed');
