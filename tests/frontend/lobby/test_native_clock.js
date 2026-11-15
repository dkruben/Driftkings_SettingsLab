/* Execute the actual native ES-module entry point and unchanged clock renderer. */
'use strict';
const assert = require('assert'), child = require('child_process'), path = require('path');
const driver = String.raw`
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const require = createRequire(process.cwd() + '/tests/run_frontend.js');
const {Node} = require('./support/frontend/dom_fixture');
const base = 'mod/res/gui/gameface/mods/driftkings/';
const entry = await import('data:text/javascript;base64,' + fs.readFileSync(base + 'main/clock_plugin.js').toString('base64'));
const renderer = fs.readFileSync(base + 'main/clock.js', 'utf8');
const body = new Node('body'), head = new Node('head');
globalThis.document = {body, head, createElement: tag => new Node(tag)};
globalThis.window = new Node('window');
window.innerWidth = 1920; window.innerHeight = 1080;
const events = new Node('engine');
globalThis.engine = {whenReady: {then: fn => fn()}, on: events.addEventListener.bind(events), off: events.removeEventListener.bind(events)};
const callbacks = new Set();
globalThis.viewEnv = {addDataChangedCallback: () => { callbacks.add(7); return 7; }, removeDataChangedCallback: id => callbacks.delete(id)};
const timers = new Map(); let timerId = 0;
globalThis.setInterval = fn => { timers.set(++timerId, fn); return timerId; };
globalThis.clearInterval = id => timers.delete(id);
const RealDate = Date; let time = new RealDate(2026, 10, 9, 10, 20, 30).getTime();
globalThis.Date = class extends RealDate { constructor(...args) { super(...(args.length ? args : [time])); } };
const config = {visible: true, hidePrestige: true, formats: [{format: '%H:%M:%S', x: 12, y: 20, width: 100, textFormat: {size: 18}}]};
const model = {DriftkingsUI: {name: 'DriftkingsHangarClock'}, payload: JSON.stringify({config})};
window.subViews = {ids: () => [42], get: () => ({model})};
let fail = false, scriptLoads = 0;
const append = head.appendChild.bind(head);
head.appendChild = node => {
    append(node);
    if (node.tagName === 'SCRIPT') {
        scriptLoads++;
        queueMicrotask(() => {
            if (fail) { node.onerror(); return; }
            vm.runInThisContext(renderer, {filename: 'clock.js'});
            node.onload();
        });
    }
    return node;
};
function changed() { model.payload = JSON.stringify({config}); events.fire('viewEnv.onDataChanged'); }
function clean() {
    assert.equal(head.children.length, 0); assert.equal(body.children.length, 0);
    assert.equal(timers.size, 0); assert.equal(callbacks.size, 0);
    Object.values(events.listeners).forEach(list => assert.equal(list.length, 0));
    Object.values(window.listeners).forEach(list => assert.equal(list.length, 0));
    assert.equal(window.__dkHangarClock, undefined);
}
let plugin = await entry.default.plugin({id: 'clock', url: 'clock_plugin.js'});
const pending = plugin.init(); assert.equal(plugin.init(), pending);
const component = await pending; assert.equal(component(), null); assert.equal(scriptLoads, 1);
assert(body.textContent.includes('10:20:30'));
assert.equal(timers.size, 1); assert.equal(callbacks.size, 1);
const policy = body.children.find(node => node.tagName === 'STYLE');
assert(policy.textContent.includes('Information_prestige_'));
const root = body.querySelector('.dk-clock-custom');
assert.equal(root.children[0].style.left, '12px'); assert.equal(root.children[0].style.top, '20px');
time += 1000; timers.forEach(fn => fn()); assert(root.textContent.includes('10:20:31'));
config.hidePrestige = false; changed(); assert.equal(policy.textContent, '');
config.visible = false; changed(); assert.equal(timers.size, 0);
assert.equal(body.querySelector('.dk-clock-custom').style.display, 'none');
config.visible = true; config.hidePrestige = true; changed();
assert.equal(timers.size, 1); assert(policy.textContent.includes('display:none'));
await plugin.destroy(); await plugin.destroy(); clean();
// Destroy during an in-flight classic script: no late owner/timer survives.
plugin = await entry.default.plugin({}); const loading = plugin.init(); const disposing = plugin.destroy();
await loading; await disposing; clean();
fail = true; plugin = await entry.default.plugin({});
await assert.rejects(plugin.init(), /Cannot load/); await plugin.destroy(); clean();
fail = false; plugin = await entry.default.plugin({}); await plugin.init();
assert.equal(body.children.filter(node => node.className === 'dk-clock-custom').length, 1);
await plugin.destroy(); clean();
window.__dkHangarClock = {dispose: () => { throw new Error('Must not destroy another owner'); }};
plugin = await entry.default.plugin({}); await assert.rejects(plugin.init(), /already exists/);
await plugin.destroy(); delete window.__dkHangarClock; clean();
`;
const result = child.spawnSync(process.execPath, ['--input-type=module', '-e', driver], {
    cwd: path.resolve(__dirname, '../../..'), encoding: 'utf8'
});
assert.strictEqual(result.status, 0, result.stdout + result.stderr);
console.log('Native clock ES module: real renderer, formats, prestige policy, timer, isolation and disposal passed');
