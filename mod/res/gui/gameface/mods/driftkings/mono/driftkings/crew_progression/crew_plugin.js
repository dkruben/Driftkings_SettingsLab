/* CT native data plugin. No imports or effects at module evaluation. */
export default {
    plugin: function () {
        var state = 'created', pending = null, resolveInit = null, root = null;
        var script = null, waiting = false, loaded = false, alarm = null, errors = [];
        var generation = {cancelled: false, report: report, fail: fail, ready: ready};
        function empty() { return null; }
        function report(error) {
            errors.push(String(error && error.message || error));
            console.error('[Driftkings] Native crew progression: ' + errors[errors.length - 1]);
        }
        function attempt(action) { try { action(); } catch (error) { report(error); } }
        function stopTimer() { if (alarm !== null) { clearTimeout(alarm); alarm = null; } }
        function release() {
            if (root && !waiting && state !== 'initializing' && root.__dkCrewProgressionLoad === generation) {
                delete root.__dkCrewProgressionLoad;
            }
        }
        function removeScript() {
            if (!script) { return; }
            script.onload = script.onerror = null;
            if (script.parentNode) { script.parentNode.removeChild(script); }
            script = null;
        }
        function cleanup() {
            generation.cancelled = true; attempt(stopTimer);
            var owner = root && root.__dkCrewProgression;
            if (owner && owner.generation === generation) { attempt(function () { owner.dispose(); }); }
            if (owner && owner.generation === generation && root.__dkCrewProgression === owner) {
                report(new Error('Crew owner cleanup incomplete; withdrawing own API'));
                delete root.__dkCrewProgression;
                attempt(function () { root.dispatchEvent(new Event('dk-carousel-config')); });
            }
            // Classic scripts can execute late; retain retirement callbacks and block a new generation.
            if (!waiting) { attempt(removeScript); }
            release();
        }
        function settle() { if (resolveInit) { var resolve = resolveInit; resolveInit = null; resolve(empty); } }
        function fail(error) {
            report(error);
            if (state !== 'destroyed' && state !== 'destroying') { state = 'failed'; }
            cleanup(); settle();
        }
        function ready() {
            if (generation.cancelled || !loaded) { return; }
            var owner = root.__dkCrewProgression;
            if (!owner || owner.generation !== generation || typeof owner.getRow !== 'function' ||
                    typeof owner.dispose !== 'function' || typeof owner.getState !== 'function') {
                fail(new Error('Crew bridge did not publish a ready API')); return;
            }
            if (owner.getState() === 'initializing') { return; }
            if (owner.getState() !== 'ready') { fail(new Error('Crew bridge is unavailable')); return; }
            state = 'ready'; stopTimer(); release(); settle();
            console.info('[Driftkings] Crew progression API ready by native plugin; snapshot=' + owner.getSnapshotState());
        }
        return Promise.resolve({
            getState: function () { return state; },
            getDiagnostics: function () { return errors.slice(); },
            getPendingResources: function () { return waiting ? 1 : 0; },
            getSnapshotState: function () {
                var owner = root && root.__dkCrewProgression;
                return owner && owner.generation === generation ? owner.getSnapshotState() : 'unavailable';
            },
            init: function () {
                if (pending) { return pending; }
                if (state === 'destroyed') { return Promise.resolve(empty); }
                pending = new Promise(function (resolve) { resolveInit = resolve; }); state = 'initializing';
                try {
                    root = typeof window === 'undefined' ? null : window;
                    if (!root || typeof document === 'undefined' || !document.head ||
                            typeof engine === 'undefined' || typeof viewEnv === 'undefined') {
                        throw new Error('Crew plugin context unavailable');
                    }
                    if (root.__dkCrewProgression || root.__dkCrewProgressionLoad) { throw new Error('Crew owner or retiring generation already exists'); }
                    root.__dkCrewProgressionLoad = generation;
                    script = document.createElement('script');
                    script.src = 'coui://gui/gameface/mods/driftkings/crew_progression/crew.js'; script.async = false;
                    script.onload = function () {
                        try {
                            waiting = false; loaded = true;
                            if (generation.cancelled) { cleanup(); return; }
                            var owner = root.__dkCrewProgression;
                            if (!owner || owner.generation !== generation) { fail(new Error('Crew renderer did not publish its owner')); return; }
                            attempt(removeScript); ready();
                        } catch (error) { fail(error); }
                    };
                    script.onerror = function () { waiting = false; fail(new Error('Cannot load crew renderer')); };
                    alarm = setTimeout(function () { alarm = null; fail(new Error('Timed out loading crew API')); }, 10000);
                    waiting = true;
                    document.head.appendChild(script);
                } catch (error) { waiting = false; fail(error); }
                return pending;
            },
            destroy: function () {
                if (state !== 'destroyed') {
                    state = 'destroying'; cleanup(); settle(); state = 'destroyed';
                    if (waiting) { report(new Error('Crew script retiring; resource still pending')); }
                }
                return Promise.resolve();
            }
        });
    }
};
