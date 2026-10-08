const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const listeners = {}, views = {}, children = [];
const head = {
    appendChild(node) { children.push(node); node.parentNode = this; },
    removeChild(node) { children.splice(children.indexOf(node), 1); node.parentNode = null; }
};
const context = {
    console, JSON, Object, Array,
    document: {head, createElement(tag) { return {tag}; }},
    engine: {
        whenReady: {then(fn) { fn(); }},
        on(name, fn) { listeners[name] = fn; },
        off(name) { delete listeners[name]; }
    },
    subViews: {ids() { return Object.keys(views); }, get(id) { return views[id]; }},
    addEventListener() {}, removeEventListener() {}
};
context.window = context;
vm.createContext(context);
const source = fs.readFileSync(path.join(__dirname, '../../res/gui/gameface/mods/Driftkings/shared/bootstrap.js'), 'utf8');
vm.runInContext(source, context);
const prefix = 'coui://gui/gameface/mods/Driftkings/CarouselStats/';
views[10] = {model: {DriftkingsUI: {name: 'DriftkingsCarouselStats',
    styles: JSON.stringify([prefix + 'carousel.css']),
    scripts: JSON.stringify([prefix + 'carousel_native.js', prefix + 'carousel_layout.js', prefix + 'carousel.js'])}}};
listeners['subViews.onAdded']();
assert.strictEqual(children.length, 2);
assert.strictEqual(children[1].src, prefix + 'carousel_native.js');
listeners['subViews.onAdded']();
assert.strictEqual(children.length, 2, 'duplicate notifications must not reload scripts');
children[1].onload();
assert.strictEqual(children[2].src, prefix + 'carousel_layout.js');
children[2].onload();
assert.strictEqual(children[3].src, prefix + 'carousel.js');
let disposed = 0;
context.__dkCarouselStats = {dispose() { disposed++; }};
children[3].onload();
delete views[10];
listeners['subViews.onRemoved']();
assert.strictEqual(disposed, 1);
assert.strictEqual(children.length, 0);
views[11] = {model: {DriftkingsUI: {name: 'DriftkingsCarouselStats', styles: '[]',
    scripts: JSON.stringify(['https://unrelated/script.js', prefix + 'carousel.js'])}}};
listeners['subViews.onAdded']();
assert.strictEqual(children.length, 1);
assert.strictEqual(children[0].src, prefix + 'carousel.js');
context.__dkUIBridge.dispose();
assert.strictEqual(disposed, 2);
assert.deepStrictEqual(Object.keys(listeners), []);
assert.strictEqual(children.length, 0);
console.log('Owned UI: ordered loading, duplicate events, removal, recreation and cleanup: OK');

assert(source.indexOf("DriftkingsModSettingsButton: '__dkModSettingsButton'") >= 0, 'settings hangar component must be registered in the owned loader');
