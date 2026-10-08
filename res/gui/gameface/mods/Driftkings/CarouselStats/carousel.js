(function () {
    'use strict';
    var FEATURE = 'DriftkingsCarouselStats';
    if (window.__dkCarouselStats) { window.__dkCarouselStats.dispose(); }
    var disposed = false, pending = null, observer = null, fallback = null;
    var callbackId = null, resourceId = null, model = null, data = {}, lastRequest = null;
    var mounted = [], lastPayload = null, imageSignature = '';
    var CARD = '.vehicle-card[data-test-id^="vehicleCard-"]';
    function matches(node, selector) {
        return !!(node && node.matches && node.matches(selector));
    }
    function inCarousel(node) {
        while (node && node !== document.body) {
            if (matches(node, CARD + ',[class*="Page_carousel_"]')) return true;
            node = node.parentNode;
        }
        return false;
    }
    function owns(node) {
        while (node && node !== document.body) {
            if (node.classList && node.classList.contains('dk-carousel-stats')) return true;
            node = node.parentNode;
        }
        return false;
    }
    function release() {
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        callbackId = null; resourceId = null; model = null; lastRequest = null; lastPayload = null; data = {};
    }
    function readModel() {
        var ids = window.subViews ? window.subViews.ids() : [];
        for (var i = 0; i < ids.length; i++) {
            var child = window.subViews.get(ids[i]), next = child && child.model;
            if (next && next.DriftkingsUI && next.DriftkingsUI.name === FEATURE) {
                if (resourceId !== ids[i]) {
                    release(); resourceId = ids[i];
                    callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
                }
                model = next;
                if (lastPayload !== model.payload) {
                    lastPayload = model.payload;
                    try { data = JSON.parse(model.payload || '{}'); } catch (error) { data = {}; }
                    imageSignature = JSON.stringify(data.images || {});
                }
                return;
            }
        }
        release();
    }
    function clear() {
        mounted.forEach(function (entry) { entry.cleanup(); });
        mounted = [];
    }
    function render() {
        pending = null;
        if (disposed) { return; }
        if (observer) { observer.disconnect(); }
        readModel();
        var retained = [];
        if (window.DKCarouselNative) window.DKCarouselNative.setData(data);
        if (model && (data.config || {}).visible) {
            // EU 2.4.0.1 hangar bundle: vehicleId is the compact descriptor (intCD).
            var cards = document.querySelectorAll(CARD);
            var ids = [], seen = {}, visible = [];
            for (var i = 0; i < cards.length; i++) {
                var card = cards[i], match = /^vehicleCard-(\d+)$/.exec(card.getAttribute('data-test-id'));
                var rect = card.getBoundingClientRect();
                if (!match || !rect.width || !rect.height || rect.right < 0 || rect.left > window.innerWidth || rect.bottom < 0 || rect.top > window.innerHeight) { continue; }
                var id = match[1];
                if (!seen[id] && ids.length < 120) { ids.push(id); seen[id] = true; }
                visible.push({card:card, id:id, width:card.clientWidth, height:card.clientHeight});
            }
            var request = ids.sort(function (a,b) { return Number(a)-Number(b); }).join(',');
            if (request !== lastRequest && typeof model.onRequestVehicles === 'function') {
                lastRequest = request; model.onRequestVehicles({ids:request});
            }
            visible.forEach(function (entry) {
                var profiles = (data.vehicles || {})[entry.id];
                if (!profiles || !window.DKCarouselLayout) return;
                var doubled = String(entry.card.className).indexOf('__double_') !== -1 || !!entry.card.querySelector('[class*="__double_"]');
                var name = window.DKCarouselLayout.profileName(data.config.cellType, doubled);
                if (!profiles[name]) return;
                var signature = JSON.stringify([entry.id, name, profiles[name], entry.width, entry.height]);
                var previous = null;
                for (var j = 0; j < mounted.length; j++) {
                    if (mounted[j].card === entry.card) { previous = mounted.splice(j, 1)[0]; break; }
                }
                if (previous && (previous.signature !== signature || previous.images !== imageSignature || previous.dirty || !entry.card.querySelector('.dk-carousel-stats'))) {
                    previous.cleanup(); previous = null;
                }
                retained.push(previous || {card:entry.card, signature:signature, images:imageSignature, dirty:false,
                    cleanup:window.DKCarouselLayout.mount(entry.card,profiles[name],document,data.images)});
            });
        } else { lastRequest = null; }
        clear(); mounted = retained;
        if (observer) { observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['data-test-id','class','style']}); }
    }
    function onMutations(records) {
        var changed = false;
        for (var i = 0; i < records.length; i++) {
            var record = records[i], node = record.target;
            if (owns(node)) continue;
            var relevant = inCarousel(node);
            // Mount/unmount of the carousel itself is reported on its parent.
            var children = [].slice.call(record.addedNodes || []).concat([].slice.call(record.removedNodes || []));
            for (var j = 0; !relevant && j < children.length; j++) {
                relevant = inCarousel(children[j]) || !!(children[j].querySelector && children[j].querySelector(CARD));
            }
            if (!relevant) continue;
            changed = true;
            for (j = 0; j < mounted.length; j++) {
                // Native React updates can replace fields inside a retained card.
                if (mounted[j].card === node || mounted[j].card.contains(node)) mounted[j].dirty = true;
            }
        }
        if (changed) schedule();
    }
    function onDataChanged() { if (!model || model.payload !== lastPayload) schedule(); }
    function schedule() { if (!disposed && pending === null) { pending = setTimeout(render,40); } }
    function dispose() {
        if (disposed) { return; } disposed = true;
        if (pending !== null) { clearTimeout(pending); }
        if (observer) { observer.disconnect(); }
        if (fallback !== null) { clearInterval(fallback); }
        engine.off('viewEnv.onDataChanged',onDataChanged);engine.off('subViews.onAdded',schedule);engine.off('subViews.onRemoved',schedule);
        window.removeEventListener('resize',schedule);window.removeEventListener('unload',dispose);
        document.removeEventListener('scroll',schedule,true);clear();release();
        if (window.DKCarouselNative) window.DKCarouselNative.dispose();
    }
    window.__dkCarouselStats = {dispose:dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged',onDataChanged);engine.on('subViews.onAdded',schedule);engine.on('subViews.onRemoved',schedule);
        if (window.MutationObserver) { observer = new MutationObserver(onMutations); } else { fallback = setInterval(schedule,500); }
        window.addEventListener('resize',schedule);window.addEventListener('unload',dispose);document.addEventListener('scroll',schedule,true);
        schedule();
    });
}());
