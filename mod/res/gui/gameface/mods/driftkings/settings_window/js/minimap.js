/* DK Settings — pré-visualização ao vivo do minimapa (Melhorias do minimapa).
   Desenha num canvas uma batalha simulada num mapa de 1000 m e segue os valores atuais do
   módulo, incluindo os que estão a ser arrastados. As opções são encontradas pelo nome da
   variável: o Python chama-lhes field_<sha1(varName)[:16]> (settings/panel/sections.py). */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, t = DK.t;
    var MAP = 1000;                              // metres per side
    var RESOLUTION = 420;                        // canvas pixels per side
    var SELF = {x: 430, y: 610, hull: -18, camera: 12};
    // The player drives the sample T32: its own view and shell ranges, and the client's fixed circles.
    var SAMPLE = DK.sample, PLAYER = SAMPLE.player;
    var RANGES = {draw: SAMPLE.circles.draw, maxView: SAMPLE.circles.maxView, proximity: SAMPLE.circles.proximity,
                  view: PLAYER.view, shell: PLAYER.shellRange};
    // Client default circle colours, used while "Alterar cores dos círculos" is off.
    var CLIENT_COLORS = SAMPLE.circleColors;
    var CIRCLE_COLOR_KEYS = {draw: 'colorDrawCircle', maxView: 'colorMaxViewCircle', proximity: 'colorMinSpottingCircle', view: 'colorViewCircle'};
    var TEAM = {ally: '#80D639', enemy: '#F05050', squad: '#FFB964', dead: '#999999'};
    // Positions and health are the scene; class and maximum health come from each vehicle's definition.
    var VEHICLES = [
        {team: 'squad', x: 372, y: 655, vehicle: 'Leopard 1', name: 'DriftSquad', hp: 0.86},
        {team: 'ally', x: 300, y: 720, vehicle: 'E 100', name: 'AllyTanker', hp: 0.62},
        {team: 'ally', x: 555, y: 770, vehicle: 'Grille 15', name: 'SniperBob', hp: 1},
        {team: 'enemy', x: 520, y: 500, vehicle: 'EBR 105', name: 'FastAndFurious', hp: 0.41},
        {team: 'enemy', x: 610, y: 300, vehicle: 'IS-7', name: 'HeavyMetal', hp: 0.93},
        {team: 'enemy', x: 760, y: 430, vehicle: 'Conqueror GC', name: 'SkyCannon', hp: 1},
        {team: 'enemy', x: 220, y: 260, vehicle: 'Obj. 140', name: 'Burned', hp: 0, dead: true},
        {team: 'enemy', x: 820, y: 190, vehicle: 'Strv 103B', name: 'Hidden', hp: 0.7, lost: true}
    ].map(function (item) {
        var real = SAMPLE.find(item.vehicle);
        item.type = SAMPLE.types[real.vtype]; item.maxHp = real.maxHp;
        return item;
    });
    function currentHp(vehicle) { return Math.round(vehicle.hp * vehicle.maxHp); }

    /* SHA-1 (ES5), only to find the controls by variable name ---------------- */
    function sha1(text) {
        var bytes = unescape(encodeURIComponent(text)), words = [], i;
        for (i = 0; i < bytes.length; i++) { words[i >> 2] |= bytes.charCodeAt(i) << (24 - (i % 4) * 8); }
        words[bytes.length >> 2] |= 0x80 << (24 - (bytes.length % 4) * 8);
        words[(((bytes.length + 8) >> 6) << 4) + 15] = bytes.length * 8;
        var h0 = 0x67452301, h1 = 0xEFCDAB89, h2 = 0x98BADCFE, h3 = 0x10325476, h4 = 0xC3D2E1F0, w = [];
        function rol(n, c) { return (n << c) | (n >>> (32 - c)); }
        for (var block = 0; block < words.length; block += 16) {
            var a = h0, b = h1, c = h2, d = h3, e = h4;
            for (i = 0; i < 80; i++) {
                w[i] = i < 16 ? (words[block + i] | 0) : rol(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);
                var f = i < 20 ? (b & c) | (~b & d) : i < 40 ? b ^ c ^ d : i < 60 ? (b & c) | (b & d) | (c & d) : b ^ c ^ d;
                var k = i < 20 ? 0x5A827999 : i < 40 ? 0x6ED9EBA1 : i < 60 ? 0x8F1BBCDC : 0xCA62C1D6;
                var temp = (rol(a, 5) + f + e + k + w[i]) | 0;
                e = d; d = c; c = rol(b, 30); b = a; a = temp;
            }
            h0 = (h0 + a) | 0; h1 = (h1 + b) | 0; h2 = (h2 + c) | 0; h3 = (h3 + d) | 0; h4 = (h4 + e) | 0;
        }
        return [h0, h1, h2, h3, h4].map(function (n) { return ('00000000' + (n >>> 0).toString(16)).slice(-8); }).join('');
    }
    function fieldId(name) { return 'field_' + sha1(name).slice(0, 16); }

    function supports(mod) {
        return mod.controls.some(function (def) { return def.id === fieldId('circles.draw.mode'); });
    }

    function create(host, mod) {
        var ids = {}, values = {}, overrides = {}, alt = false, images = {}, lastInput = null;
        var defs = {};
        mod.controls.forEach(function (def) { defs[def.id] = def; });
        function v(name, fallback) {
            var id = ids[name] || (ids[name] = fieldId(name));
            if (Object.prototype.hasOwnProperty.call(overrides, id)) { return overrides[id]; }
            return Object.prototype.hasOwnProperty.call(values, id) ? values[id] : fallback;
        }
        function def(name) { return defs[ids[name] || (ids[name] = fieldId(name))]; }

        var root = h('div.dk-live', null, null, host);
        var head = h('div.dk-live-head', null, [h('span.dk-detail-kicker', {text: t('live.title')})], root);
        h('div.dk-spacer', null, null, head);
        var modes = h('div.dk-segments', null, null, head);
        h('span.dk-segment.is-selected', {text: t('live.normal')}, null, modes);
        var frame = h('div.dk-live-frame', null, null, root);
        var canvas = h('canvas.dk-live-canvas', null, null, frame);
        var note = h('div.dk-live-note', {text: t('live.note')}, null, root);
        var paint = null;
        try { paint = canvas.getContext && canvas.getContext('2d'); } catch (error) { paint = null; }
        if (!paint) { note.textContent = t('live.unsupported'); }

        /* Drawing helpers --------------------------------------------------- */
        var px = 1, size = 0, zoom = 1, origin = {x: 0, y: 0};
        function sx(x) { return (x - origin.x) * px * zoom; }
        function sy(y) { return (y - origin.y) * px * zoom; }
        function meters(m) { return m * px * zoom; }
        function alpha(value) { return DK.clamp((typeof value === 'number' ? value : 100) / 100, 0, 1); }
        function dash(thickness, length, gap) {
            if (paint.setLineDash) { paint.setLineDash(length > 0 ? [length, Math.max(1, gap)] : []); }
            paint.lineWidth = Math.max(1, thickness || 1);
        }
        function mode(name) { return v(name, 0); }       // 0 client, 1 shown, 2 hidden
        function shown(name) { return mode(name) !== 2; }
        function macros(text, vehicle) {
            return String(text || '').replace(/\{\{([^}]+)\}\}/g, function (all, body) {
                var match = /^([\w-]+)(?:%\.(\d+)s)?/.exec(body), key = match ? match[1] : body, value;
                if (key === 'vehicle') { value = vehicle.vehicle; }
                else if (key === 'name' || key === 'nick') { value = vehicle.name; }
                else if (key === 'hp') { value = String(currentHp(vehicle)); }
                else if (key === 'hp-max') { value = String(vehicle.maxHp); }
                else if (key === 'hp-ratio') { value = String(Math.round(vehicle.hp * 100)); }
                else if (key === 'vtype' || key === 'type') { value = vehicle.type; }
                else if (key === 'cellsize') { value = String(MAP / 10); }
                else { value = ''; }
                return match && match[2] ? value.slice(0, Number(match[2])) : value;
            }).replace(/<[^>]*>/g, '');
        }
        function line(x1, y1, x2, y2) { paint.beginPath(); paint.moveTo(x1, y1); paint.lineTo(x2, y2); paint.stroke(); }
        function point(angle, distance) {
            var rad = angle * Math.PI / 180;
            return {x: SELF.x + Math.sin(rad) * distance, y: SELF.y - Math.cos(rad) * distance};
        }

        function background() {
            var mapAlpha = alpha(alt && v('presentation.alternativeEnabled', true) ? v('presentation.alternativeAlpha', 100) : v('presentation.normalAlpha', 100));
            paint.fillStyle = DK.rgba('#0A0B0C', alpha(v('presentation.backgroundAlpha', 100)));
            paint.fillRect(0, 0, size, size);
            paint.globalAlpha = mapAlpha;
            // The client's own top-down map (Prokhorovka, 1000 m); a drawn terrain while it loads or if it is missing.
            var map = load(DK.assets.mapTopDown);
            if (map && map._dkLoaded) {
                paint.drawImage(map, sx(0), sy(0), meters(MAP), meters(MAP));
            } else {
                var gradient = paint.createLinearGradient(0, 0, size, size);
                gradient.addColorStop(0, '#4E5A3C'); gradient.addColorStop(0.55, '#5F6A45'); gradient.addColorStop(1, '#3E4A33');
                paint.fillStyle = gradient;
                paint.fillRect(sx(0), sy(0), meters(MAP), meters(MAP));
                paint.fillStyle = 'rgba(70, 110, 140, 0.55)';                         // a river
                paint.beginPath(); paint.moveTo(sx(0), sy(330)); paint.lineTo(sx(1000), sy(250)); paint.lineTo(sx(1000), sy(300)); paint.lineTo(sx(0), sy(380)); paint.fill();
                paint.fillStyle = 'rgba(40, 52, 30, 0.6)';                            // woods
                [[150, 520, 90], [700, 650, 120], [860, 330, 70]].forEach(function (w) { paint.beginPath(); paint.arc(sx(w[0]), sy(w[1]), meters(w[2]), 0, Math.PI * 2); paint.fill(); });
            }
            paint.strokeStyle = 'rgba(0, 0, 0, 0.35)'; dash(1, 0, 0);
            for (var i = 1; i < 10; i++) { line(sx(i * 100), sy(0), sx(i * 100), sy(MAP)); line(sx(0), sy(i * 100), sx(MAP), sy(i * 100)); }
            paint.fillStyle = 'rgba(255, 255, 255, 0.45)';
            paint.font = Math.round(9 * zoom) + 'px Warhelios';
            paint.textAlign = 'center'; paint.textBaseline = 'middle';
            for (i = 0; i < 10; i++) {
                paint.fillText('ABCDEFGHJK'.charAt(i), sx(4), sy(i * 100 + 50));
                paint.fillText(String((i + 1) % 10), sx(i * 100 + 50), sy(8));
            }
            paint.globalAlpha = 1;
        }

        function circles() {
            var custom = v('changeColorCircles', true);
            ['draw', 'maxView', 'view', 'proximity'].forEach(function (key) {
                if (!shown('circles.' + key + '.mode')) { return; }
                var color = custom ? (DK.hex(v(CIRCLE_COLOR_KEYS[key])) || CLIENT_COLORS[key]) : CLIENT_COLORS[key];
                ring(RANGES[key], color, v('circles.' + key + '.alpha', 90), 'circles.' + key);
            });
            if (v('circles.shell.mode', 0) === 0) { ring(RANGES.shell, DK.hex(v('circles.shell.color')) || '#FF6666', v('circles.shell.alpha', 60), 'circles.shell'); }
            var extra = v('extraCircles', '[]');
            try { extra = typeof extra === 'string' ? JSON.parse(extra || '[]') : extra; } catch (error) { extra = []; }
            (DK.isArray(extra) ? extra : []).slice(0, 8).forEach(function (item) {
                if (!item || typeof item !== 'object') { return; }
                var radius = Number(item.radius || item.distance || item.r);
                if (radius > 0) { ring(radius, DK.hex(item.color) || '#FFFFFF', item.alpha === undefined ? 80 : item.alpha, null, item.thickness); }
            });
        }
        function ring(radius, color, opacity, prefix, thickness) {
            paint.strokeStyle = DK.rgba(color, alpha(opacity));
            if (prefix) { dash(v(prefix + '.thickness', 1), v(prefix + '.dash', 0), v(prefix + '.gap', 5)); } else { dash(thickness || 1, 0, 0); }
            paint.beginPath(); paint.arc(sx(SELF.x), sy(SELF.y), meters(radius), 0, Math.PI * 2); paint.stroke();
        }

        function lines() {
            var custom = v('lines.customStyle', false), length = v('lines.length', 500), opacity = alpha(v('lines.alpha', 80));
            function style(color, extraAlpha) {
                paint.strokeStyle = DK.rgba(color, opacity * extraAlpha);
                if (custom && v('lines.geometry', false)) { dash(v('lines.thickness', 1), v('lines.dash', 18), v('lines.gap', 5)); } else { dash(1, 0, 0); }
            }
            if (shown('lines.sector')) {
                style(custom ? DK.hex(v('lines.sectorColor')) || '#FFFFFF' : '#FFFFFF', 0.8);
                [-32, 32].forEach(function (offset) { var end = point(SELF.hull + offset, length); line(sx(SELF.x), sy(SELF.y), sx(end.x), sy(end.y)); });
            }
            if (v('lines.hull', true)) {
                style(DK.hex(v('lines.hullColor')) || '#60FF00', 1);
                var hull = point(SELF.hull, length * 0.6); line(sx(SELF.x), sy(SELF.y), sx(hull.x), sy(hull.y));
            }
            if (shown('lines.direction')) {
                var color = custom ? DK.hex(v('lines.directionColor')) || '#F2BB35' : '#F2BB35';
                style(color, alpha(v('lines.directionAlpha', 100)));
                var end = point(SELF.camera, length);
                line(sx(SELF.x), sy(SELF.y), sx(end.x), sy(end.y));
                var marks = v('lines.marks', 100);
                if (marks > 0) {
                    dash(1, 0, 0);
                    for (var d = marks; d < length; d += marks) {
                        var a = point(SELF.camera, d), side = 3 * zoom, rad = SELF.camera * Math.PI / 180;
                        line(sx(a.x) - Math.cos(rad) * side, sy(a.y) - Math.sin(rad) * side, sx(a.x) + Math.cos(rad) * side, sy(a.y) + Math.sin(rad) * side);
                    }
                }
                // Camera triangle at the vehicle.
                paint.fillStyle = DK.rgba(color, alpha(v('lines.triangleAlpha', 100)) * 0.35);
                var left = point(SELF.camera - 22, 70), right = point(SELF.camera + 22, 70);
                paint.beginPath(); paint.moveTo(sx(SELF.x), sy(SELF.y)); paint.lineTo(sx(left.x), sy(left.y)); paint.lineTo(sx(right.x), sy(right.y)); paint.closePath(); paint.fill();
            }
        }

        function distance(vehicle) { var dx = vehicle.x - SELF.x, dy = vehicle.y - SELF.y; return Math.sqrt(dx * dx + dy * dy); }
        function nearby(vehicle) {
            if (!v('nearby.enabled', true) || vehicle.team !== 'enemy' || vehicle.dead || vehicle.lost) { return false; }
            var range = v('nearby.range', 0), limit = range === 0 ? RANGES.view : range === 1 ? RANGES.shell : v('nearby.distance', 300);
            return distance(vehicle) <= limit;
        }
        function teamColor(vehicle) {
            if (vehicle.dead) { return TEAM.dead; }
            return TEAM[vehicle.team];
        }
        function marker(vehicle) {
            var scale = vehicle.dead ? v('icons.deadScale', 0.8) : vehicle.lost ? v('icons.lostScale', 0.9) : v('icons.scale', 1);
            var opacity = vehicle.dead ? alpha(v('icons.deadAlpha', 70)) : alpha(v('icons.alpha', 100));
            var x = sx(vehicle.x), y = sy(vehicle.y), r = 4.5 * scale * Math.max(1, zoom * 0.8);
            var color = teamColor(vehicle);
            if (vehicle.lost) {
                if (!v('showLastPositions', true)) { return false; }
                var tint = v('lostMarker.style', 0) === 1 ? '#8A8A8A' : DK.hex(v('lostMarker.' + vehicle.team + 'Color')) || '#B06060';
                color = tint;
                opacity = alpha(v('lostMarker.fade', false) ? Math.max(v('lostMarker.minimumAlpha', 25), 60) : 100);
                if (!v('lostMarker.icon', true)) { r = 2.5 * scale; }
            }
            if (nearby(vehicle)) {
                paint.strokeStyle = DK.rgba(DK.hex(v('nearby.color')) || '#FF3020', alpha(v('nearby.alpha', 90)));
                dash(2, 0, 0);
                paint.beginPath(); paint.arc(x, y, r + 5, 0, Math.PI * 2); paint.stroke();
            }
            paint.globalAlpha = opacity;
            paint.fillStyle = color;
            paint.strokeStyle = 'rgba(0, 0, 0, 0.8)'; dash(1, 0, 0);
            paint.beginPath();
            if (v('showVehicleTypes', true) && !(vehicle.lost && !v('lostMarker.icon', true))) {
                var glyph = {LT: 'i', MT: 'h', HT: 'g', TD: 'j', SPG: 'k'}[vehicle.type];
                paint.font = Math.round(r * 2.8) + 'px VehicleType';
                paint.textAlign = 'center'; paint.textBaseline = 'middle';
                paint.strokeText(glyph, x, y); paint.fillText(glyph, x, y);
            } else {
                paint.arc(x, y, r * 0.7, 0, Math.PI * 2);
                paint.fill(); paint.stroke();
            }
            if (vehicle.dead) { paint.strokeStyle = '#1A1A1A'; line(x - r, y - r, x + r, y + r); line(x - r, y + r, x + r, y - r); }
            paint.globalAlpha = 1;
            if (vehicle.lost && v('lostMarker.showSeconds', false)) { text('12s', x, y + r + 9, 8, '#DDDDDD', 1, 'center', true); }
            return true;
        }
        function text(value, x, y, sizePx, color, opacity, align, shadow) {
            paint.font = Math.round(sizePx) + 'px Warhelios';
            paint.textAlign = align; paint.textBaseline = 'middle';
            paint.globalAlpha = opacity;
            if (shadow) { paint.fillStyle = 'rgba(0, 0, 0, 0.9)'; paint.fillText(value, x + 1, y + 1); }
            paint.fillStyle = color; paint.fillText(value, x, y);
            paint.globalAlpha = 1;
        }
        function labelFor(vehicle) {
            var altMode = alt && v('presentation.alternativeEnabled', true);
            var base = vehicle.dead ? v('labels.dead') : vehicle.lost ? v('labels.lost') : altMode ? v('labels.alternative') : v('labels.normal');
            var team = vehicle.team === 'enemy' ? 'Enemy' : vehicle.team === 'squad' ? 'Squad' : 'Ally';
            var specific = vehicle.dead || vehicle.lost ? '' : altMode ? v('labels.alternative' + team, '') : v('labels.' + team.toLowerCase(), '');
            return macros(specific || base || '', vehicle);
        }
        function labels(vehicle) {
            if (!v('labels.enabled', true) && !v('showNames', false)) { return; }
            var value = labelFor(vehicle);
            if (!value) { return; }
            if (v('labels.avoidOverlap', false)) { value = value.slice(0, v('labels.compactLength', 14)); }
            var color = '#FFFFFF';
            if (v('labels.customColors', false)) {
                color = DK.hex(v(vehicle.dead ? 'labels.deadColor' : 'labels.' + vehicle.team + 'Color')) || color;
            } else if (v('labels.teamColors', true)) { color = teamColor(vehicle); }
            var align = ['left', 'center', 'right'][v('labels.align', 1)] || 'center';
            var x = sx(vehicle.x) + v('labels.x', 0) * zoom * 0.5, y = sy(vehicle.y) - 10 * zoom + v('labels.y', 0) * zoom * 0.5;
            text(value, x, y, v('labels.fontSize', 10) * Math.max(0.8, zoom * 0.8), color, alpha(v('labels.alpha', 100)), align, v('labels.shadow', true));
        }
        function health(vehicle) {
            var visibility = v('health.visibility', 0);
            if (vehicle.dead || vehicle.lost || visibility === 0 || (visibility === 1 && !alt)) { return; }
            var x = sx(vehicle.x) + v('health.x', 0) * zoom * 0.5, y = sy(vehicle.y) + v('health.y', 12) * zoom * 0.5, showMode = v('health.mode', 0);
            if (showMode === 2) {
                var w = v('health.width', 30) * Math.max(0.8, zoom * 0.7), hgt = Math.max(1, v('health.height', 3));
                paint.fillStyle = 'rgba(0, 0, 0, 0.7)'; paint.fillRect(x - w / 2 - 1, y - 1, w + 2, hgt + 2);
                paint.fillStyle = teamColor(vehicle); paint.fillRect(x - w / 2, y, w * vehicle.hp, hgt);
            } else {
                text(showMode === 1 ? Math.round(vehicle.hp * 100) + '%' : String(currentHp(vehicle)), x, y, v('health.fontSize', 9), '#FFFFFF', 1, 'center', true);
            }
        }
        function self() {
            var scale = v('icons.selfScale', 1), x = sx(SELF.x), y = sy(SELF.y), r = 7 * scale * Math.max(1, zoom * 0.8), rad = SELF.hull * Math.PI / 180;
            function rot(dx, dy) { return [x + dx * Math.cos(rad) - dy * Math.sin(rad), y + dx * Math.sin(rad) + dy * Math.cos(rad)]; }
            var tip = rot(0, -r), left = rot(-r * 0.7, r * 0.8), right = rot(r * 0.7, r * 0.8), back = rot(0, r * 0.35);
            paint.globalAlpha = alpha(v('icons.selfAlpha', 100));
            paint.fillStyle = DK.hex(v('icons.selfColor')) || '#FFFFFF';
            paint.strokeStyle = 'rgba(0, 0, 0, 0.85)'; dash(1, 0, 0);
            paint.beginPath(); paint.moveTo(tip[0], tip[1]); paint.lineTo(right[0], right[1]); paint.lineTo(back[0], back[1]); paint.lineTo(left[0], left[1]); paint.closePath();
            paint.fill(); paint.stroke();
            paint.globalAlpha = 1;
        }
        function artillery() {
            if (!v('artilleryAim.enabled', true)) { return; }
            var aim = {x: 690, y: 330}, scale = v('artilleryAim.scale', 50) / 100, sizePx = 46 * scale * zoom;
            var options = def('artilleryAim.src'), src = options && options.preview && options.preview.images ? options.preview.images[v('artilleryAim.src', 0)] : null;
            paint.globalAlpha = alpha(v('artilleryAim.alpha', 100));
            var image = src ? load(src) : null;
            if (image && image._dkLoaded) { paint.drawImage(image, sx(aim.x) - sizePx / 2, sy(aim.y) - sizePx / 2, sizePx, sizePx); }
            else {
                paint.strokeStyle = '#FFD24A'; dash(1.5, 0, 0);
                paint.beginPath(); paint.arc(sx(aim.x), sy(aim.y), sizePx / 2, 0, Math.PI * 2); paint.stroke();
                line(sx(aim.x) - sizePx / 2, sy(aim.y), sx(aim.x) + sizePx / 2, sy(aim.y)); line(sx(aim.x), sy(aim.y) - sizePx / 2, sx(aim.x), sy(aim.y) + sizePx / 2);
            }
            paint.globalAlpha = 1;
        }
        function load(src) {
            var url = DK.asset(src);
            if (!images[url]) {
                images[url] = document.createElement('img');
                images[url].onload = function () { images[url]._dkLoaded = true; draw(); };
                images[url].src = url;
            }
            return images[url];
        }
        function mapSize() {
            if (!v('mapSize.enabled', true)) { return; }
            var format = String(v('mapSize.format', '') || ''), colorMatch = /color=['"]?(#[0-9a-fA-F]{6})/.exec(format), sizeMatch = /size=['"]?(\d+)/.exec(format);
            var label = macros(format, VEHICLES[0]);
            text(label, 6 + v('mapSize.offsetX', 0) * 0.5, 10 + v('mapSize.offsetY', 0) * 0.5, sizeMatch ? Number(sizeMatch[1]) : 10,
                 colorMatch ? colorMatch[1] : '#FFCC66', alpha(v('mapSize.alpha', 80)), 'left', true);
        }

        var disposed=false;
        function draw() {
            if (disposed||!paint) { return; }
            // Fixed drawing resolution; the CSS gives the canvas a square size in UI units.
            size = RESOLUTION;
            if (canvas.width !== size) { canvas.width = size; canvas.height = size; }
            px = size / MAP;
            var altMode = alt && v('presentation.alternativeEnabled', true);
            zoom = altMode && v('presentation.zoom', true) ? v('zoomFactor', 1.5) : 1;
            origin = {x: 0, y: 0};
            if (zoom > 1) {
                var span = MAP / zoom, centre = v('presentation.center', true) ? SELF : {x: MAP / 2, y: MAP / 2};
                origin = {x: DK.clamp(centre.x - span / 2, 0, MAP - span), y: DK.clamp(centre.y - span / 2, 0, MAP - span)};
            }
            paint.clearRect(0, 0, size, size);
            if (!v('enabled', true)) {
                background();
                text(t('module.off'), size / 2, size / 2, 14, '#FFFFFF', 0.85, 'center', true);
                return;
            }
            background();
            circles();
            lines();
            artillery();
            VEHICLES.forEach(function (vehicle) {
                if (marker(vehicle)) { health(vehicle); labels(vehicle); }
            });
            self();
            mapSize();
        }

        return {
            update: function (next) {
                var input = JSON.stringify(next || {});
                var changed = input !== lastInput || Object.keys(overrides).length > 0;
                values = next || {}; overrides = {};
                if (changed) { draw(); lastInput = input; }
            },
            preview: function (key, value) { overrides[key] = value; draw(); },
            redraw: draw,
            node: root,
            dispose: function () { disposed=true;Object.keys(images).forEach(function(key){images[key].onload=null;images[key].onerror=null;});DK.remove(root); }
        };
    }

    DK.minimapPreview = {supports: supports, create: create, fieldId: fieldId};
}());
