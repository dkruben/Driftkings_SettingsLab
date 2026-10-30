'use strict';
var assert = require('assert');
var layout = require('../../../mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_layout.js');
var image = 'data:image/png;base64,iVBORw0KGgo=';
['gui/maps/driftkings/carroucel/mark_0.png', 'gui/maps/driftkings/carroucel/custom_icon.png'].forEach(function (path) {
    var images = {}; images[path] = image;
    assert.strictEqual(layout.localIcon(path, images), image);
    assert.strictEqual(layout.localIcon(path, {}), '');
});
['gui/maps/driftkings/carroucel/battles.svg','gui/maps/driftkings/carroucel/#53b329.svg'].forEach(function(path){
    var expected='coui://'+path.replace(/#/g,'%23');
    assert.strictEqual(layout.localIcon(path,{}),expected);
    assert.strictEqual(layout.localIcon('coui://'+path,{}),expected);
    assert.strictEqual(layout.localIcon('img://'+path,{}),expected);
});
var invalid={'gui/maps/driftkings/carroucel/mark_0.png':'data:image/svg+xml;base64,PHN2Zy8+'};
assert.strictEqual(layout.localIcon('gui/maps/driftkings/carroucel/mark_0.png',invalid),'');
assert.strictEqual(layout.localIcon('gui/maps/driftkings/carroucel/../battles.svg',{}),'');
assert.strictEqual(layout.localIcon('data:image/svg+xml;base64,PHN2Zy8+',{}),'');
assert.strictEqual(layout.localIcon('mods/Driftkings/Carroucel/../mark_0.png', {}), '');
console.log('Lowercase carousel icon paths: passed');
