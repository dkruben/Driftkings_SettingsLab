'use strict';
// Execute the unchanged renderers from the native document patch tags, without the OpenWG bootstrap.
const assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
const {Node} = require('../../support/frontend/dom_fixture');
const root = path.resolve(__dirname, '../../..');
const patches = fs.readdirSync(path.join(root, 'build_data/patches')).filter(name => /^native_document_.*\.json$/.test(name) && !name.includes('ratingplayers'));
assert.strictEqual(patches.length, 8);
function count(node) { return Object.values(node.listeners).reduce((sum, items) => sum + items.length, 0); }
patches.forEach(file => {
    const patch = JSON.parse(fs.readFileSync(path.join(root, 'build_data/patches', file))), feature = patch.feature;
    const window = new Node('window'), document = new Node('document'), engine = new Node('engine');
    document.body = new Node('body'); document.head = new Node('head'); document.createElement = tag => new Node(tag);
    const host = new Node('div'), premium = new Node('div'), plus = new Node('div'), menu = new Node('div');
    const card = new Node('div'), label = new Node('span');
    host.className = 'Footer_section_test'; host.appendChild(menu); card.appendChild(label);
    card.setAttribute('data-test-id', '123-content'); card.setAttribute('data-dk-barracks-id', '123');
    document.body.appendChild(host); document.body.appendChild(premium); document.body.appendChild(plus); document.body.appendChild(card);
    const cards = Array.from({length: 6}, () => new Node('div')), amounts = cards.map(() => new Node('div'));
    cards.forEach((node, index) => { node.querySelector = () => amounts[index]; });
    const statistics = {querySelectorAll: () => cards, querySelector: () => null};
    card.querySelector = selector => selector.includes('VehicleNode_name_') ? label : Node.prototype.querySelector.call(card, selector);
    document.querySelector = selector => {
        if (selector.includes('data-test-id="menu"')) { return menu; }
        if (selector.includes('data-test-id="premium"')) { return premium; }
        if (selector.includes('Statistic_base_')) { return statistics; }
        if (/TankmanTooltipApp|PersonalFileViewApp|ServiceRecordApp|TankmanInfoApp/.test(selector)) { return host; }
        return Node.prototype.querySelector.call(document.body, selector);
    };
    document.querySelectorAll = selector => {
        if (selector === '[data-test-id="premium"]') { return [premium]; }
        if (selector === '[data-test-id="wotPlus"]') { return [plus]; }
        if (selector.includes('data-dk-barracks') || selector === '[data-test-id$="-content"]') { return [card]; }
        return document.body.querySelectorAll(selector);
    };
    const observers = [], jobs = new Map(), intervals = new Map(), callbacks = new Map(); let next = 0, opens = 0;
    class Observer {
        constructor(fn) { this.fn = fn; this.connected = false; observers.push(this); }
        observe() { this.connected = true; }
        disconnect() { this.connected = false; }
    }
    window.MutationObserver = Observer;
    let data = {visible: true, title: 'Driftkings', enabled: true, config: {visible: true},
        showBuyPremiumButton: false, showWotPlusButton: false, damage: '#123456', battles: '#234567',
        showPercent: true, colorName: true, vehicles: {'123': {tier: 8, percent: 88, color: '#12AB34'}},
        surface: file.includes('crewdetails_0') ? 'barracks' : file.includes('crewdetails_2') ? 'personal_file' :
            file.includes('crewdetails_3') ? 'service_record' : 'tooltip',
        lines: ['XP 500'], kinds: ['xp'], rows: [{id: 123, lines: ['XP 500'], kinds: ['xp']}]};
    const model = {DriftkingsUI: {name: feature}, payload: JSON.stringify(data), onOpen() { opens++; }};
    let present = true;
    window.subViews = {ids: () => present ? [42] : [], get: () => ({model})};
    engine.whenReady = {then: fn => fn()}; engine.on = engine.addEventListener.bind(engine); engine.off = engine.removeEventListener.bind(engine);
    const context = vm.createContext({window, document, engine, MutationObserver: Observer, console,
        viewEnv: {addDataChangedCallback(name, id) { callbacks.set(++next, id); return next; }, removeDataChangedCallback(id) { callbacks.delete(id); }},
        setTimeout(fn) { jobs.set(++next, fn); return next; }, clearTimeout(id) { jobs.delete(id); },
        setInterval(fn) { intervals.set(++next, fn); return next; }, clearInterval(id) { intervals.delete(id); }});
    function flush() { while (jobs.size) { const batch = [...jobs.values()]; jobs.clear(); batch.forEach(fn => fn()); } }
    const html = patch.operations[0].replace;
    const scripts = [...html.matchAll(/<script defer src="([^"]+)"><\/script>/g)].map(match => match[1]);
    assert.strictEqual(scripts.length, new Set(scripts).size);
    scripts.forEach(url => vm.runInContext(fs.readFileSync(path.join(root, 'mod/res', url.slice(7)), 'utf8'), context));
    flush();
    assert.strictEqual(window.__dkUIBridge, undefined);
    assert.strictEqual(callbacks.size, 1, file + ' subscribes to its native Wulf model');
    if (feature === 'DriftkingsFooterLauncher') {
        assert.strictEqual(host.firstChild.className, 'driftkings-launcher'); host.firstChild.fire('click'); assert.strictEqual(opens, 1);
    } else if (feature === 'DriftkingsHangarHeaderOptions') {
        assert.strictEqual(premium.style.display, 'none'); assert.strictEqual(plus.style.display, 'none');
    } else if (feature === 'DriftkingsProfileRatings') {
        assert.strictEqual(amounts[0].style.color, '#123456');
    } else if (feature === 'DriftkingsCrewDetails') {
        assert.ok(document.body.querySelector('.dk-crew-details'), file + ' mounts in its original surface');
    } else {
        assert.strictEqual(card.querySelector('.dk-tech-marks__percent').textContent, '88.00%');
        assert.strictEqual(label.style.color, '#12AB34');
    }
    // Removing the model restores the native UI and releases data callbacks before the document unloads.
    present = false; engine.fire('subViews.onRemoved'); flush(); assert.strictEqual(callbacks.size, 0);
    assert.strictEqual(document.body.querySelector('.driftkings-launcher'), null);
    assert.strictEqual(document.body.querySelector('.dk-crew-details'), null);
    assert.strictEqual(document.body.querySelector('.dk-tech-marks'), null);
    window.fire('unload'); flush();
    assert.strictEqual(jobs.size, 0); assert.strictEqual(intervals.size, 0);
    assert.strictEqual(count(engine), 0); assert.strictEqual(count(window), 0);
    assert.ok(observers.every(observer => !observer.connected), file + ' disconnects document observers');
});
console.log('Eight native documents: unchanged renderers, original anchors, model removal, callbacks and unload cleanup passed');
