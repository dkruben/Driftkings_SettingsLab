/* DOM helpers, the popup/tooltip layer, drags and scrollbars. Text is always set with textContent. */
(function () {
    'use strict';
    var DK = window.DK = window.DK || {};

    function handled(event) {
        if (event && event.keyCode !== undefined && event.preventDefault) { event.preventDefault(); }
        if (event && event.stopPropagation) { event.stopPropagation(); }
        if (typeof viewEnv !== 'undefined' && typeof viewEnv.setEventHandled === 'function') { viewEnv.setEventHandled(); }
    }
    function scrollWheel(event) {
        var delta = Number(event.deltaY);
        if (!isFinite(delta) || delta === 0) { return; }
        // Gameface reports positive delta for wheel-up (opposite to browser DOM).
        // Use UI units per wheel event instead of Gameface's slow native overflow scroll.
        var scale = parseFloat(document.documentElement.style.fontSize) || 1;
        var max = Math.max(0, this.scrollHeight - this.clientHeight);
        this.scrollTop = Math.max(0, Math.min(max, this.scrollTop + (delta > 0 ? -72 : 72) * scale));
        if (this.updateScrollbar) { this.updateScrollbar(); }
        if (event.preventDefault) { event.preventDefault(); }
        handled(event);
        hideTip();
    }
    function el(tag, className, text, parent) {
        var node = document.createElement(tag);
        if (className) { node.className = className; }
        if (text !== undefined && text !== null) { node.textContent = String(text); }
        if (parent) { parent.appendChild(node); }
        if (tag === 'button') { node.addEventListener('click', handled); }
        if (tag === 'textarea' || /(^| )(dk-sidebar|dk-controls|dk-popup|dk-profile-dialog|dk-vm-properties)( |$)/.test(className || '')) {
            node.addEventListener('wheel', scrollWheel);
        }
        return node;
    }
    function setClass(node, name, on) {
        var parts = (node.className || '').split(' ').filter(function (part) { return part && part !== name; });
        if (on) { parts.push(name); }
        node.className = parts.join(' ');
    }
    function inside(node, container) {
        while (node) {
            if (node === container) { return true; }
            node = node.parentNode;
        }
        return false;
    }

    /* Popup and tooltip layer, positioned from the anchor's client rectangle. */
    var activeDrags = [];
    function cancelDrags() { activeDrags.slice().forEach(function (cancel) { cancel(); }); }
    function addDrag(cancel) { activeDrags.push(cancel); }
    function removeDrag(cancel) { var index = activeDrags.indexOf(cancel); if (index >= 0) { activeDrags.splice(index, 1); } }
    var layer = {root: null, popup: null, anchor: null, onClose: null, tip: null};
    function closePopup() {
        if (!layer.popup) { return false; }
        cancelDrags();
        var callback = layer.onClose, origin = layer.anchor;
        if (layer.popup.parentNode) { layer.popup.parentNode.removeChild(layer.popup); }
        layer.popup = layer.anchor = layer.onClose = null;
        document.removeEventListener('mousedown', outside);
        DK.modal.focus(origin);
        if (callback) { callback(); }
        return true;
    }
    function outside(event) {
        if (layer.popup && !inside(event.target, layer.popup) && !inside(event.target, layer.anchor)) { closePopup(); }
    }
    function place(node, anchor, below) {
        var rect = anchor.getBoundingClientRect();
        var height = node.offsetHeight || 0, width = node.offsetWidth || 0;
        var top = below ? rect.bottom + 2 : rect.top - height - 6;
        if (below && top + height > window.innerHeight) { top = Math.max(0, rect.top - height - 2); }
        if (top < 0) { top = rect.bottom + 6; }
        var left = Math.max(0, Math.min(rect.left, window.innerWidth - width - 4));
        node.style.left = left + 'px';
        node.style.top = top + 'px';
    }
    function openPopup(anchor, content, onClose) {
        closePopup();
        var popup = el('div', 'dk-popup', null, layer.root);
        popup.appendChild(content);
        popup.style.minWidth = anchor.getBoundingClientRect().width + 'px';
        layer.popup = popup; layer.anchor = anchor; layer.onClose = onClose || null;
        place(popup, anchor, true);
        document.addEventListener('mousedown', outside);
        return popup;
    }
    function showTip(anchor, text) {
        hideTip();
        layer.tip = el('div', 'dk-tooltip', text, layer.root);
        place(layer.tip, anchor, false);
    }
    function hideTip() {
        if (layer.tip && layer.tip.parentNode) { layer.tip.parentNode.removeChild(layer.tip); }
        layer.tip = null;
    }

    function scrollbar(node, host) {
        var track = el('div', 'dk-scroll-track', null, host);
        var thumb = el('div', 'dk-scroll-thumb', null, track);
        function update() {
            var height = node.clientHeight || 0, total = node.scrollHeight || 0;
            var usable = track.clientHeight || height;
            track.style.display = total > height ? 'block' : 'none';
            var size = Math.min(usable, Math.max(24, usable * height / Math.max(1, total)));
            thumb.style.height = size + 'px';
            thumb.style.top = (Math.max(0, usable - size) * node.scrollTop / Math.max(1, total - height)) + 'px';
        }
        track.addEventListener('mousedown', function (event) {
            if (event.button !== undefined && event.button !== 0) { return; }
            handled(event);
            if (event.preventDefault) { event.preventDefault(); }
            var rect = track.getBoundingClientRect(), thumbRect = thumb.getBoundingClientRect();
            var grip = event.target === thumb ? event.clientY - thumbRect.top : thumbRect.height / 2;
            function move(e) {
                var span = Math.max(1, rect.height - thumbRect.height);
                node.scrollTop = Math.max(0, Math.min(1, (e.clientY - rect.top - grip) / span)) * Math.max(0, node.scrollHeight - node.clientHeight);
                update(); handled(e);
            }
            function end() {
                document.removeEventListener('mousemove', move);
                document.removeEventListener('mouseup', end);
                removeDrag(end);
            }
            addDrag(end);
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', end);
            if (event.target !== thumb) { move(event); }
        });
        node.addEventListener('scroll', update);
        node.updateScrollbar = update;
        return update;
    }

    DK.dom = {el: el, setClass: setClass, scrollbar: scrollbar, inside: inside, handled: handled};
    DK.layer = {
        init: function (root) { layer.root = root; },
        open: openPopup, close: closePopup, showTip: showTip, hideTip: hideTip,
        cancelDrags: cancelDrags, addDrag: addDrag, removeDrag: removeDrag,
        anchor: function () { return layer.anchor; },
        isOpen: function () { return !!layer.popup; }
    };
}());
