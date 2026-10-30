/* DK Settings — pré-visualização da posição no ecrã.
   Ecrã 1920x1080 em miniatura (batalha, ou hangar para o relógio). O elemento do módulo aberto
   aparece destacado; os outros elementos do mod aparecem esbatidos para se verem sobreposições.
   Origens das posições, confirmadas no código do mod:
   - tempo de fecho da mira e tempo de voo: deslocamento a partir da mira (crosshairdisplayable);
   - vida do veículo: barra Gameface de 480x78 a partir da âncora alignX/alignY (vehicle_health.js);
   - marcas de excelência: painel alinhado à direita e ao centro vertical (panel.alignX/alignY);
   - Grande Calibre: a partir do canto superior esquerdo (textPosition);
   - distância ao alvo: a partir do marcador do veículo;
   - relógio do hangar: x a partir da esquerda, centro ou direita (screenHAlign), y a partir do topo. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h, t = DK.t;
    var W = 1920, H = 1080, CX = W / 2, CY = H / 2;
    var MARKER = {x: CX + 300, y: CY - 210};       // sample enemy vehicle marker
    var SAMPLE = DK.sample, PLAYER = SAMPLE.player;
    // Own health: the T32 at 79%, written and coloured as gameface/battle/vehicle_health.py does it.
    var OWN_HP = Math.round(PLAYER.maxHp * 0.79);
    var HEALTH_W = 480, HEALTH_H = 78;
    // High Caliber target: max(1000, 20% of the enemy team's HP) (battle/high_caliber_progress.py), 62% dealt.
    var ENEMY_HP = SAMPLE.enemies.reduce(function (sum, item) { return sum + item.maxHp; }, 0);
    var HC_TARGET = Math.max(1000, Math.ceil(ENEMY_HP * 0.2)), HC_PROGRESS = 62;
    var MODULES = {
        'legacy.DispersionTimer': {scene: 'battle', draw: aimTimer},
        'legacy.FlightTimer': {scene: 'battle', draw: flightTimer},
        'legacy.OwnHealth': {scene: 'battle', draw: health},
        'legacy.MarksOnGunBattle': {scene: 'battle', draw: marks},
        'legacy.MainGun': {scene: 'battle', draw: highCaliber},
        'legacy.DistanceMarker': {scene: 'battle', draw: distance},
        'legacy.main': {scene: 'hangar', draw: clock}
    };

    function key(mod) { return String(mod.id).split(':')[0]; }
    function supports(mod) { return !!MODULES[key(mod)]; }
    function grouped(value) { return String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
    // common/utils/formatting.percentToRgb: hue = min(0.8333, percent / 3), HSV channels rounded up.
    function percentColor(percent, saturation, brightness) {
        var hue = Math.min(0.8333, percent * 0.3333) * 6, i = Math.floor(hue), f = hue - i, v = brightness;
        var p = v * (1 - saturation), q = v * (1 - saturation * f), r = v * (1 - saturation * (1 - f));
        var rgb = [[v, r, p], [q, v, p], [p, v, r], [p, q, v], [r, p, v], [v, p, q]][i % 6];
        return DK.colors.rgbToHex(rgb.map(function (c) { return Math.ceil(c * 255); }));
    }
    function px(node, left, top) { node.style.left = Math.round(left) + 'rem'; node.style.top = Math.round(top) + 'rem'; }
    function text(stage, source, left, top, options) {
        var node = h('div.dk-hud-text', null, null, stage);
        DK.richText.render(node, source, {size: options.size || 16, color: options.color || '#FFFFFF', extra: options.extra});
        px(node, left, top);
        if (options.shadow !== false) { DK.toggle(node, 'has-shadow', true); }
        return node;
    }

    /* Elements -------------------------------------------------------------- */
    function aimTimer(stage, v) {
        if (!v('enabled', false)) { return null; }
        return text(stage, v('template', ''), CX + v('x', 60), CY + v('y', 110), {extra: {color: v('green', '#A6FFA6')}});
    }
    function flightTimer(stage, v) {
        if (!v('enabled', false)) { return null; }
        return text(stage, v('template', ''), CX + v('x', 100), CY + v('y', 100), {});
    }
    function health(stage, v) {
        if (!v('enabled', true)) { return null; }
        var percent = OWN_HP / PLAYER.maxHp, fill = h('div.dk-hud-health-fill');
        fill.style.width = (percent * 100) + '%';
        fill.style.backgroundColor = percentColor(percent, v('avgColor.saturation', 0.7), v('avgColor.brightness', 0.9));
        var bar = h('div.dk-hud-health', null, [h('div.dk-hud-health-track', null, [fill]),
            h('img.dk-hud-health-frame', {src: 'coui://gui/gameface/mods/driftkings/vehicle_health/frame.png'}),
            h('div.dk-hud-health-text', {text: OWN_HP + ' / ' + PLAYER.maxHp})], stage);
        // Anchored like the battle bar (shared kit position): x/y offsets from alignX/alignY.
        var x = v('x', 0), y = v('y', -80), alignX = v('alignX', 'center'), alignY = v('alignY', 'bottom');
        var left = alignX === 'right' ? W - HEALTH_W + x : alignX === 'center' ? (W - HEALTH_W) / 2 + x : x;
        var top = alignY === 'bottom' ? H - HEALTH_H + y : alignY === 'center' ? (H - HEALTH_H) / 2 + y : y;
        px(bar, left, top);
        return bar;
    }
    function marks(stage, v) {
        if (!v('enabled', true) || !v('gameface.enabled', true)) { return null; }
        var scale = v('battleMessageSizeInPercent', 60) / 60, mini = v('gameface.miniMode', true), accent = DK.hex(v('gameface.accentColor')) || '#E8C55A';
        var panel = h('div.dk-hud-panel', null, null, stage);
        panel.style.width = Math.round((mini ? 210 : 280) * scale) + 'rem';
        panel.style.fontSize = Math.round(15 * scale) + 'rem';
        if (v('background', false)) { panel.style.backgroundColor = 'rgba(0,0,0,' + v('gameface.backgroundOpacity', 0.65) + ')'; }
        h('div.dk-hud-panel-title', {text: '★★☆  87.4%', style: {color: accent}}, null, panel);
        if (v('showDelta', true)) { h('div', {text: '▲ +0.62%'}, null, panel); }
        if (!mini && v('showDamage', true)) { h('div', {text: '2 380 / 3 500'}, null, panel); }
        if (!mini && v('gameface.showTargetDamage', true)) { h('div', {text: '88% → 3 720'}, null, panel); }
        var width = (mini ? 210 : 280) * scale;
        // Anchored to the right edge and the vertical centre.
        px(panel, W + v('panel.x', 0) - width - 8, CY + v('panel.y', -177));
        return panel;
    }
    function highCaliber(stage, v) {
        if (!v('enabled', true)) { return null; }
        // Same parts as high_caliber_gameface/main_gun.js: medal, HP still needed, reason, bar and percentage.
        var scale = v('gameface.scale', 1), accent = DK.hex(v('gameface.accentColor')) || '#FFCD4F';
        var panel = h('div.dk-hud-panel.dk-hud-hc', null, null, stage);
        panel.style.width = Math.round(260 * scale) + 'rem';
        panel.style.fontSize = Math.round(15 * scale) + 'rem';
        if (v('backGroundEnabled', false)) { panel.style.backgroundColor = 'rgba(15,18,22,' + v('background.alpha', 80) / 100 + ')'; }
        var head = h('div.dk-hud-hc-head', null, null, panel);
        var medal = h('img.dk-hud-hc-medal', {src: DK.asset('gui/maps/icons/achievement/32x32/mainGun.png')}, null, head);
        medal.addEventListener('error', function () { DK.remove(medal); });
        var info = h('div', null, null, head);
        h('div.dk-hud-hc-value', {text: grouped(HC_TARGET * (100 - HC_PROGRESS) / 100) + ' HP'}, null, info);
        if (v('gameface.showSecondary', true)) { h('div.dk-hud-panel-sub', {text: t('hud.hcRemaining')}, null, info); }
        var showBar = v('gameface.showProgress', true), showPercent = v('gameface.showPercentage', true);
        if (showBar || showPercent) {
            var foot = h('div.dk-hud-hc-foot', null, null, panel);
            if (showBar) {
                var track = h('div.dk-hud-progress', null, null, foot), fill = h('div.dk-hud-progress-fill', null, null, track);
                fill.style.width = HC_PROGRESS + '%'; fill.style.backgroundColor = accent;
            }
            if (showPercent) { h('span', {text: HC_PROGRESS + '%'}, null, foot); }
        }
        px(panel, v('textPosition.x', 0), v('textPosition.y', 446));
        return panel;
    }
    function distance(stage, v) {
        var marker = h('div.dk-hud-marker', null, [h('div.dk-hud-marker-bar'), h('div.dk-hud-marker-name', {text: 'IS-7'})], stage);
        px(marker, MARKER.x - 40, MARKER.y - 30);
        if (!v('enabled', true)) { return null; }
        var anchorY = [MARKER.y, MARKER.y + 120, MARKER.y + 170][v('anchorPosition', 0)] || MARKER.y;
        var digits = v('decimalPrecision', 0), shown = (315.27).toFixed(digits) + ' m';
        var node = text(stage, shown, MARKER.x + v('anchorHorizontalOffset', 24), anchorY + v('anchorVerticalOffset', 16),
                        {size: v('textSize', 11), color: DK.hex(v('textColor')) || '#FFFFFF', shadow: v('drawTextShadow', true)});
        node.style.opacity = v('textAlpha', 1);
        return node;
    }
    function clock(stage, v) {
        if (!v('enabled', true) || !v('clock.enabled', true)) { return null; }
        var group = h('div.dk-hud-group', null, null, stage);
        for (var i = 0; i < 2; i++) {
            var p = 'clock.formats.' + i + '.', width = v(p + 'width', 0), height = v(p + 'height', 0), x = v(p + 'x', 0);
            var box = h('div.dk-hud-box', null, null, group);
            var hAlign = v(p + 'screenHAlign', 2), align = ['left', 'center', 'right'][v(p + 'textFormat.align', 0)] || 'left';
            DK.richText.render(box, v(p + 'format', ''), {size: 16, color: DK.hex(v(p + 'textFormat.color')) || '#959688', align: align});
            if (width) { box.style.width = width + 'rem'; }
            if (height) { box.style.height = height + 'rem'; }
            box.style.justifyContent = ['flex-start', 'center', 'flex-end'][v(p + 'textFormat.valign', 0)] || 'flex-start';
            if (v(p + 'shadow.enabled', false)) {
                var shadow = DK.hex(v(p + 'shadow.color')) || '#000000';
                box.style.textShadow = '0 0 ' + v(p + 'shadow.blur', 4) + 'rem ' + DK.rgba(shadow, v(p + 'shadow.alpha', 100) / 100);
            }
            var measured = width || 120;
            var left = hAlign === 0 ? x : hAlign === 1 ? CX + x - measured / 2 : W + x - measured;
            px(box, left, v(p + 'y', 0));
        }
        return group;
    }

    /* Component --------------------------------------------------------------- */
    function create(host, mod) {
        var current = key(mod), info = MODULES[current], all = {}, overrides = {};
        var root = h('div.dk-live', null, null, host), zoomed = true;
        var head = h('div.dk-live-head', null, [h('span.dk-detail-kicker', {text: t('hud.title')})], root);
        h('div.dk-spacer', null, null, head);
        var views = h('div.dk-segments', null, null, head);
        var whole = h('button.dk-segment', {text: t('hud.whole')}, null, views);
        var close = h('button.dk-segment.is-selected', {text: t('hud.zoom')}, null, views);
        function setZoom(on) { zoomed = on; DK.toggle(whole, 'is-selected', !on); DK.toggle(close, 'is-selected', on); draw(); }
        whole.addEventListener('click', function (event) { DK.stop(event); setZoom(false); });
        close.addEventListener('click', function (event) { DK.stop(event); setZoom(true); });
        var frame = h('div.dk-hud-frame' + (info.scene === 'hangar' ? '.is-hangar' : ''), null, null, root);
        var stage = h('div.dk-hud-stage', null, null, frame);
        h('div.dk-live-note', {text: t(info.scene === 'hangar' ? 'hud.noteHangar' : 'hud.note')}, null, root);

        function reader(modId) {
            var values = all[modId] || {}, own = modId === mod.id;
            return function (name, fallback) {
                var id = DK.minimapPreview.fieldId(name);
                if (own && Object.prototype.hasOwnProperty.call(overrides, id)) { return overrides[id]; }
                return Object.prototype.hasOwnProperty.call(values, id) ? values[id] : fallback;
            };
        }
        function draw() {
            DK.clear(stage);
            // Real client images behind the elements: a Prokhorovka battle shot, or a T32 in a dark hangar.
            var scene = h('div.dk-hud-scene' + (info.scene === 'hangar' ? '.is-hangar' : ''), null, null, stage);
            if (info.scene === 'battle') {
                scene.style.backgroundImage = 'url(' + DK.asset(DK.assets.battleScene) + '), linear-gradient(to bottom, #5d7182 0%, #8b9a8a 44%, #5b6346 46%, #3f4632 100%)';
            } else {
                var tank = h('img.dk-hud-hangar-tank', {src: DK.asset(DK.assets.hangarTank)}, null, scene);
                tank.addEventListener('error', function () { tank.style.display = 'none'; });
            }
            if (info.scene === 'battle') {
                var aim = h('div.dk-hud-aim', null, [h('div.dk-hud-aim-dot')], stage);
                px(aim, CX - 46, CY - 46);
            }
            // Other elements of the same scene first, faded; the open module last, on top.
            Object.keys(MODULES).forEach(function (other) {
                if (other === current || MODULES[other].scene !== info.scene) { return; }
                var modId = findId(other);
                if (!modId) { return; }
                var node = MODULES[other].draw(stage, reader(modId));
                if (node) { DK.toggle(node, 'is-other', true); }
            });
            var mine = info.draw(stage, reader(mod.id));
            if (mine) { DK.toggle(mine, 'is-current', true); }
            else { h('div.dk-hud-off', {text: t('module.off')}, null, stage); }
            focus(mine);
        }
        // "Zoom" fits the open module's elements at up to 80% of the real size; "Whole screen" shows 1920x1080.
        function focus(node) {
            var unit = parseFloat(document.documentElement.style.fontSize) || 1;
            var frameW = frame.clientWidth / unit, frameH = frame.clientHeight / unit;
            var scale = Math.min(frameW / W, frameH / H);
            stage.style.transform = 'scale(' + scale + ')';
            if (!zoomed || !node) { return; }
            var boxes = node.className.indexOf('dk-hud-group') >= 0 ? node.children : [node];
            var left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
            for (var i = 0; i < boxes.length; i++) {
                var box = boxes[i], x = box.offsetLeft / unit, y = box.offsetTop / unit;
                left = Math.min(left, x); top = Math.min(top, y);
                right = Math.max(right, x + box.offsetWidth / unit); bottom = Math.max(bottom, y + box.offsetHeight / unit);
            }
            if (!isFinite(left) || !isFinite(top)) { return; }
            scale = Math.min(0.8, frameW / Math.max(1, right - left + 24), frameH / Math.max(1, bottom - top + 24));
            var tx = frameW / 2 - (left + right) / 2 * scale, ty = frameH / 2 - (top + bottom) / 2 * scale;
            stage.style.transform = 'translate(' + tx + 'rem, ' + ty + 'rem) scale(' + scale + ')';
        }
        function findId(moduleKey) {
            var ids = Object.keys(all);
            for (var i = 0; i < ids.length; i++) { if (ids[i].split(':')[0] === moduleKey) { return ids[i]; } }
            return null;
        }
        return {
            update: function (values, everything) { all = everything || {}; all[mod.id] = values; overrides = {}; draw(); },
            preview: function (id, value) { overrides[id] = value; draw(); },
            redraw: draw,
            dispose: function () { DK.remove(root); }
        };
    }

    DK.hudPreview = {supports: supports, create: create};
}());
