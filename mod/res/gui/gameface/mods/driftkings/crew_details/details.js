(function () {
    'use strict';
    if (window.__dkCrewDetails) { window.__dkCrewDetails.dispose(); }
    var FEATURE = 'DriftkingsCrewDetails', disposed = false, pending = null, observer = null;
    var bindings = {}, mounted = [];
    var targets = {
        tooltip: '[class^="TankmanTooltipApp_base_"]',
        personal_file: '[class^="PersonalFileViewApp_content_"] [class^="TankmanInfoApp_descriptionBlock_"]',
        service_record: '[class^="ServiceRecordApp_content_"] [class^="TankmanInfoApp_descriptionBlock_"]'
    };
    function owned(node) {
        while (node && node !== document.body) {
            if (node.classList && node.classList.contains('dk-crew-details')) { return true; }
            node = node.parentNode;
        }
        return false;
    }
    function clear() {
        mounted.forEach(function (node) { if (node.parentNode) { node.parentNode.removeChild(node); } });
        mounted = [];
    }
    function release(id) {
        viewEnv.removeDataChangedCallback(bindings[id].callback, bindings[id].id);
        delete bindings[id];
    }
    function mount(host, data) {
        if (!host) { return; }
        for (var k = mounted.length - 1; k >= 0; k--) {
            if (mounted[k].parentNode === host) { host.removeChild(mounted[k]); mounted.splice(k, 1); }
        }
        var box = document.createElement('div'); box.className = 'dk-crew-details dk-crew-details--' + data.surface;
        if (data.surface === 'barracks') {
            // Native card integration: one line of inline segments. Each segment reuses the existing semantic class;
            // separators are neutral and appear only between visible segments. Text is set with textContent only.
            var single = document.createElement('div'); single.className = 'dk-crew-details__line';
            (data.segments || []).forEach(function (segment, index) {
                if (index > 0) {
                    var separator = document.createElement('span');
                    separator.className = 'dk-crew-details__line--unavailable';
                    separator.textContent = SEPARATOR; single.appendChild(separator);
                }
                var part = document.createElement('span');
                part.className = segment.kind ? 'dk-crew-details__line--' + segment.kind : '';
                part.textContent = segment.text; single.appendChild(part);
            });
            box.appendChild(single);
            host.appendChild(box); mounted.push(box);
            return;
        }
        if (data.title) {
            var title = document.createElement('div'); title.className = 'dk-crew-details__title';
            title.textContent = data.title; box.appendChild(title);
        }
        (data.lines || []).forEach(function (value, index) {
            var line = document.createElement('div'); line.className = 'dk-crew-details__line';
            var kind = (data.kinds || [])[index];
            if (/^(xp|battles|ready|complete|unavailable|total)$/.test(kind || '')) {
                line.className += ' dk-crew-details__line--' + kind;
            }
            line.textContent = value; box.appendChild(line);
        });
        host.appendChild(box); mounted.push(box);
    }
    // Barracks: one segment per visible value, from the native-localized lines and their kinds. Only a missing estimate
    // becomes a neutral dash (never zero); a single-value state keeps its own localized text and semantic kind.
    var SEPARATOR = ' · ', KINDS = /^(xp|battles|ready|complete|unavailable)$/;
    function barracksSegments(row) {
        var lines = row.lines || [], kinds = row.kinds || [];
        return lines.map(function (value, index) {
            var kind = KINDS.test(kinds[index] || '') ? kinds[index] : '';
            if (lines.length > 1 && kind === 'unavailable') { return {text: '—', kind: 'unavailable'}; }
            return {text: String(value), kind: kind};
        });
    }
    function render() {
        pending = null;
        if (disposed) { return; }
        clear();
        var present = {}, ids = window.subViews ? window.subViews.ids() : [];
        ids.forEach(function (id) {
            var child = window.subViews.get(id), model = child && child.model;
            if (!model || !model.DriftkingsUI || model.DriftkingsUI.name !== FEATURE) { return; }
            present[id] = true;
            var binding = bindings[id];
            if (!binding || binding.model !== model) {
                if (binding) { release(id); }
                binding = bindings[id] = {id: id, model: model, signature: null, data: {},
                    callback: viewEnv.addDataChangedCallback('model', id, true)};
            }
            if (binding.signature !== model.payload) {
                binding.signature = model.payload;
                try { binding.data = JSON.parse(model.payload || '{}'); } catch (error) { binding.data = {}; }
            }
            var data = binding.data, selector = data.surface === 'barracks' ? '[data-dk-barracks-id]' : targets[data.surface];
            if (!(data.config || {}).visible || !selector) { return; }
            if (data.surface === 'barracks') {
                // The information block is the native container that renders additionalContent after the skills row.
                // A card without that block gets nothing: no overlay is ever drawn over the portrait.
                var cards = document.querySelectorAll('[data-dk-barracks-kind="tankman"][data-dk-barracks-id]');
                var rows = {};
                (data.rows || []).forEach(function (row) { rows[String(row.id)] = row; });
                Array.prototype.forEach.call(cards, function (card) {
                    var row = rows[card.getAttribute('data-dk-barracks-id')];
                    var info = card.querySelector('[class^="Content_base_"]');
                    var segments = row ? barracksSegments(row) : [];
                    if (segments.length && info) { mount(info, {surface: 'barracks', segments: segments}); }
                });
                return;
            }
            var host = document.querySelector(selector);
            if (!host && (data.surface === 'personal_file' || data.surface === 'service_record')) {
                var root = document.querySelector(data.surface === 'personal_file' ? '[class^="PersonalFileViewApp_content_"]' : '[class^="ServiceRecordApp_content_"]');
                if (root) { host = document.querySelector('[class^="TankmanInfoApp_descriptionBlock_"]') || root; }
            }
            mount(host, data);
        });
        Object.keys(bindings).forEach(function (id) { if (!present[id]) { release(id); } });
    }
    function schedule() { if (!disposed && pending === null) { pending = setTimeout(render, 0); } }
    function mutations(records) {
        for (var i = 0; i < records.length; i++) {
            if (owned(records[i].target)) { continue; }
            if (records[i].type === 'attributes') { schedule(); return; }
            var nodes = Array.prototype.slice.call(records[i].addedNodes).concat(Array.prototype.slice.call(records[i].removedNodes));
            for (var j = 0; j < nodes.length; j++) {
                if (!owned(nodes[j])) { schedule(); return; }
            }
        }
    }
    function dispose() {
        if (disposed) { return; }
        disposed = true;
        if (pending !== null) { clearTimeout(pending); pending = null; }
        if (observer) { observer.disconnect(); observer = null; }
        engine.off('viewEnv.onDataChanged', schedule); engine.off('subViews.onAdded', schedule); engine.off('subViews.onRemoved', schedule);
        window.removeEventListener('unload', dispose);
        clear(); Object.keys(bindings).forEach(release);
        if (window.__dkCrewDetails && window.__dkCrewDetails.dispose === dispose) { delete window.__dkCrewDetails; }
    }
    window.__dkCrewDetails = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', schedule); engine.on('subViews.onAdded', schedule); engine.on('subViews.onRemoved', schedule);
        window.addEventListener('unload', dispose);
        if (window.MutationObserver) {
            observer = new MutationObserver(mutations);
            observer.observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-dk-barracks-id', 'data-dk-barracks-kind']});
        }
        schedule();
    });
}());
