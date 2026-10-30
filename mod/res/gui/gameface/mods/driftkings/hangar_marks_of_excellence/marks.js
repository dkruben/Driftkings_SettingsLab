/* Hangar marks: a compact card under the native mission column and a "show more" side panel.
   Python supplies every value; the card only follows the column's position and width. */
(function () {
    'use strict';
    var K = window.__dkMarksKit;
    // The column is a React widget laid out by its own animations, so the card sits under it
    // instead of inside it and is re-placed while visible.
    var COLUMN = '[class*="HangarScreen_userMissions_"]';
    var GAP = 8, FALLBACK_WIDTH = 319, FALLBACK_TOP = .45;
    var root = K.node('div', 'dk-moe', document.body);
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
    var averages = K.node('div', '', footer), achievements = K.node('div', '', footer);

    var open = false, valid = false, last = {}, timer = null;

    function setOpen(value) {
        open = !!value && valid;
        root.className = 'dk-moe' + (open ? ' dk-moe--open' : '');
        // Hidden by default in CSS, so K.show('') would not reveal it.
        K.style(detail, 'display', open ? 'block' : 'none');
        if (open) { render(last, true); }
        place();
        // The panel has no size until it has been laid out once.
        if (open) { requestAnimationFrame(place); }
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
        K.text(averages, K.label(data, 'direct', '') + ': ' + K.formatted(data.averageDirect) + ' · ' + K.label(data, 'assist', '') + ': ' + K.formatted(data.averageAssist));
        K.text(achievements, 'WN8 ' + (data.wn8 || '—') + ' · ' + (data.winRate || '—') + ' · ' + (data.mastery || '—'));
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
        if (timer === null) { timer = setInterval(function () { if (root.style.display !== 'none') { place(); } }, 200); }
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

    card.addEventListener('click', toggle);
    close.addEventListener('click', closeClick);
    detail.addEventListener('click', function (event) { event.stopPropagation(); });
    document.addEventListener('mousedown', outside, true);
    document.addEventListener('keydown', key, true);
    setOpen(false);
    var kit = K.connect('DriftkingsMarksOnGunHangar', '__dkHangarMarks', root, render, position, null);
    var dispose = kit.dispose;
    kit.dispose = function () {
        if (timer !== null) { clearInterval(timer); timer = null; }
        document.removeEventListener('mousedown', outside, true);
        document.removeEventListener('keydown', key, true);
        dispose();
    };
}());
