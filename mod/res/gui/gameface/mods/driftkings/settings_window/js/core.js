/* DK Settings — núcleo: elementos, classes, eventos, textos e formatação de valores.
   ES5 para o Gameface: sem classList, sem let/const, sem arrow functions. */
(function () {
    'use strict';
    var DK = window.DK = {};

    /* Elements ------------------------------------------------------------ */
    // h('div.a.b', {title: 'x'}, [children or text], parent)
    function h(spec, attrs, children, parent) {
        var parts = spec.split('.'), node = document.createElement(parts[0] || 'div');
        if (parts.length > 1) { node.className = parts.slice(1).join(' '); }
        if (attrs) {
            for (var key in attrs) {
                if (!Object.prototype.hasOwnProperty.call(attrs, key) || attrs[key] === undefined || attrs[key] === null) { continue; }
                if (key === 'text') { node.textContent = String(attrs[key]); }
                else if (key === 'style') { for (var s in attrs.style) { if (Object.prototype.hasOwnProperty.call(attrs.style, s)) { node.style[s] = attrs.style[s]; } } }
                else if (key.indexOf('on') === 0) { node.addEventListener(key.slice(2), attrs[key]); }
                else if (key === 'tabIndex' || key === 'type' || key === 'value' || key === 'maxLength' || key === 'placeholder' || key === 'src' || key === 'title' || key === 'disabled' || key === 'readOnly') { node[key] = attrs[key]; }
                else { node.setAttribute(key, attrs[key]); }
            }
        }
        if (children !== undefined && children !== null) { append(node, children); }
        if (parent) { parent.appendChild(node); }
        if (parts[0] === 'button' && !node.type) { node.type = 'button'; }
        return node;
    }
    function append(node, children) {
        if (Object.prototype.toString.call(children) === '[object Array]') {
            for (var i = 0; i < children.length; i++) { if (children[i] !== null && children[i] !== undefined) { append(node, children[i]); } }
        } else if (typeof children === 'string' || typeof children === 'number') {
            node.appendChild(document.createTextNode(String(children)));
        } else { node.appendChild(children); }
    }
    function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }
    function remove(node) { if (node && node.parentNode) { node.parentNode.removeChild(node); } }
    function has(node, name) { return (' ' + (node.className || '') + ' ').indexOf(' ' + name + ' ') >= 0; }
    function toggle(node, name, on) {
        var parts = String(node.className || '').split(' '), result = [];
        for (var i = 0; i < parts.length; i++) { if (parts[i] && parts[i] !== name) { result.push(parts[i]); } }
        if (on) { result.push(name); }
        var next = result.join(' ');
        if (next !== node.className) { node.className = next; }
    }
    function show(node, visible) { node.style.display = visible ? '' : 'none'; }
    function inside(node, container) {
        while (node) { if (node === container) { return true; } node = node.parentNode; }
        return false;
    }
    // Stops the event here and tells the client it was handled, so the hangar does not react.
    function stop(event) {
        if (!event) { return; }
        if (event.preventDefault) { event.preventDefault(); }
        if (event.stopPropagation) { event.stopPropagation(); }
        if (typeof viewEnv !== 'undefined' && viewEnv.setEventHandled) { viewEnv.setEventHandled(); }
    }
    function focus(node) { if (node && !node.disabled && node.focus) { node.focus(); } }
    // Gameface reports a positive deltaY for wheel-up; browsers report the opposite.
    // The browser preview sets DK_BROWSER_WHEEL. Returns +1 for "up", -1 for "down", 0 for none.
    function wheel(event) {
        var delta = Number(event.deltaY);
        if (isFinite(delta) && delta !== 0) {
            if (window.DK_BROWSER_WHEEL) { delta = -delta; }
            return delta > 0 ? 1 : -1;
        }
        // Legacy wheelDelta is positive for wheel-up everywhere.
        var legacy = Number(event.wheelDelta);
        return legacy > 0 ? 1 : legacy < 0 ? -1 : 0;
    }

    /* Data ---------------------------------------------------------------- */
    function copy(value) { return value === undefined ? undefined : JSON.parse(JSON.stringify(value)); }
    function same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
    function contains(list, item) { return !!list && list.indexOf(item) >= 0; }
    function isArray(value) { return Object.prototype.toString.call(value) === '[object Array]'; }
    function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }
    function decimals(step) { var text = String(step), dot = text.indexOf('.'); return dot < 0 ? 0 : text.length - dot - 1; }
    function snap(value, min, max, step) {
        var result = min + Math.round((value - min) / step) * step;
        return parseFloat(clamp(result, min, max).toFixed(decimals(step)));
    }
    function hex(value) { return DK.colors.normalizeColor(value); }
    function rgb(color) { var n = parseInt(color.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
    function rgba(color, alpha) { return 'rgba(' + rgb(color).concat([alpha]).join(',') + ')'; }
    function mix(color, amount) {
        return 'rgb(' + rgb(color).map(function (c) { return Math.round(amount >= 0 ? c + (255 - c) * amount : c * (1 + amount)); }).join(',') + ')';
    }
    // JSON text in the format Python's json.dumps writes by default (", " and ": ", ASCII escapes),
    // so an untouched marker document stays byte-identical after a round trip.
    function pyJson(value, ascii) {
        if (value === null || typeof value === 'boolean') { return String(value === null ? 'null' : value); }
        if (typeof value === 'number') { return isFinite(value) ? String(value) : 'null'; }
        if (typeof value === 'string') {
            var text = JSON.stringify(value);
            return ascii ? text.replace(/[\u007f-￿]/g, function (c) { return '\\u' + ('000' + c.charCodeAt(0).toString(16)).slice(-4); }) : text;
        }
        if (isArray(value)) { return '[' + value.map(function (item) { return pyJson(item, ascii); }).join(', ') + ']'; }
        var keys = Object.keys(value);
        return '{' + keys.map(function (key) { return pyJson(key, ascii) + ': ' + pyJson(value[key], ascii); }).join(', ') + '}';
    }

    /* Text ---------------------------------------------------------------- */
    // Strings the game catalog does not define yet; a catalog key with the same name wins.
    var catalog = {};
    function setCatalog(labels) { catalog=labels||{}; }
    function t(key,fallback) {
        var value=catalog[key];
        return value===undefined||value===null?(fallback===undefined?key:fallback):value;
    }
    function tf(key, values) {
        return String(t(key)).replace(/\{(\w+)\}/g, function (all, name) { return values[name] === undefined ? all : values[name]; });
    }

    DK.h = h; DK.clear = clear; DK.remove = remove; DK.has = has; DK.toggle = toggle; DK.show = show;
    DK.inside = inside; DK.stop = stop; DK.focus = focus; DK.wheel = wheel;
    DK.copy = copy; DK.same = same; DK.contains = contains; DK.isArray = isArray; DK.clamp = clamp; DK.snap = snap;
    DK.hex = hex; DK.rgb = rgb; DK.rgba = rgba; DK.mix = mix; DK.pyJson = pyJson;
    DK.t = t; DK.tf = tf; DK.setCatalog = setCatalog; DK.catalog = function () { return catalog; };
}());
