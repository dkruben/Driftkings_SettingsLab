/* DK Settings — camadas: menus ancorados, dica, janelas modais (pilha com foco preso) e scroll. */
(function () {
    'use strict';
    var DK = window.DK, h = DK.h;
    var root = null, menu = null, tip = null, stack = [];

    /* Menus anchored to a control ----------------------------------------- */
    function place(node, anchor, above) {
        var rect = anchor.getBoundingClientRect(), height = node.offsetHeight || 0, width = node.offsetWidth || 0;
        var top = above ? rect.top - height - 6 : rect.bottom + 2;
        if (!above && top + height > window.innerHeight - 4) { top = Math.max(4, rect.top - height - 2); }
        if (top < 4) { top = rect.bottom + 6; }
        node.style.left = Math.max(4, Math.min(rect.left, window.innerWidth - width - 4)) + 'px';
        node.style.top = top + 'px';
    }
    function outside(event) {
        if (menu && !DK.inside(event.target, menu.node) && !DK.inside(event.target, menu.anchor)) { closeMenu(); }
    }
    function closeMenu(keepFocus) {
        if (!menu) { return false; }
        var old = menu;
        menu = null;
        DK.remove(old.node);
        document.removeEventListener('mousedown', outside, true);
        if (old.onClose) { old.onClose(); }
        if (!keepFocus) { DK.focus(old.anchor); }
        return true;
    }
    function openMenu(anchor, content, onClose) {
        closeMenu(true);
        var node = h('div.dk-menu', null, content, root);
        node.style.minWidth = anchor.getBoundingClientRect().width + 'px';
        menu = {node: node, anchor: anchor, onClose: onClose};
        place(node, anchor, false);
        node.addEventListener('wheel', function (event) {
            node.scrollTop -= DK.wheel(event) * 40;
            DK.stop(event);
        });
        document.addEventListener('mousedown', outside, true);
        return node;
    }

    /* Tooltip -------------------------------------------------------------- */
    function showTip(anchor, text) {
        hideTip();
        if (!text) { return; }
        tip = h('div.dk-tip', {text: text}, null, root);
        place(tip, anchor, true);
    }
    function hideTip() { DK.remove(tip); tip = null; }

    /* Modal dialogs (stacked) ---------------------------------------------- */
    function focusables(node) {
        var list = node.querySelectorAll('button,input,textarea,[tabindex]'), result = [];
        for (var i = 0; i < list.length; i++) {
            if (!list[i].disabled && list[i].tabIndex >= 0 && list[i].offsetWidth > 0) { result.push(list[i]); }
        }
        return result;
    }
    // options: {host, className, onClose(reason), focus}
    function openModal(content, options) {
        options = options || {};
        closeMenu(true); hideTip();
        var overlay = h('div.dk-modal-backdrop', null, null, options.host || root);
        var panel = h('div.dk-modal' + (options.className ? '.' + options.className : ''), {role: 'dialog', 'aria-modal':'true'}, content, overlay);
        var entry = {overlay: overlay, panel: panel, origin: options.origin || document.activeElement, onClose: options.onClose};
        overlay.addEventListener('mousedown', function (event) { if (event.target === overlay && options.dismissable !== false) { closeModal(entry, 'outside'); } });
        stack.push(entry);
        var first = options.focus || focusables(panel)[0];
        setTimeout(function () { DK.focus(first); }, 0);
        entry.close = function (reason) { closeModal(entry, reason || 'code'); };
        return entry;
    }
    function closeModal(entry, reason) {
        var index = stack.indexOf(entry);
        if (index < 0) { return; }
        stack.splice(index, 1);
        DK.remove(entry.overlay);
        DK.focus(entry.origin);
        if (entry.onClose) { entry.onClose(reason); }
    }
    function topModal() { return stack.length ? stack[stack.length - 1] : null; }
    // Keyboard owned by the layer: Esc closes the menu or the top dialog, Tab stays inside it.
    function key(event) {
        if (event.keyCode === 27) {
            if (closeMenu()) { DK.stop(event); return true; }
            var top = topModal();
            if (top) { DK.stop(event); closeModal(top, 'escape'); return true; }
            return false;
        }
        if (event.keyCode === 9 && topModal()) {
            var list = focusables(topModal().panel), index = list.indexOf(document.activeElement);
            if (list.length) { DK.stop(event); DK.focus(list[(index + (event.shiftKey ? -1 : 1) + list.length) % list.length]); }
            return true;
        }
        return false;
    }

    /* Scroll areas: fixed-step wheel and a thin draggable bar ------------- */
    // Gameface's native overflow scroll is slow; wheel steps are applied here.
    function scroller(viewport, host) {
        var cancelDrag=null, disposed=false;
        var track = h('div.dk-scroll', null, null, host), thumb = h('div.dk-scroll-thumb', null, null, track);
        function update() {
            if(disposed){return;}
            var height = viewport.clientHeight, total = viewport.scrollHeight;
            DK.show(track, total > height + 1);
            var usable = track.clientHeight || height;
            var size = Math.min(usable, Math.max(28, usable * height / Math.max(1, total)));
            thumb.style.height = size + 'px';
            thumb.style.top = ((usable - size) * viewport.scrollTop / Math.max(1, total - height)) + 'px';
        }
        viewport.addEventListener('wheel', function (event) {
            if (event.defaultPrevented) { return; }
            var unit = parseFloat(document.documentElement.style.fontSize) || 1;
            var max = Math.max(0, viewport.scrollHeight - viewport.clientHeight);
            viewport.scrollTop = DK.clamp(viewport.scrollTop - DK.wheel(event) * 80 * unit, 0, max);
            update(); hideTip(); DK.stop(event);
        });
        viewport.addEventListener('scroll', update);
        track.addEventListener('mousedown', function (event) {
            if (event.button !== 0 || disposed) { return; }
            if(cancelDrag){cancelDrag();}
            DK.stop(event);
            var rect = track.getBoundingClientRect(), thumbRect = thumb.getBoundingClientRect();
            var grip = event.target === thumb ? event.clientY - thumbRect.top : thumbRect.height / 2;
            function move(e) {
                var span = Math.max(1, rect.height - thumbRect.height);
                viewport.scrollTop = DK.clamp((e.clientY - rect.top - grip) / span, 0, 1) * Math.max(0, viewport.scrollHeight - viewport.clientHeight);
                update();
            }
            function end() { document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', end);cancelDrag=null; }
            cancelDrag=end;
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', end);
            if (event.target !== thumb) { move(event); }
        });
        return {update:update,to:function(top){viewport.scrollTop=Math.max(0,top);update();},dispose:function(){disposed=true;if(cancelDrag){cancelDrag();}DK.remove(track);}};
    }

    DK.layer = {
        init: function (node) { root = node; },
        menu: openMenu, closeMenu: closeMenu, menuOpen: function () { return !!menu; },
        tip: showTip, hideTip: hideTip, key: key, scroller: scroller
    };
    DK.modal = {open: openModal, top: topModal, closeAll: function () { while (stack.length) { closeModal(stack[stack.length - 1], 'code'); } }};
}());
