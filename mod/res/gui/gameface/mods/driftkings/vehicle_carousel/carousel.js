(function () {
    'use strict';
    var FEATURE = 'DriftkingsCarouselStats';
    var generation = window.__dkCarouselLoad || {};
    if (generation.cancelled || window.__dkCarouselStats) { return; }
    var native = window.DKCarouselNative, layout = window.DKCarouselLayout;
    if (!native || !layout) { throw new Error('Carousel helpers unavailable'); }
    var disposed = false, pending = null, observer = null, fallback = null;
    var callbackId = null, resourceId = null, model = null, data = {}, lastRequest = null;
    var mounted = [], inFlight = [], lastPayload = null, imageSignature = '', state = 'initializing';
    function report(error) {
        console.error('[Driftkings] Carousel bridge: ' + error);
        if (typeof generation.report === 'function') { generation.report(error); }
    }
    function attempt(action) { try { action(); } catch (error) { report(error); } }
    function current() {
        return !disposed && !generation.cancelled && window.__dkCarouselStats === owner &&
            window.DKCarouselNative === native && window.DKCarouselLayout === layout;
    }
    function fail(error) {
        if (disposed) { return; }
        state = 'failed'; report(error); dispose();
        if (typeof generation.fail === 'function') { generation.fail(error); }
    }
    function guard(action) { return function () {
        if (!current()) { return; }
        try { return action.apply(null, arguments); } catch (error) { fail(error); }
    }; }
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
        var callback = callbackId, id = resourceId;
        callbackId = null; resourceId = null; model = null; lastRequest = null; lastPayload = null; data = {};
        if (callback !== null) { attempt(function () { viewEnv.removeDataChangedCallback(callback, id); }); }
    }
    function readModel() {
        var ids = window.subViews ? window.subViews.ids() : [];
        for (var i = 0; i < ids.length; i++) {
            var child = window.subViews.get(ids[i]), next = child && child.model;
            if (next && next.DriftkingsUI && next.DriftkingsUI.name === FEATURE) {
                if (resourceId !== ids[i] || model !== next) {
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
        var entries = mounted.concat(inFlight); mounted = []; inFlight = [];
        entries.forEach(function (entry, index) { if (entries.indexOf(entry) === index) { attempt(entry.cleanup); } });
    }
    function render() {
        pending = null;
        if (disposed) { return; }
        if (observer) { observer.disconnect(); }
        readModel();
        var retained = []; inFlight = retained;
        native.setData(data);
        if (!current()) { return; }
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
                visible.push({card: card, id: id, width: card.clientWidth, height: card.clientHeight});
            }
            var request = ids.sort(function (a, b) { return Number(a) - Number(b); }).join(',');
            if (request !== lastRequest && typeof model.onRequestVehicles === 'function') {
                lastRequest = request; model.onRequestVehicles({ids: request});
                if (!current()) { return; }
            }
            visible.forEach(function (entry) {
                var profiles = (data.vehicles || {})[entry.id];
                if (!profiles || !window.DKCarouselLayout) return;
                var doubled = String(entry.card.className).indexOf('__double_') !== -1 || !!entry.card.querySelector('[class*="__double_"]');
                var name = layout.profileName(data.config.cellType, doubled);
                if (!profiles[name]) return;
                var signature = JSON.stringify([entry.id, name, profiles[name], entry.width, entry.height]);
                var previous = null;
                for (var j = 0; j < mounted.length; j++) {
                    if (mounted[j].card === entry.card) { previous = mounted.splice(j, 1)[0]; break; }
                }
                if (previous && (previous.signature !== signature || previous.images !== imageSignature || previous.dirty || !entry.card.querySelector('.dk-carousel-stats'))) {
                    previous.cleanup(); previous = null;
                }
                retained.push(previous || {card: entry.card, signature: signature, images: imageSignature, dirty: false,
                    cleanup: layout.mount(entry.card, profiles[name], document, data.images)});
            });
        } else { lastRequest = null; }
        inFlight = []; clear(); mounted = retained;
        if (observer) { observer.observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-test-id', 'class', 'style']}); }
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
    function schedule() { if (current() && pending === null) { pending = setTimeout(guard(render), 40); } }
    var callbacks = {data: guard(onDataChanged), schedule: guard(schedule), mutations: guard(onMutations), dispose: guard(dispose)};
    function dispose() {
        if (disposed) { return; } disposed = true;
        var timer = pending, interval = fallback; pending = fallback = null;
        if (timer !== null) { attempt(function () { clearTimeout(timer); }); }
        if (interval !== null) { attempt(function () { clearInterval(interval); }); }
        if (observer) { attempt(function () { observer.disconnect(); }); observer = null; }
        attempt(function () { engine.off('viewEnv.onDataChanged', callbacks.data); });
        attempt(function () { engine.off('subViews.onAdded', callbacks.schedule); });
        attempt(function () { engine.off('subViews.onRemoved', callbacks.schedule); });
        attempt(function () { window.removeEventListener('resize', callbacks.schedule); });
        attempt(function () { window.removeEventListener('unload', callbacks.dispose); });
        attempt(function () { document.removeEventListener('scroll', callbacks.schedule, true); });
        clear(); release();
        if (window.__dkCarouselStats === owner) { delete window.__dkCarouselStats; }
        if (native.generation === generation || !window.__dkCarouselLoad) { attempt(function () { native.dispose(); }); }
        if (state !== 'failed') { state = 'destroyed'; }
    }
    var owner = {dispose: dispose, generation: generation, getState: function () { return state; },
        getModelState: function () { return disposed ? 'unavailable' : model ? 'bound' : 'waiting'; }};
    window.__dkCarouselStats = owner;
    generation.renderer = owner;
    try {
        var ready = engine.whenReady.then(guard(function () {
            engine.on('viewEnv.onDataChanged', callbacks.data);
            engine.on('subViews.onAdded', callbacks.schedule); engine.on('subViews.onRemoved', callbacks.schedule);
            if (window.MutationObserver) { observer = new MutationObserver(callbacks.mutations); }
            else { fallback = setInterval(callbacks.schedule, 500); }
            window.addEventListener('resize', callbacks.schedule); window.addEventListener('unload', callbacks.dispose);
            document.addEventListener('scroll', callbacks.schedule, true);
            render();
            if (!current()) { return; }
            state = 'ready';
            if (typeof generation.ready === 'function') { generation.ready(); }
        }));
        if (ready && typeof ready.catch === 'function') { ready.catch(fail); }
    } catch (error) { fail(error); }
}());
