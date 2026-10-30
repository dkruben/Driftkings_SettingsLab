/* DK Settings — contrato com o Python (gameface/lobby/settings_window.py):
   model.schema e model.state chegam como texto JSON; as ações saem por model.onAction({data}). */
(function () {
    'use strict';
    var DK = window.DK;
    var handlers = null, callbackId = null, lastSchema = null, lastState = null, currentState = null, disposed = false;

    function parse(text) { try { return JSON.parse(text || '{}'); } catch (error) { return null; } }
    function read() {
        var model = window.model;
        if (!model || !handlers) { return; }
        var schemaChanged = false, stateChanged = false;
        // Only changed JSON is parsed; a new schema reuses the latest valid state.
        if (model.schema !== lastSchema) {
            lastSchema = model.schema;
            var schema = parse(lastSchema);
            if (schema && schema.mods) { handlers.schema(schema); schemaChanged = true; }
        }
        if (model.state !== lastState) {
            lastState = model.state;
            var state = parse(lastState);
            if (state && state.values) { currentState = state; stateChanged = true; }
        }
        if ((schemaChanged || stateChanged) && currentState) { handlers.state(currentState); }
    }
    function changed(data, indexes, ids) {
        if (disposed || (ids && ids.indexOf && ids.indexOf(callbackId) < 0)) { return; }
        read();
    }
    function resized() { if (!disposed && handlers && handlers.resize) { handlers.resize(); } }

    DK.bridge = {
        start: function (callbacks) {
            handlers = callbacks;
            engine.whenReady.then(function () {
                if (disposed) { return; }
                callbackId = viewEnv.addDataChangedCallback('model', 0, true);
                engine.on('viewEnv.onDataChanged', changed);
                engine.on('clientResized', resized);
                engine.on('self.onScaleUpdated', resized);
                read();
            });
        },
        send: function (action, data) {
            if (disposed || !window.model) { return; }
            var message = data || {};
            message.action = action;
            window.model.onAction({data: JSON.stringify(message)});
        },
        /* Pixels per UI unit (the client's interface scale). */
        unit: function () {
            var value = typeof viewEnv.remToPx === 'function' ? Number(viewEnv.remToPx(1)) : 1;
            return isFinite(value) && value > 0 ? value : 1;
        },
        clientRem: function () {
            if (typeof viewEnv.getClientSizeRem === 'function') {
                var size = viewEnv.getClientSizeRem();
                if (size && size.width > 0 && size.height > 0) { return {width: size.width, height: size.height}; }
            }
            var unit = DK.bridge.unit();
            return {width: (window.innerWidth || 1920) / unit, height: (window.innerHeight || 1080) / unit};
        },
        dispose: function () {
            if (disposed) { return; }
            disposed = true;
            engine.off('viewEnv.onDataChanged', changed);
            engine.off('clientResized', resized);
            engine.off('self.onScaleUpdated', resized);
            if (callbackId !== null) { viewEnv.removeDataChangedCallback(callbackId, 0); }
            handlers = null; currentState = null;
        }
    };
}());
