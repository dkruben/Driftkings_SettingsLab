/* UI-only modal lifetime and focus. */
(function () {
    'use strict';
    var DK = window.DK = window.DK || {}, active = null;
    function focus(node) { if (node && !node.disabled && node.focus) { node.focus(); } }
    function items(root) {
        var list = root.querySelectorAll('button,input,textarea,select,[tabindex]');
        return Array.prototype.filter.call(list, function (n) { return !n.disabled && n.tabIndex >= 0 && n.style.display !== 'none'; });
    }
    function close(apply) {
        if (!active) { return false; }
        var old = active; active = null;
        document.removeEventListener('keydown', keydown);
        if (old.overlay && old.overlay.parentNode) { old.overlay.parentNode.removeChild(old.overlay); }
        if (old.options.cleanup) { old.options.cleanup(); }
        focus(old.origin);
        var cb = apply === null ? null : apply ? old.options.apply : old.options.cancel; if (cb) { cb(); }
        return true;
    }
    function keydown(e) {
        if (!active || (e.keyCode !== 27 && e.keyCode !== 9)) { return; }
        if (e.preventDefault) { e.preventDefault(); } if (e.stopPropagation) { e.stopPropagation(); }
        if (e.stopImmediatePropagation) { e.stopImmediatePropagation(); }
        if (typeof viewEnv !== 'undefined' && viewEnv.setEventHandled) { viewEnv.setEventHandled(); }
        if (e.keyCode === 27) { close(false); return; }
        var list = items(active.panel), index = list.indexOf(document.activeElement);
        if (list.length) { focus(list[(index + (e.shiftKey ? -1 : 1) + list.length) % list.length]); }
    }
    function open(panel, options) {
        close(false); options = options || {};
        var origin = options.origin || document.activeElement, overlay = document.createElement('div');
        overlay.className = 'dk-modal-overlay'; panel.className += ' dk-modal-panel';
        panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true');
        overlay.appendChild(panel); (options.host || document.body).appendChild(overlay);
        active = {overlay: overlay, panel: panel, origin: origin, options: options};
        overlay.addEventListener('mousedown', function (e) { if (e.target === overlay) { close(false); } });
        document.addEventListener('keydown', keydown);
        focus(items(panel)[0]);
    }
    function bind(panel, options) {
        close(null); options = options || {};
        active = {overlay: null, panel: panel, origin: options.origin || document.activeElement, options: options};
        panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true');
        document.addEventListener('keydown', keydown); focus(items(panel)[0]);
    }
    DK.modal = {bind: bind, open: open, close: close, focus: focus, isOpen: function () { return !!active; }};
}());
