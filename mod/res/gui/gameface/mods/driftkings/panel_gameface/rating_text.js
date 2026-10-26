/* Player ratings: value parsing and Flash text converted to flex text runs. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(); }
    else { root.DKRatingText = factory(); }
}(this, function () {
    'use strict';
    function flag(value) { return !(value === false || value === null || value === undefined || value === '' || value === 0 || value === '0' || value === 'false'); }
    function number(value, fallback) { var n=Number(value); return value === null || value === undefined || !isFinite(n) ? fallback : n; }
    function localImage(value) {
        value=String(value || '').replace(/^img:\/\//,'coui://');
        return /^coui:\/\/gui\/[a-z0-9_./-]+\.(png|dds|webp)$/i.test(value) && value.indexOf('..')<0 ? value : '';
    }
    function color(value) {
        if (typeof value === 'number') { return '#'+('000000'+value.toString(16)).slice(-6); }
        value=String(value || '');
        return /^#[a-f0-9]{6}$/i.test(value) ? value : 'transparent';
    }
    function writeRuns(target,html) {
        if (!html) { return; }
        if (!/[<&]/.test(html)) {
            var run=document.createElement('span'); run.style.flexShrink='0'; run.style.whiteSpace='pre';
            run.textContent=html; target.appendChild(run); return;
        }
        var parsed=document.createElement('div'); parsed.innerHTML=html; copyRuns(parsed,target,{});
    }
    function copyRuns(source, target, inherited) {
        for (var i = 0; i < source.childNodes.length; i++) {
            var child = source.childNodes[i];
            if (child.nodeType === 3) {
                if (inherited.hidden || !child.nodeValue) { continue; }
                var run = document.createElement('span');
                run.style.flexShrink = '0'; run.style.whiteSpace = 'pre';
                Object.keys(inherited).forEach(function (key) { if (key !== 'hidden') { run.style[key] = inherited[key]; } });
                run.textContent = child.nodeValue; target.appendChild(run);
                continue;
            }
            if (child.nodeType !== 1) { continue; }
            var tag = child.tagName.toLowerCase();
            if (/^(script|style|iframe|object)$/.test(tag)) { continue; }
            if (inherited.hidden) { continue; }
            if (tag==='img') {
                var src=localImage(child.getAttribute('src'));
                if (src) {
                    var image=document.createElement('img'); image.src=src; image.style.flexShrink='0';
                    image.style.width=Math.max(0,number(child.getAttribute('width'),22))+'rem';
                    image.style.height=Math.max(0,number(child.getAttribute('height'),22))+'rem';
                    target.appendChild(image);
                }
                continue;
            }
            if (tag==='br') {
                var line=document.createElement('span'); line.style.flexBasis='100%'; line.style.height='0'; target.appendChild(line); continue;
            }
            var style = {};
            Object.keys(inherited).forEach(function (key) { style[key] = inherited[key]; });
            if (tag === 'b') { style.fontWeight = 'bold'; }
            if (tag === 'i') { style.fontStyle = 'italic'; }
            if (tag === 'u') { style.textDecoration = 'underline'; }
            if (tag === 'font') {
                var fontColor = child.getAttribute('color'), size = child.getAttribute('size');
                var face = child.getAttribute('face'), alpha = child.getAttribute('alpha');
                if (/^#[0-9a-f]{6}$/i.test(fontColor)) { style.color = fontColor; }
                if (size === '0') { style.hidden = true; }
                else if (Number(size) >= 8 && Number(size) <= 40) { style.fontSize = Number(size) + 'rem'; }
                // $FieldFont means the native font, not a wider Arial substitute.
                if (face === '$FieldFont') { delete style.fontFamily; }
                else if (face && /^[a-z0-9 _-]+$/i.test(face)) { style.fontFamily = face; }
                if (/^#[0-9a-f]{2}$/i.test(alpha)) { style.opacity = (inherited.opacity === undefined ? 1 : inherited.opacity) * parseInt(alpha.slice(1), 16) / 255; }
            }
            copyRuns(child, target, style);
        }
    }
    return {flag:flag, number:number, localImage:localImage, color:color, writeRuns:writeRuns, copyRuns:copyRuns};
}));
