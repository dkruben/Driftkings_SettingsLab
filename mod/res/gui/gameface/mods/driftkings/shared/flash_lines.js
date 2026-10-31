/* The Flash subset of the battle text templates (font colour/size, b, i, u, br, p) as flat runs, one row
   per line: Gameface lays every element out as a flex box, so nested inline markup would stack. */
(function () {
    'use strict';
    if (window.__dkFlashLines) { return; }
    var K = window.__dkMarksKit;
    // Flash field fonts map to the client font; other faces are kept only when the view loads them.
    var NATIVE = {'$FieldFont': '400', '$TitleFont': '700'};
    var LOADED = /^(Warhelios|dkm|DriftkingsFont|VehicleType|vtype|DynamicDefault|dynamic|DynamicOutline|dynamic2|mono|ZurichCondMono)$/;

    function face(name, style) {
        if (NATIVE.hasOwnProperty(name)) { style.fontFamily = 'Warhelios'; style.fontWeight = NATIVE[name]; }
        else if (LOADED.test(name || '')) { style.fontFamily = name; }
    }

    /* options.faces also applies <font face> and <font alpha>, as the screen texts did in Flash; the
       crosshair texts always used the view font. */
    function lines(html, target, lineClass, options) {
        options = options || {};
        var parsed = document.createElement('div'), line = K.node('div', lineClass, target);
        parsed.innerHTML = html;
        function walk(source, style) {
            for (var i = 0; i < source.childNodes.length; i++) {
                var child = source.childNodes[i];
                if (child.nodeType === 3) {
                    if (!child.nodeValue) { continue; }
                    var run = K.node('span', '', line, child.nodeValue);
                    run.style.whiteSpace = 'pre'; run.style.flexShrink = '0';
                    for (var key in style) { if (style.hasOwnProperty(key)) { run.style[key] = style[key]; } }
                    continue;
                }
                if (child.nodeType !== 1) { continue; }
                var tag = child.tagName.toLowerCase();
                if (tag === 'br') { line = K.node('div', lineClass, target); continue; }
                if (/^(script|style|iframe|object|img)$/.test(tag)) { continue; }
                var next = {};
                for (var name in style) { if (style.hasOwnProperty(name)) { next[name] = style[name]; } }
                if (tag === 'b') { next.fontWeight = 'bold'; }
                if (tag === 'i') { next.fontStyle = 'italic'; }
                if (tag === 'u') { next.textDecoration = 'underline'; }
                if (tag === 'font') {
                    var color = child.getAttribute('color'), size = Number(child.getAttribute('size'));
                    if (/^#[0-9a-f]{6}$/i.test(color || '')) { next.color = color; }
                    if (size >= 8 && size <= 40) { next.fontSize = size + 'rem'; }
                    if (options.faces) {
                        face(child.getAttribute('face'), next);
                        var alpha = child.getAttribute('alpha');
                        if (/^#[0-9a-f]{2}$/i.test(alpha || '')) { next.opacity = String(parseInt(alpha.slice(1), 16) / 255); }
                    }
                }
                walk(child, next);
            }
        }
        walk(parsed, {});
    }

    window.__dkFlashLines = {lines: lines, face: face};
}());
