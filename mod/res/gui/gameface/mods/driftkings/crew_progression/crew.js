/* Feed native crew tooltip arguments; this bridge creates no visual nodes. */
(function () {
    'use strict';
    var generation = window.__dkCrewProgressionLoad || {};
    if (generation.cancelled || window.__dkCrewProgression) { return; }
    var model = null, resourceId = null, callbackId = null, signature = null, data = {};
    var disposed = false, state = 'initializing', snapshot = 'waiting', pending = null, announced = false;
    var cleanups = [];
    function report(error) {
        console.error('[Driftkings] Crew progression bridge: ' + error);
        if (typeof generation.report === 'function') { generation.report(error); }
    }
    function attempt(action) { try { action(); return true; } catch (error) { report(error); return false; } }
    function notify() { announced = true; window.dispatchEvent(new Event('dk-carousel-config')); }
    function release() {
        var callback = callbackId, id = resourceId;
        callbackId = null; resourceId = null; model = null; signature = null; data = {}; snapshot = 'waiting';
        return callback === null || attempt(function () { viewEnv.removeDataChangedCallback(callback, id); });
    }
    function dispose() {
        if (disposed) { return; }
        disposed = true; data = {}; snapshot = 'destroyed';
        if (pending !== null) { attempt(function () { clearTimeout(pending); }); pending = null; }
        cleanups.splice(0).reverse().forEach(attempt);
        release(); snapshot = 'destroyed';
        if (window.__dkCrewProgression === owner) { delete window.__dkCrewProgression; }
        attempt(notify);
        if (state !== 'failed') { state = 'destroyed'; }
    }
    function fail(error) {
        if (disposed) { return; }
        state = 'failed'; report(error); dispose();
        if (typeof generation.fail === 'function') { generation.fail(error); }
    }
    function guard(action) {
        return function () {
            if (disposed || generation.cancelled || window.__dkCrewProgression !== owner) { return; }
            try { return action.apply(null, arguments); } catch (error) { fail(error); }
        };
    }
    function strings(values) { return Array.isArray(values) && values.every(function (value) { return typeof value === 'string'; }); }
    function parse(payload) {
        var next = JSON.parse(payload || '{}'), rows = next.rows || [];
        if (!next || typeof next !== 'object' || !Array.isArray(rows)) { throw new Error('Invalid crew snapshot'); }
        rows.forEach(function (row) {
            if (!row || typeof row.id !== 'number' || !isFinite(row.id) ||
                    !strings(row.lines) || !strings(row.kinds) || row.lines.length !== row.kinds.length) {
                throw new Error('Invalid crew progression row');
            }
        });
        return next;
    }
    function refresh() {
        if (pending !== null) { clearTimeout(pending); pending = null; }
        var ids = window.subViews ? window.subViews.ids() : [], found = null, id = null;
        for (var i = 0; i < ids.length; i++) {
            var child = window.subViews.get(ids[i]), next = child && child.model;
            if (next && next.DriftkingsUI && next.DriftkingsUI.name === 'DriftkingsCrewProgression') { found = next; id = ids[i]; break; }
        }
        if (!found) {
            if (model || !announced) { release(); notify(); }
            return;
        }
        if (resourceId !== id || model !== found) {
            if (!release()) { throw new Error('Could not release previous crew subscription'); }
            resourceId = id; model = found;
            callbackId = viewEnv.addDataChangedCallback('model', resourceId, true);
        }
        if (signature !== model.payload) {
            var payload = model.payload, current = parse(payload);
            data = current; signature = payload;
            snapshot = (data.config || {}).visible && (data.rows || []).length ? 'ready' : 'empty';
            notify();
        }
    }
    function schedule() { if (pending === null) { pending = setTimeout(guard(refresh), 0); } }
    function getRow(id) {
        if (disposed || generation.cancelled || window.__dkCrewProgression !== owner) { return null; }
        try {
            var child = model && window.subViews && window.subViews.get(resourceId);
            if (!child || child.model !== model || model.payload !== signature) {
                data = {}; signature = null; snapshot = 'waiting'; schedule(); return null;
            }
            if (!(data.config || {}).visible) { return null; }
            var rows = data.rows || [];
            for (var i = 0; i < rows.length; i++) { if (rows[i].id === id) { return rows[i]; } }
        } catch (error) { fail(error); }
        return null;
    }
    var owner = {getRow: getRow, dispose: dispose, generation: generation,
        getState: function () { return state; }, getSnapshotState: function () { return snapshot; }};
    window.__dkCrewProgression = owner;
    try {
        var ready = engine.whenReady.then(guard(function () {
            ['viewEnv.onDataChanged', 'subViews.onAdded', 'subViews.onRemoved'].forEach(function (name) {
                var callback = guard(refresh);
                cleanups.push(function () { engine.off(name, callback); }); engine.on(name, callback);
            });
            var unload = guard(dispose);
            cleanups.push(function () { window.removeEventListener('unload', unload); });
            window.addEventListener('unload', unload);
            refresh(); state = 'ready';
            if (typeof generation.ready === 'function') { generation.ready(); }
        }));
        if (ready && typeof ready.catch === 'function') { ready.catch(fail); }
    } catch (error) { fail(error); }
}());
