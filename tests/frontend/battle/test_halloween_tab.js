/* Halloween TAB: native nickname colours without an extra statistics panel. */
const assert = require('assert');
const path = require('path');
const folder = path.resolve(__dirname, '../../../mod/res/gui/gameface/mods/driftkings/panel_gameface');

function element(tag) {
    return {tagName: tag.toUpperCase(), childNodes: [], style: {}, className: '', textContent: '', parentNode: null,
        appendChild(child) { child.parentNode = this; this.childNodes.push(child); return child; },
        removeChild(child) { this.childNodes.splice(this.childNodes.indexOf(child), 1); child.parentNode = null; }};
}
const body = element('body');
const native = body.appendChild(element('div'));
let nativeNames = [];
global.document = {body, createElement() { throw new Error('Halloween TAB must not create an extra panel'); }, querySelectorAll(selector) {
    assert.strictEqual(selector, '[class*="PlayerInfo_base__tabWindow_"] [class*="PlayerInfo_userName_"]');
    return nativeNames;
}};
const table = require(path.join(folder, 'halloween_tab.js'));

const player = {id: 1, index: 0, enabled: true, name: 'Anna', clan: 'CL', vehicle: 'Maus', alive: true, self: true,
    stats: true, rating: 'wn8', r: 1834.6, 'c:r': '#5A3175', winrate: 52.345, 'c:winrate': '#4099BF',
    battles: 12345, 'c:battles': '#02C9B3'};
const bot = {id: 6, index: 1, enabled: true, name: '<b>Bot</b>', clan: '', vehicle: 'Pumpkin', alive: false,
    self: false, stats: false, rating: 'wn8', r: null, 'c:r': '#AAAAAA', winrate: null, battles: null};

// Rendering leaves the native DOM intact and never creates an extra table.
table.render({enabled: true, screen: 'hwTab', rows: [player, bot]});
assert.deepStrictEqual(body.childNodes, [native]);
table.render({enabled: false, screen: 'hwTab', rows: [player]});
assert.deepStrictEqual(body.childNodes, [native]);

function nickname(name, original = '', priority = '') {
    const node = element('div'), values = {color: original}, priorities = {color: priority};
    node.textContent = name;
    node.writes = 0;
    node.style = {
        getPropertyValue(key) { return values[key] || ''; },
        getPropertyPriority(key) { return priorities[key] || ''; },
        setProperty(key, value, importance) { values[key] = value; priorities[key] = importance || ''; node.writes++; },
        removeProperty(key) { delete values[key]; delete priorities[key]; }
    };
    Object.defineProperty(node.style, 'color', {
        get() { return values.color || ''; },
        set(value) { values.color = value; priorities.color = ''; node.writes++; }
    });
    return node;
}
const anna = nickname('Anna', '#FFDD33', 'important'), pumpkin = nickname('<b>Bot</b>', '#CFCFCF');
nativeNames = [pumpkin, anna]; // Native sorting can differ from the payload order.
table.render({enabled: true, screen: 'hwTab', rows: [player, bot]});
assert.strictEqual(anna.style.getPropertyValue('color'), '#5A3175');
assert.strictEqual(anna.style.getPropertyPriority('color'), '');
assert.strictEqual(pumpkin.style.getPropertyValue('color'), '#CFCFCF');
assert.strictEqual(anna.textContent, 'Anna');
assert.strictEqual(anna.childNodes.length, 0);
const writes = anna.writes;
table.refresh();
assert.strictEqual(anna.writes, writes); // Equal payload/native state does not rewrite CSS.

const replacement = nickname('Anna');
nativeNames = [replacement, pumpkin];
table.refresh(); // React can replace a native name without changing our payload.
assert.strictEqual(anna.style.getPropertyValue('color'), '#FFDD33');
assert.strictEqual(anna.style.getPropertyPriority('color'), 'important');
assert.strictEqual(replacement.style.getPropertyValue('color'), '#5A3175');

replacement.style.setProperty('color', '#EFEFEF'); // Preserve a newer native inline style.
table.refresh();
assert.strictEqual(replacement.style.getPropertyValue('color'), '#5A3175');
table.render({enabled: true, screen: 'hwTab', rows: [Object.assign({}, player, {'c:r': '#00FF00'})]});
assert.strictEqual(replacement.style.getPropertyValue('color'), '#00FF00');
table.render({enabled: false, screen: 'hwTab', rows: [player]});
assert.strictEqual(replacement.style.getPropertyValue('color'), '#EFEFEF');
assert.strictEqual(replacement.style.getPropertyPriority('color'), '');

table.render({enabled: true, screen: 'hwTab', rows: [player]});
table.render({enabled: true, screen: 'hwTab', rows: [Object.assign({}, player, {stats: false})]});
assert.strictEqual(replacement.style.getPropertyValue('color'), '#EFEFEF');
table.render({enabled: true, screen: 'hwTab', rows: [player, Object.assign({}, player, {id: 2})]});
assert.strictEqual(replacement.style.getPropertyValue('color'), '#EFEFEF'); // Ambiguous names stay native.
table.render({enabled: true, screen: 'hwTab', rows: [Object.assign({}, player, {'c:r': 'red'})]});
assert.strictEqual(replacement.style.getPropertyValue('color'), '#EFEFEF');
table.render({enabled: true, screen: 'hwTab', rows: [player]});
replacement.style.setProperty('color', '#112233');
table.hide();
assert.strictEqual(replacement.style.getPropertyValue('color'), '#112233'); // Do not undo another writer.
assert.deepStrictEqual(body.childNodes, [native]);

// Gameface exposes style.color without the full browser CSSStyleDeclaration API.
const gamefaceName = nickname('Anna', '#CFCFCF');
delete gamefaceName.style.getPropertyPriority;
delete gamefaceName.style.getPropertyValue;
delete gamefaceName.style.setProperty;
delete gamefaceName.style.removeProperty;
nativeNames = [gamefaceName];
assert.doesNotThrow(() => table.render({enabled: true, screen: 'hwTab', rows: [player]}));
assert.strictEqual(body.childNodes.length, 1);
assert.strictEqual(gamefaceName.style.color, '#5A3175');
table.refresh();
table.hide();
assert.strictEqual(gamefaceName.style.color, '#CFCFCF');
assert.deepStrictEqual(body.childNodes, [native]);

console.log('Halloween TAB native colours without an extra panel: passed');
