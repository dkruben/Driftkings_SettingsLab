/* Nested scrolling and HUD sizing regressions; geometry is explicit, not browser layout. */
const assert = require('assert');
const {createEnvironment} = require('../../support/frontend/dom_fixture');
const env = createEnvironment(), {DK, document} = env;
const host = document.createElement('div'), viewport = document.createElement('div');
host.appendChild(viewport);
viewport.clientHeight = 100; viewport.scrollHeight = 500;
const scroll = DK.layer.scroller(viewport, host);
let stopped = false;
function wheel(node, delta) {
    stopped = false;
    node.fire('wheel', {wheelDelta: delta, preventDefault() { stopped = true; }});
}
viewport.scrollTop = 400; wheel(viewport, -120);
assert(!stopped, 'at the bottom, the parent must receive wheel-down');
viewport.scrollTop = 0; wheel(viewport, 120);
assert(!stopped, 'at the top, the parent must receive wheel-up');
wheel(viewport, -120); assert(stopped); assert.strictEqual(viewport.scrollTop, 80);
viewport.scrollHeight = 900; scroll.to(800);
assert.strictEqual(viewport.scrollTop, 800, 'newly expanded content remains reachable');
scroll.dispose();
assert.strictEqual(viewport.listeners.wheel.length, 0);
assert.strictEqual(viewport.listeners.scroll.length, 0);
const control = DK.controls.create({id:'text', type:'textarea', label:'Text'}, {commit(){}, preview(){}});
const area = control.node.querySelector('textarea');
area.clientHeight = 100; area.scrollHeight = 300; area.scrollTop = 200;
wheel(area, -120); assert(!stopped, 'textarea boundaries also allow the page to scroll');
wheel(area, 120); assert(stopped); assert.strictEqual(area.scrollTop, 140);
control.dispose();

DK.app.dispose();
console.log('Panel nested scrolling, disposal and text entities passed');
