/* A Flash-formatted text at a fixed place on the screen: x/y in interface units from the alignX/alignY
   edge, as in the retired Flash overlay. Python supplies the text, the module's base font, colour,
   alignment and drop shadow; with the battle cursor (Ctrl) an unlocked text can be dragged and the new
   position is sent back. */
(function () {
    'use strict';
    if (window.__dkScreenText) { return; }
    var K = window.__dkMarksKit, F = window.__dkFlashLines;

    function bounded(value, fallback, low, high) { return Math.max(low, Math.min(high, K.number(value, fallback))); }
    function rgba(color, alpha) {
        var value = /^#[0-9a-f]{6}$/i.test(color || '') ? parseInt(color.slice(1), 16) : 0;
        return 'rgba(' + [(value >> 16) & 255, (value >> 8) & 255, value & 255, alpha].join(',') + ')';
    }
    /* Flash DropShadowFilter settings as a CSS text shadow. Like the retired overlay, alpha and strength
       read as 0..1 or 0..100; blur is the larger of blurX/blurY. A strength above 1 repeats the layer,
       a weaker one fades it. */
    function shadow(cfg) {
        if (!cfg || cfg.enabled === false) { return 'none'; }
        var angle = bounded(cfg.angle, 0, 0, 360) * Math.PI / 180, distance = bounded(cfg.distance, 0, 0, 255);
        var alpha = bounded(cfg.alpha, 1, 0, 100), strength = bounded(cfg.strength, 1, 0, 255);
        var blur = Math.max(bounded(cfg.blurX, 2, 0, 255), bounded(cfg.blurY, 2, 0, 255));
        alpha = alpha > 1 ? alpha / 100 : alpha;
        strength = strength > 1 ? strength / 100 : strength;
        if (!alpha || !strength) { return 'none'; }
        var layer = (distance * Math.cos(angle)).toFixed(2) + 'rem ' + (distance * Math.sin(angle)).toFixed(2) + 'rem ' +
            blur + 'rem ' + rgba(cfg.color, Math.round(alpha * Math.min(1, strength) * 1000) / 1000);
        var layers = [], count = Math.max(1, Math.min(4, Math.round(strength)));
        for (var i = 0; i < count; i++) { layers.push(layer); }
        return layers.join(', ');
    }

    window.__dkScreenText = function (feature, owner, modifier) {
        var root = K.node('div', 'dk-screen-text dk-screen-text--' + modifier, document.body);
        // The first child is the drag handle for the shared battle kit: the whole text.
        var content = K.node('div', 'dk-screen-text__content', root);
        var last = '';

        function render(data) {
            var cfg = data.config || {}, style = data.style || {}, html = String(data.text || '');
            var interactive = cfg.draggable === true && cfg.locked === false, base = {fontFamily: 'Warhelios', fontWeight: '400'};
            F.face(style.font, base);
            K.style(root, 'pointerEvents', interactive ? 'auto' : 'none');
            K.style(content, 'cursor', interactive ? 'move' : 'default');
            K.style(root, 'fontFamily', base.fontFamily);
            K.style(root, 'fontWeight', style.bold ? '700' : base.fontWeight);
            K.style(root, 'fontStyle', style.italic ? 'italic' : 'normal');
            K.style(root, 'fontSize', bounded(style.size, 16, 8, 40) + 'rem');
            K.style(root, 'color', /^#[0-9a-f]{6}$/i.test(style.color || '') ? style.color : '#FFFFFF');
            K.style(root, 'opacity', String(bounded(cfg.alpha, 1, 0, 1)));
            K.style(root, 'textShadow', shadow(cfg.shadow));
            K.style(content, 'alignItems', style.align === 'center' ? 'center' : style.align === 'right' ? 'flex-end' : 'flex-start');
            if (html !== last) {
                last = html;
                while (content.firstChild) { content.removeChild(content.firstChild); }
                F.lines(html, content, 'dk-screen-text__line', {faces: true});
            }
        }
        function position(element, cfg) {
            K.position(element, cfg);
            // A new text can still measure empty right after display:block.
            requestAnimationFrame(function () { K.position(element, cfg); });
        }
        return K.connect(feature, owner, root, render, position, K.savedPosition);
    };
}());
