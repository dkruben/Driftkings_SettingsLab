(function () {
    'use strict';
    var FEATURE = 'DriftkingsMarksOnGunTechTree';
    if (window.__dkTechMarks) { window.__dkTechMarks.dispose(); }
    var disposed = false;
    var timer = null;
    var callbackId = null;
    var resourceId = null;
    var lastPayload = null;
    var data = {}, currentModel = null;
    var CARD = '[data-test-id$="-content"]';
    var observer = null;
    var fallbackTimer = null;
    var coloredNames = [];

    function color(stats) {
        return /^#[0-9a-f]{6}$/i.test(stats.color) ? stats.color : '#c7c7c7';
    }
    function number(value, fallback, min, max) {
        var result = Number(value);
        return isFinite(result) ? Math.max(min, Math.min(max, result)) : fallback;
    }
    function restoreNames() {
        coloredNames.forEach(function (entry) { entry.element.style.color = entry.color; });
        coloredNames = [];
    }
    function readModel() {
        var ids = window.subViews ? window.subViews.ids() : [];
        for (var i = 0; i < ids.length; i++) {
            var subview = window.subViews.get(ids[i]);
            var model = subview && subview.model;
            if (model && model.DriftkingsUI && model.DriftkingsUI.name === FEATURE) {
                if (resourceId !== ids[i]) {
                    if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
                    resourceId = ids[i];
                    callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
                }
                currentModel = model;
                if (lastPayload !== model.payload) {
                    lastPayload = model.payload;
                    try { data = JSON.parse(model.payload || '{}'); } catch (error) { data = {}; }
                }
                return;
            }
        }
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        callbackId = resourceId = lastPayload = currentModel = null;
        data = {};
    }
    function render() {
        timer = null;
        if (disposed) { return; }
        // Do not observe our own DOM updates, which would cause a render loop.
        if (observer) { observer.disconnect(); }
        readModel();
        restoreNames();
        var old = document.querySelectorAll('.dk-tech-marks');
        for (var n = 0; n < old.length; n++) { old[n].parentNode.removeChild(old[n]); }
        if (data.enabled && data.vehicles) {
            var cards = document.querySelectorAll(CARD);
            for (var i = 0; i < cards.length; i++) {
                var card = cards[i];
                var match = /^(\d+)-content$/.exec(card.getAttribute('data-test-id'));
                var stats = match && data.vehicles[match[1]];
                if (!stats) { continue; }
                var badge = document.createElement('div');
                badge.className = 'dk-tech-marks';
                badge.style.left = number(data.offsetX, 0, -300, 300) + 'rem';
                badge.style.top = number(data.offsetY, -18, -100, 100) + 'rem';
                badge.style.fontSize = number(data.fontSize, 14, 9, 24) + 'rem';
                if (data.showPercent && stats.tier >= 5) {
                    var percent = document.createElement('span');
                    percent.textContent = number(stats.percent, 0, 0, 100).toFixed(2) + '%';
                    percent.style.color = color(stats);
                    badge.appendChild(percent);
                }
                var masteryLevel = Math.round(number(stats.mastery, 0, 0, 4));
                if (data.showMastery) {
                    var mastery = document.createElement('img');
                    mastery.className = 'dk-tech-marks__mastery';
                    mastery.src = masteryLevel === 0 ?
                        'coui://gui/maps/icons/achievements/summary/mastery/mastery_empty_small.png' :
                        'coui://gui/maps/icons/achievement/32x32/markOfMastery' + masteryLevel + '.png';
                    mastery.alt = ['No mastery', 'Mastery III', 'Mastery II', 'Mastery I', 'Ace tanker'][masteryLevel];
                    badge.appendChild(mastery);
                }
                if (badge.childNodes.length) { card.appendChild(badge); }
                if (data.colorName && stats.tier >= 5 && stats.percent > 0) {
                    var name = card.querySelector('[class*="VehicleNode_name_"]');
                    if (name) {
                        coloredNames.push({element: name, color: name.style.color});
                        name.style.color = color(stats);
                    }
                }
            }
        }
        if (observer) { observer.observe(document.body, {childList: true, subtree: true}); }
    }
    function changed() {
        if (!currentModel || currentModel.payload !== lastPayload) schedule();
    }
    function mutations(records) {
        for (var i = 0; i < records.length; i++) {
            var node = records[i].target;
            while (node && node !== document.body) {
                if (node.classList && node.classList.contains('dk-tech-marks')) break;
                if (node.matches && node.matches(CARD)) { schedule(); return; }
                node = node.parentNode;
            }
            if (node && node !== document.body) continue;
            var children = [].slice.call(records[i].addedNodes || []).concat([].slice.call(records[i].removedNodes || []));
            for (var j = 0; j < children.length; j++) {
                node = children[j];
                if ((node.matches && node.matches(CARD)) || (node.querySelector && node.querySelector(CARD))) {
                    schedule(); return;
                }
            }
        }
    }
    function schedule() {
        if (!disposed && timer === null) { timer = setTimeout(render, 0); }
    }
    function dispose() {
        disposed = true;
        if (timer !== null) { clearTimeout(timer); }
        if (observer) { observer.disconnect(); }
        if (fallbackTimer !== null) { clearInterval(fallbackTimer); }
        engine.off('viewEnv.onDataChanged', changed);
        engine.off('subViews.onAdded', schedule);
        engine.off('subViews.onRemoved', schedule);
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        restoreNames();
        var badges = document.querySelectorAll('.dk-tech-marks');
        for (var i = 0; i < badges.length; i++) { badges[i].parentNode.removeChild(badges[i]); }
        window.removeEventListener('unload', dispose);
    }
    window.__dkTechMarks = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', changed);
        engine.on('subViews.onAdded', schedule);
        engine.on('subViews.onRemoved', schedule);
        if (window.MutationObserver) { observer = new MutationObserver(mutations); }
        else { fallbackTimer = setInterval(schedule, 500); }
        window.addEventListener('unload', dispose);
        schedule();
    });
}());
