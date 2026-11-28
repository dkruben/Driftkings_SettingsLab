/* DK Settings — pré-visualização de texto formatado.
   Mostra como fica um texto em HTML do Flash (font, b, i, u, br, p, img, textformat) com as
   macros preenchidas por valores de exemplo. Suporta as quatro sintaxes usadas pelo mod:
   %(nome)s / %(nome).1f (Python), {nome} e {c:nome}, {{nome}} e {{nome%.16s}}, e datas %H:%M. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h;
    function decode(text) {
        var names = {amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: '\u00a0'};
        return text.replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi, function (entity, value) {
            if (value.charAt(0) !== '#') { return names[value.toLowerCase()]; }
            var point = value.charAt(1).toLowerCase() === 'x' ? parseInt(value.slice(2), 16) : Number(value.slice(1));
            if (point < 0 || point > 1114111 || (point >= 55296 && point <= 57343)) { return entity; }
            if (point <= 65535) { return String.fromCharCode(point); }
            point -= 65536;
            return String.fromCharCode(55296 + (point >> 10), 56320 + (point & 1023));
        });
    }
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
        wnx: 1480, xwn8: 1610, xeff: 1520, wn8effd: 1.42,
        battles: 12450, avgDamage: 2380, damage: 350, dmg: 350, icons: '••', vehicles: 'IS-7, Obj. 140', vehicle: 'T32', name: 'Driftking',
        nick: 'Driftking', clan: '[DK]', hp: 1304, 'hp-max': 1650, 'hp-ratio': 79, level: 'VIII', tier: 8, type: 'HT', vtype: 'HT',
        pos: 'E5', load: 12, cellsize: 100, frags: 2, kills: 2, assist: 820, blocked: 640, spotted: 3, marks: 2, mark: 87.4, mastery: 'M',
        'squad-num': '', place: 3, time: '04:32', countedArmor: 168, piercingPower: 225, piercingReserve: 57, caliber: 105,
        ricochet: '', noDamage: '', message: ''
    };
    var SAMPLE_COLORS = {wn8: '#02C9B3', wnx: '#02C9B3', eff: '#A6FFA6', xeff: '#A6FFA6', xwn8: '#A6FFA6', wtr: '#D042F3', xte: '#A6FFA6',
                         winrate: '#A6FFA6', dmg: '#F8F400', hp: '#80D639'};

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
        // Carousel fields use rating macros ({{v.x?a|b}}, {{v.c:x}}, {{icon:x}}); they have their own evaluator.
        if (DK.carouselMacros && /\{\{(v\.|icon:)/.test(text)) { text = DK.carouselMacros.macros(text).replace(/dkicon:\w+/g, ''); }
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
            .replace(/\{(c:)?([a-zA-Z][\w-]*)(?::(\.\d+f|d))?\}/g, function (all, isColor, name, spec) {
                if (isColor) { return colorMacro(name, extra); }
                var value = sampleValue(name, extra);
                if (value === undefined) { return unknown(name); }
                if (spec === 'd') { return String(Math.floor(Number(value))); }
                if (spec) { return Number(value).toFixed(Number(spec.slice(1, -1))); }
                return String(value);
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
    // Layout: each logical line is a horizontal flex row without wrapping. Inline elements (font, b, i, u, span) and
    // text runs are independent flex items inside their row; an explicit break (br, p, textformat) starts a new row.
    // Rows and segments have no fixed height, so the preview box follows its content. The DOM is built with
    // createElement and textContent only; no template text is ever parsed as HTML by the browser.
    var JUSTIFY = {left: 'flex-start', center: 'center', right: 'flex-end'};
    function render(container, source, options) {
        options = options || {};
        DK.clear(container);
        var text = fill(source, options.extra);
        var root = h('div.dk-rich-line', null, null, container);
        if (options.color) { root.style.color = options.color; }
        if (options.size) { root.style.fontSize = options.size + 'rem'; }
        var row = null, inline = [], blocks = [];
        function ensureRow() {
            if (row) { return row; }
            row = h('div.dk-rich-row', null, null, root);
            var align = options.align || '', styles = {};
            blocks.forEach(function (block) {
                if (block.align) { align = block.align; }
                Object.keys(block.styles).forEach(function (key) { styles[key] = block.styles[key]; });
            });
            if (JUSTIFY[align]) { row.style.justifyContent = JUSTIFY[align]; }
            Object.keys(styles).forEach(function (key) { row.style[key] = styles[key]; });
            inline = [{name: '', node: row}];
            return row;
        }
        function current() { return inline[inline.length - 1].node; }
        function endRow() { row = null; inline = []; }
        // An explicit break ends the row; a break on an empty row keeps one line of height.
        function lineBreak() {
            ensureRow();
            if (!row.childNodes.length) { row.appendChild(document.createTextNode('​')); }
            endRow();
        }
        // Closing tags match the source element name; every inline element is a span in the DOM.
        function pop(name) {
            for (var i = inline.length - 1; i > 0; i--) {
                if (inline[i].name === name) { inline.length = i; return; }
            }
        }
        var pattern = /<\/?([a-zA-Z]+)([^>]*)>|([^<]+)/g, match;
        while ((match = pattern.exec(text)) !== null) {
            if (match[3] !== undefined) {
                // A newline in the text is a real break, as in the production formatter; other text stays one run.
                match[3].split(/\r?\n/).forEach(function (part, index) {
                    if (index > 0) { lineBreak(); }
                    var run = decode(part);
                    if (run) { ensureRow(); current().appendChild(document.createTextNode(run)); }
                });
                continue;
            }
            var name = match[1].toLowerCase(), closing = match[0].charAt(1) === '/', attrs = match[2];
            if (name === 'br') {
                if (!closing) { lineBreak(); }
                continue;
            }
            if (name === 'p' || name === 'textformat') {
                endRow();
                if (closing) { blocks.pop(); continue; }
                var block = {align: attribute(attrs, 'align') || '', styles: {}};
                if (name === 'textformat') {
                    var leading = attribute(attrs, 'leading'), right = attribute(attrs, 'rightMargin'), left = attribute(attrs, 'leftMargin'), indent = attribute(attrs, 'indent');
                    if (leading && isFinite(Number(leading))) { block.styles.marginBottom = Number(leading) + 'rem'; }
                    if (right && isFinite(Number(right))) { block.styles.paddingRight = Number(right) + 'rem'; }
                    if (left && isFinite(Number(left))) { block.styles.paddingLeft = Number(left) + 'rem'; }
                    if (indent && isFinite(Number(indent))) { block.styles.textIndent = Number(indent) + 'rem'; }
                }
                blocks.push(block);
                continue;
            }
            if (name === 'img') {
                ensureRow();
                var box = h('span.dk-rich-img', null, null, current()), src = imageSource(attribute(attrs, 'src'));
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
            var tag = name === 'font' ? 'SPAN' : name === 'b' ? 'B' : name === 'i' ? 'I' : name === 'u' ? 'U' : name === 'span' ? 'SPAN' : null;
            if (!tag) { continue; }
            if (closing) { pop(name); continue; }
            ensureRow();
            var node = h('span.dk-rich-seg', null, null, current());
            if (name === 'b') { node.style.fontWeight = 'bold'; }
            if (name === 'i') { node.style.fontStyle = 'italic'; }
            if (name === 'u') { node.style.textDecoration = 'underline'; }
            if (name === 'font') {
                var color = DK.hex(attribute(attrs, 'color')), size = attribute(attrs, 'size'), alpha = attribute(attrs, 'alpha');
                if (color) { node.style.color = color; }
                var face = attribute(attrs, 'face');
                if (face) { node.style.fontFamily = face === '$FieldFont' || face === '$TitleFont' ? 'Warhelios' : face; }
                if (size && isFinite(Number(size))) { node.style.fontSize = Number(size) + 'rem'; }
                if (alpha && /^#[0-9a-fA-F]{2}$/.test(alpha)) { node.style.opacity = parseInt(alpha.slice(1), 16) / 255; }
            }
            inline.push({name: name, node: node});
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
