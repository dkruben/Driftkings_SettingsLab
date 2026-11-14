'use strict';
var assert = require('assert');
var createScheduler = require('../../support/frontend/deterministic_scheduler');
var scheduler = createScheduler(), seen = [];
var first = scheduler.setTimeout(function () { seen.push('first'); }, 10);
var cancelled = scheduler.setTimeout(function () { throw Error('Cancelled timer ran'); }, 0);
var frame = scheduler.requestAnimationFrame(function (time) { seen.push('frame:' + time); });
var cancelledFrame = scheduler.requestAnimationFrame(function () { throw Error('Cancelled frame ran'); });
assert.strictEqual(new Set([first, cancelled, frame, cancelledFrame]).size, 4);
scheduler.clearTimeout(cancelled); scheduler.cancelAnimationFrame(cancelledFrame);
assert.deepStrictEqual(scheduler.pending(), {timers: [{id: first, due: 10}], frames: [frame]});
assert.deepStrictEqual(seen, [], 'inspection is inert');
scheduler.runTimers(); assert.deepStrictEqual(seen, []);
scheduler.advance(10); assert.deepStrictEqual(seen, [], 'clock advancement is inert');
scheduler.runTimers(); assert.deepStrictEqual(seen, ['first']);
scheduler.frame(); assert.deepStrictEqual(seen, ['first', 'frame:26']);

// Queue snapshots: nested work waits for its own next turn, including new frames.
scheduler = createScheduler(); seen = [];
scheduler.setTimeout(function () {
    seen.push('a'); scheduler.setTimeout(function () { seen.push('nested'); }, 0);
}, 0);
scheduler.setTimeout(function () { seen.push('b'); }, 0);
scheduler.runTimers(); assert.deepStrictEqual(seen, ['a', 'b']);
assert.strictEqual(scheduler.pending().timers.length, 1);
scheduler.runTimers(); assert.deepStrictEqual(seen, ['a', 'b', 'nested']);
scheduler.requestAnimationFrame(function () {
    seen.push('frame1'); scheduler.requestAnimationFrame(function () { seen.push('frame2'); });
});
scheduler.frame(); assert.strictEqual(seen[3], 'frame1'); assert.strictEqual(scheduler.pending().frames.length, 1);
scheduler.frame(); assert.strictEqual(seen[4], 'frame2');

// A callback can cancel another callback in the current snapshot without clearing its peers.
scheduler = createScheduler(); seen = [];
var timerVictim, frameVictim;
scheduler.setTimeout(function () { scheduler.clearTimeout(timerVictim); seen.push('timer'); }, 0);
timerVictim = scheduler.setTimeout(function () { throw Error('Cancelled peer timer ran'); }, 0);
scheduler.setTimeout(function () { seen.push('peer'); }, 0);
scheduler.requestAnimationFrame(function () { scheduler.cancelAnimationFrame(frameVictim); seen.push('frame'); });
frameVictim = scheduler.requestAnimationFrame(function () { throw Error('Cancelled peer frame ran'); });
scheduler.flush(); assert.deepStrictEqual(seen, ['timer', 'peer', 'frame']);
assert.deepStrictEqual(scheduler.pending(), {timers: [], frames: []});

// Deadlines beat insertion order; equal deadlines retain ID order and timer arguments.
scheduler = createScheduler(); seen = [];
scheduler.setTimeout(function () { seen.push('late'); }, 20);
scheduler.setTimeout(function (value) { seen.push(value); }, 5, 'early1');
scheduler.setTimeout(function () { seen.push('early2'); }, 5);
scheduler.advance(5); scheduler.runTimers();
assert.deepStrictEqual(seen, ['early1', 'early2']);
scheduler.advance(15); scheduler.runTimers();
assert.deepStrictEqual(seen, ['early1', 'early2', 'late']);

// Cross-queue scheduling is explicit: firing a frame does not implicitly run a timer.
scheduler = createScheduler(); seen = [];
scheduler.setTimeout(function () {
    seen.push('timer');
    scheduler.requestAnimationFrame(function () {
        seen.push('frame'); scheduler.setTimeout(function () { seen.push('next timer'); }, 0);
    });
}, 0);
scheduler.runTimers(); assert.deepStrictEqual(seen, ['timer']);
scheduler.frame(); assert.deepStrictEqual(seen, ['timer', 'frame']);
assert.strictEqual(scheduler.pending().timers.length, 1);
scheduler.runTimers(); assert.deepStrictEqual(seen, ['timer', 'frame', 'next timer']);

// An exception is observable and does not discard unrelated queued callbacks.
scheduler = createScheduler(); seen = [];
scheduler.setTimeout(function () { throw Error('injected timer error'); }, 0);
scheduler.setTimeout(function () { seen.push('survivor'); }, 0);
assert.throws(scheduler.runTimers, /injected timer error/);
assert.strictEqual(scheduler.pending().timers.length, 1);
scheduler.runTimers(); assert.deepStrictEqual(seen, ['survivor']);

// Unknown/wrong-queue IDs are harmless, and a runaway fixture is bounded.
scheduler = createScheduler();
var retained = scheduler.requestAnimationFrame(function () {});
scheduler.clearTimeout(retained); assert.deepStrictEqual(scheduler.pending().frames, [retained]);
scheduler.cancelAnimationFrame(retained);
function repeat() { scheduler.setTimeout(repeat, 0); }
repeat(); assert.throws(function () { scheduler.flush(3); }, /did not become idle/);
console.log('Deterministic scheduler: cancellation, independent queues, nesting, order and inspection passed');
