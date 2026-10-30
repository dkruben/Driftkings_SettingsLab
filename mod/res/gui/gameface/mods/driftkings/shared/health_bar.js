/* One renderer and geometry for the battle bar and its settings preview. ES5. */
(function () {
    'use strict';
    var BASE = 'coui://gui/gameface/mods/driftkings/vehicle_health/assets/';
    // New frames retain their original transparent canvas; the image viewport crops it in CSS.
    var STYLES = [
        {name: 'classic', file: 'frame.png', width: 480, height: 78, canvas: [960, 156], crop: [0, 156], slot: [189.888, 74.9736, 668.256, 38.5788]},
        {name: 'bastion', file: 'bastion.png', width: 480, height: 110, canvas: [1536, 1024], crop: [352, 352], slot: [279, 469, 1090, 109]},
        {name: 'vanguard', file: 'vanguard.png', width: 480, height: 120, canvas: [1536, 1024], crop: [288, 384], slot: [253, 405, 1167, 174]},
        {name: 'ion', file: 'ion.png', width: 480, height: 94, canvas: [1536, 1024], crop: [370, 300.8], slot: [273, 461, 1074, 123]}
    ];
    function preset(value) { return typeof value === 'number' && value === Math.floor(value) && STYLES[value] ? STYLES[value] : STYLES[0]; }
    function node(tag, name, parent) {
        var result = document.createElement(tag);
        result.className = name;
        parent.appendChild(result);
        return result;
    }
    function create(root) {
        var content = node('div', 'dk-health__content', root);
        var track = node('div', 'dk-health__track', content);
        var fill = node('div', 'dk-health__fill', track);
        node('div', 'dk-health__stripes', fill);
        node('div', 'dk-health__gloss', fill);
        var imageBox = node('div', 'dk-health__image', content);
        var frame = node('img', 'dk-health__frame', imageBox);
        frame.alt = '';
        var label = node('div', 'dk-health__text', content);
        var previous = null;
        function layout(skin) {
            if (skin === previous) { return; }
            previous = skin;
            root.style.width = skin.width + 'rem';
            root.style.height = skin.height + 'rem';
            root.setAttribute('data-health-style', skin.name);
            var area = {left: skin.slot[0] / skin.canvas[0] * 100 + '%',
                top: (skin.slot[1] - skin.crop[0]) / skin.crop[1] * 100 + '%',
                width: skin.slot[2] / skin.canvas[0] * 100 + '%',
                height: skin.slot[3] / skin.crop[1] * 100 + '%'};
            [track, label].forEach(function (element) {
                Object.keys(area).forEach(function (key) { element.style[key] = area[key]; });
            });
            frame.src = BASE + skin.file;
            frame.style.top = -skin.crop[0] / skin.crop[1] * 100 + '%';
            frame.style.height = skin.canvas[1] / skin.crop[1] * 100 + '%';
        }
        return {render: function (data) {
            layout(preset(data.style));
            var percent = typeof data.percent === 'number' && isFinite(data.percent) ? data.percent : 0;
            fill.style.width = Math.max(0, Math.min(1, percent)) * 100 + '%';
            fill.style.backgroundColor = /^#[0-9a-f]{6}$/i.test(data.color) ? data.color : '#3FC23A';
            label.textContent = data.text || '';
        }};
    }
    window.__dkHealthBar = {create: create, preset: preset};
}());
