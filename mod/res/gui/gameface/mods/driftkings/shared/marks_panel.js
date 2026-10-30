/* Shared presentation and model lifecycle. No marks calculation lives in JS. */
(function () {
    'use strict';
    if (window.__dkMarksKit) { return; }
    function node(tag, cls, parent, text) {
        var value = document.createElement(tag);
        value.className = cls;
        if (text !== undefined) { value.textContent = text; }
        if (parent) { parent.appendChild(value); }
        return value;
    }
    function text(element, value) {
        value = value === null || value === undefined ? '\u2014' : String(value);
        if (element.textContent !== value) { element.textContent = value; }
    }
    function style(element, key, value) { if (element.style[key] !== value) { element.style[key] = value; } }
    function show(element, visible) { style(element, 'display', visible ? '' : 'none'); }
    function number(value, fallback) { return typeof value === 'number' && isFinite(value) ? value : fallback; }
    var locale = {decimal: '.', group: ','};
    function setLocale(cfg) {
        locale.decimal = cfg && typeof cfg.decimalSeparator === 'string' && cfg.decimalSeparator ? cfg.decimalSeparator : '.';
        locale.group = cfg && typeof cfg.groupSeparator === 'string' ? cfg.groupSeparator : ',';
    }
    function formatted(value, precision) {
        if (typeof value !== 'number' || !isFinite(value)) { return '\u2014'; }
        var parts = (precision === undefined ? Math.round(value).toString() : value.toFixed(precision)).split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, locale.group);
        return parts.join(locale.decimal);
    }
    function percent(value) {
        return typeof value === 'number' && isFinite(value) ? value.toFixed(2).replace('.', locale.decimal) + '%' : '\u2014';
    }
    function roman(value) {
        var n = number(value, 0), tiers = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'];
        return n > 0 && n === Math.round(n) ? (tiers[n] || String(n)) : '';
    }
    function color(value, fallback) {
        if (typeof value === 'number' && isFinite(value)) { return '#' + ('000000' + Math.max(0, Math.min(16777215, value)).toString(16)).slice(-6); }
        return /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
    }
    function label(data, key, fallback) { return (data.labels || {})[key] || fallback; }
    // Warhelios has no star glyphs, so the marks are drawn from shared/assets images.
    function stars(parent) {
        var row = node('div', 'dk-mog__stars', parent);
        return [0, 1, 2].map(function () { return node('span', 'dk-mog__star', row); });
    }
    function updateStars(items, count) {
        items.forEach(function (item, index) {
            var cls = 'dk-mog__star' + (index < count ? ' dk-mog__star--earned' : '');
            if (item.className !== cls) { item.className = cls; }
        });
    }
    function graph(parent) {
        var area = node('div', 'dk-mog__graph', parent), segments = [], points = [], refs = [], previous = null;
        var axisMax = node('span', 'dk-mog__axis dk-mog__axis--max', area), axisMin = node('span', 'dk-mog__axis dk-mog__axis--min', area);
        function pool(list, tag, cls, count) { while (list.length < count) { list.push(node(tag, cls, area)); } }
        return {
            element: area,
            draw: function (samples) {
                // The size is part of the signature: segments are laid out in pixels, so a width change must redraw.
                var signature = JSON.stringify(samples || []) + '|' + area.clientWidth + 'x' + area.clientHeight + '|' + locale.decimal + '|' + locale.group;
                if (signature === previous) { return; }
                previous = signature;
                var valid = (samples || []).filter(function (p) { return typeof p.battles === 'number' && isFinite(p.battles) && typeof p.percent === 'number' && isFinite(p.percent); });
                var width = 100, min = 100, max = 0;
                valid.forEach(function (p) { min = Math.min(min, p.percent); max = Math.max(max, p.percent); });
                var span = Math.max(.1, max - min), first = valid.length ? valid[0].battles : 0;
                var duration = valid.length ? Math.max(1, valid[valid.length - 1].battles - first) : 1;
                function yOf(value) { return 90 - (value - min) / span * 80; }
                pool(points, 'i', 'dk-mog__point', valid.length);
                pool(segments, 'i', 'dk-mog__segment', Math.max(0, valid.length - 1));
                points.forEach(function (dot, i) {
                    show(dot, i < valid.length);
                    if (i >= valid.length) { return; }
                    var x = (valid[i].battles - first) / duration * width, y = yOf(valid[i].percent);
                    style(dot, 'left', x + '%'); style(dot, 'top', y + '%');
                    dot.title = valid[i].battles + ': ' + percent(valid[i].percent);
                    if (i > 0) {
                        var px = (valid[i - 1].battles - first) / duration * width, py = yOf(valid[i - 1].percent);
                        var dx = (x - px) / 100 * area.clientWidth, dy = (y - py) / 100 * area.clientHeight;
                        style(segments[i - 1], 'left', px + '%'); style(segments[i - 1], 'top', py + '%');
                        style(segments[i - 1], 'width', Math.sqrt(dx * dx + dy * dy) + 'px');
                        style(segments[i - 1], 'transform', 'rotate(' + Math.atan2(dy, dx) + 'rad)');
                    }
                });
                segments.forEach(function (line, i) { show(line, i < valid.length - 1); });
                // Reference lines for the excellence thresholds that fall inside the plotted range.
                var visible = valid.length ? [65, 85, 95].filter(function (t) { return t > min && t < max; }) : [];
                pool(refs, 'div', 'dk-mog__ref', visible.length);
                refs.forEach(function (line, i) {
                    show(line, i < visible.length);
                    if (i >= visible.length) { return; }
                    style(line, 'top', yOf(visible[i]) + '%');
                    text(line, formatted(visible[i]) + '%');
                });
                text(axisMax, valid.length ? percent(max) : ''); text(axisMin, valid.length ? percent(min) : '');
                show(axisMax, valid.length > 0); show(axisMin, valid.length > 0);
                area.title = valid.length ? percent(min) + ' \u2014 ' + percent(max) : '';
            },
            invalidate: function () { previous = null; }
        };
    }
    // One scale for the three excellence marks. Positions are piecewise linear so each interval has room:
    // 0-65 | 65-85 | 85-95 | 95-100. The fill shows the real percentage; ticks fill when a mark is reached.
    var SCALE_STOPS = [[0, 0], [65, 36], [85, 64], [95, 88], [100, 100]];
    function scalePosition(percentValue) {
        var v = Math.max(0, Math.min(100, number(percentValue, 0)));
        for (var i = 1; i < SCALE_STOPS.length; i++) {
            if (v <= SCALE_STOPS[i][0]) {
                var a = SCALE_STOPS[i - 1], b = SCALE_STOPS[i];
                return a[1] + (v - a[0]) / (b[0] - a[0]) * (b[1] - a[1]);
            }
        }
        return 100;
    }
    function scale(parent) {
        var box = node('div', 'dk-mog__scale', parent), track = node('div', 'dk-mog__bar', box), fill = node('div', 'dk-mog__fill', track);
        var marker = node('i', 'dk-mog__marker', track), ticks = [], names = node('div', 'dk-mog__ticks', box);
        [65, 85, 95].forEach(function (limit) {
            var left = scalePosition(limit) + '%';
            var tick = node('i', 'dk-mog__tick', track); style(tick, 'left', left);
            var name = node('span', 'dk-mog__tickname', names, limit + '%'); style(name, 'left', left);
            ticks.push({tick: tick, name: name, limit: limit});
        });
        return {
            element: box, fill: fill,
            update: function (value, earned, observed, showMarks) {
                show(names, showMarks !== false);
                style(box, 'paddingBottom', showMarks === false ? '0' : '');
                style(fill, 'width', scalePosition(value) + '%');
                ticks.forEach(function (item, index) {
                    show(item.tick, showMarks !== false);
                    var hit = number(value, 0) >= item.limit || number(earned, 0) > index;
                    item.tick.className = 'dk-mog__tick' + (hit ? ' dk-mog__tick--hit' : '');
                    item.name.className = 'dk-mog__tickname' + (hit ? ' dk-mog__tickname--hit' : '');
                });
                var showMarker = typeof observed === 'number' && isFinite(observed);
                show(marker, showMarker);
                if (showMarker) { style(marker, 'left', scalePosition(observed) + '%'); }
            }
        };
    }
    function connect(feature, owner, root, render, position, savePosition) {
        if (window[owner]) { window[owner].dispose(); }
        var disposed = false, model = null, resourceId = null, callbackId = null;
        var lastPayload = null, pending = null, drag = null, shield = null, data = {};
        function capture(active) {
            // Battle views only receive input over hit-testable nodes. A full-screen layer keeps
            // mousemove/mouseup flowing once the cursor leaves the panel during a drag.
            if (active && !shield) {
                shield = node('div', 'dk-drag-shield', document.body);
                style(shield, 'position', 'fixed'); style(shield, 'left', '0'); style(shield, 'top', '0');
                style(shield, 'width', '100%'); style(shield, 'height', '100%'); style(shield, 'zIndex', '9999');
                style(shield, 'pointerEvents', 'auto'); style(shield, 'cursor', 'move');
                style(shield, 'backgroundColor', 'rgba(0,0,0,0.004)');
            } else if (!active && shield) {
                if (shield.parentNode) { shield.parentNode.removeChild(shield); }
                shield = null;
            }
        }
        function cancel() { drag = null; capture(false); }
        function input(event) {
            // Capture before the native UI or nested header nodes stop bubbling.
            var target = event.target, header = root.firstChild;
            while (target && target !== root) {
                if (target === header) { start(event); return; }
                target = target.parentNode;
            }
        }
        function release() {
            if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
            callbackId = null; model = null; resourceId = null; lastPayload = null;
        }
        function update() {
            pending = null;
            if (disposed) { return; }
            var found = null, id = null;
            if (window.subViews) {
                var ids = window.subViews.ids();
                for (var i = 0; i < ids.length; i++) {
                    var child = window.subViews.get(ids[i]);
                    if (child && child.model && child.model.DriftkingsUI && child.model.DriftkingsUI.name === feature) { found = child.model; id = ids[i]; break; }
                }
            }
            if (!found) { release(); data = {}; cancel(); show(root, false); return; }
            if (id !== resourceId || found !== model) {
                release(); resourceId = id; model = found;
                callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
            }
            if (lastPayload === model.payload) { return; }
            lastPayload = model.payload;
            try { data = JSON.parse(model.payload || '{}'); } catch (error) { data = {}; }
            if ((data.config || {}).locked || (data.config || {}).draggable === false) { cancel(); }
            var visible = !!(data.config || {}).visible;
            style(root, 'display', visible ? 'block' : 'none');
            if (!visible) { cancel(); return; }
            render(data); position(root, data.config || {});
        }
        function schedule() { if (!disposed && pending === null) { pending = setTimeout(update, 0); } }
        function changed() { if (!model || model.payload !== lastPayload) { schedule(); } }
        function resize() { if (!disposed && (data.config || {}).visible) { render(data, true); position(root, data.config || {}); } }
        function start(event) {
            if (!savePosition || event.button !== 0 || !model || !(data.config || {}).visible || (data.config || {}).locked || (data.config || {}).draggable === false) { return; }
            var rect = root.getBoundingClientRect(); drag = {x: event.clientX, y: event.clientY, left: rect.left, top: rect.top};
            capture(true);
            event.preventDefault(); event.stopPropagation();
        }
        function move(event) {
            if (!drag) { return; }
            var bounds = root.getBoundingClientRect();
            style(root, 'left', Math.max(0, Math.min(window.innerWidth - bounds.width, drag.left + event.clientX - drag.x)) + 'px');
            style(root, 'top', Math.max(0, Math.min(window.innerHeight - bounds.height, drag.top + event.clientY - drag.y)) + 'px');
            event.preventDefault(); event.stopPropagation();
        }
        function end() {
            if (!drag) { return; }
            cancel();
            if (model && typeof model.onSavePosition === 'function') { model.onSavePosition(savePosition(root, data.config || {})); }
        }
        function stop(event) { event.stopPropagation(); }
        function dispose() {
            if (disposed) { return; }
            disposed = true; cancel();
            if (pending !== null) { clearTimeout(pending); pending = null; }
            engine.off('viewEnv.onDataChanged', changed); engine.off('subViews.onAdded', schedule); engine.off('subViews.onRemoved', schedule);
            window.removeEventListener('resize', resize); window.removeEventListener('unload', dispose);
            document.removeEventListener('mousedown', input, true);
            document.removeEventListener('mousemove', move, true); document.removeEventListener('mouseup', end, true);
            root.removeEventListener('mousedown', stop); root.removeEventListener('click', stop);
            release(); if (root.parentNode) { root.parentNode.removeChild(root); }
            if (window[owner] && window[owner].dispose === dispose) { delete window[owner]; }
        }
        window[owner] = {dispose: dispose};
        engine.whenReady.then(function () {
            if (disposed) { return; }
            engine.on('viewEnv.onDataChanged', changed); engine.on('subViews.onAdded', schedule); engine.on('subViews.onRemoved', schedule);
            window.addEventListener('resize', resize); window.addEventListener('unload', dispose);
            if (savePosition) {
                root.addEventListener('mousedown', stop); root.addEventListener('click', stop);
                document.addEventListener('mousedown', input, true);
                document.addEventListener('mousemove', move, true); document.addEventListener('mouseup', end, true);
            }
            schedule();
        });
        return window[owner];
    }
    function unit() { return parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 1; }
    function position(root, cfg) {
        var bounds = root.getBoundingClientRect(), match = /scale\(([^)]+)\)/.exec(root.style.transform);
        var fit = Math.min(1, window.innerHeight * .94 / Math.max(1, bounds.height));
        if (fit < 1 && match) {
            style(root, 'transform', 'scale(' + parseFloat(match[1]) * fit + ')');
            bounds = root.getBoundingClientRect();
        }
        var width = bounds.width, height = bounds.height;
        var x = number(cfg.x, 20) * unit(), y = number(cfg.y, 20) * unit();
        if (cfg.alignX === 'right') { x += window.innerWidth - width; }
        else if (cfg.alignX === 'center') { x += (window.innerWidth - width) / 2; }
        if (cfg.alignY === 'bottom') { y += window.innerHeight - height; }
        else if (cfg.alignY === 'center') { y += (window.innerHeight - height) / 2; }
        style(root, 'left', Math.max(0, Math.min(window.innerWidth - width, x)) + 'px');
        style(root, 'top', Math.max(0, Math.min(window.innerHeight - height, y)) + 'px');
    }
    function anchor(start, size, total, names) {
        var middle = start + size / 2;
        return middle < total / 3 ? names[0] : middle > total * 2 / 3 ? names[2] : names[1];
    }
    function savedPosition(root) {
        // Anchor to the nearest screen edge, like the native HUD, so a resolution change keeps the
        // panel beside the elements it was placed next to instead of sliding underneath them.
        var x = parseFloat(root.style.left), y = parseFloat(root.style.top), rect = root.getBoundingClientRect();
        var alignX = anchor(x, rect.width, window.innerWidth, ['left', 'center', 'right']);
        var alignY = anchor(y, rect.height, window.innerHeight, ['top', 'center', 'bottom']);
        if (alignX === 'right') { x -= window.innerWidth - rect.width; }
        else if (alignX === 'center') { x -= (window.innerWidth - rect.width) / 2; }
        if (alignY === 'bottom') { y -= window.innerHeight - rect.height; }
        else if (alignY === 'center') { y -= (window.innerHeight - rect.height) / 2; }
        return {x: Math.round(x / unit()), y: Math.round(y / unit()), alignX: alignX, alignY: alignY};
    }
    function theme(root, cfg, compact, baseWidth) {
        var accent = color(cfg.accentColor, '#E8C55A'), bg = color(cfg.backgroundColor, '#0b141b');
        style(root, 'borderColor', '#518896'); style(root, 'color', color(cfg.titleColor, '#E8E4DA'));
        style(root, 'backgroundColor', 'rgba(' + parseInt(bg.slice(1,3),16) + ',' + parseInt(bg.slice(3,5),16) + ',' + parseInt(bg.slice(5,7),16) + ',' + number(cfg.backgroundOpacity, number(cfg.backgroundAlpha, .82)) + ')');
        var scale = Math.max(.1, Math.min(10, number(cfg.scale, 1)));
        var base = number(baseWidth, compact ? 650 : cfg.compactMode ? 640 : 760);
        scale = Math.min(scale, window.innerWidth / (base * unit()) * .96);
        style(root, 'width', base + 'rem'); style(root, 'transform', 'scale(' + scale + ')');
        style(root, 'opacity', String(number(cfg.alpha, 1)));
        return accent;
    }
    window.__dkMarksKit = {node:node, text:text, style:style, show:show, number:number,
        setLocale:setLocale, formatted:formatted, percent:percent, roman:roman, label:label, stars:stars, updateStars:updateStars,
        graph:graph, scale:scale, connect:connect, position:position, savedPosition:savedPosition, theme:theme};
}());
