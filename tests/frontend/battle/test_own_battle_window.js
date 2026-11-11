'use strict';
// Own battle window: the TeamStrength layout document loads the catalog assets itself, once and in
// order, and the unchanged renderer finds its card through subViews without the OpenWG bootstrap.
var assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
var base = path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings');
var prefix = 'coui://gui/gameface/mods/driftkings/';
var html = fs.readFileSync(path.join(base, 'battle_statistics/model.html'), 'utf8');
function urls(pattern) { var result = [], match; while ((match = pattern.exec(html))) { result.push(match[1]); } return result; }
var scripts = urls(/<script src="([^"]+)"><\/script>/g), styles = urls(/<link rel="stylesheet" href="([^"]+)">/g);
// The same assets, in the same order, as the interface catalog entry.
var catalog = fs.readFileSync(path.join(base, '../../../../scripts/client/driftkings/interface_catalog.py'), 'utf8');
var entry = catalog.split("'DriftkingsTeamStrength': {")[1].split('},')[0];
function list(key) { return (new RegExp("'" + key + "': \\[([^\\]]*)\\]").exec(entry)[1].match(/coui:[^']+/g) || []); }
var spec = {scripts: list('scripts'), styles: list('styles')};
assert.ok(/'transport': 'own_window'/.test(entry), 'the catalog selects the own window for TeamStrength');
assert.strictEqual(spec.scripts.length, 4);
// The OpenWG bootstrap no longer loads this feature, so its scripts cannot be loaded twice; the other
// eight HUD cards and the rest of the OpenWG consumers are still listed.
var bootstrap = fs.readFileSync(path.join(base, 'shared/bootstrap.js'), 'utf8');
var features = JSON.parse(bootstrap.split('/* GENERATED CATALOG START */')[1].split('/* GENERATED CATALOG END */')[0]
    .replace(/^\s*var features = /, '').replace(/;\s*$/, ''));
assert.strictEqual(features.DriftkingsTeamStrength, undefined);
assert.strictEqual(Object.keys(features).length, 14);
['DriftkingsOwnHealth', 'DriftkingsAimingCountdown', 'DriftkingsFlightTime', 'DriftkingsPenetration', 'DriftkingsBattleEfficiency',
 'DriftkingsTargetInformation', 'DriftkingsMainGun', 'DriftkingsMarksOnGunBattle'].forEach(function (name) {
    assert.ok(features[name], name + ' stays an OpenWG consumer');
});
assert.deepStrictEqual(scripts, spec.scripts);
assert.deepStrictEqual(styles, [prefix + 'shared/fonts.css'].concat(spec.styles));
scripts.concat(styles).forEach(function (url) {
    assert.strictEqual(url.indexOf(prefix), 0, url);
    assert.ok(fs.existsSync(path.join(base, url.slice(prefix.length))), 'missing asset ' + url);
});
assert.ok(!/bootstrap\.js|openwg|ModInject/i.test(html.replace(/<!--[\s\S]*?-->/g, '')), 'no OpenWG entry point in the document');
assert.ok(/pointer-events:\s*none/.test(html) && /background:\s*transparent/.test(html), 'the empty document must not cover or capture the battle');

function target() {
    return {handlers: {}, addEventListener: function (name, fn) {
        (this.handlers[name] || (this.handlers[name] = [])).push(fn);
    }, removeEventListener: function (name, fn) {
        this.handlers[name] = (this.handlers[name] || []).filter(function (item) { return item !== fn; });
    }, fire: function (name, event) {
        (this.handlers[name] || []).slice().forEach(function (fn) { fn(event); });
    }, count: function () {
        var self = this; return Object.keys(self.handlers).reduce(function (total, name) { return total + self.handlers[name].length; }, 0);
    }};
}
function element(tag) {
    var node = target(), attributes = {};
    node.tagName = tag; node.nodeType = 1; node.style = {}; node.children = []; node.childNodes = node.children;
    node.appendChild = function (child) {
        if (child.parentNode) { child.parentNode.removeChild(child); }
        child.parentNode = node; node.children.push(child);
    };
    node.removeChild = function (child) { node.children.splice(node.children.indexOf(child), 1); child.parentNode = null; };
    node.getAttribute = function (name) { return attributes[name]; };
    node.setAttribute = function (name, value) { attributes[name] = value; };
    Object.defineProperty(node, 'firstChild', {get: function () { return node.children[0]; }});
    Object.defineProperty(node, 'innerHTML', {set: function (text) {
        node.children.length = 0;
        var child = element('#text'); child.nodeType = 3; child.nodeValue = text; node.appendChild(child);
    }});
    node.getBoundingClientRect = function () {
        return {left: parseFloat(node.style.left) || 0, top: parseFloat(node.style.top) || 0, width: 120, height: 40};
    };
    return node;
}
function documentContext(models) {
    var document = target(), window = target(), engine = target(), queue = [], callbacks = [];
    document.body = element('body'); document.documentElement = element('html'); document.createElement = element;
    window.innerWidth = 1920; window.innerHeight = 1080;
    window.getComputedStyle = function () { return {fontSize: '2px'}; };
    window.subViews = {ids: function () { return Object.keys(models).map(Number); }, get: function (id) { return {model: models[id]}; }};
    engine.whenReady = {then: function (fn) { fn(); }}; engine.on = engine.addEventListener; engine.off = engine.removeEventListener;
    var context = vm.createContext({window: window, document: document, engine: engine, Date: Date,
        viewEnv: {addDataChangedCallback: function (name, id) { callbacks.push(id); return callbacks.length; },
                  removeDataChangedCallback: function (id) { callbacks[id - 1] = null; }},
        setTimeout: function (fn) { queue.push(fn); return queue.length; }, clearTimeout: function () { queue = []; },
        requestAnimationFrame: function (fn) { queue.push(fn); return queue.length; }});
    return {document: document, window: window, engine: engine, callbacks: callbacks,
        flush: function () { while (queue.length) { queue.shift()(); } },
        // Classic scripts of the document, executed in document order.
        loadDocument: function () {
            scripts.forEach(function (url) { vm.runInContext(fs.readFileSync(path.join(base, url.slice(prefix.length)), 'utf8'), context); });
            this.flush();
        }};
}

var saved = [];
var model = {payload: '{}', DriftkingsUI: {name: 'DriftkingsTeamStrength'}, onSavePosition: function (value) { saved.push(value); }};
var page = documentContext({42: model});
page.loadDocument();
var owner = page.window.__dkTeamStrength;
assert.ok(owner && typeof owner.dispose === 'function', 'the renderer creates its usual owner');
assert.strictEqual(page.window.__dkUIBridge, undefined, 'the OpenWG bootstrap bridge is not involved');
assert.strictEqual(page.document.body.children.length, 1, 'one renderer root');
var root = page.document.body.firstChild;
assert.strictEqual(root.className, 'dk-screen-text dk-screen-text--strength');
assert.deepStrictEqual(page.callbacks, [42], 'subscribed once to the card found through subViews');

// The payload published by Python is unchanged: same text, style, position and shadow handling.
var data = {text: 'Allies 12000 : 9000 Enemies', style: {font: '$FieldFont', size: 16, color: '#DBD7D2', bold: false, italic: true, align: 'left'},
    config: {visible: true, draggable: false, locked: false, x: -58, y: 2, alignX: 'right', alignY: 'top', alpha: 1,
             shadow: {alpha: 0.8, angle: 90, blurX: 2, blurY: 2, color: '#000000', distance: 0, enabled: true, strength: 100}}};
function update() { model.payload = JSON.stringify(data); page.engine.fire('viewEnv.onDataChanged'); page.flush(); }
update();
assert.strictEqual(root.style.display, 'block');
assert.strictEqual(root.style.left, (1920 - 120 - 116) + 'px');
assert.strictEqual(root.style.top, '4px');
assert.strictEqual(root.style.fontStyle, 'italic'); assert.strictEqual(root.style.color, '#DBD7D2');
assert.strictEqual(root.style.pointerEvents, 'none', 'a text that cannot be dragged never captures the mouse');
data.config.visible = false; update();
assert.strictEqual(root.style.display, 'none');
// onSavePosition: an unlocked text is dragged with the battle cursor and reports its new position.
data.config.visible = true; data.config.draggable = true; update();
assert.strictEqual(root.style.pointerEvents, 'auto');
var grip = root.children[0].children[0].children[0] || root.children[0].children[0];
var event = {target: grip, button: 0, clientX: 1700, clientY: 20, preventDefault: function () {}, stopPropagation: function () {}};
page.document.fire('mousedown', event);
event.clientX = 1000; event.clientY = 1000; page.document.fire('mousemove', event);
page.document.fire('mouseup', event);
assert.strictEqual(saved.length, 1);
assert.deepStrictEqual(Object.keys(JSON.parse(JSON.stringify(saved[0]))).sort(), ['alignX', 'alignY', 'x', 'y']);

// Teardown is idempotent and releases the root, the subscription and every listener.
owner.dispose(); owner.dispose();
assert.strictEqual(page.document.body.children.length, 0);
assert.deepStrictEqual(page.callbacks, [null]);
assert.strictEqual(page.engine.count(), 0);
assert.strictEqual(page.document.count(), 0);

// A document without the card (or with another feature's card) stays empty and inert.
var foreign = documentContext({7: {payload: JSON.stringify(data), DriftkingsUI: {name: 'DriftkingsBattleEfficiency'}}});
foreign.loadDocument();
assert.deepStrictEqual(foreign.callbacks, []);
assert.ok(foreign.document.body.children.every(function (node) { return node.style.display !== 'block'; }));
foreign.window.__dkTeamStrength.dispose();

// Loading the document twice in one page (defensive) keeps a single renderer root.
var twice = documentContext({42: {payload: JSON.stringify(data), DriftkingsUI: {name: 'DriftkingsTeamStrength'}}});
twice.loadDocument(); twice.loadDocument();
assert.strictEqual(twice.document.body.children.length, 1, 'no duplicated renderer');
twice.window.__dkTeamStrength.dispose();
console.log('Own battle window document: catalog assets in order, unchanged TeamStrength renderer, drag, teardown and isolation passed');
