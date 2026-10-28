/* Halloween TAB: reversible rating colours on native player names. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(); }
    else {
        if (root.DKHalloweenTab) { root.DKHalloweenTab.hide(); }
        root.DKHalloweenTab = factory();
    }
}(this, function () {
    'use strict';
    var currentRows = [], coloredNames = [];
    var NAME_SELECTOR = '[class*="PlayerInfo_base__tabWindow_"] [class*="PlayerInfo_userName_"]';
    function finite(value) { return value !== null && value !== undefined && value !== '' && isFinite(Number(value)); }
    function color(value) { return /^#[0-9a-fA-F]{6}$/.test(String(value)) ? String(value) : ''; }
    function restoreName(record) {
        var style = record.element.style;
        if (style.color !== record.applied) { return; }
        if (record.priority && typeof style.setProperty === 'function') { style.setProperty('color', record.original, record.priority); }
        else { style.color = record.original; }
    }
    function refresh() {
        if (!currentRows.length || !document.querySelectorAll) { return; }
        var lookup = {}, retained = [], nodes = document.querySelectorAll(NAME_SELECTOR);
        currentRows.forEach(function (row) {
            var key = '$' + row.name;
            if (Object.prototype.hasOwnProperty.call(lookup, key)) { lookup[key] = null; }
            else { lookup[key] = row; }
        });
        Array.prototype.forEach.call(nodes, function (element) {
            var row = lookup['$' + String(element.textContent).replace(/^\s+|\s+$/g, '')];
            var tint = row && row.enabled !== false && row.stats && finite(row.r) ? color(row['c:r']) : '';
            if (!tint) { return; }
            var record = null, style = element.style;
            coloredNames.some(function (saved) {
                if (saved.element !== element) { return false; }
                record = saved; return true;
            });
            var owned = record && style.color === record.applied;
            if (!owned) {
                record = {element: element, original: style.color || '',
                    priority: typeof style.getPropertyPriority === 'function' ? style.getPropertyPriority('color') : ''};
            }
            if (!owned || record.tint !== tint) {
                style.color = tint;
                record.tint = tint; record.applied = style.color;
            }
            retained.push(record);
        });
        coloredNames.forEach(function (record) {
            if (!retained.some(function (saved) { return saved.element === record.element; })) { restoreName(record); }
        });
        coloredNames = retained;
    }
    function hide() {
        coloredNames.forEach(restoreName);
        currentRows = []; coloredNames = [];
    }
    function render(data) {
        currentRows = data && data.enabled && data.rows ? data.rows : [];
        if (!currentRows.length) { hide(); return; }
        refresh();
    }
    return {render: render, refresh: refresh, hide: hide};
}));
