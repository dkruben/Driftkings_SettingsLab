/* Runs the real OpenWG 1.1.6 bootstrap alongside the owned Driftkings loader. */
const assert = require('assert'), fs = require('fs'), vm = require('vm'), path = require('path');
const handlers = {}, views = {}, headNodes = [], injected = [];
const owned = fs.readFileSync(path.join(__dirname, '../../res/gui/gameface/mods/Driftkings/shared/bootstrap.js'), 'utf8');
const bootstrap = 'coui://gui/gameface/mods/Driftkings/shared/bootstrap.js';
const context = {console, JSON, Object, Array, Set};
const head = {
    appendChild(node) { headNodes.push(node); node.parentNode = head; },
    removeChild(node) { headNodes.splice(headNodes.indexOf(node), 1); node.parentNode = null; }
};
context.document = {
    head, documentElement: {style: {}},
    styleSheets: [{cssRules: [], insertRule() {}}],
    createElement(tag) { return {tag}; },
    body: {appendChild(node) { injected.push(node.src); if (node.src === bootstrap) vm.runInContext(owned, context); }}
};
context.engine = {
    whenReady: {then(fn) { fn(); }},
    on(name, fn) { (handlers[name] || (handlers[name] = [])).push(fn); },
    off(name, fn) { handlers[name] = (handlers[name] || []).filter(item => item !== fn); }
};
context.subViews = {ids() { return Object.keys(views); }, get(id) { return views[id]; }};
context.addEventListener = function () {};
context.removeEventListener = function () {};
context.window = context;
vm.createContext(context);
const prefix = 'coui://gui/gameface/mods/Driftkings/CarouselStats/';
function child() { return {model: {
    ModInjectModel: {scripts: [{value: bootstrap}]},
    DriftkingsUI: {name: 'DriftkingsCarouselStats', styles: '[]', scripts: JSON.stringify([prefix+'first.js', prefix+'second.js'])}
}}; }
views[11] = child();
views[12] = {model: {ModInjectModel: {scripts: [{value: 'coui://gui/gameface/mods/ModsList/main.js'}]}}};
const dependencySource = require('child_process').execFileSync('python', ['-c',
    "import zipfile,sys; z=zipfile.ZipFile('res/wotmods/net.openwg.gameface_1.1.6.wotmod'); sys.stdout.buffer.write(z.read('res/gui/gameface/js/index.js'))"],
    {cwd: path.join(__dirname, '../..'), encoding: 'utf8'});
vm.runInContext(dependencySource, context);
assert(injected.includes(bootstrap));
assert(injected.includes('coui://gui/gameface/mods/ModsList/main.js'));
assert.strictEqual(headNodes.length, 1);
assert.strictEqual(headNodes[0].src, prefix+'first.js');
headNodes[0].onload();
assert.strictEqual(headNodes[1].src, prefix+'second.js');
const bridge = context.__dkUIBridge;
views[13] = child();
handlers['subViews.onAdded'].slice().forEach(fn => fn(['13']));
assert.strictEqual(context.__dkUIBridge, bridge, 'second bootstrap keeps existing lifecycle');
assert.strictEqual(headNodes.length, 2, 'same feature must not load twice');
let disposed = 0;
context.__dkCarouselStats = {dispose() { disposed++; }};
delete views[11]; delete views[13];
handlers['subViews.onRemoved'].slice().forEach(fn => fn(['11', '13']));
assert.strictEqual(disposed, 1);
assert.strictEqual(headNodes.length, 0);
bridge.dispose();
assert.strictEqual(handlers['subViews.onAdded'].length, 1, 'OpenWG listener is retained');
assert(views[12], 'ModList view is retained');
console.log('OpenWG 1.1.6 + Driftkings: initial injection, ordered scripts, duplicate bootstrap and independent cleanup: OK');
