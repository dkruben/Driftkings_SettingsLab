(function () {
    'use strict';
    if (window.__dkHangarHeaderOptions)window.__dkHangarHeaderOptions.dispose();
    var disposed = false, subscription = null, resource = null, cfg = {}, changedNodes = [], expiry = null, observer = null, pending = null;
    function restore() { changedNodes.forEach(function (x) { x.node.style.display = x.display; }); changedNodes = []; if (expiry && expiry.parentNode)expiry.parentNode.removeChild(expiry); expiry = null; }
    function hide(selector) { var nodes = document.querySelectorAll(selector); for (var i = 0; i < nodes.length; i++) { changedNodes.push({node: nodes[i], display: nodes[i].style.display}); nodes[i].style.display = 'none'; } }
    function pad(n) { return n < 10 ? '0' + n : String(n); }
    function render() {
        pending = null; if (disposed)return;
        if (observer)observer.disconnect(); restore();
        if (cfg.enabled) {
            if (cfg.showBuyPremiumButton === false)hide('[data-test-id="premium"]');
            if (cfg.showWotPlusButton === false)hide('[data-test-id="wotPlus"]');
            var premium = document.querySelector('[data-test-id="premium"]');
            if (cfg.premiumTime && cfg.showBuyPremiumButton !== false && premium && Number(cfg.expiry) > 0) {
                var date = new Date(Number(cfg.expiry) * 1000); expiry = document.createElement('span'); expiry.className = 'dk-premium-expiry';
                expiry.style.fontSize = '12rem'; expiry.style.display = 'block';
                expiry.textContent = pad(date.getDate()) + '/' + pad(date.getMonth() + 1) + '/' + date.getFullYear() + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes()); premium.appendChild(expiry);
            }
        }
        if (observer)observer.observe(document.body, {childList: true, subtree: true});
    }
    function schedule() { if (pending === null)pending = setTimeout(render, 0); }
    function refresh() {
        if (disposed)return; var found = null, id = null;
        if (window.subViews) { var ids = window.subViews.ids(); for (var i = 0; i < ids.length; i++) { var view = window.subViews.get(ids[i]); if (view && view.model && view.model.DriftkingsUI && view.model.DriftkingsUI.name === 'DriftkingsHangarHeaderOptions') { found = view.model; id = ids[i]; break; } } }
        if (resource !== id) { if (subscription !== null)viewEnv.removeDataChangedCallback(subscription, resource); resource = id; subscription = id === null ? null : viewEnv.addDataChangedCallback('model', id, true); }
        try { cfg = JSON.parse(found ? found.payload : '{}'); } catch (e) { cfg = {}; }schedule();
    }
    function dispose() { if (disposed)return; disposed = true; if (observer)observer.disconnect(); if (pending !== null)clearTimeout(pending); restore(); if (subscription !== null)viewEnv.removeDataChangedCallback(subscription, resource); engine.off('viewEnv.onDataChanged', refresh); engine.off('subViews.onAdded', refresh); engine.off('subViews.onRemoved', refresh); window.removeEventListener('unload', dispose); }
    window.__dkHangarHeaderOptions = {dispose: dispose};
    engine.whenReady.then(function () { if (disposed)return; if (window.MutationObserver)observer = new window.MutationObserver(schedule); engine.on('viewEnv.onDataChanged', refresh); engine.on('subViews.onAdded', refresh); engine.on('subViews.onRemoved', refresh); window.addEventListener('unload', dispose); refresh(); });
}());
