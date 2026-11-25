/* Driftkings-owned loader: catalog assets, ordered scripts and explicit disposal. */
(function () {
    'use strict';
    if (window.__dkUIBridge) { return; }
    var active = {}, retiring = {}, disposed = false;
    var fonts = document.createElement('link');
    fonts.rel = 'stylesheet';
    fonts.href = 'coui://gui/gameface/mods/driftkings/shared/fonts.css';
    document.head.appendChild(fonts);
    /* GENERATED CATALOG START */
    var features = {};
    /* GENERATED CATALOG END */

    function remove(node) {
        node.onload = node.onerror = null;
        if (node.parentNode) { node.parentNode.removeChild(node); }
    }
    function disposeOwner(name) {
        var key = features[name].owner, owner = window[key];
        try {
            if (owner && typeof owner.dispose === 'function') { owner.dispose(); }
        } catch (error) {
            console.error('[Driftkings] Cannot dispose UI owner: ' + name, error);
        } finally {
            if (window[key] === owner) { delete window[key]; }
        }
    }
    function unload(name) {
        var entry = active[name];
        if (!entry) { return; }
        entry.cancelled = true;
        delete active[name];
        // Let an in-flight script finish before loading another generation.
        // It may still execute after its view disappeared and create an owner.
        if (entry.pending) { retiring[name] = entry; }
        disposeOwner(name);
        entry.nodes.forEach(function (node) {
            if (node !== entry.pending) { remove(node); }
        });
    }
    function retired(name, entry, node) {
        disposeOwner(name);
        remove(node);
        if (retiring[name] === entry) { delete retiring[name]; }
        if (!disposed) { refresh(); }
    }
    function load(name) {
        if (disposed || active[name] || retiring[name] || !features[name]) { return; }
        var spec = features[name];
        var entry = active[name] = {nodes: [], pending: null, cancelled: false};
        spec.styles.forEach(function (url) {
            var node = document.createElement('link');
            node.rel = 'stylesheet'; node.href = url;
            node.onerror = function () {
                if (active[name] === entry) { unload(name); }
            };
            entry.nodes.push(node); document.head.appendChild(node);
        });
        function next(index) {
            if (disposed || entry.cancelled || index >= spec.scripts.length) { return; }
            var node = document.createElement('script');
            node.async = false; node.src = spec.scripts[index];
            node.onload = function () {
                entry.pending = null;
                node.onload = node.onerror = null;
                if (entry.cancelled) { retired(name, entry, node); return; }
                next(index + 1);
            };
            node.onerror = function () {
                entry.pending = null;
                console.error('[Driftkings] Cannot load UI asset: ' + node.src);
                if (entry.cancelled) { retired(name, entry, node); return; }
                unload(name);
            };
            entry.pending = node;
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
            if (meta && features[meta.name]) { present[meta.name] = true; load(meta.name); }
        });
        Object.keys(active).forEach(function (name) { if (!present[name]) { unload(name); } });
    }
    function dispose() {
        if (disposed) { return; }
        disposed = true;
        remove(fonts);
        engine.off('subViews.onAdded', refresh);
        engine.off('subViews.onRemoved', refresh);
        Object.keys(active).forEach(unload);
        window.removeEventListener('unload', dispose);
        if (window.__dkUIBridge === bridge) { delete window.__dkUIBridge; }
    }
    var bridge = window.__dkUIBridge = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('subViews.onAdded', refresh);
        engine.on('subViews.onRemoved', refresh);
        window.addEventListener('unload', dispose);
        refresh();
    });
}());
