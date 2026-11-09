/* CT native plugin contract: default.plugin() -> init()/destroy(). No OpenWG entry point. */
export default {
    plugin: function () {
        var nodes = [], pending = null, current = null, stopped = false;
        function empty() { return null; }
        function cleanup() {
            var owner = current;
            current = null;
            try {
                if (owner) { owner.dispose(); }
            } finally {
                if (owner && window.__dkHangarClock === owner) { delete window.__dkHangarClock; }
                nodes.forEach(function (node) {
                    node.onload = node.onerror = null;
                    if (node.parentNode) { node.parentNode.removeChild(node); }
                });
                nodes = [];
            }
        }
        return Promise.resolve({
            init: function () {
                if (pending) { return pending; }
                if (stopped) { return Promise.reject(new Error('Clock native plugin already destroyed')); }
                if (window.__dkHangarClock) { return Promise.reject(new Error('Clock owner already exists')); }
                pending = new Promise(function (resolve, reject) {
                    ['shared/fonts.css', 'main/clock.css'].forEach(function (path) {
                        var style = document.createElement('link');
                        style.rel = 'stylesheet';
                        style.href = 'coui://gui/gameface/mods/driftkings/' + path;
                        nodes.push(style); document.head.appendChild(style);
                    });
                    var script = document.createElement('script');
                    script.src = 'coui://gui/gameface/mods/driftkings/main/clock.js';
                    script.async = false;
                    script.onload = function () {
                        current = window.__dkHangarClock;
                        if (!current || typeof current.dispose !== 'function') {
                            cleanup(); reject(new Error('Clock native script did not create its owner')); return;
                        }
                        console.info('[Driftkings] Clock started by native user-missions plugin');
                        if (stopped) { cleanup(); }
                        resolve(empty);
                    };
                    script.onerror = function () { cleanup(); reject(new Error('Cannot load native clock script')); };
                    nodes.push(script); document.head.appendChild(script);
                });
                return pending;
            },
            destroy: function () {
                stopped = true;
                // A pending classic script can still execute: wait, then dispose its own generation.
                if (pending) { return pending.then(cleanup, cleanup); }
                cleanup(); return Promise.resolve();
            }
        });
    }
};
