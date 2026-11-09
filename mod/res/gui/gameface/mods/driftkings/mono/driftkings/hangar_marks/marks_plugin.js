/* Native CT entry point. Optional renderers load only after this module executes. */
export default {
    plugin: function () {
        var state = 'created', pending = null, finish = null, nodes = [], errors = [], cleaned = false;
        var base = 'coui://gui/gameface/mods/driftkings/';
        var generation = {cancelled: false, pending: 0, fail: fail, report: report};
        function empty() { return null; }
        function report(error) {
            errors.push(String(error && error.message || error));
            console.error('[Driftkings] Native hangar marks: ' + errors[errors.length - 1]);
        }
        function attempt(action) { try { action(); } catch (error) { report(error); } }
        function remove(node) {
            node.onload = node.onerror = null;
            if (node.parentNode) { node.parentNode.removeChild(node); }
        }
        function release() {
            if (!generation.pending && state !== 'initializing' && window.__dkHangarMarksLoad === generation) { delete window.__dkHangarMarksLoad; }
        }
        function cleanup() {
            generation.cancelled = true;
            if (!cleaned) {
                cleaned = true;
                var owner = window.__dkHangarMarks;
                if (owner && owner.generation === generation) { attempt(function () { owner.dispose(); }); }
            }
            nodes.forEach(function (node) {
                // A classic script may execute after removal. Retain its retirement callback.
                if (node.dkStopTimer) { attempt(node.dkStopTimer); }
                if (node.dkCancel) { attempt(node.dkCancel); }
                if (!node.dkPending) { attempt(function () { remove(node); }); }
            });
            nodes = nodes.filter(function (node) { return node.dkPending; });
            release();
        }
        function settle() { if (finish) { var resolve = finish; finish = null; resolve(empty); } }
        function fail(error) {
            report(error);
            if (state !== 'destroying' && state !== 'destroyed') { state = 'failed'; }
            cleanup(); settle();
        }
        function load(path, style) {
            if (generation.cancelled) { return Promise.resolve(); }
            return new Promise(function (resolve) {
                var node, alarm = null;
                try {
                    node = document.createElement(style ? 'link' : 'script');
                    if (style) { node.rel = 'stylesheet'; node.href = base + path; }
                    else { node.src = base + path; node.async = false; }
                    node.dkPending = true; generation.pending++; nodes.push(node);
                    node.dkStopTimer = function () {
                        if (alarm !== null) { clearTimeout(alarm); alarm = null; }
                    };
                    function done(error) {
                        if (!node.dkPending) { return; }
                        node.dkStopTimer(); node.dkStopTimer = null;
                        node.dkPending = false; generation.pending--;
                        node.dkCancel = null;
                        node.onload = node.onerror = null;
                        if (error && !generation.cancelled) { fail(error); }
                        if (generation.cancelled) { attempt(function () { remove(node); }); }
                        release(); resolve();
                    }
                    node.onload = function () { done(null); };
                    node.onerror = function () { done(new Error('Cannot load ' + path)); };
                    if (style) { node.dkCancel = function () { done(null); }; }
                    alarm = setTimeout(function () {
                        alarm = null;
                        if (!generation.cancelled) { fail(new Error('Timed out loading ' + path)); }
                        // Do not allow an optional renderer to suspend native allSettled forever.
                        // Classic scripts remain quarantined until their eventual load/error event.
                        resolve();
                    }, 10000);
                    document.head.appendChild(node);
                } catch (error) {
                    if (alarm !== null) { clearTimeout(alarm); }
                    if (node && node.dkPending) { node.dkPending = false; generation.pending--; }
                    fail(error); resolve();
                }
            });
        }
        return Promise.resolve({
            getState: function () { return state; },
            getDiagnostics: function () { return errors.slice(); },
            getPendingResources: function () { return generation.pending; },
            init: function () {
                if (pending) { return pending; }
                if (state === 'destroyed') { return Promise.resolve(empty); }
                pending = new Promise(function (resolve) { finish = resolve; });
                state = 'initializing';
                if (window.__dkHangarMarks || window.__dkHangarMarksLoad) {
                    fail(new Error('Hangar marks owner or retiring generation already exists')); return pending;
                }
                window.__dkHangarMarksLoad = generation;
                var styles = Promise.all(['shared/fonts.css', 'shared/marks_panel.css', 'hangar_marks_of_excellence/marks.css'].map(function (path) {
                    return load(path, true);
                }));
                var scripts = Promise.resolve().then(function () {
                    if (!generation.cancelled && !window.__dkMarksKit) { return load('shared/marks_panel.js', false); }
                }).then(function () {
                    if (!generation.cancelled) { return load('hangar_marks_of_excellence/marks.js', false); }
                });
                Promise.all([styles, scripts]).then(function () {
                    if (generation.cancelled) { cleanup(); settle(); return; }
                    var owner = window.__dkHangarMarks;
                    if (!owner || owner.generation !== generation || owner.getState() === 'failed') {
                        fail(new Error('Hangar marks renderer did not create a valid owner')); return;
                    }
                    state = 'ready'; release();
                    console.info('[Driftkings] Hangar marks renderer loaded by native plugin');
                    settle();
                }).catch(fail);
                return pending;
            },
            destroy: function () {
                if (state !== 'destroyed') {
                    state = 'destroying'; cleanup(); settle(); state = 'destroyed';
                    if (generation.pending) { report(new Error('Retiring pending resources: ' + generation.pending)); }
                }
                return Promise.resolve();
            }
        });
    }
};
