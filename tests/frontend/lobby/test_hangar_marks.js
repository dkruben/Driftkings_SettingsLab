'use strict';
// The hangar marks card follows the native mission column and opens a side panel with the rest.
var assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
function target() {
    return {handlers: {}, addEventListener: function (name, fn) {
        (this.handlers[name] || (this.handlers[name] = [])).push(fn);
    }, removeEventListener: function (name, fn) {
        this.handlers[name] = (this.handlers[name] || []).filter(function (item) { return item !== fn; });
    }, fire: function (name, event) {
        (this.handlers[name] || []).slice().forEach(function (fn) { fn(event); });
    }};
}
function element(tag) {
    var node = target(), attributes = {};
    node.tagName = tag; node.style = {}; node.children = []; node.clientWidth = 400; node.clientHeight = 95;
    node.appendChild = function (child) { child.parentNode = node; node.children.push(child); };
    node.removeChild = function (child) { node.children.splice(node.children.indexOf(child), 1); child.parentNode = null; };
    node.getAttribute = function (name) { return name === 'src' ? node.src : attributes[name]; };
    node.setAttribute = function (name, value) { attributes[name] = value; };
    Object.defineProperty(node, 'firstChild', {get: function () { return node.children[0]; }});
    node.getBoundingClientRect = function () {
        return {left: parseFloat(node.style.left) || 0, top: parseFloat(node.style.top) || 0,
            width: parseFloat(node.style.width) || 300, height: 64};
    };
    return node;
}
var column = element('div');
column.getBoundingClientRect = function () { return {left: 1600, right: 1919, width: 319, top: 60, bottom: 500, height: 440}; };
column.children = [element('div'), element('div')];
column.children[0].getBoundingClientRect = function () { return {left: 1600, right: 1919, width: 319, top: 60, bottom: 540, height: 480}; };
// A faded-out group still takes space in the column's layout and must not push the card down.
column.children[1].style.opacity = '0';
column.children[1].getBoundingClientRect = function () { return {left: 1600, right: 1919, width: 319, top: 540, bottom: 760, height: 220}; };
var document = target();
document.body = element('body'); document.documentElement = element('html'); document.createElement = element;
document.querySelector = function (selector) { return selector.indexOf('HangarScreen_userMissions_') >= 0 ? column : null; };
var window = target();
window.innerWidth = 1920; window.innerHeight = 1080;
window.getComputedStyle = function (node) { return {fontSize: '1px', opacity: (node && node.style.opacity) || '1', display: '', visibility: 'visible'}; };
var queue = [], intervals = 0;
var model = {payload: '{}', DriftkingsUI: {name: 'DriftkingsMarksOnGunHangar'}};
window.subViews = {ids: function () { return [42]; }, get: function () { return {model: model}; }};
var engine = target();
engine.whenReady = {then: function (fn) { fn(); }}; engine.on = engine.addEventListener; engine.off = engine.removeEventListener;
var context = vm.createContext({window: window, document: document, engine: engine,
    viewEnv: {addDataChangedCallback: function () { return 7; }, removeDataChangedCallback: function () {}},
    setTimeout: function (fn) { queue.push(fn); return queue.length; }, clearTimeout: function () { queue = []; },
    setInterval: function () { intervals++; return intervals; }, clearInterval: function () { intervals--; },
    requestAnimationFrame: function (fn) { queue.push(fn); return queue.length; }});
var base = path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings');
function load(relative) { vm.runInContext(fs.readFileSync(path.join(base, relative), 'utf8'), context); }
function flush() { while (queue.length) { queue.shift()(); } }
load('shared/marks_panel.js'); load('hangar_marks_of_excellence/marks.js'); flush();
var root = document.body.firstChild;
function find(cls, parent) {
    parent = parent || root;
    if ((' ' + parent.className + ' ').indexOf(' ' + cls + ' ') >= 0) { return parent; }
    for (var i = 0; i < parent.children.length; i++) { var found = find(cls, parent.children[i]); if (found) { return found; } }
    return null;
}
var data = {state: 'data', target: {eligible: true, threshold: 95}, currentMark: 90.63, displayMarks: 2,
    markColor: '#02C9B3', markIcon: 'coui://gui/maps/icons/marksOnGun/67x71/usa_2_marks.png',
    vehicle: 'M6', tier: 6, nation: 'E.U.A.', movingAverage: 1369, targetDamage: 1440, damageNeeded: 71,
    milestone: {nextMilestone: 95, gap: 4.37}, recent: {samples: []},
    labels: {current: 'Marca consolidada', more: 'Ver mais', title: 'Marcas de excelência no hangar'},
    config: {visible: true, decimalSeparator: ',', groupSeparator: ' '}};
function update() { model.payload = JSON.stringify(data); engine.fire('viewEnv.onDataChanged'); flush(); }
var click = {button: 0, stopPropagation: function () {}};
update();
// Basic information on the card, placed under the column's lowest group with the same width.
assert.strictEqual(root.style.display, 'block');
var card = find('dk-moe-card'), detail = find('dk-moe-detail');
assert.strictEqual(card.style.width, '319px');
assert.strictEqual(root.style.left, '1600px');
assert.strictEqual(root.style.top, '548px');
assert.strictEqual(intervals, 1);
assert.strictEqual(find('dk-moe-card__percent').textContent, '90,63%');
assert.strictEqual(find('dk-moe-card__percent').style.color, '#02C9B3');
assert.strictEqual(find('dk-moe-card__icon').children[0].src, data.markIcon);
assert.strictEqual(find('dk-moe-card__more').children[0].textContent, 'Ver mais');
var earned = find('dk-moe-card__body').children[1].children.filter(function (star) { return star.className.indexOf('earned') >= 0; });
assert.strictEqual(earned.length, 2);
// "Show more" opens the side panel; Escape and a click elsewhere close it.
assert.strictEqual(detail.style.display, 'none');
detail.offsetHeight = 700;
card.fire('click', click); flush();
assert.strictEqual(detail.style.display, 'block');
// Too tall to fit below the card's top edge: it moves up so its bottom stays on screen.
assert.strictEqual(detail.style.top, (1080 - 8 - (548 + 700)) + 'px');
assert.strictEqual(root.className, 'dk-moe dk-moe--open');
assert.strictEqual(find('dk-moe-detail__title').textContent, 'Marcas de excelência no hangar');
assert.strictEqual(find('dk-moe-detail__vehicle').textContent, 'M6 · VI · E.U.A.');
assert.strictEqual(find('dk-moe-detail__next').children[1].textContent, '4,37  ');
document.fire('keydown', {keyCode: 27, stopPropagation: function () {}});
assert.strictEqual(detail.style.display, 'none');
card.fire('click', click);
document.fire('mousedown', {target: document.body});
assert.strictEqual(detail.style.display, 'none');
card.fire('click', click);
find('dk-moe-detail__close').fire('click', click);
assert.strictEqual(detail.style.display, 'none');
// Without reliable data the card shows the reason and cannot open.
data.state = 'empty'; data.message = 'Marcas disponíveis no nível V'; update();
assert.strictEqual(find('dk-moe-card__more').style.display, 'none');
assert.strictEqual(find('dk-moe-card__message').textContent, 'Marcas disponíveis no nível V');
card.fire('click', click);
assert.strictEqual(detail.style.display, 'none');
// Without the native column the card keeps to the right edge.
document.querySelector = function () { return null; };
data.state = 'data'; update();
engine.fire('viewEnv.onDataChanged'); window.fire('resize'); flush();
assert.strictEqual(root.style.left, (1920 - 319 - 16) + 'px');
window.__dkHangarMarks.dispose();
assert.strictEqual(intervals, 0);
console.log('Hangar marks card under the mission column with a show-more panel: passed');
