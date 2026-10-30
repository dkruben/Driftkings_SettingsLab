'use strict';
// Gameface exposes style.color but not CSSStyleDeclaration.getPropertyPriority.
var assert = require('assert'), fs = require('fs'), vm = require('vm'), path = require('path');
var jobs = [], events = {}, callbacks = 0, removed = 0;
function leaf() { return {style: {color: ''}}; }
var damage = leaf(), battles = leaf(), wins = leaf(), points = leaf();
points.querySelector = function () { return null; };
var cards = [
    {querySelector: function () { return damage; }}, {},
    {querySelector: function (selector) { return selector.indexOf('amount') >= 0 ? battles : wins; }}, {}, {}, {}
];
var root = {querySelectorAll: function () { return cards; }, querySelector: function () { return points; }};
var model = {DriftkingsUI: {name: 'DriftkingsProfileRatings'}, payload: '{}'};
var engine = {
    whenReady: {then: function (fn) { fn(); }},
    on: function (name, fn) { events[name] = fn; },
    off: function (name) { delete events[name]; }
};
var window = {subViews: {ids: function () { return [1]; }, get: function () { return {model: model}; }},
    addEventListener: function () {}, removeEventListener: function () {}};
var context = {window: window, engine: engine, document: {body: {}, querySelector: function () { return root; }},
    viewEnv: {addDataChangedCallback: function () { callbacks++; return 1; }, removeDataChangedCallback: function () { removed++; }},
    setTimeout: function (fn) { jobs.push(fn); return jobs.length; }, clearTimeout: function () {}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../../mod/res/gui/gameface/mods/driftkings/profile_ratings/ratings.js'), 'utf8'), context);
function flush() { while (jobs.length) { jobs.shift()(); } }
function update(data) { model.payload = JSON.stringify(data); events['viewEnv.onDataChanged'](); flush(); }
flush();
update({damage: '#00CC00', battles: '#FF0000', wins: '#CC66CC', rating: '#99CC00'});
assert.strictEqual(damage.style.color, '#00CC00');
assert.strictEqual(battles.style.color, '#FF0000');
assert.strictEqual(wins.style.color, '#CC66CC');
assert.strictEqual(points.style.color, '#99CC00');
update({});
[damage, battles, wins, points].forEach(function (node) { assert.strictEqual(node.style.color, ''); });
update({wins: '#CC66CC'});
window.__dkProfileRatings.dispose();
assert.strictEqual(wins.style.color, '');
assert.strictEqual(callbacks, 1);
assert.strictEqual(removed, 1);
console.log('Native profile Gameface colors: passed');
