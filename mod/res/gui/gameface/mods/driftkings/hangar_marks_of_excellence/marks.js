/* Hangar marks: a compact card under the native mission column and a "show more" side panel.
   Python supplies every value; the card only follows the column's position and width. */
(function () {
    'use strict';
    var K = window.__dkMarksKit, generation = window.__dkHangarMarksLoad || {};
    if (generation.cancelled || window.__dkHangarMarks) { return; }
    var stopped = false, status = 'initializing', cleanups = [], frame = null;
    var model = null, resourceId = null, callbackId = null, pendingUpdate = null, previous = null;
    var root = null, timer = null;
    function attempt(action) { try { action(); } catch (error) { console.error('[Driftkings] Hangar marks cleanup: ' + error); if (typeof generation.report === 'function') { generation.report(error); } } }
    function releaseModel() {
        var callback = callbackId, id = resourceId;
        callbackId = null; model = null; resourceId = null; previous = null;
        if (callback !== null) { attempt(function () { viewEnv.removeDataChangedCallback(callback, id); }); }
    }
    function dispose() {
        if (stopped) { return; }
        stopped = true;
        if (pendingUpdate !== null) { attempt(function () { clearTimeout(pendingUpdate); }); pendingUpdate = null; }
        if (frame !== null) { attempt(function () { cancelAnimationFrame(frame); }); frame = null; }
        if (timer !== null) { attempt(function () { clearInterval(timer); }); timer = null; }
        cleanups.splice(0).reverse().forEach(attempt);
        releaseModel();
        attempt(function () { if (root && root.parentNode) { root.parentNode.removeChild(root); } });
        if (window.__dkHangarMarks === owner) { delete window.__dkHangarMarks; }
        if (status !== 'failed') { status = 'destroyed'; }
    }
    function failed(error) {
        if (stopped) { return; }
        status = 'failed'; console.error('[Driftkings] Hangar marks renderer failed: ' + error);
        dispose();
        if (typeof generation.fail === 'function') { generation.fail(error); }
    }
    function guard(action) {
        return function () {
            if (stopped || generation.cancelled) { return; }
            try { return action.apply(null, arguments); } catch (error) { failed(error); }
        };
    }
    function listen(target, name, action, capture) {
        var callback = guard(action);
        cleanups.push(function () { target.removeEventListener(name, callback, capture); });
        target.addEventListener(name, callback, capture);
    }
    function listenEngine(name, action) {
        var callback = guard(action);
        cleanups.push(function () { engine.off(name, callback); }); engine.on(name, callback);
    }
    var owner = {dispose: dispose, generation: generation, getState: function () { return status; }};
    window.__dkHangarMarks = owner;
    try {
    // The column is a React widget laid out by its own animations, so the card sits under it
    // instead of inside it and is re-placed while visible.
    var COLUMN = '[class*="HangarScreen_userMissions_"]';
    var GAP = 8, FALLBACK_WIDTH = 319, FALLBACK_TOP = .45;
    root = document.createElement('div'); root.className = 'dk-moe'; document.body.appendChild(root);
    var card = K.node('div', 'dk-moe-card', root);
    K.node('div', 'dk-moe-card__hover', card);
    var iconBox = K.node('div', 'dk-moe-card__icon', card), icon = K.node('img', '', iconBox);
    icon.alt = '';
    var body = K.node('div', 'dk-moe-card__body', card);
    var title = K.node('div', 'dk-moe-card__title', body), stars = K.stars(body);
    var message = K.node('div', 'dk-moe-card__message', body);
    var side = K.node('div', 'dk-moe-card__side', card);
    var percent = K.node('div', 'dk-moe-card__percent', side);
    var more = K.node('div', 'dk-moe-card__more', side), moreText = K.node('span', '', more);
    K.node('i', 'dk-moe-card__caret', more);

    var detail = K.node('div', 'dk-moe-detail', root);
    var head = K.node('div', 'dk-moe-detail__head', detail);
    var heading = K.node('div', 'dk-moe-detail__title', head), close = K.node('div', 'dk-moe-detail__close', head, '×');
    var vehicle = K.node('div', 'dk-moe-detail__vehicle', detail);
    var hero = K.node('div', 'dk-moe-detail__hero', detail);
    var heroText = K.node('div', '', hero), currentLabel = K.node('div', 'dk-moe-detail__label', heroText);
    var current = K.node('div', 'dk-moe-detail__percent', heroText), heroStars = K.stars(hero);
    var progress = K.node('div', 'dk-moe-detail__progress', detail), scale = K.scale(progress);
    var next = K.node('div', 'dk-moe-detail__next', progress), nextLabel = K.node('span', '', next), gap = K.node('span', '', next);
    var metrics = K.node('div', 'dk-moe-detail__metrics', detail), cards = [];
    ['ema', 'target', 'needed'].forEach(function () {
        var item = K.node('div', 'dk-moe-detail__metric', metrics);
        cards.push({label: K.node('div', 'dk-moe-detail__label', item), value: K.node('div', 'dk-moe-detail__value', item)});
    });
    var note = K.node('div', 'dk-moe-detail__muted', detail);
    var history = K.node('div', 'dk-moe-detail__history', detail), historyLabel = K.node('div', 'dk-moe-detail__label', history);
    var chart = K.graph(history), historyInfo = K.node('div', 'dk-moe-detail__muted', history);
    var range = K.node('div', 'dk-moe-detail__muted', history);
    var footer = K.node('div', 'dk-moe-detail__footer', detail);
    var averages = K.node('div', 'dk-moe-detail__statistics dk-moe-detail__statistics--averages', footer);
    var achievements = K.node('div', 'dk-moe-detail__statistics', footer);

    var open = false, valid = false, last = {};

    function setOpen(value) {
        open = !!value && valid;
        root.className = 'dk-moe' + (open ? ' dk-moe--open' : '');
        // Hidden by default in CSS, so K.show('') would not reveal it.
        K.style(detail, 'display', open ? 'block' : 'none');
        if (open) { render(last, true); }
        place();
        // The panel has no size until it has been laid out once.
        if (open && frame === null) { frame = requestAnimationFrame(guard(function () { frame = null; place(); })); }
    }
    function render(data, resized) {
        last = data;
        var cfg = data.config || {}, milestone = data.milestone || {};
        valid = data.state === 'data' && !!(data.target || {}).eligible;
        K.setLocale(cfg);
        var color = /^#[0-9a-f]{6}$/i.test(data.markColor) ? data.markColor : '#eae6d8';
        // Card: the basic information only.
        K.text(title, K.label(data, 'current', ''));
        K.show(iconBox, valid && !!data.markIcon);
        if (data.markIcon && icon.getAttribute('src') !== data.markIcon) { icon.src = data.markIcon; }
        K.style(icon, 'opacity', valid && data.displayMarks > 0 ? '1' : '.35');
        K.show(stars[0].parentNode, valid); K.updateStars(stars, valid ? data.displayMarks : 0);
        K.show(message, !valid); K.text(message, data.message || K.label(data, 'unavailable', ''));
        K.show(percent, valid); K.text(percent, K.percent(data.currentMark)); K.style(percent, 'color', color);
        K.show(more, valid); K.text(moreText, K.label(data, 'more', ''));
        if (!valid && open) { setOpen(false); return; }
        if (!open) { return; }
        // Side panel: everything else.
        K.text(heading, K.label(data, 'title', ''));
        K.text(vehicle, (data.vehicle || '—') + (K.roman(data.tier) ? ' · ' + K.roman(data.tier) : '') + (data.nation ? ' · ' + data.nation : ''));
        K.show(vehicle, cfg.showVehicleInfo !== false);
        K.text(currentLabel, K.label(data, 'current', ''));
        K.text(current, K.percent(data.currentMark)); K.style(current, 'color', color);
        K.updateStars(heroStars, data.displayMarks);
        K.show(progress, cfg.showProgress !== false || cfg.showMilestones !== false);
        scale.update(data.currentMark, data.displayMarks, null, cfg.showMilestones !== false);
        K.show(scale.fill, cfg.showProgress !== false); K.show(next, cfg.showProgress !== false);
        K.style(scale.fill, 'backgroundColor', color);
        K.text(nextLabel, milestone.completed ? K.label(data, 'completed', '') : K.label(data, 'next', '') + ' ' + milestone.nextMilestone + '%');
        K.text(gap, milestone.completed ? '' : K.formatted(milestone.gap, 2) + ' ' + K.label(data, 'gapUnit', '') + ' ' + K.label(data, 'remaining', ''));
        K.show(metrics, cfg.showDamageStatistics !== false);
        K.text(cards[0].label, K.label(data, 'ema', ''));
        K.text(cards[1].label, K.label(data, 'expected', '') + ((data.target || {}).threshold && !milestone.completed ? ' (' + data.target.threshold + '%)' : ''));
        K.text(cards[2].label, K.label(data, 'emaGap', ''));
        K.text(cards[0].value, K.formatted(data.movingAverage));
        K.style(cards[0].value, 'color', data.movingAverageColor || '#cfcfcf');
        K.text(cards[1].value, K.formatted(data.targetDamage)); K.text(cards[2].value, K.formatted(data.damageNeeded));
        K.style(cards[2].value, 'color', color);
        K.text(note, K.label(data, 'estimateNote', '')); K.show(note, cfg.showDamageStatistics !== false);
        K.show(history, cfg.showHistory !== false);
        K.text(historyLabel, K.label(data, 'history', ''));
        var samples = (data.recent || {}).samples || [], sufficient = samples.length >= 2;
        K.show(chart.element, sufficient);
        if (resized) { chart.invalidate(); }
        if (sufficient && cfg.showHistory !== false) { chart.draw(samples); }
        K.text(historyInfo, sufficient ? K.label(data, 'historyNote', '') : K.label(data, 'waiting', ''));
        // Warhelios has no arrow glyph; » is in the font.
        K.text(range, sufficient ? samples[0].battles + ' » ' + samples[samples.length - 1].battles + ' · ' + K.percent(samples[0].percent) + ' » ' + K.percent(samples[samples.length - 1].percent) : '');
        K.show(footer, cfg.showAdvancedStatistics !== false);
        K.text(averages, '');
        K.node('span', '', averages, K.label(data, 'direct', '') + ': ');
        var damage = K.node('span', '', averages, K.formatted(data.averageDirect));
        K.style(damage, 'color', data.damageColor || '#cfcfcf');
        K.node('span', '', averages, ' · ' + K.label(data, 'assist', '') + ': ' + K.formatted(data.averageAssist));
        K.text(achievements, '');
        [['WNX', data.wnx, data.wnxColor], ['WN8', data.wn8, data.wn8Color], ['WinRate', data.winRate, data.winRateColor]].forEach(function (metric, i) {
            if (i) { K.node('span', 'dk-moe-detail__separator', achievements, '·'); }
            K.node('span', '', achievements, metric[0] + ' ');
            var value = K.node('span', '', achievements, metric[1] || '—');
            K.style(value, 'color', metric[2] || '#cfcfcf');
        });
        if (data.masteryIcon && data.masteryRank >= 1 && data.masteryRank <= 4) {
            K.node('span', '', achievements, ' · ');
            var ace = K.node('img', 'dk-moe-detail__ace', achievements);
            ace.src = data.masteryIcon; ace.alt = data.mastery; ace.title = data.mastery;
        }
    }
    function unit() { return parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 1; }
    function shown(node) {
        var style = window.getComputedStyle(node);
        return style.display !== 'none' && style.visibility !== 'hidden' && !(parseFloat(style.opacity) < .05);
    }
    function columnBox() {
        var column = document.querySelector(COLUMN);
        if (!column) { return null; }
        var box = column.getBoundingClientRect(), bottom = null;
        // The column keeps faded-out groups in its layout, so its own box can reach far below the
        // last visible group: use the lowest group that is actually shown.
        for (var i = 0; i < column.children.length; i++) {
            var child = column.children[i], rect = child.getBoundingClientRect();
            if (rect.height > 0 && shown(child)) { bottom = bottom === null ? rect.bottom : Math.max(bottom, rect.bottom); }
        }
        return box.width > 0 ? {left: box.left, right: box.right, width: box.width, bottom: bottom === null ? box.bottom : bottom} : null;
    }
    function place() {
        if (root.style.display === 'none') { return; }
        var px = unit(), column = columnBox();
        var width = column ? column.width : FALLBACK_WIDTH * px;
        K.style(card, 'width', width + 'px');
        var height = card.getBoundingClientRect().height;
        var left = column ? column.right - width : window.innerWidth - width - 16 * px;
        var top = column ? column.bottom + GAP * px : window.innerHeight * FALLBACK_TOP;
        top = Math.max(0, Math.min(window.innerHeight - height, top));
        K.style(root, 'left', left + 'px'); K.style(root, 'top', top + 'px');
        if (open) {
            // The side panel opens to the left of the card, top-aligned, and moves up to stay on screen.
            var panel = Math.max(detail.offsetHeight || 0, detail.getBoundingClientRect().height);
            if (panel > 0) {
                K.style(detail, 'bottom', 'auto');
                K.style(detail, 'top', Math.max(-top, Math.min(0, window.innerHeight - 8 * px - (top + panel))) + 'px');
            } else if (top > window.innerHeight / 2) {
                // Not measured yet: low on the screen, grow upward from the card's bottom edge.
                K.style(detail, 'top', 'auto'); K.style(detail, 'bottom', '0');
            }
        }
    }
    function position() {
        place();
        if (timer === null) { timer = setInterval(guard(function () { if (root.style.display !== 'none') { place(); } }), 200); }
    }
    function inside(target) {
        while (target) { if (target === root) { return true; } target = target.parentNode; }
        return false;
    }
    function toggle(event) {
        if (event.button !== 0) { return; }
        event.stopPropagation();
        setOpen(!open);
    }
    function closeClick(event) { event.stopPropagation(); setOpen(false); }
    function outside(event) { if (open && !inside(event.target)) { setOpen(false); } }
    function key(event) { if (open && (event.keyCode === 27 || event.key === 'Escape')) { event.stopPropagation(); setOpen(false); } }

    listen(card, 'click', toggle);
    listen(close, 'click', closeClick);
    listen(detail, 'click', function (event) { event.stopPropagation(); });
    listen(document, 'mousedown', outside, true);
    listen(document, 'keydown', key, true);
    setOpen(false);
    // Local read-only connection: callbacks and partial subscriptions belong to this generation.
    // The shared kit remains unchanged for battle, clock and other OpenWG consumers.
    function update() {
        pendingUpdate = null;
        var found = null, id = null;
        if (window.subViews) {
            var ids = window.subViews.ids();
            for (var i = 0; i < ids.length; i++) {
                var child = window.subViews.get(ids[i]);
                if (child && child.model && child.model.DriftkingsUI && child.model.DriftkingsUI.name === 'DriftkingsMarksOnGunHangar') {
                    found = child.model; id = ids[i]; break;
                }
            }
        }
        if (!found) { releaseModel(); K.show(root, false); return; }
        if (found !== model || id !== resourceId) {
            releaseModel(); model = found; resourceId = id;
            callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
        }
        if (previous === model.payload) { return; }
        var data = JSON.parse(model.payload || '{}');
        K.style(root, 'display', (data.config || {}).visible ? 'block' : 'none');
        if ((data.config || {}).visible) { render(data); position(); }
        previous = model.payload;
    }
    function schedule() { if (pendingUpdate === null) { pendingUpdate = setTimeout(guard(update), 0); } }
    var ready = engine.whenReady.then(guard(function () {
        listenEngine('viewEnv.onDataChanged', schedule);
        listenEngine('subViews.onAdded', schedule); listenEngine('subViews.onRemoved', schedule);
        listen(window, 'resize', function () { if ((last.config || {}).visible) { render(last, true); position(); } });
        listen(window, 'unload', dispose);
        status = 'ready'; schedule();
    }));
    if (ready && typeof ready.catch === 'function') { ready.catch(failed); }
    } catch (error) { failed(error); }
}());
