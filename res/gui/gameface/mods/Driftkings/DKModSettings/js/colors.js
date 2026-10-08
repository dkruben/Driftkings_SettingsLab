/* Pure color and alpha boundaries. No model or DOM dependencies. */
(function () {
    'use strict';
    var DK = window.DK = window.DK || {};
    function parseColor(value) {
        var m = /^(#|0x)?([0-9a-f]{6})$/i.exec(String(value).trim());
        return m ? {hex: '#' + m[2].toUpperCase(), prefix: m[1] || ''} : null;
    }
    function normalizeColor(value) { var c = parseColor(value); return c ? c.hex : null; }
    function formatColor(value, original) {
        var c = parseColor(value), previous = parseColor(original);
        return c ? (previous ? previous.prefix : '#') + c.hex.slice(1) : null;
    }
    function hexToRgb(value) {
        var c = parseColor(value); if (!c) { return null; }
        var n = parseInt(c.hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }
    function rgbToHex(rgb) {
        if (!rgb || rgb.length !== 3 || rgb.some(function (n) { return typeof n !== 'number' || !isFinite(n) || n < 0 || n > 255; })) { return null; }
        return '#' + rgb.map(function (n) { var s = Math.round(n).toString(16).toUpperCase(); return s.length < 2 ? '0' + s : s; }).join('');
    }
    function limit(scale) {
        if (scale === 'normalized') { return 1; }
        if (scale === 'byte') { return 255; }
        if (!scale || scale === 'percent') { return 100; }
        throw new Error('Unknown alpha scale');
    }
    function normalizeAlpha(value, scale) {
        if (typeof value !== 'number' || !isFinite(value)) { return null; }
        return Math.max(0, Math.min(limit(scale), value));
    }
    function alphaToUi(value, scale) { var n = normalizeAlpha(value, scale); return n === null ? null : n * 100 / limit(scale); }
    function alphaFromUi(value, scale) { var n = normalizeAlpha(value, 'percent'); return n === null ? null : scale === 'byte' ? Math.round(n * 255 / 100) : n * limit(scale) / 100; }
    function spectrum(x, y) {
        var h = Math.max(0, Math.min(1, y)) * 6, i = Math.floor(h) % 6, f = h - Math.floor(h);
        var rgb = [[1,f,0],[1-f,1,0],[0,1,f],[0,1-f,1],[f,0,1],[1,0,1-f]][i];
        x = Math.max(0, Math.min(1, x));
        return rgbToHex(rgb.map(function (n) { return 255 * (x <= 0.5 ? n * x * 2 : n + (1-n) * (x-0.5)*2); }));
    }
    function spectrumPosition(value) {
        var rgb = hexToRgb(value); if (!rgb) { return {x:0.5,y:0}; }
        rgb = rgb.map(function (n) { return n/255; });
        var hi=Math.max.apply(Math,rgb), lo=Math.min.apply(Math,rgb), delta=hi-lo, h=0;
        if(delta){ h=hi===rgb[0]?(rgb[1]-rgb[2])/delta:hi===rgb[1]?2+(rgb[2]-rgb[0])/delta:4+(rgb[0]-rgb[1])/delta; h=(h+6)%6; }
        return {x:hi+lo>1 ? (1+lo)/2 : hi/2,y:h/6};
    }
    DK.colors = {parseColor: parseColor, formatColor: formatColor, normalizeColor: normalizeColor,
        hexToRgb: hexToRgb, rgbToHex: rgbToHex, normalizeAlpha: normalizeAlpha,
        alphaToUi: alphaToUi, alphaFromUi: alphaFromUi, spectrum: spectrum, spectrumPosition: spectrumPosition};
}());
