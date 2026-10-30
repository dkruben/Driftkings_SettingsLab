/* Presentation only: Python supplies health, colour, text, position and visibility. */
(function () {
    'use strict';
    var K = window.__dkMarksKit;
    var root = K.node('div', 'dk-health', document.body);
    // The shared renderer's first child is the drag handle for the whole bar.
    var bar = window.__dkHealthBar.create(root);

    function render(data) {
        var cfg = data.config || {};
        var interactive = cfg.draggable === true && cfg.locked === false;
        K.style(root, 'transform', 'scale(' + Math.max(0.25, Math.min(4, K.number(cfg.scale, 1))) + ')');
        K.style(root, 'pointerEvents', interactive ? 'auto' : 'none');
        K.style(root.firstChild, 'cursor', interactive ? 'move' : 'default');
        bar.render(data);
    }

    function position(element, cfg) {
        K.position(element, cfg);
        // Right after display:block the box can still measure empty; place it again once laid out.
        requestAnimationFrame(function () { K.position(element, cfg); });
    }

    K.connect('DriftkingsOwnHealth', '__dkOwnHealth', root, render, position, K.savedPosition);
}());
