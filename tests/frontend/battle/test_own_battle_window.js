'use strict';
// Shared own battle window: the host layout document loads the catalog assets of every own_window
// feature itself, once and in order, and each unchanged renderer finds its own card through subViews
// without the OpenWG bootstrap. All nine HUD cards live in the same document, independently.
var assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
var base = path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings');
var prefix = 'coui://gui/gameface/mods/driftkings/';
var html = fs.readFileSync(path.join(base, 'battle_statistics/model.html'), 'utf8');
function urls(pattern) { var result = [], match; while ((match = pattern.exec(html))) { result.push(match[1]); } return result; }
var scripts = urls(/<script src="([^"]+)"><\/script>/g), styles = urls(/<link rel="stylesheet" href="([^"]+)">/g);
// The same assets as the interface catalog entries: the host feature first, then the others, no repeats.
var catalog = fs.readFileSync(path.join(base, '../../../../scripts/client/driftkings/interface_catalog.py'), 'utf8');
function feature(name) {
    var entry = catalog.split("'" + name + "': {")[1].split('},')[0];
    function list(key) { return (new RegExp("'" + key + "': \\[([^\\]]*)\\]").exec(entry)[1].match(/coui:[^']+/g) || []); }
    assert.ok(/'transport': 'own_window'/.test(entry), 'the catalog selects the own window for ' + name);
    return {scripts: list('scripts'), styles: list('styles'), owner: /'owner': '([^']+)'/.exec(entry)[1]};
}
var strengthSpec = feature('DriftkingsTeamStrength'), healthSpec = feature('DriftkingsOwnHealth');
function union(a, b) { return a.concat(b.filter(function (url) { return a.indexOf(url) < 0; })); }
var names = ['DriftkingsTeamStrength', 'DriftkingsOwnHealth', 'DriftkingsAimingCountdown', 'DriftkingsFlightTime',
    'DriftkingsPenetration', 'DriftkingsBattleEfficiency', 'DriftkingsTargetInformation', 'DriftkingsMainGun', 'DriftkingsMarksOnGunBattle'];
var spec = {scripts: [], styles: []};
names.forEach(function (name) {
    var card = feature(name);
    spec.scripts = union(spec.scripts, card.scripts); spec.styles = union(spec.styles, card.styles);
});
assert.strictEqual(strengthSpec.scripts.length, 4);
assert.strictEqual(spec.scripts.length, 15, 'the shared kits load once for all nine cards');
assert.deepStrictEqual(scripts.slice(0, 6), union(strengthSpec.scripts, healthSpec.scripts), 'beta.7 asset order preserved');
var bootstrap = fs.readFileSync(path.join(base, 'shared/bootstrap.js'), 'utf8');
var features = JSON.parse(bootstrap.split('/* GENERATED CATALOG START */')[1].split('/* GENERATED CATALOG END */')[0]
    .replace(/^\s*var features = /, '').replace(/;\s*$/, ''));
assert.strictEqual(Object.keys(features).length, 6);
names.forEach(function (name) { assert.strictEqual(features[name], undefined, name + ' has no OpenWG entry'); });
function disposeAll(page) {
    names.forEach(function (name) { var owner = page.window[feature(name).owner]; if (owner) { owner.dispose(); } });
}
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
    node.removeAttribute = function (name) { delete attributes[name]; };
    node.querySelector = function (selector) {
        var name = selector.replace(/^\./, '');
        for (var i = 0; i < node.children.length; i++) {
            var child = node.children[i];
            if (String(child.className || '').split(' ').indexOf(name) >= 0) { return child; }
            var found = child.querySelector ? child.querySelector(selector) : null;
            if (found) { return found; }
        }
        return null;
    };
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

var saved = [], savedHealth = [];
var model = {payload: '{}', DriftkingsUI: {name: 'DriftkingsTeamStrength'}, onSavePosition: function (value) { saved.push(value); }};
var healthModel = {payload: '{}', DriftkingsUI: {name: 'DriftkingsOwnHealth'}, onSavePosition: function (value) { savedHealth.push(value); }};
var page = documentContext({42: model, 43: healthModel});
page.loadDocument();
var owner = page.window.__dkTeamStrength, healthOwner = page.window.__dkOwnHealth;
assert.ok(owner && typeof owner.dispose === 'function', 'the renderer creates its usual owner');
assert.ok(healthOwner && typeof healthOwner.dispose === 'function' && healthOwner !== owner, 'OwnHealth has its own owner');
assert.strictEqual(page.window.__dkUIBridge, undefined, 'the OpenWG bootstrap bridge is not involved');
assert.strictEqual(page.document.body.children.length, 9, 'one renderer root per feature');
var root = page.document.body.children[0], healthRoot = page.document.body.children[1];
assert.strictEqual(root.className, 'dk-screen-text dk-screen-text--strength');
assert.strictEqual(healthRoot.className, 'dk-health');
assert.deepStrictEqual(page.callbacks.slice().sort(), [42, 43], 'each renderer subscribed once to its own card');

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

// OwnHealth renders from its own payload; neither feature's data touches the other's nodes.
var strengthLeft = root.style.left, strengthDisplay = root.style.display;
var health = {percent: 0.75, text: '1800 / 2400', style: 0, color: '#12AB34',
    config: {visible: true, draggable: false, locked: false, x: 0, y: 300, alignX: 'center', alignY: 'top'}};
function updateHealth() { healthModel.payload = JSON.stringify(health); page.engine.fire('viewEnv.onDataChanged'); page.flush(); }
updateHealth();
assert.strictEqual(healthRoot.style.display, 'block');
assert.strictEqual(healthRoot.querySelector('.dk-health__fill').style.width, '75%');
assert.strictEqual(healthRoot.querySelector('.dk-health__text').textContent, '1800 / 2400');
assert.strictEqual(healthRoot.style.pointerEvents, 'none');
assert.strictEqual(root.style.left, strengthLeft); assert.strictEqual(root.style.display, strengthDisplay);
health.config.visible = false; updateHealth();
assert.strictEqual(healthRoot.style.display, 'none');
assert.strictEqual(root.style.display, 'block', 'hiding the health bar leaves the team strength text visible');
data.config.visible = false; health.config.visible = true; update(); updateHealth();
assert.strictEqual(root.style.display, 'none'); assert.strictEqual(healthRoot.style.display, 'block');
// Dragging the health bar reports through its own model only.
health.config.draggable = true; updateHealth();
assert.strictEqual(healthRoot.style.pointerEvents, 'auto');
var hold = {target: healthRoot.children[0], button: 0, clientX: 900, clientY: 610, preventDefault: function () {}, stopPropagation: function () {}};
page.document.fire('mousedown', hold);
hold.clientX = 1000; hold.clientY = 700; page.document.fire('mousemove', hold);
page.document.fire('mouseup', hold);
assert.strictEqual(savedHealth.length, 1);
assert.strictEqual(saved.length, 1, 'the team strength position was not saved again');

// Teardown is per feature and idempotent: one owner leaves the other untouched.
owner.dispose(); owner.dispose();
assert.strictEqual(page.document.body.children.length, 8);
assert.strictEqual(page.document.body.children[0], healthRoot);
health.percent = 0.5; updateHealth();
assert.strictEqual(healthRoot.querySelector('.dk-health__fill').style.width, '50%');
healthOwner.dispose(); healthOwner.dispose();
disposeAll(page);
assert.strictEqual(page.document.body.children.length, 0);
assert.deepStrictEqual(page.callbacks, [null, null]);
assert.strictEqual(page.engine.count(), 0);
assert.strictEqual(page.document.count(), 0);

// A document without the card (or with another feature's card) stays empty and inert.
var foreign = documentContext({7: {payload: JSON.stringify(data), DriftkingsUI: {name: 'DriftkingsRatingPlayers'}}});
foreign.loadDocument();
assert.deepStrictEqual(foreign.callbacks, []);
assert.ok(foreign.document.body.children.every(function (node) { return node.style.display !== 'block'; }));
disposeAll(foreign);

// Only OwnHealth present (TeamStrength component not installed): the host document still serves it.
var alone = documentContext({43: {payload: JSON.stringify(health), DriftkingsUI: {name: 'DriftkingsOwnHealth'}}});
alone.loadDocument();
assert.deepStrictEqual(alone.callbacks, [43]);
assert.strictEqual(alone.document.body.children.filter(function (node) { return node.style.display === 'block'; }).length, 1);
disposeAll(alone);

// Loading the document twice in one page (defensive) keeps a single renderer root.
var twice = documentContext({42: {payload: JSON.stringify(data), DriftkingsUI: {name: 'DriftkingsTeamStrength'}}});
twice.loadDocument(); twice.loadDocument();
assert.strictEqual(twice.document.body.children.filter(function (node) { return node.className === 'dk-screen-text dk-screen-text--strength'; }).length, 1, 'no duplicated renderer');
disposeAll(twice);
// All nine real renderers together: models, positions and saves stay isolated.
var models = {}, saves = {}, payloads = {}, roots = {};
names.forEach(function (name, index) {
    saves[name] = [];
    payloads[name] = {text: name, percent: 0.5, state: 'unavailable', progress: 25,
        primaryText: '3000 HP', secondaryText: 'remaining', progressText: '25%', progressLabel: 'Progress',
        style: {font: '$FieldFont', size: 16, color: '#DBD7D2', align: 'left'},
        config: {visible: true, draggable: true, locked: false, scale: 1,
            x: 20 + index * 10, y: 20 + index * 10, anchorX: 0.5, anchorY: 0.5}};
    models[100 + index] = {payload: JSON.stringify(payloads[name]), DriftkingsUI: {name: name},
        onSavePosition: function (value) { saves[name].push(value); }};
});
var together = documentContext(models);
together.loadDocument();
assert.strictEqual(together.document.body.children.length, 9);
assert.strictEqual(together.callbacks.filter(Boolean).length, 9);
names.forEach(function (name, index) {
    roots[name] = together.document.body.children[index];
    assert.strictEqual(roots[name].style.display, 'block', name + ' renders beside the other cards');
});
names.forEach(function (name, index) {
    var node = roots[name], before = names.map(function (other) { return roots[other].style.left; });
    var event = {target: node.firstChild, button: 0, clientX: 200, clientY: 200,
        preventDefault: function () {}, stopPropagation: function () {}};
    together.document.fire('mousedown', event);
    event.clientX = 300; event.clientY = 300;
    together.document.fire('mousemove', event); together.document.fire('mouseup', event);
    assert.strictEqual(saves[name].length, 1, name + ' saves through its own model');
    names.forEach(function (other, otherIndex) {
        if (other !== name) {
            assert.strictEqual(roots[other].style.left, before[otherIndex], other + ' position stays independent');
            assert.strictEqual(saves[other].length, otherIndex < index ? 1 : 0);
        }
    });
    payloads[name].config.visible = false;
    models[100 + index].payload = JSON.stringify(payloads[name]);
    together.engine.fire('viewEnv.onDataChanged'); together.flush();
    assert.strictEqual(node.style.display, 'none');
});
// Reloading the document retains exactly one root and subscription per card.
together.loadDocument();
assert.strictEqual(together.document.body.children.length, 9);
assert.strictEqual(together.callbacks.filter(Boolean).length, 9);
disposeAll(together);
assert.strictEqual(together.document.body.children.length, 0);
assert.strictEqual(together.callbacks.filter(Boolean).length, 0);
assert.strictEqual(together.document.count(), 0);
assert.strictEqual(together.window.count(), 0);
assert.strictEqual(together.engine.count(), 0);
console.log('Shared own battle window: nine independent renderers, payloads, drag, visibility, deduplication and teardown passed');
