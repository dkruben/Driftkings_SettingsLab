/* Halloween TAB: a separate allies table; the native TabScreen rows are never touched. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) { module.exports = factory(); }
    else {
        if (root.DKHalloweenTab) { root.DKHalloweenTab.hide(); }
        root.DKHalloweenTab = factory();
    }
}(this, function () {
    'use strict';
    var MISSING = '—', node = null, lastKey = null;
    function finite(value) { return value !== null && value !== undefined && value !== '' && isFinite(Number(value)); }
    function color(value) { return /^#[0-9a-fA-F]{6}$/.test(String(value)) ? String(value) : ''; }
    function rating(row) {
        if (!row.stats || !finite(row.r)) { return MISSING; }
        return row.rating === 'winrate' ? Number(row.r).toFixed(1) + '%' : String(Math.round(Number(row.r)));
    }
    function winrate(row) { return row.stats && finite(row.winrate) ? Number(row.winrate).toFixed(1) + '%' : MISSING; }
    function battles(row) {
        if (!row.stats || !finite(row.battles)) { return MISSING; }
        var count = Number(row.battles);
        return count < 1000 ? String(Math.round(count)) : (count / 1000).toFixed(1) + 'k';
    }
    // Cells as plain text and colours; names are player input and never parsed as markup.
    function cells(row) {
        return [
            {text: row.name + (row.clan ? ' [' + row.clan + ']' : ''), width: 170, align: 'left',
             color: row.self ? '#FFDD33' : ''},
            {text: row.vehicle || '', width: 100, align: 'left', color: ''},
            {text: rating(row), width: 56, align: 'right', color: row.stats ? color(row['c:r']) : ''},
            {text: winrate(row), width: 60, align: 'right', color: row.stats ? color(row['c:winrate']) : ''},
            {text: battles(row), width: 56, align: 'right', color: row.stats ? color(row['c:battles']) : ''}];
    }
    function header(rows) {
        var label = rows.length && rows[0].rating ? String(rows[0].rating).toUpperCase() : '';
        return [{text: '', width: 170}, {text: '', width: 100}, {text: label, width: 56, align: 'right'},
            {text: '', width: 60}, {text: '', width: 56}];
    }
    function line(doc, entries, opacity) {
        var element = doc.createElement('div');
        element.style.display = 'flex'; element.style.flexDirection = 'row'; element.style.height = '22rem';
        element.style.alignItems = 'center'; element.style.opacity = opacity;
        entries.forEach(function (entry) {
            var cell = doc.createElement('div');
            cell.textContent = entry.text;
            cell.style.width = entry.width + 'rem'; cell.style.textAlign = entry.align || 'left';
            cell.style.overflow = 'hidden'; cell.style.whiteSpace = 'nowrap'; cell.style.paddingRight = '6rem';
            if (entry.color) { cell.style.color = entry.color; }
            element.appendChild(cell);
        });
        return element;
    }
    function build(doc, rows) {
        var box = doc.createElement('div');
        box.className = 'dk-hw-tab';
        box.style.position = 'absolute'; box.style.left = '24rem'; box.style.top = '160rem';
        box.style.padding = '8rem 10rem'; box.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
        box.style.color = '#D9D9D9'; box.style.fontSize = '14rem'; box.style.pointerEvents = 'none';
        box.appendChild(line(doc, header(rows), 0.7));
        rows.forEach(function (row) { box.appendChild(line(doc, cells(row), row.alive ? 1 : 0.5)); });
        return box;
    }
    function hide() {
        if (node && node.parentNode) { node.parentNode.removeChild(node); }
        node = null; lastKey = null;
    }
    function render(data) {
        var rows = data && data.enabled && data.rows ? data.rows : [];
        if (!rows.length) { hide(); return; }
        var key = JSON.stringify(rows);
        if (key === lastKey && node && node.parentNode) { return; }
        hide();
        node = build(document, rows); lastKey = key;
        document.body.appendChild(node);
    }
    return {render: render, hide: hide, cells: cells, header: header};
}));
