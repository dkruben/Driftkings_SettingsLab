/* Player ratings TAB helpers: values, safe text runs and row matching. */
const assert = require('assert');
const path = require('path');
const folder = path.resolve(__dirname, '../../../mod/res/gui/gameface/mods/driftkings/panel_gameface');
const text = require(path.join(folder, 'rating_text.js'));
const rows = require(path.join(folder, 'rating_rows.js'));

function element(tag, attributes, children) {
    return {nodeType: 1, tagName: tag.toUpperCase(), attributes: attributes || {}, childNodes: children || [], style: {},
        getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null; },
        appendChild(child) { this.childNodes.push(child); return child; }};
}
const node = value => ({nodeType: 3, nodeValue: value});
global.document = {createElement: tag => element(tag)};

// Values.
assert.deepStrictEqual([0, '0', 'false', '', null, undefined, false].map(text.flag), [false, false, false, false, false, false, false]);
assert.deepStrictEqual([1, '1', 'true', 'yes', true].map(text.flag), [true, true, true, true, true]);
assert.strictEqual(text.number('12.5', 3), 12.5);
assert.strictEqual(text.number('x', 3), 3);
assert.strictEqual(text.number(null, 3), 3);
assert.strictEqual(text.color(65280), '#00ff00');
assert.strictEqual(text.color('#FFAA00'), '#FFAA00');
assert.strictEqual(text.color('0xFFAA00'), 'transparent');
assert.strictEqual(text.color('FFAA00'), 'transparent');
assert.strictEqual(text.color('red'), 'transparent');
assert.strictEqual(text.localImage('img://gui/maps/icons/a.png'), 'coui://gui/maps/icons/a.png');
assert.strictEqual(text.localImage('coui://gui/../secret.png'), '');
assert.strictEqual(text.localImage('http://example.com/a.png'), '');

// Flash text becomes flat runs; scripts, hidden text and unsafe attributes are dropped.
const target = element('div');
text.copyRuns(element('div', {}, [node('A '),
    element('font', {color: '#12Ab34', size: '16', alpha: '#80'}, [element('b', {}, [node('bold')]), element('br')]),
    element('font', {size: '0'}, [node('hidden')]),
    element('script', {}, [node('bad()')]),
    element('img', {src: 'img://gui/maps/icons/b.png', width: '10'}),
    element('img', {src: 'http://example.com/x.png'})]), target, {});
assert.strictEqual(target.childNodes.length, 4);
assert.strictEqual(target.childNodes[0].textContent, 'A ');
assert.deepStrictEqual(target.childNodes[1].style, {flexShrink: '0', whiteSpace: 'pre', color: '#12Ab34', fontSize: '16rem',
    opacity: 128 / 255, fontWeight: 'bold'});
assert.strictEqual(target.childNodes[2].style.flexBasis, '100%');
assert.strictEqual(target.childNodes[3].src, 'coui://gui/maps/icons/b.png');
assert.strictEqual(target.childNodes[3].style.width, '10rem');
const plain = element('div');
text.writeRuns(plain, 'No markup');
assert.strictEqual(plain.childNodes[0].textContent, 'No markup');

for (const face of ['XVMSymbol', 'xvm', 'Fonte á', '字体']) {
    const custom = element('div');
    text.copyRuns(element('div', {}, [element('font', {face}, [node('á Ж 中 !')])]), custom, {});
    assert.strictEqual(custom.childNodes[0].style.fontFamily, face);
    assert.strictEqual(custom.childNodes[0].textContent, 'á Ж 中 !');
}

// Rows: a unique name wins, otherwise the native position in the team order.
const data = {rows: [
    {id: 1, ally: true, aliases: ['Player One'], cfg: {enabled: true}},
    {id: 2, ally: true, aliases: ['Twin'], cfg: {enabled: true}},
    {id: 3, ally: true, aliases: ['Twin'], cfg: {enabled: true}},
    {id: 4, ally: false, aliases: ['Enemy'], cfg: {enabled: false}}],
    order: {left: [3, 2, 1], right: [4]}};
const lookup = rows.index(data);
assert.strictEqual(rows.match(lookup, data, 'left', 2, 'Player  One').id, 1);
assert.strictEqual(rows.match(lookup, data, 'left', 0, 'Player One').id, 1);
assert.strictEqual(rows.match(lookup, data, 'left', 1, 'Twin').id, 2);
assert.strictEqual(rows.match(lookup, data, 'right', 0, 'Unknown').id, 4);
assert.strictEqual(rows.match(lookup, data, 'right', 5, 'Unknown'), undefined);
assert.strictEqual(data.rows[0]._dkSignature, JSON.stringify({enabled: true}));
console.log('ratings helpers: ok');
