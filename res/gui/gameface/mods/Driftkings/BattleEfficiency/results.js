(function () {
    'use strict';
    var FEATURE = 'DriftkingsBattleEfficiency';
    if (window.__dkBattleEfficiency) { window.__dkBattleEfficiency.dispose(); }
    var disposed = false, node = null, resourceId = null, callbackId = null;
    var lastPayload = null, timer = null;

    // Translate the configured Flash text to a small, safe HTML subset.
    function copyText(source, target) {
        for (var i = 0; i < source.childNodes.length; i++) {
            var child = source.childNodes[i];
            if (child.nodeType === 3) { target.appendChild(document.createTextNode(child.nodeValue)); continue; }
            if (child.nodeType !== 1) { continue; }
            var tag = child.tagName.toLowerCase();
            if (tag === 'script' || tag === 'style' || tag === 'iframe') { continue; }
            var dest = document.createElement(/^(b|i|u|br|p)$/.test(tag) ? tag : 'span');
            if (tag === 'font') {
                var color = child.getAttribute('color'), size = Number(child.getAttribute('size'));
                if (/^#[0-9a-f]{6}$/i.test(color)) { dest.style.color = color; }
                if (size >= 8 && size <= 40) { dest.style.fontSize = size + 'px'; }
            }
            copyText(child, dest); target.appendChild(dest);
        }
    }
    function hide() {
        if (node && node.parentNode) { node.parentNode.removeChild(node); }
        node = null;
    }
    function render(payload) {
        var data;
        try { data = JSON.parse(payload || '{}'); } catch (e) { data = {}; }
        if (!data.enabled || !data.html) { hide(); return; }
        if (!node) { node = document.createElement('div'); node.id = 'dk-battle-efficiency'; document.body.appendChild(node); }
        while (node.firstChild) { node.removeChild(node.firstChild); }
        var parsed = document.createElement('div');
        parsed.innerHTML = data.html;
        copyText(parsed, node);
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
            if (lastPayload !== model.payload) { lastPayload = model.payload; render(lastPayload); }
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
