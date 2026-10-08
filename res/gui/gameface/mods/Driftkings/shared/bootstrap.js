/* Driftkings-owned loader. Uses only the client's engine/subViews API. */
(function () {
    'use strict';
    if (window.__dkUIBridge) { return; }
    var active = {}, disposed = false;
    var owners = {
        DriftkingsCarouselStats: '__dkCarouselStats',
        DriftkingsHangarClock: '__dkHangarClock',
        DriftkingsModSettingsButton: '__dkModSettingsButton',
        DriftkingsMarksOnGunHangar: '__dkHangarMarks',
        DriftkingsMarksOnGunTechTree: '__dkTechMarks',
        DriftkingsBattleEfficiency: '__dkBattleEfficiency',
        DriftkingsRatingPlayers: '__dkPlayerRatings'
    };
    function urls(value) {
        var list;
        try { list = JSON.parse(value || '[]'); } catch (error) { return []; }
        if (!Array.isArray(list)) { return []; }
        return list.filter(function (url) {
            return typeof url === 'string' && url.indexOf('coui://gui/gameface/mods/Driftkings/') === 0;
        });
    }
    function unload(name) {
        var entry = active[name];
        if (!entry) { return; }
        entry.cancelled = true;
        var owner = window[owners[name]];
        if (owner && typeof owner.dispose === 'function') { owner.dispose(); }
        entry.nodes.forEach(function (node) {
            node.onerror = null;
            if (node.parentNode) { node.parentNode.removeChild(node); }
        });
        delete active[name];
    }
    function load(meta) {
        if (active[meta.name] || !owners[meta.name]) { return; }
        var entry = active[meta.name] = {nodes: [], cancelled: false};
        urls(meta.styles).forEach(function (url) {
            var node = document.createElement('link');
            node.rel = 'stylesheet'; node.href = url;
            entry.nodes.push(node); document.head.appendChild(node);
        });
        var scripts = urls(meta.scripts);
        function next(index) {
            if (disposed || entry.cancelled || index >= scripts.length) { return; }
            var node = document.createElement('script');
            node.async = false; node.src = scripts[index];
            node.onload = function () {
                if (entry.cancelled) {
                    var lateOwner = window[owners[meta.name]];
                    if (!active[meta.name] && lateOwner && lateOwner.dispose) { lateOwner.dispose(); }
                    return;
                }
                next(index + 1);
            };
            node.onerror = function () {
                console.error('[Driftkings] Cannot load UI asset: ' + node.src);
                unload(meta.name);
            };
            entry.nodes.push(node); document.head.appendChild(node);
        }
        next(0);
    }
    function refresh() {
        if (disposed || !window.subViews) { return; }
        var present = {};
        window.subViews.ids().forEach(function (id) {
            var child = window.subViews.get(id);
            var meta = child && child.model && child.model.DriftkingsUI;
            if (meta && owners[meta.name]) { present[meta.name] = true; load(meta); }
        });
        Object.keys(active).forEach(function (name) { if (!present[name]) { unload(name); } });
    }
    function dispose() {
        if (disposed) { return; }
        disposed = true;
        engine.off('subViews.onAdded', refresh);
        engine.off('subViews.onRemoved', refresh);
        Object.keys(active).forEach(unload);
        window.removeEventListener('unload', dispose);
    }
    window.__dkUIBridge = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('subViews.onAdded', refresh);
        engine.on('subViews.onRemoved', refresh);
        window.addEventListener('unload', dispose);
        refresh();
    });
}());
