'use strict';

// Test-only clock. Inspection never runs work; each turn snapshots its own queue.
module.exports = function createScheduler() {
    var clock = 0, nextId = 1, timers = new Map(), frames = new Map();
    function setTimeout(callback, delay) {
        var id = nextId++, wait = Number(delay) || 0;
        timers.set(id, {id: id, due: clock + Math.max(0, wait), callback: callback,
            args: Array.prototype.slice.call(arguments, 2)});
        return id;
    }
    function requestAnimationFrame(callback) {
        var id = nextId++;
        frames.set(id, callback);
        return id;
    }
    function pending() {
        return {timers: Array.from(timers.values()).map(function (entry) {
            return {id: entry.id, due: entry.due};
        }).sort(function (a, b) { return a.due - b.due || a.id - b.id; }), frames: Array.from(frames.keys())};
    }
    function runTimers() {
        var due = pending().timers.filter(function (entry) { return entry.due <= clock; });
        due.forEach(function (item) {
            var entry = timers.get(item.id);
            if (!entry) { return; }
            timers.delete(item.id);
            entry.callback.apply(undefined, entry.args);
        });
    }
    function frame() {
        clock += 16;
        Array.from(frames.keys()).forEach(function (id) {
            var callback = frames.get(id);
            if (!callback) { return; }
            frames.delete(id);
            callback(clock);
        });
    }
    function advance(milliseconds) {
        if (!Number.isFinite(milliseconds) || milliseconds < 0) { throw Error('Invalid clock advance'); }
        clock += milliseconds;
    }
    function flush(limit) {
        limit = limit === undefined ? 1000 : limit;
        for (var turn = 0; timers.size || frames.size; turn++) {
            if (turn >= limit) { throw Error('Scheduler did not become idle'); }
            if (timers.size && !frames.size) { clock = Math.max(clock, pending().timers[0].due); }
            runTimers();
            if (frames.size) { frame(); }
        }
    }
    return {setTimeout: setTimeout, clearTimeout: function (id) { timers.delete(id); },
        requestAnimationFrame: requestAnimationFrame, cancelAnimationFrame: function (id) { frames.delete(id); },
        now: function () { return clock; }, pending: pending, runTimers: runTimers, frame: frame,
        advance: advance, flush: flush};
};
