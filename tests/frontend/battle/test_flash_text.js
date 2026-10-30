/* Shared Flash text conversion: equivalent options and safe DOM output. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.resolve(__dirname, '../../..');

function element(tag, attributes, children) {
    return {nodeType: 1, tagName: tag.toUpperCase(), attributes: attributes || {},
        childNodes: children || [], style: {},
        getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null; },
        appendChild(child) { this.childNodes.push(child); return child; }};
}
function text(value) { return {nodeType: 3, nodeValue: value}; }
const document = {createElement: tag => element(tag), createTextNode: text};
const context = {window: {}, document};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'mod/res/gui/gameface/mods/driftkings/shared/flash_text.js'), 'utf8'), context);
function output(source, options) {
    const target = element('div');
    context.window.DriftkingsFlashText.copy(source, target, options);
    return target;
}
const rich = element('div', {}, [text('A < B & C'),
    element('font', {color: '#12Ab34', size: '16', face: '$FieldFont', alpha: '#80'}, [
        element('b', {onclick: 'bad()'}, [text('bold')]), element('br')]),
    element('font', {size: '0'}, [text('hidden')]),
    element('script', {}, [text('bad()')]), element('style', {}, [text('bad')]),
    element('iframe', {src: 'bad'}, [text('bad')]),
    element('a', {href: 'javascript:bad()'}, [text('safe text')]),
    {nodeType: 8, nodeValue: 'comment'}]);
const simple = output(rich);
assert.strictEqual(simple.childNodes[0].nodeValue, 'A < B & C');
assert.deepStrictEqual(simple.childNodes[1].style, {color: '#12Ab34', fontSize: '16px'});
assert.deepStrictEqual(simple.childNodes[1].childNodes[0].attributes, {});
assert.deepStrictEqual(simple.childNodes[2].style, {});
assert.strictEqual(simple.childNodes.length, 4);
assert.strictEqual(simple.childNodes[3].tagName, 'SPAN');
assert.deepStrictEqual(simple.childNodes[3].attributes, {});
const options = {fontFamily: true, fontAlpha: true, hideZeroSize: true, sizeUnit: 'rem'};
const ratings = output(rich, options);
assert.deepStrictEqual(ratings.childNodes[1].style, {fontFamily: '', opacity: 128 / 255, color: '#12Ab34', fontSize: '16rem'});
assert.deepStrictEqual(ratings.childNodes[2].style, {display: 'none'});
for (const size of ['7', '41', 'NaN', 'Infinity', '-1']) {
    const invalid = output(element('div', {}, [element('font', {size, color: 'red', alpha: '#GG', face: 'Arial; color:red'}, [text('text')])]), options);
    assert.deepStrictEqual(invalid.childNodes[0].style, {});
}
for (const size of ['8', '40']) {
    const result = output(element('div', {}, [element('font', {size}, [])]), options);
    assert.strictEqual(result.childNodes[0].style.fontSize, size + 'rem');
}
assert.strictEqual(output(element('div', {}, [element('font', {face: 'Times New Roman'}, [])]), options).childNodes[0].style.fontFamily, 'Times New Roman');
for (const face of ['dkm', 'DriftkingsFont', 'Fonte Ã¡', 'å­—ä½“']) {
    const result = output(element('div', {}, [element('font', {face}, [text('Ã¡ Ð– ä¸­ !')])]), options);
    assert.strictEqual(result.childNodes[0].style.fontFamily, face);
    assert.strictEqual(result.childNodes[0].childNodes[0].nodeValue, 'Ã¡ Ð– ä¸­ !');
}
// A second load is safe when two injected features request the shared script.
vm.runInContext(fs.readFileSync(path.join(root, 'mod/res/gui/gameface/mods/driftkings/shared/flash_text.js'), 'utf8'), context);
assert.deepStrictEqual(output(rich, options).childNodes[1].style, ratings.childNodes[1].style);
console.log('Shared Flash text: formatting, filtering, feature options and reload OK');
module.exports = {element, rich, output, options, document};
