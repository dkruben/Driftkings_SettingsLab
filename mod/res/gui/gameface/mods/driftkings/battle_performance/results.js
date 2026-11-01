(function () {
    'use strict';
    var FEATURE = 'driftkingsbattleEfficiency';
    if (window.__dkBattleEfficiency) { window.__dkBattleEfficiency.dispose(); }
    var disposed = false, node = null, resourceId = null, callbackId = null;
    var lastPayload = null, timer = null;

    function formatSeparators(parent) {
        var children = Array.prototype.slice.call(parent.childNodes);
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child.nodeType === 1) { formatSeparators(child); continue; }
            if (child.nodeType !== 3) { continue; }
            var value = child.nodeValue, pattern = / *\| *|\t/g, match, offset = 0;
            while ((match = pattern.exec(value)) !== null) {
                if (match.index > offset) {
                    parent.insertBefore(document.createTextNode(value.slice(offset, match.index)), child);
                }
                var spacer = document.createElement('span');
                spacer.className = match[0] === '\t' ? 'dk-results-tab' : 'dk-results-separator';
                parent.insertBefore(spacer, child);
                offset = pattern.lastIndex;
            }
            if (offset) {
                if (offset < value.length) { parent.insertBefore(document.createTextNode(value.slice(offset)), child); }
                parent.removeChild(child);
            }
        }
    }

    // Translate the configured Flash text to a small, safe HTML subset.
    function hide() {
        if (node && node.parentNode) { node.parentNode.removeChild(node); }
        node = null;
    }
    function render(payload) {
        var data;
        try { data = JSON.parse(payload || '{}'); } catch (e) { data = {}; }
        if (!data.enabled || !data.html) { hide(); return; }
        // Native post_battle/random BattleInfo: append after the vehicle state.
        // Match the CSS module name, independent of its generated hash or locale.
        var host = document.querySelector('[class^="BattleInfo_"]');
        if (!host) { hide(); return; }
        if (!node) { node = document.createElement('div'); node.id = 'dk-battle-efficiency'; }
        if (node.parentNode !== host) { host.appendChild(node); }
        while (node.firstChild) { node.removeChild(node.firstChild); }
        var parsed = document.createElement('div');
        parsed.innerHTML = window.DriftkingsFlashText.inert(data.html.replace(/<tab\s*\/?\s*>/gi, '\t'));
        window.DriftkingsFlashText.copy(parsed, node, {fontFamily: true, fontAlpha: true, sizeUnit: 'rem'});
        formatSeparators(node);
    }
    function refresh() {
        if (disposed || !window.subViews) { return; }
        var ids = window.subViews.ids();
        for (var i = 0; i < ids.length; i++) {
            var subview = window.subViews.get(ids[i]), model = subview && subview.model;
            if (!model || !model.DriftkingsUI || model.DriftkingsUI.name !== FEATURE) { continue; }
            if (resourceId !== ids[i]) {
                if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
                resourceId = ids[i]; lastPayload = null;
                callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
            }
            // React can replace the native line when switching result tabs.
            // Reattach even when the ratings payload itself did not change.
            var host = document.querySelector('[class^="BattleInfo_"]');
            if (lastPayload !== model.payload || !node || node.parentNode !== host) {
                lastPayload = model.payload; render(lastPayload);
            }
            return;
        }
        lastPayload = null; hide();
    }
    function dispose() {
        disposed = true;
        if (timer !== null) { clearInterval(timer); }
        engine.off('viewEnv.onDataChanged', refresh);
        engine.off('subViews.onAdded', refresh); engine.off('subViews.onRemoved', refresh);
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        window.removeEventListener('unload', dispose); hide();
    }
    window.__dkBattleEfficiency = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', refresh);
        engine.on('subViews.onAdded', refresh); engine.on('subViews.onRemoved', refresh);
        window.addEventListener('unload', dispose);
        timer = setInterval(refresh, 500); refresh();
    });
}());
