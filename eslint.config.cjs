/* Build tooling runs on Node 20; the checked client scripts stay ES5. */
module.exports = [
    {
        files: ["mod/res/gui/gameface/**/*.js"],
        languageOptions: {
            ecmaVersion: 5,
            sourceType: "script",
            globals: {
                window: "readonly",
                document: "readonly",
                console: "readonly",
                Event: "readonly",
                MutationObserver: "readonly",
                getComputedStyle: "readonly",
                requestAnimationFrame: "readonly",
                cancelAnimationFrame: "readonly",
                engine: "readonly",
                viewEnv: "readonly",
                setTimeout: "readonly",
                clearTimeout: "readonly",
                setInterval: "readonly",
                clearInterval: "readonly"
            }
        },
        rules: {
            "no-undef": "error",
            "no-unused-vars": ["error", { args: "none", caughtErrors: "none" }],
            "no-redeclare": "error",
            semi: ["error", "always"]
        }
    },
    {
        files: ["mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_layout.js",
            "mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_native.js",
            "mod/res/gui/gameface/mods/driftkings/panel_gameface/rating_rows.js",
            "mod/res/gui/gameface/mods/driftkings/shared/rating_text.js",
            "mod/res/gui/gameface/mods/driftkings/panel_gameface/halloween_tab.js"],
        languageOptions: { globals: { module: "readonly" } }
    },
    {
        // The CT native plugin loader imports an ES module; the clock renderer remains ES5.
        files: ["mod/res/gui/gameface/mods/driftkings/main/clock_plugin.js",
            "mod/res/gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js",
            "mod/res/gui/gameface/mods/driftkings/mono/driftkings/crew_progression/crew_plugin.js",
            "mod/res/gui/gameface/mods/driftkings/mono/driftkings/vehicle_carousel/carousel_plugin.js"],
        languageOptions: { ecmaVersion: 2015, sourceType: "module", globals: { Promise: "readonly" } }
    },
    {files: ["mod/res/gui/gameface/mods/driftkings/shared/native_*.js",
        "mod/res/gui/gameface/mods/driftkings/battle_performance/*.js",
        "mod/res/gui/gameface/mods/driftkings/mono/driftkings/battle_results/*.js"],
     languageOptions: {ecmaVersion: 2022, sourceType: "module"}}
];
