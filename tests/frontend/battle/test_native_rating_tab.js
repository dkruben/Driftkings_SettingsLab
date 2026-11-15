'use strict';
const assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
const {Node} = require('../../support/frontend/dom_fixture');
const root = path.resolve(__dirname, '../../..');
const patch = JSON.parse(fs.readFileSync(path.join(root, 'build_data/patches/native_document_ratingplayers_0_2.4.2_ct.json')));
const scripts = [...patch.operations[0].replace.matchAll(/<script defer src="([^"]+)"><\/script>/g)].map(match => match[1]);
assert.strictEqual(scripts.length, 3);
assert.ok(scripts.every(url => !/halloween|bootstrap/i.test(url)));
function environment() {
    const window = new Node('window'), document = new Node('document'), engine = new Node('engine');
    document.body = new Node('body'); document.documentElement = new Node('html');
    document.createElement = tag => new Node(tag);
    function query(node, selector) {
        const match = /\[class\*="([^"]+)"\]/.exec(selector), found = [];
        function walk(parent) {
            parent.children.forEach(child => {
                if (match ? child.className.includes(match[1]) : child.matches(selector)) { found.push(child); }
                walk(child);
            });
        }
        walk(node); return found;
    }
    document.querySelectorAll = selector => query(document.body, selector);
    function player(name, right) {
        const row = new Node('div'), nick = new Node('div');
        row.className = 'Player_base_ab12' + (right ? ' Player_right_ab12' : '');
        nick.className = 'UserInfo_userNameWrapper_ab12'; nick.textContent = name;
        row.appendChild(nick); document.body.appendChild(row);
        row.querySelector = selector => query(row, selector)[0] || null;
        return {row, nick};
    }
    const ally = player('Ally', false), enemy = player('Enemy', true);
    const jobs = new Map(), intervals = new Map(), callbacks = new Map(), observers = []; let next = 0;
    window.innerWidth = 1920; window.innerHeight = 1080;
    window.getComputedStyle = node => Object.assign({fontSize: '1px', fontFamily: 'Warhelios', fontWeight: 'normal',
        fontStyle: 'normal', color: '#ffffff', lineHeight: '20px', opacity: '1', display: 'block', visibility: 'visible'}, node.style);
    class Observer {
        constructor(fn) { this.fn = fn; observers.push(this); }
        observe() { this.connected = true; }
        disconnect() { this.connected = false; }
    }
    let present = true;
    const samples = [], model = {DriftkingsUI: {name: 'DriftkingsRatingPlayers'}, payload: '{}', onPerformance: sample => samples.push(sample)};
    window.subViews = {ids: () => present ? [42] : [], get: () => ({model})};
    engine.whenReady = {then: fn => fn()}; engine.on = engine.addEventListener.bind(engine); engine.off = engine.removeEventListener.bind(engine);
    Object.assign(window, {window, document, engine, MutationObserver: Observer, console,
        viewEnv: {addDataChangedCallback(name, id) { callbacks.set(++next, id); return next; }, removeDataChangedCallback(id) { callbacks.delete(id); }},
        setTimeout(fn) { jobs.set(++next, fn); return next; }, clearTimeout(id) { jobs.delete(id); },
        setInterval(fn) { intervals.set(++next, fn); return next; }, clearInterval(id) { intervals.delete(id); }});
    const context = vm.createContext(window);
    function flush() { while (jobs.size) { const batch = [...jobs.values()]; jobs.clear(); batch.forEach(fn => fn()); } }
    scripts.forEach(url => vm.runInContext(fs.readFileSync(path.join(root, 'mod/res', url.slice(7)), 'utf8'), context));
    flush();
    function update(data) { model.payload = JSON.stringify(data); engine.fire('viewEnv.onDataChanged'); flush(); }
    return {window, document, engine, callbacks, intervals, jobs, observers, ally, enemy, samples, update,
        removeModel() { present = false; engine.fire('subViews.onRemoved'); flush(); },
        addModel() { present = true; engine.fire('subViews.onAdded'); flush(); }};
}
for (let battle = 0; battle < 2; battle++) {
    const page = environment();
    const payload = {enabled: true, screen: 'tab', diagnostics: true, order: {left: [1], right: [2]}, rows: [
        {id: 1, ally: true, aliases: ['Ally'], cfg: {enabled: true, formatLeftNick: 'Ally 1800 WN8'}},
        {id: 2, ally: false, aliases: ['Enemy'], cfg: {enabled: true, formatRightNick: 'Enemy 2200 WN8'}}]};
    assert.strictEqual(page.window.__dkUIBridge, undefined);
    assert.strictEqual(page.window.DKHalloweenTab, undefined);
    page.update(payload);
    let overlays = page.document.querySelectorAll('.dk-tab-roster-field');
    assert.strictEqual(overlays.length, 2);
    assert.ok(overlays.some(node => node.textContent.includes('1800 WN8')));
    assert.strictEqual(page.ally.nick.style.visibility, 'hidden');
    assert.strictEqual(page.enemy.nick.style.visibility, 'hidden');
    const first = overlays[0];
    page.engine.fire('viewEnv.onDataChanged');
    assert.strictEqual(page.document.querySelectorAll('.dk-tab-roster-field')[0], first, 'equal payload reuses the renderer');
    page.update({enabled: false, screen: 'tab', rows: []});
    assert.notStrictEqual(page.ally.nick.style.visibility, 'hidden');
    page.update(payload);
    assert.strictEqual(page.document.querySelectorAll('.dk-tab-roster-field').length, 2);
    page.removeModel();
    assert.strictEqual(page.callbacks.size, 0);
    assert.strictEqual(page.document.querySelectorAll('.dk-tab-roster-field').length, 0);
    assert.notStrictEqual(page.ally.nick.style.visibility, 'hidden');
    page.addModel();
    assert.strictEqual(page.callbacks.size, 1);
    assert.strictEqual(page.document.querySelectorAll('.dk-tab-roster-field').length, 2);
    page.window.fire('unload');
    assert.strictEqual(page.document.querySelectorAll('.dk-tab-roster-field').length, 0);
    assert.strictEqual(page.callbacks.size, 0); assert.strictEqual(page.intervals.size, 0); assert.strictEqual(page.jobs.size, 0);
    assert.ok(Object.values(page.engine.listeners).every(items => items.length === 0));
    assert.ok(Object.values(page.window.listeners).every(items => items.length === 0));
    assert.ok(page.observers.every(observer => !observer.connected));
    assert.ok(page.samples.length > 0, 'performance command remains connected to the native model');
}
console.log('Native TAB: actual document assets, ally/enemy text, reuse, reopen, two battles and cleanup passed');
