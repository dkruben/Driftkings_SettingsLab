/* DK Settings — pré-visualização de texto formatado.
   Mostra como fica um texto em HTML do Flash (font, b, i, u, br, p, img, textformat) com as
   macros preenchidas por valores de exemplo. Suporta as quatro sintaxes usadas pelo mod:
   %(nome)s / %(nome).1f (Python), {nome} e {c:nome}, {{nome}} e {{nome%.16s}}, e datas %H:%M. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, decoder = document.createElement('textarea');
    // Date codes as the hangar clock writes them (main/clock.js dateFormat): week from Monday, names from the
    // client's own calendar (schema.calendar, gameface/lobby/main.calendar_names) and English otherwise.
    var CALENDAR = {days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                    shortDays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
                    shortMonths: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']};
    function dateCode(key, now) {
        if (key === '%') { return '%'; }
        var names = DK.calendar || {}, hour = now.getHours(), weekday = (now.getDay() + 6) % 7;
        function list(name) { return names[name] && names[name].length ? names[name] : CALENDAR[name]; }
        function pad(n) { return ('0' + n).slice(-2); }
        var value = {H: pad(hour), I: pad(hour % 12 || 12), M: pad(now.getMinutes()), S: pad(now.getSeconds()), d: pad(now.getDate()),
                     m: pad(now.getMonth() + 1), Y: String(now.getFullYear()), y: pad(now.getFullYear() % 100),
                     A: list('days')[weekday], a: list('shortDays')[weekday], B: list('months')[now.getMonth()],
                     b: list('shortMonths')[now.getMonth()], p: hour < 12 ? 'AM' : 'PM'}[key.charAt(0)];
        return key.length === 1 ? value : key.charAt(1) === 'u' ? value.toUpperCase() : value.toLowerCase();
    }
    var SAMPLE = {
        timer: 1.8, percent: 76, flightTime: 1.42, distance: 315, dist: 315, wn8: 2150, eff: 1650, wtr: 7400, xte: 82, winrate: 54.2, diff: '+120',
        battles: 12450, avgDamage: 2380, damage: 350, dmg: 350, icons: '◆◆', vehicles: 'IS-7, Obj. 140', vehicle: 'T32', name: 'Driftking',
        nick: 'Driftking', clan: '[DK]', hp: 1304, 'hp-max': 1650, 'hp-ratio': 79, level: 'VIII', tier: 8, type: 'HT', vtype: 'HT',
        pos: 'E5', cellsize: 100, frags: 2, kills: 2, assist: 820, blocked: 640, spotted: 3, marks: 2, mark: 87.4, mastery: 'M',
        'squad-num': '', place: 3, time: '04:32'
    };
    var SAMPLE_COLORS = {wn8: '#02C9B3', eff: '#A6FFA6', wtr: '#D042F3', xte: '#A6FFA6', winrate: '#A6FFA6', dmg: '#F8F400', hp: '#80D639'};

    function sampleValue(name, extra) {
        if (extra && Object.prototype.hasOwnProperty.call(extra, name)) { return extra[name]; }
        return SAMPLE[name];
    }
    function colorMacro(name, extra) {
        return (extra && extra.color) && name === 'color' ? extra.color : SAMPLE_COLORS[name] || (extra && extra.color) || '#F8F400';
    }
    function unknown(name) { return '\u2039' + name + '\u203A'; }

    // Fills every macro syntax. extra: {color, ...} values specific to the module.
    function fill(text, extra) {
        var now = new Date();   // the clock shows the client's current time
        text = String(text || '');
        // Carousel fields use rating macros ({{v.x?a|b}}, {{v.c_x}}, {{icon:x}}); they have their own evaluator.
        if (DK.carouselPreview && /\{\{(v\.|icon:)/.test(text)) { text = DK.carouselPreview.macros(text).replace(/dkicon:\w+/g, ''); }
        return text
            .replace(/%\((\w[\w-]*)\)(\.(\d+))?([sdif])/g, function (all, name, dot, digits, kind) {
                var value = name === 'color' ? colorMacro(name, extra) : sampleValue(name, extra);
                if (value === undefined) { return unknown(name); }
                if (kind === 'd' || kind === 'i') { return String(Math.round(Number(value))); }
                if (kind === 'f') { return Number(value).toFixed(digits ? Number(digits) : 6); }
                return String(value);
            })
            .replace(/%([aAbB][ul]|[HIMSdmYyaAbBp%])/g, function (all, key) { return dateCode(key, now); })
            .replace(/\{\{([^}]+)\}\}/g, function (all, body) {
                if (/^c:/.test(body)) { return colorMacro(body.slice(2), extra); }
                var match = /^([\w-]+)(?:%\.(\d+)s)?/.exec(body), name = match ? match[1] : body, value = sampleValue(name, extra);
                if (name === 'i18n' || /^i18n:/.test(body)) { return body.split(':')[1] || ''; }
                if (value === undefined) { return unknown(name); }
                value = String(value);
                return match && match[2] ? value.slice(0, Number(match[2])) : value;
            })
            .replace(/\{(c:)?([a-zA-Z][\w-]*)\}/g, function (all, isColor, name) {
                if (isColor) { return colorMacro(name, extra); }
                var value = sampleValue(name, extra);
                return value === undefined ? unknown(name) : String(value);
            });
    }

    function attribute(tag, name) {
        var match = new RegExp(name + "\\s*=\\s*(?:'([^']*)'|\"([^\"]*)\"|([^\\s>]+))", 'i').exec(tag);
        return match ? (match[1] !== undefined ? match[1] : match[2] !== undefined ? match[2] : match[3]) : null;
    }
    function imageSource(src) {
        if (!src) { return ''; }
        if (/^img:\/\//.test(src)) { src = src.slice(6); }
        return DK.asset(src);
    }

    // Builds the formatted text into container. options: {color, size, extra, align}
    function render(container, source, options) {
        options = options || {};
        DK.clear(container);
        var text = fill(source, options.extra);
        var root = h('div.dk-rich-line', null, null, container), stack = [root], current = root;
        if (options.color) { root.style.color = options.color; }
        if (options.size) { root.style.fontSize = options.size + 'rem'; }
        if (options.align) { root.style.textAlign = options.align; }
        var pattern = /<\/?([a-zA-Z]+)([^>]*)>|([^<]+)/g, match;
        function push(node) { current.appendChild(node); stack.push(node); current = node; }
        function pop(tag) {
            for (var i = stack.length - 1; i > 0; i--) {
                if (stack[i].tagName === tag) { stack.length = i; current = stack[i - 1]; return; }
            }
        }
        while ((match = pattern.exec(text)) !== null) {
            if (match[3] !== undefined) {
                decoder.innerHTML = match[3];
                current.appendChild(document.createTextNode(decoder.value));
                continue;
            }
            var name = match[1].toLowerCase(), closing = match[0].charAt(1) === '/', attrs = match[2];
            if (name === 'br') { current.appendChild(document.createElement('br')); continue; }
            if (name === 'img') {
                var box = h('span.dk-rich-img', null, null, current), src = imageSource(attribute(attrs, 'src'));
                var image = h('img', {src: src}, null, box);
                var width = attribute(attrs, 'width'), height = attribute(attrs, 'height');
                if (width) { image.style.width = width + 'rem'; }
                if (height) { image.style.height = height + 'rem'; }
                image.addEventListener('error', function (event) {
                    var holder = event.target.parentNode;
                    DK.clear(holder);
                    DK.toggle(holder, 'is-missing', true);
                    holder.textContent = (holder.title || 'img').split('/').pop();
                });
                box.title = src;
                continue;
            }
            var tag = name === 'font' ? 'SPAN' : name === 'b' ? 'B' : name === 'i' ? 'I' : name === 'u' ? 'U' : name === 'p' ? 'DIV' : name === 'textformat' ? 'DIV' : name === 'span' ? 'SPAN' : null;
            if (!tag) { continue; }
            if (closing) { pop(tag); continue; }
            var node = document.createElement(tag);
            if (name === 'font') {
                var color = DK.hex(attribute(attrs, 'color')), size = attribute(attrs, 'size'), alpha = attribute(attrs, 'alpha');
                if (color) { node.style.color = color; }
                var face=attribute(attrs,'face');
                if(face){node.style.fontFamily=face==='$FieldFont'||face==='$TitleFont'?'Warhelios':face;}

                if (size && isFinite(Number(size))) { node.style.fontSize = Number(size) + 'rem'; }
                if (alpha && /^#[0-9a-fA-F]{2}$/.test(alpha)) { node.style.opacity = parseInt(alpha.slice(1), 16) / 255; }
            } else if (name === 'p') {
                var align = attribute(attrs, 'align');
                if (align) { node.style.textAlign = align; }
            } else if (name === 'textformat') {
                var leading = attribute(attrs, 'leading'), right = attribute(attrs, 'rightMargin'), left = attribute(attrs, 'leftMargin'), indent = attribute(attrs, 'indent');
                if (leading && isFinite(Number(leading))) { node.style.marginBottom = Number(leading) + 'rem'; }
                if (right && isFinite(Number(right))) { node.style.paddingRight = Number(right) + 'rem'; }
                if (left && isFinite(Number(left))) { node.style.paddingLeft = Number(left) + 'rem'; }
                if (indent && isFinite(Number(indent))) { node.style.textIndent = Number(indent) + 'rem'; }
            }
            push(node);
        }
        return root;
    }

    // Text fields worth a preview: markup or macros, but not JSON or plain paths.
    function applies(def, value) {
        if (def.type !== 'text' && def.type !== 'textarea') { return false; }
        var text = String(value === undefined || value === null ? (def['default'] || '') : value);
        if (/^\s*[[{]\s*["[{\]]/.test(text) || /^\s*\[\s*\]\s*$/.test(text)) { return false; }
        return /<(font|b|i|u|br|img|p|textformat|span)\b/i.test(text) || /%\(\w+\)|\{\{[^}]+\}\}|\{c?:?[a-zA-Z][\w-]*\}|%[HMSAdbY]/.test(text);
    }

    DK.richText = {render: render, fill: fill, applies: applies};
}());
