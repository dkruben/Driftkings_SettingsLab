'use strict';
var assert = require('assert');
var layout = require('../../mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_layout.js');
var selectors = [], nodes = [];
global.getComputedStyle = function () { return {position:'relative', transform:'none'}; };
var card = {clientWidth:200, clientHeight:100,
    querySelectorAll:function (selector) {
        selectors.push(selector);
        var node = {style:{visibility:'visible', opacity:'1'}};
        nodes.push(node); return [node];
    },
    appendChild:function (node) { node.parentNode=this; },
    insertBefore:function (node) { node.parentNode=this; },
    removeChild:function (node) { node.parentNode=null; }};
var document = {createElement:function () { return {style:{}, appendChild:function () {}}; }};
var fields = {};
['flag','tankIcon','tankName','info','infoImg','rentInfo','crystalsIcon','coreBorder','xp'].forEach(function (key) {
    fields[key]={enabled:false,alpha:100,dx:0,dy:0,scale:1};
});
var cleanup = layout.mount(card,{width:200,height:100,fields:fields,extraFields:[]},document,{});
nodes.forEach(function (node) {
    assert.strictEqual(node.style.visibility,'hidden');
    assert.strictEqual(node.style.opacity,'0','Hidden native parents must also suppress visible descendants');
});
assert(selectors.some(function (s) { return s.indexOf('Overlay_alertText_')!==-1; }));
assert(selectors.some(function (s) { return s.indexOf('Bonuses_rent_')!==-1; }));
assert(selectors.some(function (s) { return s.indexOf('Bonuses_bonus_')!==-1; }));
cleanup();
nodes.forEach(function (node) { assert.strictEqual(node.style.opacity,'1'); assert.strictEqual(node.style.visibility,'visible'); });
delete global.getComputedStyle;
console.log('Native carousel field visibility and restoration: passed');

// Explicit-width labels align their contents as well as their anchor box.
var layers = [];
function element() { return {style:{}, children:[], appendChild:function(child) { this.children.push(child); child.parentNode=this; }}; }
var previewDocument = {createElement:element, createTextNode:function(text) { return {text:text}; }};
var previewCard = {clientWidth:210,clientHeight:140,querySelectorAll:function() { return []; },
    appendChild:function(child) { layers.push(child); child.parentNode=this; },
    insertBefore:function(child) { layers.push(child); child.parentNode=this; }};
global.getComputedStyle = function() { return {position:'relative'}; };
layout.mount(previewCard,{width:210,height:140,fields:{},extraFields:['left','center','right'].map(function(align) {
    return {layer:'top',align:align,width:80,height:20,x:100,y:10,fontSize:16,alpha:100,
        format:"<font face='mono'>1234</font>",shadow:{enabled:false}};
})},previewDocument,{});
var aligned = layers[1].children;
assert.deepStrictEqual(aligned.map(function(n) { return n.style.justifyContent; }),['flex-start','center','flex-end']);
assert.deepStrictEqual(aligned.map(function(n) { return n.style.textAlign; }),['left','center','right']);
assert.strictEqual(aligned[2].style.transform,'translateX(-100%)');
assert.strictEqual(aligned[2].children[0].children[0].style.fontFamily,'monospace');
var nativeFont=element();
layout.richText(nativeFont,"<font face='$FieldFont'>native</font>",previewDocument,{},true);
assert.strictEqual(nativeFont.children[0].style.fontFamily,'inherit');
delete global.getComputedStyle;
console.log('Carousel fixed-width text alignment and font aliases: passed');
