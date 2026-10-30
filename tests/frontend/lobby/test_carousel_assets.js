'use strict';
var assert = require('assert');
var layout = require('../../../mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_layout.js');
var image = 'data:image/png;base64,iVBORw0KGgo=';
['gui/maps/driftkings/carroucel/battles.png', 'gui/maps/driftkings/carroucel/#53b329.png'].forEach(function (path) {
    var images = {}; images[path] = image;
    assert.strictEqual(layout.localIcon(path, images), image);
    assert.strictEqual(layout.localIcon(path, {}), '');
});
assert.strictEqual(layout.localIcon('mods/Driftkings/Carroucel/../battles.png', {}), '');
console.log('Lowercase carousel icon paths: passed');
