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

    // Detached markup still loads <img>, so event attributes are disabled before innerHTML parses it.
    function inert(html) {
        return String(html).replace(/<(?:[^>"']|"[^"]*"|'[^']*')*>/g, function (tag) {
            return tag.replace(/(\s)on[a-z]+\s*=/gi, '$1data-dk-off=');
        });
    }

    /* options.faces also applies <font face> and <font alpha>, as the screen texts did in Flash; the
       crosshair texts always used the view font. */
    function lines(html, target, lineClass, options) {
        options = options || {};
        var parsed = document.createElement('div'), line = K.node('div', lineClass, target), cell = null, column = 0;
        // <br>, <tab> e <img> do Flash viram spans fechados: o parser do Gameface perde os atributos do <br>
        // e alguns <br> (depois de uma imagem, dentro de <p>), também nos textos da mira.
        html = inert(html).replace(/<br\s*\/?>/gi, "<span data-dk-br='1'></span>");
        parsed.innerHTML = options.rich ? html.replace(/<tab\s*\/?>/gi, "<span data-dk-tab='1'></span>")
            .replace(/<img\b([^>]*?)\s*\/?>/gi, "<span data-dk-img='1'$1></span>") : html;
        function newLine() { line = K.node('div', lineClass, target); cell = null; column = 0; }
        function lineStyle(style) {
            if (style.lineLeading !== undefined) { line.style.marginBottom = style.lineLeading; }
            if (style.lineAlign) { line.style.justifyContent = style.lineAlign; }
        }
        function walk(source, style) {
            for (var i = 0; i < source.childNodes.length; i++) {
                var child = source.childNodes[i];
                if (child.nodeType === 3) {
                    if (!child.nodeValue) { continue; }
                    var parts = options.rich ? child.nodeValue.replace(/\r\n?/g, '\n').split('\n') : [child.nodeValue];
                    for (var part = 0; part < parts.length; part++) {
                        if (part) { newLine(); }
                        lineStyle(style);
                        var run = K.node('span', '', cell || line, parts[part]);
                        run.style.whiteSpace = 'pre'; run.style.flexShrink = '0';
                        for (var key in style) {
                            if (style.hasOwnProperty(key) && key !== 'lineLeading' && key !== 'lineAlign' && key !== 'tabStops') { run.style[key] = style[key]; }
                        }
                    }
                    continue;
                }
                if (child.nodeType !== 1) { continue; }
                var tag = child.tagName.toLowerCase();
                if (tag === 'br' || (tag === 'span' && child.getAttribute('data-dk-br') === '1')) { newLine(); continue; }
                if (tag === 'span' && child.getAttribute('data-dk-tab') === '1') {
                    var stops = style.tabStops || [];
                    if (stops.length > column) {
                        if (!cell) {
                            cell = K.node('div', '', null);
                            while (line.firstChild) { cell.appendChild(line.firstChild); }
                            line.appendChild(cell);
                        }
                        // Largura fixa como no Flash; flexDirection ou minWidth nas células empilham a linha no Gameface.
                        cell.style.display = 'flex'; cell.style.alignItems = 'baseline'; cell.style.flexShrink = '0';
                        cell.style.width = Math.max(0, stops[column] - (column ? stops[column - 1] : 0)) + 'rem';
                        column++;
                        cell = K.node('div', '', line); cell.style.display = 'flex'; cell.style.alignItems = 'baseline';
                    } else { K.node('span', '', cell || line, '\t').style.whiteSpace = 'pre'; }
                    continue;
                }
                if (tag === 'span' && child.getAttribute('data-dk-img') === '1') {
                    if (!options.images) { continue; }
                    var src = options.images(child.getAttribute('src'));
                    if (src) {
                        var image = K.node('img', '', cell || line);
                        image.src = src; image.style.flexShrink = '0';
                        ['width', 'height'].forEach(function (key) {
                            var value = Number(child.getAttribute(key));
                            if (value > 0 && value <= 2048) { image.style[key] = value + 'rem'; }
                        });
                    }
                    continue;
                }
                if (/^(script|style|iframe|object|img)$/.test(tag)) { continue; }
                var next = {};
                for (var name in style) { if (style.hasOwnProperty(name)) { next[name] = style[name]; } }
                if (options.rich && tag === 'textformat') {
                    var leading = Number(child.getAttribute('leading'));
                    if (child.getAttribute('leading') !== null && isFinite(leading)) { next.lineLeading = Math.max(0, leading) + 'rem'; }
                    var tabs = child.getAttribute('tabstops');
                    if (/^\[\s*\d+(\s*,\s*\d+)*\s*\]$/.test(tabs || '')) {
                        next.tabStops = tabs.slice(1, -1).split(',').map(Number);
                    }
                }
                if (options.rich && tag === 'p') {
                    if (line.childNodes.length) { newLine(); }
                    var align = child.getAttribute('align');
                    next.lineAlign = align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start';
                }
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
                if (options.rich && tag === 'p' && child.nextSibling) { newLine(); }
            }
        }
        walk(parsed, options.rich ? {lineLeading: Math.max(0, Number(options.leading) || 0) + 'rem'} : {});
    }

    window.__dkFlashLines = {lines: lines, face: face};
}());
