/* CT native carousel transport. Evaluation has no DOM effects. */
export default {
    plugin: function () {
        var state = 'created', pending = null, resolveInit = null, root = null, alarm = null;
        var nodes = [], waiting = null, scriptsDone = false, cssLeft = 0, errors = [];
        var scripts = ['carousel_native.js', 'carousel_layout.js', 'carousel.js'];
        var keys = ['DKCarouselNative', 'DKCarouselLayout', '__dkCarouselStats'];
        var generation = {cancelled: false, report: report, fail: fail, ready: ready};
        function empty() { return null; }
        function report(error) {
            errors.push(String(error && error.message || error));
            console.error('[Driftkings] Native carousel: ' + errors[errors.length - 1]);
        }
        function attempt(action) { try { action(); } catch (error) { report(error); } }
        function remove(node) {
            node.onload = node.onerror = null;
            if (node.parentNode) { node.parentNode.removeChild(node); }
        }
        function release() {
            if (root && !waiting && state !== 'initializing' && root.__dkCarouselLoad === generation) {
                delete root.__dkCarouselLoad;
            }
        }
        function settle() { if (resolveInit) { var resolve = resolveInit; resolveInit = null; resolve(empty); } }
        function cleanup() {
            generation.cancelled = true;
            if (alarm !== null) { var timer = alarm; alarm = null; attempt(function () { clearTimeout(timer); }); }
            var renderer = generation.renderer;
            if (renderer && renderer.generation === generation) { attempt(function () { renderer.dispose(); }); }
            if (generation.native) { attempt(function () { generation.native.dispose(); }); }
            keys.forEach(function (key) {
                var owner = root && root[key];
                if (owner && owner.generation === generation) { delete root[key]; }
            });
            nodes.forEach(function (node) { if (node !== waiting) { attempt(function () { remove(node); }); } });
            release();
        }
        function fail(error) {
            report(error);
            if (state !== 'destroyed' && state !== 'destroying') { state = 'failed'; }
            cleanup(); settle();
        }
        function ready() {
            if (generation.cancelled || !scriptsDone || cssLeft) { return; }
            var renderer = root.__dkCarouselStats;
            if (!renderer || renderer.generation !== generation || renderer.getState() !== 'ready') { return; }
            state = 'ready';
            if (alarm !== null) { clearTimeout(alarm); alarm = null; }
            release(); settle();
            console.info('[Driftkings] Carousel native ready; model=' + renderer.getModelState());
        }
        function loadScript(index) {
            if (generation.cancelled) { return; }
            if (index === scripts.length) { scriptsDone = true; ready(); return; }
            var node = document.createElement('script');
            node.src = 'coui://gui/gameface/mods/driftkings/vehicle_carousel/' + scripts[index]; node.async = false;
            node.onload = function () {
                try {
                    waiting = null;
                    if (generation.cancelled) { cleanup(); return; }
                    var owner = root[keys[index]];
                    if (!owner || owner.generation !== generation) { throw new Error('Carousel resource did not publish its owner: ' + scripts[index]); }
                    remove(node); loadScript(index + 1);
                } catch (error) { fail(error); }
            };
            node.onerror = function () { waiting = null; fail(new Error('Cannot load carousel script: ' + scripts[index])); };
            nodes.push(node); waiting = node;
            try { document.head.appendChild(node); } catch (error) { waiting = null; throw error; }
        }
        return Promise.resolve({
            getState: function () { return state; },
            getDiagnostics: function () { return errors.slice(); },
            getPendingResources: function () { return waiting ? 1 : 0; },
            getModelState: function () {
                var owner = root && root.__dkCarouselStats;
                return owner && owner.generation === generation ? owner.getModelState() : 'unavailable';
            },
            init: function () {
                if (pending) { return pending; }
                if (state === 'destroyed') { return Promise.resolve(empty); }
                pending = new Promise(function (resolve) { resolveInit = resolve; }); state = 'initializing';
                try {
                    root = typeof window === 'undefined' ? null : window;
                    if (!root || typeof document === 'undefined' || !document.head ||
                            typeof engine === 'undefined' || typeof viewEnv === 'undefined') { throw new Error('Carousel context unavailable'); }
                    if (root.__dkCarouselLoad || keys.some(function (key) { return !!root[key]; })) { throw new Error('Carousel owner or retiring generation already exists'); }
                    root.__dkCarouselLoad = generation;
                    // Bounds resource/engine loading, not the availability of vehicle data.
                    alarm = setTimeout(function () { alarm = null; fail(new Error('Timed out loading carousel resources/API')); }, 10000);
                    cssLeft = 2;
                    ['shared/fonts.css', 'vehicle_carousel/carousel.css'].forEach(function (path) {
                        if (generation.cancelled) { return; }
                        var node = document.createElement('link'); node.rel = 'stylesheet';
                        node.href = 'coui://gui/gameface/mods/driftkings/' + path;
                        node.onload = function () { if (!generation.cancelled) { cssLeft--; node.onload = node.onerror = null; ready(); } };
                        node.onerror = function () { if (!generation.cancelled) { fail(new Error('Cannot load carousel CSS: ' + path)); } };
                        nodes.push(node); document.head.appendChild(node);
                    });
                    if (!generation.cancelled) { loadScript(0); }
                } catch (error) { fail(error); }
                return pending;
            },
            destroy: function () {
                if (state !== 'destroyed') {
                    state = 'destroying'; cleanup(); settle(); state = 'destroyed';
                    if (waiting) { report(new Error('Carousel classic script retiring; resource still pending')); }
                }
                return Promise.resolve();
            }
        });
    }
};
