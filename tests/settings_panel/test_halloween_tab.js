/* Halloween TAB table: formatting, safe text, colours and its own node only. */
const assert = require('assert');
const path = require('path');
const folder = path.resolve(__dirname, '../../mod/res/gui/gameface/mods/driftkings/panel_gameface');

function element(tag) {
    return {tagName: tag.toUpperCase(), childNodes: [], style: {}, className: '', textContent: '', parentNode: null,
        appendChild(child) { child.parentNode = this; this.childNodes.push(child); return child; },
        removeChild(child) { this.childNodes.splice(this.childNodes.indexOf(child), 1); child.parentNode = null; }};
}
const body = element('body');
const native = body.appendChild(element('div'));
global.document = {body, createElement: element};
const table = require(path.join(folder, 'halloween_tab.js'));

const player = {id: 1, index: 0, enabled: true, name: 'Anna', clan: 'CL', vehicle: 'Maus', alive: true, self: true,
    stats: true, rating: 'wn8', r: 1834.6, 'c:r': '#5A3175', winrate: 52.345, 'c:winrate': '#4099BF',
    battles: 12345, 'c:battles': '#02C9B3'};
const bot = {id: 6, index: 1, enabled: true, name: '<b>Bot</b>', clan: '', vehicle: 'Pumpkin', alive: false,
    self: false, stats: false, rating: 'wn8', r: null, 'c:r': '#AAAAAA', winrate: null, battles: null};

// Formatting and colours.
assert.deepStrictEqual(table.cells(player).map(cell => cell.text), ['Anna [CL]', 'Maus', '1835', '52.3%', '12.3k']);
assert.deepStrictEqual(table.cells(player).map(cell => cell.color), ['#FFDD33', '', '#5A3175', '#4099BF', '#02C9B3']);
assert.deepStrictEqual(table.cells(Object.assign({}, player, {rating: 'winrate', r: 55, battles: 999})).map(cell => cell.text).slice(2),
    ['55.0%', '52.3%', '999']);
assert.deepStrictEqual(table.cells(Object.assign({}, player, {'c:r': 'red', 'c:winrate': '0x00FF00'})).map(cell => cell.color).slice(2, 4),
    ['', '']);
// Mode entities (accountDBID 0) have no statistics: dashes in the neutral colour.
assert.deepStrictEqual(table.cells(bot).map(cell => cell.text), ['<b>Bot</b>', 'Pumpkin', '—', '—', '—']);
assert.deepStrictEqual(table.cells(bot).map(cell => cell.color).slice(2), ['', '', '']);
assert.strictEqual(table.header([player])[2].text, 'WN8');

// Rendering adds one node of its own; names stay text, dead rows are dimmed.
table.render({enabled: true, screen: 'hwTab', rows: [player, bot]});
assert.strictEqual(body.childNodes.length, 2);
const box = body.childNodes[1];
assert.strictEqual(box.className, 'dk-hw-tab');
assert.strictEqual(box.childNodes.length, 3);
assert.strictEqual(box.childNodes[2].childNodes[0].textContent, '<b>Bot</b>');
assert.strictEqual(box.childNodes[2].childNodes[0].childNodes.length, 0);
assert.deepStrictEqual(box.childNodes.map(row => row.style.opacity), [0.7, 1, 0.5]);
assert.strictEqual(native.childNodes.length, 0);

// An equal payload keeps the node; a change replaces it; disabled or empty removes it.
table.render({enabled: true, screen: 'hwTab', rows: [player, bot]});
assert.strictEqual(body.childNodes[1], box);
table.render({enabled: true, screen: 'hwTab', rows: [player]});
assert.strictEqual(body.childNodes.length, 2);
assert.notStrictEqual(body.childNodes[1], box);
table.render({enabled: false, screen: 'hwTab', rows: [player]});
assert.deepStrictEqual(body.childNodes, [native]);
table.render({enabled: true, screen: 'hwTab', rows: [player]});
table.hide();
assert.deepStrictEqual(body.childNodes, [native]);

console.log('Halloween TAB table: passed');
