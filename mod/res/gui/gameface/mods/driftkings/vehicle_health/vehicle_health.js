/* Presentation only: Python supplies health, colour, text, position and visibility. */
(function () {
    'use strict';
    var K = window.__dkMarksKit;
    var root = K.node('div', 'dk-health', document.body);
    // The first child is the drag handle for the shared battle kit: the whole bar.
    var content = K.node('div', 'dk-health__content', root);
    var track = K.node('div', 'dk-health__track', content);
    var fill = K.node('div', 'dk-health__fill', track);
    K.node('div', 'dk-health__stripes', fill);
    K.node('div', 'dk-health__gloss', fill);
    var frame = K.node('img', 'dk-health__frame', content);
    frame.src = 'coui://gui/gameface/mods/driftkings/vehicle_health/frame.png';
    frame.alt = '';
    var label = K.node('div', 'dk-health__text', content);

    function render(data) {
        var cfg = data.config || {};
        var percent = Math.max(0, Math.min(1, K.number(data.percent, 0)));
        var interactive = cfg.draggable === true && cfg.locked === false;
        K.style(root, 'transform', 'scale(' + Math.max(0.25, Math.min(4, K.number(cfg.scale, 1))) + ')');
        K.style(root, 'pointerEvents', interactive ? 'auto' : 'none');
        K.style(content, 'cursor', interactive ? 'move' : 'default');
        K.style(fill, 'width', percent * 100 + '%');
        K.style(fill, 'backgroundColor', data.color || '#3FC23A');
        K.text(label, data.text);
    }

    function position(element, cfg) {
        K.position(element, cfg);
        // Right after display:block the box can still measure empty; place it again once laid out.
        requestAnimationFrame(function () { K.position(element, cfg); });
    }

    K.connect('DriftkingsOwnHealth', '__dkOwnHealth', root, render, position, K.savedPosition);
}());
