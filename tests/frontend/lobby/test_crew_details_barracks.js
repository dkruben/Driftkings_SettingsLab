'use strict';
// Barracks card progression: one compact line inside the native information block, never over the portrait.
// The fixture cannot evaluate attribute selectors, so the two lookups the script performs are answered explicitly.
const assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
const {Node} = require('../../support/frontend/dom_fixture');
const base = path.resolve(__dirname, '../../../mod/res/gui/gameface/mods/driftkings/');
const CARD_SELECTOR = '[data-dk-barracks-kind="tankman"][data-dk-barracks-id]';
const INFO_SELECTOR = '[class^="Content_base_"]';
const DOT = ' · ', DASH = '—';

function environment(cards, infos) {
    const document = new Node('document'), models = new Map(), callbacks = new Map(), jobs = new Map();
    let next = 0;
    document.body = new Node('body');
    document.createElement = tag => new Node(tag);
    document.querySelectorAll = selector => (selector === CARD_SELECTOR ? cards : []);
    const window = {subViews: {ids: () => [...models.keys()], get: id => models.get(id)}, addEventListener() {}, removeEventListener() {}};
    const context = {
        window, document, console, JSON, Math, Object, Array, String, Number, isFinite, Error, Promise,
        Event: class { constructor(type) { this.type = type; } },
        engine: {whenReady: Promise.resolve(), on() {}, off() {}},
        viewEnv: {
            addDataChangedCallback(name, id) { callbacks.set(++next, id); return next; },
            removeDataChangedCallback(id) { callbacks.delete(id); }
        },
        setTimeout(fn) { jobs.set(++next, fn); return next; },
        clearTimeout(id) { jobs.delete(id); }
    };
    vm.createContext(context);
    cards.forEach(card => { card.querySelector = selector => (selector === INFO_SELECTOR ? infos.get(card) || null : null); });
    return {context, models, flush() { [...jobs.values()].forEach(fn => fn()); jobs.clear(); }};
}

async function settle(env) {
    for (let i = 0; i < 10; i++) { await Promise.resolve(); }
    env.flush();
    for (let i = 0; i < 10; i++) { await Promise.resolve(); }
    env.flush();
}

function card(id) {
    const node = new Node('div');
    node.setAttribute('data-dk-barracks-kind', 'tankman');
    node.setAttribute('data-dk-barracks-id', String(id));
    return node;
}

function dkBoxes(node) { return node.children.filter(child => child.className.indexOf('dk-crew-details') >= 0); }

function setModel(env, id, data) {
    env.models.set(id, {model: {DriftkingsUI: {name: 'DriftkingsCrewDetails'}, payload: JSON.stringify(data)}});
}

async function runScript(env) {
    vm.runInContext(fs.readFileSync(path.join(base, 'crew_details/details.js'), 'utf8'), env.context);
    await settle(env);
}

// One barracks card with its native information block; returns the single mounted line text, or null.
async function renderOne(rows, config = {visible: true}) {
    const node = card(101), info = new Node('div');
    const env = environment([node], new Map([[node, info]]));
    setModel(env, 7, {surface: 'barracks', config, rows: rows.map(row => Object.assign({id: 101}, row))});
    await runScript(env);
    const boxes = dkBoxes(info);
    const result = boxes.length ? boxes[0].children[0].textContent : null;
    env.context.window.__dkCrewDetails.dispose();
    return result;
}

// Renders one card and returns the segment elements of its single line.
async function renderSegments(rows) {
    const node = card(101), info = new Node('div');
    const env = environment([node], new Map([[node, info]]));
    setModel(env, 7, {surface: 'barracks', config: {visible: true}, rows: rows.map(row => Object.assign({id: 101}, row))});
    await runScript(env);
    const parts = dkBoxes(info)[0].children[0].children;
    env.context.window.__dkCrewDetails.dispose();
    return parts;
}

async function main() {
    // 1. Both values share one line inside the native information block; the card root carries no overlay.
    {
        const node = card(101), info = new Node('div');
        const env = environment([node], new Map([[node, info]]));
        setModel(env, 7, {surface: 'barracks', config: {visible: true},
            rows: [{id: 101, lines: ['196,351 XP', '~257 battles (estimate)'], kinds: ['xp', 'battles']}]});
        await runScript(env);
        const boxes = dkBoxes(info);
        assert.equal(boxes.length, 1);
        assert.equal(boxes[0].className, 'dk-crew-details dk-crew-details--barracks');
        assert.equal(boxes[0].children.length, 1, 'exactly one line');
        assert.equal(boxes[0].children[0].textContent, '196,351 XP' + DOT + '~257 battles (estimate)');
        assert.equal(dkBoxes(node).length, 0, 'no overlay on the card root');
        // 2. Re-render with changed data replaces the line; no duplicate elements.
        setModel(env, 7, {surface: 'barracks', config: {visible: true},
            rows: [{id: 101, lines: ['12 XP', 'Estimate: no history'], kinds: ['xp', 'unavailable']}]});
        env.context.window.__dkCrewDetails.dispose();
        await runScript(env);
        assert.equal(dkBoxes(info).length, 1);
        assert.equal(dkBoxes(info)[0].children[0].textContent, '12 XP' + DOT + DASH, 'missing estimate is a dash, never zero');
        // 3. Module or enhancement disabled: nothing is mounted anywhere.
        setModel(env, 7, {surface: 'barracks', config: {visible: false}, rows: []});
        env.context.window.__dkCrewDetails.dispose();
        await runScript(env);
        assert.equal(dkBoxes(info).length, 0);
        env.context.window.__dkCrewDetails.dispose();
        assert.equal(env.context.window.__dkCrewDetails, undefined, 'dispose releases the script');
    }
    // 4. Each progression state, including the single-value and perk-selection lines.
    const states = [
        [{lines: ['196,351 XP'], kinds: ['xp']}, '196,351 XP'],
        [{lines: ['~257 battles (estimate)'], kinds: ['battles']}, '~257 battles (estimate)'],
        [{lines: ['Estimate: no history'], kinds: ['unavailable']}, 'Estimate: no history'],
        [{lines: ['Choose a perk'], kinds: ['ready']}, 'Choose a perk'],
        [{lines: ['All perks completed'], kinds: ['complete']}, 'All perks completed'],
        [{lines: ['196,351 XP', 'Estimate: no history'], kinds: ['xp', 'unavailable']}, '196,351 XP' + DOT + DASH],
    ];
    for (const [row, expected] of states) {
        assert.equal(await renderOne([row]), expected);
    }
    // 5. Disabled configuration and a card with no progression row: nothing is mounted.
    assert.equal(await renderOne([], {visible: false}), null);
    assert.equal(await renderOne([]), null);
    // 6. Missing native information block: no overlay fallback on the card root.
    {
        const orphan = card(202);
        const env = environment([orphan], new Map());
        setModel(env, 8, {surface: 'barracks', config: {visible: true},
            rows: [{id: 202, lines: ['1 XP'], kinds: ['xp']}]});
        await runScript(env);
        assert.equal(dkBoxes(orphan).length, 0);
        env.context.window.__dkCrewDetails.dispose();
    }
    // 7. A row for another crew member is never shown on this card.
    {
        const other = card(303), info = new Node('div');
        const env = environment([other], new Map([[other, info]]));
        setModel(env, 9, {surface: 'barracks', config: {visible: true},
            rows: [{id: 999, lines: ['stale'], kinds: ['xp']}]});
        await runScript(env);
        assert.equal(dkBoxes(info).length, 0);
        env.context.window.__dkCrewDetails.dispose();
    }
    // 8. Semantic segments: each visible value keeps its existing class; separators are neutral and only between values.
    {
        const node = card(101), info = new Node('div');
        const env = environment([node], new Map([[node, info]]));
        setModel(env, 7, {surface: 'barracks', config: {visible: true},
            rows: [{id: 101, lines: ['48,076 XP', '~94 battles (estimate)'], kinds: ['xp', 'battles']}]});
        await runScript(env);
        const parts = dkBoxes(info)[0].children[0].children;
        assert.deepEqual(parts.map(part => part.textContent), ['48,076 XP', DOT, '~94 battles (estimate)']);
        assert.equal(parts[0].className, 'dk-crew-details__line--xp');
        assert.equal(parts[1].className, 'dk-crew-details__line--unavailable', 'neutral separator');
        assert.equal(parts[2].className, 'dk-crew-details__line--battles');
        env.context.window.__dkCrewDetails.dispose();
    }
    {
        const parts = await renderSegments([{lines: ['210,000 XP', 'Estimate: no history'], kinds: ['xp', 'unavailable']}]);
        assert.deepEqual(parts.map(part => part.className), ['dk-crew-details__line--xp', 'dk-crew-details__line--unavailable',
            'dk-crew-details__line--unavailable']);
        assert.equal(parts[2].textContent, DASH, 'unavailable indicator is a dash, never zero');
    }
    {
        const single = await renderSegments([{lines: ['Choose a perk'], kinds: ['ready']}]);
        assert.deepEqual(single.map(part => part.className), ['dk-crew-details__line--ready']);
        const complete = await renderSegments([{lines: ['All perks completed'], kinds: ['complete']}]);
        assert.deepEqual(complete.map(part => part.className), ['dk-crew-details__line--complete']);
        const onlyBattles = await renderSegments([{lines: ['~94 battles (estimate)'], kinds: ['battles']}]);
        assert.deepEqual(onlyBattles.map(part => part.className), ['dk-crew-details__line--battles']);
    }
    // 9. The colours are the existing stylesheet values, and the progression payload never reaches innerHTML.
    {
        const css = fs.readFileSync(path.join(base, 'crew_details/details.css'), 'utf8');
        const colour = name => new RegExp('\.dk-crew-details__line--' + name + '[^{]*\{ *color: *(#[0-9a-fA-F]{6})').exec(css);
        assert.equal(colour('xp')[1].toLowerCase(), '#00ffff');
        assert.equal(colour('battles')[1].toLowerCase(), '#28f09c');
        assert.equal(colour('ready')[1].toLowerCase(), '#28f09c');
        assert.equal(colour('complete')[1].toLowerCase(), '#28f09c');
        assert.equal(colour('unavailable')[1].toLowerCase(), '#8c8c7e');
        const source = fs.readFileSync(path.join(base, 'crew_details/details.js'), 'utf8');
        assert.ok(!/innerHTML/.test(source), 'no innerHTML in the Gameface script');
    // 10. Layout contract for the segments (beta.18 in game: the second and third values stayed invisible under the
    // inline/block layout). The line is a horizontal flex row without wrapping, and each segment is an independent flex
    // item that does not shrink, the pattern of the vehicle carousel fields. The synthetic DOM cannot evaluate CSS, so
    // this checks the stylesheet text only; in-game rendering is validated by the owner.
    {
        const css = fs.readFileSync(path.join(base, 'crew_details/details.css'), 'utf8');
        assert.ok(/\.dk-crew-details--barracks \.dk-crew-details__line \{[^}]*display: ?flex[^}]*flex-direction: ?row[^}]*flex-wrap: ?nowrap/.test(css),
            'the line is a horizontal non-wrapping flex row');
        assert.ok(/\.dk-crew-details--barracks \.dk-crew-details__line > span \{[^}]*flex: ?0 0 auto/.test(css),
            'each segment is an independent non-shrinking flex item');
        assert.ok(!/__line > span \{[^}]*display: ?inline/.test(css), 'the beta.18 inline workaround is removed');
        assert.ok(/\.dk-crew-details--barracks \{[^}]*height: ?16rem/.test(css), 'the box keeps its single-line height');
    }
    }
}

main().then(() => console.log('Barracks progression card: one line, states, toggles, missing data and cleanup passed'),
    error => { console.error(error); process.exitCode = 1; });
