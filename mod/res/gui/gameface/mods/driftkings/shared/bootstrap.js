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
    var features = {
        "DriftkingsCarouselStats": {
            "owner": "__dkCarouselStats",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel_native.js",
                "coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel_layout.js",
                "coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/vehicle_carousel/carousel.css"
            ]
        },
        "DriftkingsCrewDetails": {
            "owner": "__dkCrewDetails",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/crew_details/details.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/crew_details/details.css"
            ]
        },
        "DriftkingsCrewProgression": {
            "owner": "__dkCrewProgression",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/crew_progression/crew.js"
            ],
            "styles": []
        },
        "DriftkingsHangarClock": {
            "owner": "__dkHangarClock",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/main/clock.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/main/clock.css"
            ]
        },
        "DriftkingsHangarHeaderOptions": {
            "owner": "__dkHangarHeaderOptions",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/hangar_preferences/header_options.js"
            ],
            "styles": []
        },
        "DriftkingsMainGun": {
            "owner": "__dkMainGun",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/shared/marks_panel.js",
                "coui://gui/gameface/mods/driftkings/high_caliber_gameface/main_gun.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/high_caliber_gameface/main_gun.css"
            ]
        },
        "DriftkingsMarksOnGunBattle": {
            "owner": "__dkBattleMarks",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/shared/marks_panel.js",
                "coui://gui/gameface/mods/driftkings/battle_marks_of_excellence/marks.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/shared/marks_panel.css",
                "coui://gui/gameface/mods/driftkings/battle_marks_of_excellence/marks.css"
            ]
        },
        "DriftkingsMarksOnGunHangar": {
            "owner": "__dkHangarMarks",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/shared/marks_panel.js",
                "coui://gui/gameface/mods/driftkings/hangar_marks_of_excellence/marks.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/shared/marks_panel.css",
                "coui://gui/gameface/mods/driftkings/hangar_marks_of_excellence/marks.css"
            ]
        },
        "DriftkingsMarksOnGunTechTree": {
            "owner": "__dkTechMarks",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/tech_tree_marks_of_excellence/marks.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/shared/marks_tokens.css",
                "coui://gui/gameface/mods/driftkings/tech_tree_marks_of_excellence/marks.css"
            ]
        },
        "DriftkingsProfileRatings": {
            "owner": "__dkProfileRatings",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/profile_ratings/ratings.js"
            ],
            "styles": []
        },
        "DriftkingsRatingPlayers": {
            "owner": "__dkPlayerRatings",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/panel_gameface/rating_text.js",
                "coui://gui/gameface/mods/driftkings/panel_gameface/rating_rows.js",
                "coui://gui/gameface/mods/driftkings/panel_gameface/ratings.js"
            ],
            "styles": []
        },
        "driftkingsbattleEfficiency": {
            "owner": "__dkBattleEfficiency",
            "scripts": [
                "coui://gui/gameface/mods/driftkings/shared/flash_text.js",
                "coui://gui/gameface/mods/driftkings/battle_performance/results.js"
            ],
            "styles": [
                "coui://gui/gameface/mods/driftkings/battle_performance/results.css"
            ]
        }
    };
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
