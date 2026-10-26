/* Render the supported Flash text subset without copying arbitrary attributes. */
(function () {
    'use strict';

    function copy(source, target, options) {
        options = options || {};
        for (var i = 0; i < source.childNodes.length; i++) {
            var child = source.childNodes[i];
            if (child.nodeType === 3) {
                target.appendChild(document.createTextNode(child.nodeValue));
                continue;
            }
            if (child.nodeType !== 1) { continue; }
            var tag = child.tagName.toLowerCase();
            if (tag === 'script' || tag === 'style' || tag === 'iframe') { continue; }
            var dest = document.createElement(/^(b|i|u|br|p)$/.test(tag) ? tag : 'span');
            if (tag === 'font') {
                var color = child.getAttribute('color');
                var rawSize = child.getAttribute('size'), size = Number(rawSize);
                if (options.fontFamily) {
                    var face = child.getAttribute('face');
                    // Views without the game's fonts (the settings window) pass the font they load.
                    if (face === '$FieldFont') { dest.style.fontFamily = options.fieldFont || 'Arial'; }
                    else if (face && /^[a-z0-9 _-]+$/i.test(face)) { dest.style.fontFamily = face; }
                }
                if (options.fontAlpha) {
                    var alpha = child.getAttribute('alpha');
                    if (/^#[0-9a-f]{2}$/i.test(alpha)) { dest.style.opacity = parseInt(alpha.slice(1), 16) / 255; }
                }
                if (/^#[0-9a-f]{6}$/i.test(color)) { dest.style.color = color; }
                if (options.hideZeroSize && rawSize === '0') { dest.style.display = 'none'; }
                else if (size >= 8 && size <= 40) { dest.style.fontSize = size + (options.sizeUnit === 'rem' ? 'rem' : 'px'); }
            }
            copy(child, dest, options);
            target.appendChild(dest);
        }
    }

    window.DriftkingsFlashText = {copy: copy};
}());
