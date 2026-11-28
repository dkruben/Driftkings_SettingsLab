/* DK Settings — macros de estatísticas do carrossel para os exemplos inline dos campos de formatação.
   Avalia {{v.x}}, {{v.c:x}}, {{v.x%2d~%}}, {{v.x?sim|não}}, {{v.x|omissão}} e macros aninhadas sobre dois veículos
   de exemplo (estatísticas fictícias, identificadas como exemplo). O cartão de pré-visualização foi removido. */
(function () {
    'use strict';
    var DK = window.DK;
    var SCALE = ['#FE0E00', '#FE7903', '#F8F400', '#A6FFA6', '#02C9B3', '#D042F3'];
    var LIMITS = {tdb: [500, 750, 1000, 1800, 2500], winrate: [47, 49, 52, 57, 62], battles: [100, 300, 1000, 2000, 5000], hitsRatio: [60, 66, 72, 78, 84],
                  damageRating: [20, 50, 65, 85, 95], wn8effd: [0.5, 0.7, 0.9, 1.2, 1.9], wn8: [300, 900, 1500, 2300, 3200]};
    var VEHICLES = [
        {name: 'T32', nation: 'usa', tank: 'a12_t32', tier: 8, flag: ['#2c4a6b', '#1a2c40'], level: 'VIII', type: 'heavyTank', short: 'HT', selected: true, premium: false, xp: 'x2',
         stats: {battles: 1245, winrate: 54.3, hitsRatio: 78.4, tdb: 2380, tfb: 1, wn8expd: 1950, wn8effd: 1.22, wn8: 2150, battletiermin: 8, battletiermax: 10,
                 marksOnGun: 2, damageRating: 87.4, mastery: 3}},
        {name: 'Obj. 140', nation: 'ussr', tank: 'r97_object_140', tier: 10, flag: ['#6b2c2c', '#401a1a'], level: 'X', type: 'mediumTank', short: 'MT', selected: false, premium: false, info: false,
         stats: {battles: 312, winrate: 48.6, hitsRatio: 70.2, tdb: 3150, tfb: 1, wn8expd: 3400, wn8effd: 0.93, wn8: 1420, battletiermin: 10, battletiermax: 10,
                 marksOnGun: 0, damageRating: 41.2, mastery: 1}}
    ];
    // Class colours from lobby/vehicle_carousel.py (CLASS_COLORS); {{v.c:type}} names the card background image.
    var CLASS_COLORS = {lightTank: '#53b329', mediumTank: '#1ea2d2', heavyTank: '#957d5b', 'AT-SPG': '#f13439', SPG: '#b87ab2'};


    /* Rating macros ---------------------------------------------------------- */
    function colorOf(name, value) {
        var limits = LIMITS[name];
        if (!limits || typeof value !== 'number') { return null; }
        for (var i = 0; i < limits.length; i++) { if (value < limits[i]) { return SCALE[i]; } }
        return SCALE[SCALE.length - 1];
    }
    function lookup(name, vehicle) {
        name = name.replace(/^v\./, '');
        var aliases = {tdb: 'avgDamage', winrate: 'winRate', hitsRatio: 'hitRate', damageRating: 'marks', tfb: 'avgFrags', t_battles: 'battles', markOfMastery: 'mastery'};
        if (name.indexOf('c:') === 0) {
            var key = name.slice(2);
            if (key === 'type') { return CLASS_COLORS[vehicle.type] || '#957d5b'; }
            if (vehicle.colors) { return vehicle.colors[aliases[key] || key] || null; }
            return colorOf(key === 'wn8expd' ? 'tdb' : key, vehicle.stats[key]);
        }
        if (name === 'name') { return vehicle.name; }
        if (name === 'premium') { return vehicle.premium || null; }
        if (name === 'selected') { return vehicle.selected || null; }
        if (name === 'level') { return vehicle.level; }
        if (vehicle.colors) { return vehicle.stats[aliases[name] || name]; }
        if (name === 'tfb') { return vehicle.stats.tfb ? vehicle.stats.tdb : null; }
        var value = vehicle.stats[name];
        return value === 0 && /marksOnGun/.test(name) ? null : value;
    }
    function format(value, spec) {
        if (!spec) { return String(value); }
        var match = /%-?(\d*)(?:\.(\d+))?([sdif])/.exec(spec);
        if (!match || typeof value !== 'number') { return String(value); }
        return match[3] === 'f' ? value.toFixed(match[2] ? Number(match[2]) : 2) : match[3] === 's' ? String(value) : String(Math.round(value));
    }
    function evaluate(body, vehicle) {
        if (body.indexOf('icon:') === 0) {
            var kind = body.slice(5);
            if (kind === 'mastery' && vehicle.stats.mastery) { return DK.assets.mastery(vehicle.stats.mastery); }
            if (kind === 'marksOnGun') {
                var count = vehicle.stats.marksOnGun;
                if (!count) { return 'gui/maps/driftkings/carroucel/mark_0.png'; }
                return vehicle.colors ? 'gui/maps/icons/marksOnGun/95x85/' + vehicle.nation + '_' + count + '_' + (count === 1 ? 'mark' : 'marks') + '.png' : DK.assets.marks(count);
            }
            if (vehicle.colors) {
                if (kind === 'mastery') { return '--'; }
                var icons = {damage: 'efficiency/48x48/damage.png', assist: 'efficiency/48x48/help.png', blocked: 'efficiency/48x48/armor.png', wins: 'dossier/wins40x32.png', battles: 'dossier/battles40x32.png'};
                return icons[kind] ? 'gui/maps/icons/library/' + icons[kind] : '';
            }
            return 'dkicon:' + kind;
        }
        var name = /^[\w.:-]+/.exec(body);
        name = name ? name[0] : body;
        var rest = body.slice(name.length), value = lookup(name, vehicle), present = value !== undefined && value !== null && value !== '';
        if (rest.charAt(0) === '?') {
            var bar = rest.indexOf('|');
            return value ? rest.slice(1, bar < 0 ? undefined : bar) : bar < 0 ? '' : rest.slice(bar + 1);
        }
        var spec = /^%[-\d.]*[sdif]/.exec(rest);
        if (spec) { rest = rest.slice(spec[0].length); }
        var suffix = '', fallback = null;
        if (rest.charAt(0) === '~') { var end = rest.indexOf('|'); suffix = rest.slice(1, end < 0 ? undefined : end); rest = end < 0 ? '' : rest.slice(end); }
        if (rest.charAt(0) === '|') { fallback = rest.slice(1); }
        if (!present) { return fallback === null ? (vehicle.colors ? '--' : '') : fallback; }
        return format(value, spec ? spec[0] : null) + suffix;
    }
    // Innermost macros first, so {{v.tfb?{{v.wn8expd%d}}|}} works.
    function macros(text, vehicle) {
        text = String(text === undefined || text === null ? '' : text);
        vehicle = vehicle || VEHICLES[0];
        for (var guard = 0; guard < 30 && /\{\{[^{}]*\}\}/.test(text); guard++) {
            text = text.replace(/\{\{([^{}]*)\}\}/g, function (all, body) { return evaluate(body, vehicle); });
        }
        return text;
    }

    DK.carouselMacros = {macros: macros};
}());
