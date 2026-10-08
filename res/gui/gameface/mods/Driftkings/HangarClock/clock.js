(function () {
    'use strict';
    if (window.__dkHangarClock) { window.__dkHangarClock.dispose(); }
    var disposed = false, root = null, fields = {}, timer = null, callbackId = null, resourceId = null;
    var lastPayload = null, model = null, lastDate = null;
    var cfg = {}, styles = ['minimal', 'digital', 'analog', 'flip', 'panel'];
    function node(tag, cls, parent) {
        var n = document.createElement(tag); n.className = 'dk-clock__' + cls;
        parent.appendChild(n); return n;
    }
    function pad(n) { return n < 10 ? '0' + n : String(n); }
    function bounded(v, fallback, min, max) {
        v = Number(v); return isFinite(v) ? Math.max(min, Math.min(max, v)) : fallback;
    }
    function create() {
        root = document.createElement('div'); root.className = 'dk-clock';
        root.setAttribute('role', 'timer'); root.setAttribute('aria-live', 'off');
        fields.face = node('div', 'face', root);
        for (var i = 0; i < 12; i++) {
            var tick = node('i', 'tick', fields.face);
            tick.style.transform = 'rotate(' + i * 30 + 'deg)';
        }
        fields.hour = node('i', 'hand hour', fields.face);
        fields.minute = node('i', 'hand minute', fields.face);
        fields.second = node('i', 'hand second', fields.face);
        node('i', 'pin', fields.face);
        fields.content = node('div', 'content', root);
        fields.weekday = node('div', 'weekday', fields.content);
        var time = node('div', 'time', fields.content);
        fields.h = node('span', 'digit', time);
        node('span', 'colon', time).textContent = ':';
        fields.m = node('span', 'digit', time);
        fields.s = node('span', 'seconds', time);
        fields.period = node('span', 'period', time);
        fields.date = node('div', 'date', fields.content);
        document.body.appendChild(root);
    }
    function position() {
        if (!root) { return; }
        var unit = parseFloat(getComputedStyle(document.documentElement).fontSize) || 1;
        var scale = bounded(cfg.clockScale, 100, 50, 200) / 100;
        root.style.fontSize = 16 * scale * unit + 'px';
        // The right/top anchor preserves the old hangar clock's placement.
        var x = window.innerWidth - root.offsetWidth + bounded(cfg.clockX, -40, -3840, 3840) * unit;
        var y = bounded(cfg.clockY, 55, -2160, 2160) * unit;
        root.style.left = Math.max(0, Math.min(window.innerWidth - root.offsetWidth, x)) + 'px';
        root.style.top = Math.max(0, Math.min(window.innerHeight - root.offsetHeight, y)) + 'px';
    }
    function text(field, value) {
        if (field.textContent !== value) field.textContent = value;
    }
    function tick() {
        if (disposed || !root || !cfg.visible) { return; }
        var now = new Date(), h = now.getHours(), m = now.getMinutes(), s = now.getSeconds();
        text(fields.h, pad(cfg.clock24Hour === false ? (h % 12 || 12) : h));
        text(fields.m, pad(m));
        text(fields.s, cfg.clockSeconds === false ? '' : ':' + pad(s));
        text(fields.period, cfg.clock24Hour === false ? (h < 12 ? 'AM' : 'PM') : '');
        var dateKey = now.toDateString();
        if (lastDate !== dateKey) {
            lastDate = dateKey;
            text(fields.weekday, now.toLocaleDateString(undefined, {weekday: 'long'}));
            text(fields.date, now.toLocaleDateString(undefined, {day: '2-digit', month: 'short', year: 'numeric'}));
        }
        if (Math.round(bounded(cfg.clockStyle, 0, 0, 4)) === 2) {
            fields.hour.style.transform = 'rotate(' + ((h % 12) * 30 + m / 2) + 'deg)';
            fields.minute.style.transform = 'rotate(' + (m * 6 + s / 10) + 'deg)';
            fields.second.style.transform = 'rotate(' + s * 6 + 'deg)';
        }
        fields.second.style.display = cfg.clockSeconds === false ? 'none' : 'block';
        position();
    }
    function release() {
        if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, resourceId); }
        callbackId = null; resourceId = null; model = null; lastPayload = null;
    }
    function refresh() {
        if (disposed) { return; }
        var found = null, id = null;
        if (window.subViews) {
            var ids = window.subViews.ids();
            for (var i = 0; i < ids.length; i++) {
                var child = window.subViews.get(ids[i]);
                if (child && child.model && child.model.DriftkingsUI && child.model.DriftkingsUI.name === 'DriftkingsHangarClock') {
                    found = child.model; id = ids[i]; break;
                }
            }
        }
        if (resourceId !== id) {
            release(); resourceId = id;
            if (id !== null) { callbackId = viewEnv.addDataChangedCallback('model', id, true); }
        }
        model = found;
        var payload = found ? found.payload || '{}' : '{}';
        if (root && lastPayload === payload) return;
        lastPayload = payload;
        try { cfg = JSON.parse(payload).config || {}; }
        catch (e) { cfg = {}; }
        if (!root) { create(); }
        root.className = 'dk-clock dk-clock--' + styles[Math.round(bounded(cfg.clockStyle, 0, 0, 4))];
        root.style.display = cfg.visible ? 'flex' : 'none';
        if (timer !== null) { clearInterval(timer); timer = null; }
        if (cfg.visible) { tick(); timer = setInterval(tick, 1000); }
    }
    function changed() { if (!model || model.payload !== lastPayload) refresh(); }
    function dispose() {
        if (disposed) { return; } disposed = true;
        if (timer !== null) { clearInterval(timer); timer = null; }
        engine.off('viewEnv.onDataChanged', changed);
        engine.off('subViews.onAdded', refresh); engine.off('subViews.onRemoved', refresh);
        release(); window.removeEventListener('resize', position); window.removeEventListener('unload', dispose);
        if (root && root.parentNode) { root.parentNode.removeChild(root); } root = null;
    }
    window.__dkHangarClock = {dispose: dispose};
    engine.whenReady.then(function () {
        if (disposed) { return; }
        engine.on('viewEnv.onDataChanged', changed);
        engine.on('subViews.onAdded', refresh); engine.on('subViews.onRemoved', refresh);
        window.addEventListener('resize', position); window.addEventListener('unload', dispose); refresh();
    });
}());
