/* A Flash-formatted text placed at the crosshair plus an offset in interface units.
   Python supplies the text, the crosshair position (fraction of the screen) and the offset;
   with the battle cursor (Ctrl) the text can be dragged and the new offset is sent back. */
(function () {
    'use strict';
    if (window.__dkReticleText) { return; }
    var K = window.__dkMarksKit;

    function unit() { return parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 1; }
    // Point of the text box that sits on the offset: its left edge, centre or right edge.
    function anchorShift(align, width) { return align === 'center' ? width / 2 : align === 'right' ? width : 0; }

    window.__dkReticleText = function (feature, owner, modifier) {
        var root = K.node('div', 'dk-reticle-text dk-reticle-text--' + modifier, document.body);
        // The first child is the drag handle for the shared battle kit: the whole text.
        var content = K.node('div', 'dk-reticle-text__content', root);
        var last = '', drag = null;

        function inside(target) {
            while (target) { if (target === root) { return true; } target = target.parentNode; }
            return false;
        }
        // These texts change every frame; keep the dragged position until the saved offset returns.
        function down(event) {
            if (event.button === 0 && root.style.pointerEvents === 'auto' && inside(event.target)) {
                drag = {x: (root.__dkCfg || {}).x, y: (root.__dkCfg || {}).y, active: true, until: 0};
            }
        }
        function up() { if (drag && drag.active) { drag.active = false; drag.until = Date.now() + 1500; } }
        function held(cfg) {
            if (!drag) { return false; }
            if (drag.active || (Date.now() < drag.until && cfg.x === drag.x && cfg.y === drag.y)) { return true; }
            drag = null;
            return false;
        }

        function render(data) {
            var cfg = data.config || {}, html = String(data.text || '');
            var interactive = cfg.draggable === true && cfg.locked === false;
            K.style(root, 'pointerEvents', interactive ? 'auto' : 'none');
            K.style(content, 'cursor', interactive ? 'move' : 'default');
            K.style(content, 'alignItems', cfg.align === 'center' ? 'center' : cfg.align === 'right' ? 'flex-end' : 'flex-start');
            if (html !== last) {
                last = html;
                while (content.firstChild) { content.removeChild(content.firstChild); }
                window.__dkFlashLines.lines(html, content, 'dk-reticle-text__line');
            }
            root.__dk = {x: K.number(data.anchorX, .5), y: K.number(data.anchorY, .5)};
            root.__dkCfg = cfg;
        }
        function place(element, cfg) {
            if (held(cfg)) { return; }
            var anchor = element.__dk || {x: .5, y: .5}, px = unit(), box = element.getBoundingClientRect();
            var left = anchor.x * window.innerWidth + K.number(cfg.x, 0) * px - anchorShift(cfg.align, box.width);
            var top = anchor.y * window.innerHeight + K.number(cfg.y, 0) * px;
            K.style(element, 'left', Math.round(left) + 'px');
            K.style(element, 'top', Math.round(top) + 'px');
        }
        function position(element, cfg) {
            place(element, cfg);
            // A new text can still measure empty right after display:block.
            requestAnimationFrame(function () { place(element, cfg); });
        }
        function saved(element, cfg) {
            var anchor = element.__dk || {x: .5, y: .5}, px = unit(), box = element.getBoundingClientRect();
            var left = parseFloat(element.style.left) + anchorShift(cfg.align, box.width);
            return {x: Math.round((left - anchor.x * window.innerWidth) / px),
                y: Math.round((parseFloat(element.style.top) - anchor.y * window.innerHeight) / px)};
        }
        document.addEventListener('mousedown', down, true);
        document.addEventListener('mouseup', up, true);
        var kit = K.connect(feature, owner, root, render, position, saved), dispose = kit.dispose;
        kit.dispose = function () {
            document.removeEventListener('mousedown', down, true);
            document.removeEventListener('mouseup', up, true);
            dispose();
        };
        return kit;
    };
}());
