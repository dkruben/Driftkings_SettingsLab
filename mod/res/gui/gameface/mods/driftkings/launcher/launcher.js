/* Footer-specific adapter. OpenWG and the existing Driftkings bootstrap own loading. */
(function () {
    'use strict';
    if (window.__dkFooterLauncher) { window.__dkFooterLauncher.dispose(); }
    var disposed = false, observer = null, pending = null, button = null;
    var model = null, resource = null, subscription = null, visible = false, title = '';
    function click() { if (!disposed && visible && model) { model.onOpen(); } }
    function removeButton() {
        if (!button) { return; }
        button.removeEventListener('click', click);
        if (button.parentNode) { button.parentNode.removeChild(button); }
        button = null;
    }
    function render() {
        pending = null;
        if (disposed) { return; }
        if (observer) { observer.disconnect(); }
        // CT footer bundle places the menu directly in Footer_section_*.
        // Without that anchor, fail closed instead of drawing a floating button.
        var menu = document.querySelector('div[data-test-id="menu"]');
        var section = menu && menu.parentNode;
        if (!visible || !section || String(section.className).indexOf('Footer_section_') < 0) {
            removeButton();
        } else {
            if (!button) {
                button = document.createElement('button');
                button.className = 'driftkings-launcher'; button.type = 'button';
                button.setAttribute('data-test-id', 'driftkings-launcher');
                var image = document.createElement('img');
                image.className = 'driftkings-launcher__icon';
                image.src = 'coui://gui/maps/icons/driftkings/small.png'; image.alt = '';
                button.appendChild(image); button.addEventListener('click', click);
            }
            button.title = title; button.setAttribute('aria-label', title);
            if (button.parentNode !== section) { section.insertBefore(button, menu); }
        }
        if (observer) { observer.observe(document.body, {childList: true, subtree: true}); }
    }
    function schedule() { if (!disposed && pending === null) { pending = setTimeout(render, 0); } }
    function refresh() {
        if (disposed) { return; }
        var found = null, id = null;
        if (window.subViews) {
            window.subViews.ids().some(function (key) {
                var child = window.subViews.get(key), value = child && child.model;
                if (value && value.DriftkingsUI && value.DriftkingsUI.name === 'DriftkingsFooterLauncher') {
                    found = value; id = key; return true;
                }
                return false;
            });
        }
        if (resource !== id) {
            if (subscription !== null) { viewEnv.removeDataChangedCallback(subscription, resource); }
            resource = id;
            subscription = id === null ? null : viewEnv.addDataChangedCallback('model', id, true);
        }
        model = found;
        try {
            var config = JSON.parse(model ? model.payload : '{}');
            visible = config.visible === true; title = config.title || 'Driftkings';
        } catch (error) { visible = false; console.error('[Driftkings] Invalid launcher payload', error); }
        schedule();
    }
    function dispose() {
        if (disposed) { return; }
        disposed = true;
        if (observer) { observer.disconnect(); }
        if (pending !== null) { clearTimeout(pending); pending = null; }
        if (subscription !== null) { viewEnv.removeDataChangedCallback(subscription, resource); }
        engine.off('viewEnv.onDataChanged', refresh);
        engine.off('subViews.onAdded', refresh); engine.off('subViews.onRemoved', refresh);
        window.removeEventListener('unload', dispose);
        removeButton(); model = null;
        if (window.__dkFooterLauncher === owner) { delete window.__dkFooterLauncher; }
    }
    var owner = window.__dkFooterLauncher = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        if (window.MutationObserver) { observer = new window.MutationObserver(schedule); }
        engine.on('viewEnv.onDataChanged', refresh);
        engine.on('subViews.onAdded', refresh); engine.on('subViews.onRemoved', refresh);
        window.addEventListener('unload', dispose); refresh();
    });
}());
