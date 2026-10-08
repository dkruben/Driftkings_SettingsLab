/* Python <-> Gameface transport: model.schema / model.state strings and the onAction command. */
(function () {
    'use strict';
    var DK = window.DK = window.DK || {};
    var callbackId = null, disposed = false, lastSchema = null, lastState = null, handlers = null;

    function parse(text) {
        try { return JSON.parse(text || '{}'); } catch (error) { return null; }
    }
    function changed(data, indexes, ids) {
        if (disposed || !handlers || (ids && ids.indexOf(callbackId) < 0)) { return; }
        read();
    }
    function read() {
        var model = window.model;
        if (!model) { return; }
        // Event driven: only parse and render the payload that actually changed.
        if (model.schema !== lastSchema) {
            lastSchema = model.schema;
            var schema = parse(lastSchema);
            if (schema && schema.mods) { handlers.schema(schema); }
        }
        if (model.state !== lastState) {
            lastState = model.state;
            var state = parse(lastState);
            if (state && state.values) { handlers.state(state); }
        }
    }
    function resized() { if (!disposed && handlers && handlers.layout) { handlers.layout(); } }
    DK.bridge = {
        start: function (callbacks) {
            handlers = callbacks;
            engine.whenReady.then(function () {
                if (disposed) { return; }
                callbackId = viewEnv.addDataChangedCallback('model', 0, true);
                engine.on('clientResized', resized);
                engine.on('self.onScaleUpdated', resized);
                engine.on('viewEnv.onDataChanged', changed);
                read();
            });
        },
        send: function (action, data) {
            if (disposed || !window.model) { return; }
            var message = data || {};
            message.action = action;
            window.model.onAction({data: JSON.stringify(message)});
        },
        /* Pixels per UI unit (interface scale); 1 when the client does not expose it. */
        scale: function () {
            var unit = typeof viewEnv.remToPx === 'function' ? Number(viewEnv.remToPx(1)) : 1;
            return isFinite(unit) && unit > 0 ? unit : 1;
        },
        clientSizeRem: function () {
            if (typeof viewEnv.getClientSizeRem === 'function') {
                var size = viewEnv.getClientSizeRem();
                if (size && size.width > 0 && size.height > 0) { return size; }
            }
            var unit = DK.bridge.scale();
            return {width: (window.innerWidth || 1920) / unit, height: (window.innerHeight || 1080) / unit};
        },
        dispose: function () {
            if (disposed) { return; }
            disposed = true;
            engine.off('clientResized', resized);
            engine.off('self.onScaleUpdated', resized);
            engine.off('viewEnv.onDataChanged', changed);
            if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, 0); }
            handlers = null;
        }
    };
}());
