/* Player ratings: payload rows indexed by team, id and player name. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(); }
    else { root.DKRatingRows = factory(); }
}(this, function () {
    'use strict';
    function nameKey(name) { return '$' + String(name).replace(/\s/g, ''); }
    function index(data) {
        var lookup = {left: {ids: {}, names: {}}, right: {ids: {}, names: {}}};
        data.rows.forEach(function (row) {
            var team = lookup[row.ally ? 'left' : 'right']; team.ids[row.id] = row;
            row._dkSignature = JSON.stringify(row.cfg);
            (row.aliases || []).forEach(function (alias) {
                var key = nameKey(alias);
                if (!team.names[key]) { team.names[key] = []; }
                if (team.names[key].indexOf(row) < 0) { team.names[key].push(row); }
            });
        });
        return lookup;
    }
    // A unique displayed name wins; otherwise the native position in the team's order.
    function match(lookup, data, team, position, name) {
        var candidates = lookup[team].names[nameKey(name)] || [];
        var id = data.order && data.order[team] && data.order[team][position];
        return candidates.length === 1 ? candidates[0] : lookup[team].ids[id];
    }
    return {index: index, match: match};
}));
