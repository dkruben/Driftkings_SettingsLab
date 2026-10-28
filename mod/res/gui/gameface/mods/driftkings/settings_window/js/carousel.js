/* DK Settings — pré-visualização do carrossel de veículos.
   Desenha cartões de exemplo com o perfil normal ou compacto: tamanho e espaçamento do cartão,
   campos nativos (enabled, alpha, dx, dy, scale) e campos extra (formato, ícone, posição,
   tamanho, alinhamento, camada, cor de fundo), com as macros de estatísticas avaliadas sobre estatísticas
   de exemplo: {{v.x}}, {{v.c_x}}, {{v.x%2d~%}}, {{v.x?sim|não}}, {{v.x|omissão}} e macros aninhadas.
   Dois veículos usam estatísticas fictícias identificadas como exemplo; parte das posições nativas continua aproximada; os campos extra usam as posições reais. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, t = DK.t;
    var SCALE = ['#FE0E00', '#FE7903', '#F8F400', '#A6FFA6', '#02C9B3', '#D042F3'];
    var LIMITS = {tdb: [500, 750, 1000, 1800, 2500], winrate: [47, 49, 52, 57, 62], battles: [100, 300, 1000, 2000, 5000], hitsRatio: [60, 66, 72, 78, 84],
                  damageRating: [20, 50, 65, 85, 95], wn8effd: [0.5, 0.7, 0.9, 1.2, 1.9], wn8: [300, 900, 1500, 2300, 3200]};
    var SHADOW = {alpha: 80, blur: 2, color: '#000000', distance: 0, angle: 0, enabled: true, strength: 2};
    var VEHICLES = [
        {name: 'T32', nation: 'usa', tank: 'a12_t32', tier: 8, flag: ['#2c4a6b', '#1a2c40'], level: 'VIII', type: 'heavyTank', short: 'HT', selected: true, premium: false, xp: 'x2',
         stats: {battles: 1245, winrate: 54.3, hitsRatio: 78.4, tdb: 2380, tfb: 1, wn8expd: 1950, wn8effd: 1.22, wn8: 2150, battletiermin: 8, battletiermax: 10,
                 marksOnGun: 2, damageRating: 87.4, mastery: 3}},
        {name: 'Obj. 140', nation: 'ussr', tank: 'r97_object_140', tier: 10, flag: ['#6b2c2c', '#401a1a'], level: 'X', type: 'mediumTank', short: 'MT', selected: false, premium: false, info: true,
         stats: {battles: 312, winrate: 48.6, hitsRatio: 70.2, tdb: 3150, tfb: 1, wn8expd: 3400, wn8effd: 0.93, wn8: 1420, battletiermin: 10, battletiermax: 10,
                 marksOnGun: 0, damageRating: 41.2, mastery: 1}}
    ];
    // Class colours from lobby/vehicle_carousel.py (CLASS_COLORS); {{v.c_type}} names the card background image.
    var CLASS_COLORS = {lightTank: '#53b329', mediumTank: '#1ea2d2', heavyTank: '#957d5b', 'AT-SPG': '#f13439', SPG: '#b87ab2'};
    // Approximate places of the client's own card elements, as fractions of the card.
    var NATIVE = {
        flag: {x: 0, y: 0, w: 1, h: 1}, tankIcon: {x: 0.5, y: 0.5}, tankType: {right: 8, bottom: 25},
        level: {right: 30, bottom: 25}, tankName: {right: 8, bottom: 6}, xp: {x: 0, y: 0}, favorite: {x: 1, y: 1},
        info: {x: 0.30, y: 0.42}, progressionPoints: {right: 8, top: 4}
    };

    function supports(mod) { return String(mod.id).split(':')[0] === 'legacy.CarouselStats'; }

    /* Rating macros ---------------------------------------------------------- */
    function colorOf(name, value) {
        var limits = LIMITS[name];
        if (!limits || typeof value !== 'number') { return null; }
        for (var i = 0; i < limits.length; i++) { if (value < limits[i]) { return SCALE[i]; } }
        return SCALE[SCALE.length - 1];
    }
    function lookup(name, vehicle) {
        name = name.replace(/^v\./, '');
        var aliases = {tdb:'avgDamage',winrate:'winRate',hitsRatio:'hitRate',damageRating:'marks',tfb:'avgFrags',t_battles:'battles',markOfMastery:'mastery'};
        if (name.indexOf('c_') === 0) {
            var key = name.slice(2);
            if (key === 'type') { return CLASS_COLORS[vehicle.type] || '#957d5b'; }
            if (vehicle.colors) { return vehicle.colors[aliases[key] || key] || null; }
            return colorOf(key === 'wn8expd' ? 'tdb' : key, vehicle.stats[key]);
        }
        if (name === 'name') { return vehicle.name; }
        if (name === 'premium') { return vehicle.premium || null; }
        if (name === 'selected') { return vehicle.selected || null; }
        if (name === 'level') { return vehicle.level; }
        if (vehicle.colors) { return vehicle.stats[aliases[name] || name]; }
        if (name === 'tfb') { return vehicle.stats.tfb ? vehicle.stats.tdb : null; }
        var value = vehicle.stats[name];
        return value === 0 && /marksOnGun/.test(name) ? null : value;
    }
    function format(value, spec) {
        if (!spec) { return String(value); }
        var match = /%-?(\d*)(?:\.(\d+))?([sdif])/.exec(spec);
        if (!match || typeof value !== 'number') { return String(value); }
        return match[3] === 'f' ? value.toFixed(match[2] ? Number(match[2]) : 2) : match[3] === 's' ? String(value) : String(Math.round(value));
    }
    function evaluate(body, vehicle) {
        if (body.indexOf('icon:') === 0) {
            var kind = body.slice(5);
            if (kind === 'mastery' && vehicle.stats.mastery) { return DK.assets.mastery(vehicle.stats.mastery); }
            if (kind === 'marksOnGun') {
                var count = vehicle.stats.marksOnGun;
                if (!count) { return 'gui/maps/driftkings/carroucel/mark_0.png'; }
                return vehicle.colors ? 'gui/maps/icons/marksOnGun/95x85/' + vehicle.nation + '_' + count + '_' + (count === 1 ? 'mark' : 'marks') + '.png' : DK.assets.marks(count);
            }
            if (vehicle.colors) {
                if (kind === 'mastery') { return '--'; }
                var icons = {damage:'efficiency/48x48/damage.png',assist:'efficiency/48x48/help.png',blocked:'efficiency/48x48/armor.png',wins:'dossier/wins40x32.png',battles:'dossier/battles40x32.png'};
                return icons[kind] ? 'gui/maps/icons/library/' + icons[kind] : '';
            }
            return 'dkicon:' + kind;
        }
        var name = /^[\w.:-]+/.exec(body);
        name = name ? name[0] : body;
        var rest = body.slice(name.length), value = lookup(name, vehicle), present = value !== undefined && value !== null && value !== '';
        if (rest.charAt(0) === '?') {
            var bar = rest.indexOf('|');
            return value ? rest.slice(1, bar < 0 ? undefined : bar) : bar < 0 ? '' : rest.slice(bar + 1);
        }
        var spec = /^%[-\d.]*[sdif]/.exec(rest);
        if (spec) { rest = rest.slice(spec[0].length); }
        var suffix = '', fallback = null;
        if (rest.charAt(0) === '~') { var end = rest.indexOf('|'); suffix = rest.slice(1, end < 0 ? undefined : end); rest = end < 0 ? '' : rest.slice(end); }
        if (rest.charAt(0) === '|') { fallback = rest.slice(1); }
        if (!present) { return fallback === null ? (vehicle.colors ? '--' : '') : fallback; }
        return format(value, spec ? spec[0] : null) + suffix;
    }
    // Innermost macros first, so {{v.tfb?{{v.wn8expd%d}}|}} works.
    function macros(text, vehicle) {
        text = String(text === undefined || text === null ? '' : text);
        vehicle = vehicle || VEHICLES[0];
        for (var guard = 0; guard < 30 && /\{\{[^{}]*\}\}/.test(text); guard++) {
            text = text.replace(/\{\{([^{}]*)\}\}/g, function (all, body) { return evaluate(body, vehicle); });
        }
        return text;
    }

    /* Rendering ----------------------------------------------------------------------- */
    function image(src) {
        if (!src || src === '--') { return ''; }
        if (src.indexOf('dkicon:') === 0) { return 'dkicon:' + src.slice(7); }
        src = src.replace(/^img:\/\//, '');
        return DK.asset(src);
    }
    // Small formatted-text renderer for card fields (font, b, i, u, br, img).
    function rich(parent, text) {
        var current = parent, stack = [parent], parts = String(text || '').split(/(<[^>]*>)/g);
        parts.forEach(function (part) {
            if (!part) { return; }
            if (/^<\/(b|i|u|font)>$/i.test(part)) { if (stack.length > 1) { stack.pop(); } current = stack[stack.length - 1]; return; }
            if (/^<br\s*\/?>$/i.test(part)) { current.appendChild(document.createElement('br')); return; }
            var img = /^<img\s([^>]*)>$/i.exec(part);
            if (img) { icon(current, (/src\s*=\s*['"]([^'"]*)['"]/i.exec(img[1]) || [])[1], Number((/width\s*=\s*['"](\d+)/i.exec(img[1]) || [])[1]), Number((/height\s*=\s*['"](\d+)/i.exec(img[1]) || [])[1])); return; }
            var open = /^<(b|i|u|font)(\s[^>]*)?>$/i.exec(part);
            if (open) {
                var node = document.createElement('span'), tag = open[1].toLowerCase(), attrs = open[2] || '';
                if (tag === 'b') { node.style.fontWeight = 'bold'; }
                if (tag === 'i') { node.style.fontStyle = 'italic'; }
                if (tag === 'u') { node.style.textDecoration = 'underline'; }
                var color = /color\s*=\s*['"]([^'"]*)['"]/i.exec(attrs), size = /size\s*=\s*['"](\d+)['"]/i.exec(attrs), face = /face\s*=\s*['"]([^'"]*)['"]/i.exec(attrs);
                if (color && DK.hex(color[1])) { node.style.color = DK.hex(color[1]); }
                if (size) { node.style.fontSize = DK.clamp(Number(size[1]), 8, 40) + 'rem'; }
                if (face) { node.style.fontFamily=face[1]==='$FieldFont'||face[1]==='$TitleFont'?'Warhelios':face[1]; }
                current.appendChild(node); stack.push(node); current = node;
                return;
            }
            if (part.charAt(0) === '<') { return; }
            current.appendChild(document.createTextNode(part.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')));
        });
    }
    function icon(parent, src, width, height) {
        src = image(src);
        if (!src) { return; }
        if (src.indexOf('dkicon:') === 0) {
            var badge = h('span.dk-car-badge', {text: src.slice(7) === 'mastery' ? 'M' : '★'}, null, parent);
            if (width) { badge.style.width = width + 'rem'; badge.style.height = (height || width) + 'rem'; badge.style.fontSize = Math.round((height || width) * 0.6) + 'rem'; }
            return;
        }
        var img = h('img.dk-car-img', {src: src}, null, parent);
        if (width) { img.style.width = width + 'rem'; }
        if (height) { img.style.height = height + 'rem'; }
        // The mod hides images it cannot load; so does the preview.
        img.addEventListener('error', function () { img.style.display = 'none'; });
    }

    // A client image that fails to load is hidden, never shown broken.
    function withFallback(img) {
        img.addEventListener('error', function () { img.style.visibility = 'hidden'; });
        return img;
    }

    function create(host, mod) {
        var values = {}, overrides = {}, layout = null, defs = {}, vehicles = VEHICLES, nativeRows = 1;
        mod.controls.forEach(function (def) { defs[def.id] = def; });
        function v(path, fallback) {
            var id = DK.minimapPreview.fieldId(path);
            if (Object.prototype.hasOwnProperty.call(overrides, id)) { return overrides[id]; }
            if (Object.prototype.hasOwnProperty.call(values, id)) { return values[id]; }
            return fallback;
        }
        function has(path) { return !!defs[DK.minimapPreview.fieldId(path)]; }

        var root = h('div.dk-live', null, null, host);
        var head = h('div.dk-live-head', null, [h('span.dk-detail-kicker', {text: t('car.title')})], root);
        h('div.dk-spacer', null, null, head);
        var views = h('div.dk-segments', null, null, head);
        var normal = h('button.dk-segment', {text: t('car.normal')}, null, views);
        var small = h('button.dk-segment', {text: t('car.small')}, null, views);
        normal.addEventListener('click', function (event) { DK.stop(event); layout = 'normal'; draw(); });
        small.addEventListener('click', function (event) { DK.stop(event); layout = 'small'; draw(); });
        var frame = h('div.dk-car-frame', null, null, root);
        var strip = h('div.dk-car-strip', null, null, frame);
        var note = h('div.dk-live-note', {text: t('car.note')}, null, root);

        function profileName() {
            if (layout) { return layout; }
            var cell = v('carousel.cellType', 0);
            return cell === 2 || cell === 'small' || ((cell === 0 || cell === 'auto') && nativeRows > 1) ? 'small' : 'normal';
        }
        function field(layers, profile, index, vehicle) {
            var p = 'carousel.' + profile + '.extraFields.' + index + '.';
            if (v(p + 'enabled', true) === false) { return; }
            var alpha = Number(macros(v(p + 'alpha', 100), vehicle));
            if (!isFinite(alpha)) { alpha = 100; }
            // "Fundo" (substrate) sits under the card's own elements, "Frente" (top) over them.
            var layer = v(p + 'layer', 1), under = layer === 0 || layer === 'substrate';
            var node = h('div.dk-car-field', null, null, under ? layers.under : layers.over), align = ['left', 'center', 'right'][v(p + 'align', 0)] || 'left';
            node.style.left = v(p + 'x', 0) + 'rem';
            node.style.top = v(p + 'y', 0) + 'rem';
            node.style.opacity = DK.clamp(alpha, 0, 100) / 100;
            node.style.textAlign = align;
            node.style.justifyContent = {left:'flex-start',center:'center',right:'flex-end'}[align];
            if (align === 'right') { node.style.transform = 'translateX(-100%)'; }
            else if (align === 'center') { node.style.transform = 'translateX(-50%)'; }
            var width = v(p + 'width', 0), height = v(p + 'height', 0);
            if (width) { node.style.width = width + 'rem'; }
            if (height) { node.style.height = height + 'rem'; }
            var bg = DK.hex(macros(v(p + 'bgColor', ''), vehicle));
            if (bg) { node.style.backgroundColor = bg; }
            node.style.fontSize = v(p + 'fontSize', 12) + 'rem';
            var textColor = DK.hex(macros(v(p + 'color', ''), vehicle));
            if (textColor) { node.style.color = textColor; }
            var shadowPath = p + 'shadow.', shared = 'carousel.' + profile + '.textFieldShadow.';
            if (v(shadowPath + 'enabled', v(shared + 'enabled', SHADOW.enabled))) {
                var angle = v(shadowPath + 'angle', v(shared + 'angle', 45)) * Math.PI / 180;
                var distance = v(shadowPath + 'distance', v(shared + 'distance', 1));
                var shadowColor = DK.hex(macros(v(shadowPath + 'color', v(shared + 'color', '#000000')), vehicle)) || '#000000';
                node.style.textShadow = Math.cos(angle) * distance + 'rem ' + Math.sin(angle) * distance + 'rem ' + v(shadowPath + 'blur', v(shared + 'blur', 2)) + 'rem ' + DK.rgba(shadowColor, v(shadowPath + 'alpha', v(shared + 'alpha', 80)) / 100);
            }
            var showIcons = v('showIcons', true) !== false;
            var src = v(p + 'src', null), text = v(p + 'format', '');
            if (src && showIcons) { icon(node, macros(src, vehicle), v(p + 'iconSize', 14), v(p + 'iconSize', 14)); }
            if (text) {
                var filled = macros(text, vehicle);
                if (!showIcons) { filled = filled.replace(/<img[^>]*>/gi, ''); }
                rich(h('span', null, null, node), filled);
            }
        }
        function native(card, profile, key, vehicle, build) {
            var p = 'carousel.' + profile + '.fields.' + key + '.';
            if (v(p + 'enabled', true) === false) { return; }
            var place = NATIVE[key], node = build();
            if (!node) { return; }
            card.appendChild(node);
            node.style.position = 'absolute';
            if (place.right !== undefined) { node.style.right = place.right + 'rem'; }
            else { node.style.left = (place.x * 100) + '%'; }
            if (place.bottom !== undefined) { node.style.bottom = place.bottom + 'rem'; }
            else if (place.top !== undefined) { node.style.top = place.top + 'rem'; }
            else { node.style.top = (place.y * 100) + '%'; }
            if (place.w) { node.style.width = (place.w * 100) + '%'; node.style.height = (place.h * 100) + '%'; }
            node.style.opacity = DK.clamp(Number(v(p + 'alpha', 100)), 0, 100) / 100;
            node.style.transform = 'translate(' + v(p + 'dx', 0) + 'rem,' + v(p + 'dy', 0) + 'rem) scale(' + v(p + 'scale', 1) + ')';
            // Baseline anchors from the EU 2.4.1.1 native carousel CSS.
            if (key === 'tankIcon') {
                node.style.width = (profile === 'small' ? 230 : 260) + 'rem';
                node.style.height = (profile === 'small' ? 184 : 208) + 'rem';
                node.style.transform = 'translate(-50%,-53%) ' + node.style.transform;
            } else if (key === 'favorite') {
                node.style.width = '22rem'; node.style.height = '27rem';
                node.style.transform = 'translate(-100%,-100%) ' + node.style.transform;

            } else if (key === 'flag') {
                node.style.width = (profile === 'small' ? 120 : 128) + 'rem';
                node.style.height = (profile === 'small' ? 90 : 96) + 'rem';
            }
            node.style.transformOrigin = '0 0';
        }
        function card(profile, vehicle, width, height) {
            var node = h('div.dk-car-card' + (vehicle.selected ? '.is-selected' : ''));
            node.style.width = width + 'rem';
            node.style.height = height + 'rem';
            node.style.backgroundColor = 'rgba(10,10,10,' + (v('carousel.slotBackgroundAlpha', 100) / 100 * 0.3) + ')';
            var layers = {under: h('div.dk-car-layer', null, null, node)};
            // The client's own images: nation flag (160x100), vehicle (420x307), class and tier icons.
            native(node, profile, 'flag', vehicle, function () {
                var flag = h('div.dk-car-flag');
                flag.style.backgroundImage = 'url(' + DK.asset(DK.assets.flag(vehicle.nation)) + '), linear-gradient(to right, ' + (vehicle.flag || ['#1a2c40','#101820'])[0] + ', ' + (vehicle.flag || ['#1a2c40','#101820'])[1] + ')';
                return flag;
            });
            native(node, profile, 'tankIcon', vehicle, function () { return withFallback(h('img.dk-car-tank-img', {src: DK.asset(vehicle.image || DK.assets.tank(vehicle.tank))})); });
            native(node, profile, 'tankType', vehicle, function () { return withFallback(h('img.dk-car-type-img', {src: DK.asset(DK.assets.type(vehicle.type))})); });
            native(node, profile, 'level', vehicle, function () { return h('div.dk-car-level', {text: vehicle.level}); });
            native(node, profile, 'tankName', vehicle, function () { return h('div.dk-car-name' + (vehicle.premium ? '.is-premium' : ''), {text: vehicle.name}); });
            native(node, profile, 'xp', vehicle, function () { return vehicle.xp ? h('div.dk-car-xp', {text: '★ ' + vehicle.xp}) : null; });
            native(node, profile, 'favorite', vehicle, function () { return vehicle.favorite ? withFallback(h('img.dk-car-favorite-img', {src: DK.asset(DK.assets.favorite)})) : null; });
            native(node, profile, 'info', vehicle, function () { return vehicle.info ? h('div.dk-car-info', {text: t('car.inBattle')}) : null; });
            native(node, profile, 'progressionPoints', vehicle, function () { return h('div.dk-car-progression', {text: vehicle.progression || '0/400'}); });
            layers.over = h('div.dk-car-layer', null, null, node);
            for (var i = 0; i < 64; i++) {
                if (!has('carousel.' + profile + '.extraFields.' + i + '.x')) { break; }
                field(layers, profile, i, vehicle);
            }
            if (vehicle.selected) {
                var border = h('div.dk-car-border', null, null, node);
                border.style.opacity = v('carousel.slotSelectedBorderAlpha', 100) / 100;
            }
            return node;
        }
        function draw() {
            var profile = profileName();
            DK.toggle(normal, 'is-selected', profile === 'normal');
            DK.toggle(small, 'is-selected', profile === 'small');
            DK.clear(strip);
            if (v('enabled', true) === false) { h('div.dk-hud-off.dk-car-off', {text: t('module.off')}, null, strip); return; }
            var width = v('carousel.' + profile + '.width', profile === 'small' ? 160 : 210);
            var height = v('carousel.' + profile + '.height', profile === 'small' ? 70 : 140);
            var gap = v('carousel.' + profile + '.gap', 10);
            var configuredRows = Number(v('carousel.rows', 0));
            var rows = configuredRows >= 1 && configuredRows <= 4 ? configuredRows : vehicles === VEHICLES ? (profile === 'small' ? 2 : 1) : nativeRows;
            rows = Math.min(rows, vehicles.length);
            var columns = Math.min(2, Math.ceil(vehicles.length / rows));
            strip.style.backgroundColor = 'rgba(0,0,0,' + (v('carousel.backgroundAlpha', 60) / 100 * 0.6) + ')';
            var total = {w: columns * width + (columns - 1) * gap + 16, h: rows * height + (rows - 1) * gap + 16};
            var unit = parseFloat(document.documentElement.style.fontSize) || 1, room = (frame.clientWidth / unit) || 344;
            var scale = Math.min(1, room / total.w);
            strip.style.width = total.w + 'rem';
            strip.style.height = total.h + 'rem';
            strip.style.transform = 'scale(' + scale + ')';
            frame.style.height = Math.ceil(total.h * scale) + 'rem';
            var index = 0;
            for (var c = 0; c < columns; c++) {
                var column = h('div.dk-car-column', null, null, strip);
                if (c) { column.style.marginLeft = gap + 'rem'; }
                for (var r = 0; r < rows && index < vehicles.length; r++) {
                    var node = card(profile, vehicles[index % vehicles.length], width, height);
                    if (r) { node.style.marginTop = gap + 'rem'; }
                    column.appendChild(node);
                    index += 1;
                }
            }
        }
        return {
            update: function (next, everything, snapshot) {
                values = next || {}; overrides = {};
                nativeRows = snapshot && snapshot.nativeRows >= 1 && snapshot.nativeRows <= 4 ? snapshot.nativeRows : 1;
                vehicles = snapshot && snapshot.source === 'examples' && snapshot.vehicles && snapshot.vehicles.length ? snapshot.vehicles : VEHICLES;
                note.textContent = t('car.note');
                draw();
            },
            preview: function (id, value) { overrides[id] = value; draw(); },
            redraw: draw,
            dispose: function () { DK.remove(root); }
        };
    }

    DK.carouselPreview = {supports: supports, create: create, macros: macros};
}());
