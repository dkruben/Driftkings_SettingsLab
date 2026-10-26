/* UI cache regressions. No game, browser or third-party packages required. */
require('./test_settings_window.js');
require('./test_vehicle_markers_model.js');
require('./test_vehicle_markers_editor.js');
require('./test_ratings.js');
require('./test_main_gun.js');
require('./test_flash_text.js');
require('./test_profile_ratings.js');
require('./test_carousel_assets.js');
require('./test_carousel_fields.js');
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.resolve(__dirname, '../..');
const uiRoot = path.join(root, 'mod/res/gui/gameface/mods/driftkings/settings_window');
let source = fs.readFileSync(path.join(uiRoot, 'js/app.js'), 'utf8');
const startup = source.lastIndexOf('\n    build();');
assert(startup > 0);
source = source.slice(0, startup) + `
DK.test = {ui: ui, layout: layout, filter: filter, scroll: scheduleScrollbars,
    dispose: dispose, label: label, categoryLabel: categoryLabel,
    data: function (next) {
        if ('state' in next) { state = next.state; }
        if ('query' in next) { query = next.query; }
        if ('tab' in next) { activeTab = next.tab; }
        if ('rendered' in next) { rendered = next.rendered; }
        if ('mods' in next) { mods = next.mods; }
        if ('controls' in next) { controls = next.controls; }
        if ('labels' in next) { schema = {labels: next.labels}; lastFilter = null; }
    }};
}());`;

let writes = 0, refreshes = 0, width = 1440, height = 900, scale = 1, timerId = 0;
const timers = new Map();
function node() {
    return {className: '', style: new Proxy({}, {set(target, key, value) {
        writes++; target[key] = value; return true;
    }})};
}
const DK = {dom: {el() {}, setClass(n, name, on) {
    n.className = n.className.split(' ').filter(x => x && x !== name).concat(on ? [name] : []).join(' ');
}}, bridge: {scale: () => scale, clientSizeRem: () => ({width, height}), dispose() {}},
    modal: {close() {}}, layer: {close() {}, hideTip() {}}, profileDialogs: {close() {}, isOpen() { return false; }}};
const context = {window: {DK, removeEventListener() {}},
    document: {documentElement: node(), removeEventListener() {}},
    setTimeout(fn) { timers.set(++timerId, fn); return timerId; },
    clearTimeout(id) { timers.delete(id); }};
vm.createContext(context);
vm.runInContext(source, context);
const test = DK.test;
Object.assign(test.ui, {window: node(), sidebarScroll() { refreshes++; }, controlScroll() { refreshes++; }});
test.layout();
const initialWrites = writes;
test.layout();
assert.strictEqual(writes, initialWrites, 'Repeated layout must not rewrite sizes');
width = 900; test.layout();
assert(writes > initialWrites);
assert(test.ui.window.className.includes('is-narrow'));
scale = 2; test.layout();
assert.strictEqual(context.document.documentElement.style.fontSize, '2px');
test.data({state: {theme: {uiScale: 125}}}); test.layout();
assert.strictEqual(context.document.documentElement.style.fontSize, '2.5px');
height = 800; const beforeHeight = writes; test.layout(); assert(writes > beforeHeight);
assert.strictEqual(timers.size, 1, 'Geometry refreshes must share one scrollbar job');
const job = timers.values().next().value; timers.clear(); job();
assert.strictEqual(refreshes, 2);

const nav = node(), control = node(), updates = node();
Object.assign(test.ui, {nav: {alpha: nav}, groups: [], updates});
test.data({rendered: 'alpha', state: {updater: {downloadPercent: 1}},
    mods: {alpha: {name: 'Alpha', controls: []}},
    controls: {value: {node: control, definition: {label: 'Value', tab: 'Main'}}},
    labels: {'updates.title': 'Updates', 'category.battle': 'Batalha', author: ''}});
test.filter(); const afterFirst = writes;
test.data({state: {updater: {downloadPercent: 90}}}); test.filter();
assert.strictEqual(writes, afterFirst, 'Progress-only changes must not refilter');
test.data({tab: 'Main'}); test.filter();
assert.strictEqual(updates.style.display, 'none');
test.filter(); assert.strictEqual(updates.style.display, 'none');
test.data({tab: '', query: 'unmatched'}); test.filter();
assert.strictEqual(nav.style.display, 'none'); assert.strictEqual(control.style.display, 'none');
test.data({query: '', state: {}}); test.filter();
assert.strictEqual(nav.style.display, 'flex'); assert.strictEqual(updates.style.display, 'none');
test.data({state: {updater: {}}, rendered: 'beta'}); test.filter();
assert.strictEqual(updates.style.display, '');
test.data({labels: {'category.battle': 'Battle'}}); const beforeSchema = writes; test.filter();
assert(writes > beforeSchema, 'Schema changes must invalidate filtering');
assert.strictEqual(test.categoryLabel('battle'), 'Battle');
assert.strictEqual(test.label('absent', 'Fallback'), 'Fallback');
test.data({labels: {author: ''}}); assert.strictEqual(test.label('author', 'Author'), '');
test.scroll(); assert.strictEqual(timers.size, 1);
test.dispose(); assert.strictEqual(timers.size, 0, 'Disposal must cancel deferred scroll work');
console.log('PASS: layout/filter caching, invalidation, translated labels and scrollbar lifetime');
