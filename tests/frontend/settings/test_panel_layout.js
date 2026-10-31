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

// Minimal measured geometry for HUD elements, including fields outside the screen.
const create = document.createElement.bind(document);
document.createElement = function(tag) {
    const node = create(tag);
    Object.defineProperties(node, {
        offsetLeft: {get(){return parseFloat(this.style.left) || 0;}},
        offsetTop: {get(){return parseFloat(this.style.top) || 0;}},
        offsetWidth: {get(){return parseFloat(this.style.width) || 100;}},
        offsetHeight: {get(){return parseFloat(this.style.height) || 20;}},
        clientWidth: {get(){return 344;}}, clientHeight: {get(){return 194;}}
    });
    return node;
};
const liveHost = create('div');
const preview = DK.hudPreview.create(liveHost, {id:'legacy.MainGun'});
const values = {}, id = DK.minimapPreview.fieldId;
values[id('gameface.scale')] = 10;
values[id('textPosition.x')] = -500;
preview.update(values);
const stage = liveHost.querySelector('.dk-hud-stage');
assert(!/NaN|Infinity/.test(stage.style.transform));
const scale = Number(/scale\(([^)]+)\)/.exec(stage.style.transform)[1]);
assert(scale > 0 && scale <= 344 / 2624, 'zoom fits oversized panels with a margin');
assert(!stage.style.transform.includes('translate'), 'zoom translation uses parent coordinates, not a scaled transform');
assert(Number.isFinite(parseFloat(stage.style.left)));
assert(Number.isFinite(parseFloat(stage.style.top)));
liveHost.querySelector('.dk-segment').fire('click');
assert.strictEqual(stage.style.transform, 'scale(' + Math.min(344/1920,194/1080) + ')');
assert.strictEqual(stage.style.left,'0');assert.strictEqual(stage.style.top,'0');
preview.dispose();
// The screenshot regressions must contain a foreground element, not only a scene image.
for (const [moduleId,template,expected] of [
    ['legacy.FlightTimer','%(flightTime).1fs - %(distance)dm','1.4s - 315m'],
    ['legacy.FlightTimer','{flightTime:.1f}s - {distance:d}m','1.4s - 315m'],
    ['legacy.DispersionTimer','%(timer).1fs - %(percent)d%%','1.8s - 76%']
]) {
    const timer = DK.hudPreview.create(liveHost, {id:moduleId});
    timer.update({[id('enabled')]:true, [id('template')]:template});
    assert.strictEqual(liveHost.querySelector('.is-current').textContent, expected);
    timer.preview(id('x'), 250);
    assert.strictEqual(liveHost.querySelector('.is-current').style.left,'1210rem');
    timer.dispose();
}
DK.app.dispose();
console.log('Panel nested scrolling, disposal, text entities and responsive HUD zoom passed');
