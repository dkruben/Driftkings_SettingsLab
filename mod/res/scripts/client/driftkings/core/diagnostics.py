# -*- coding: utf-8 -*-
"""Opt-in bounded aggregates. No payloads, timers, subscriptions or engine imports."""
import math
from timeit import default_timer

from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Performance')


class Diagnostics(object):
    def __init__(self, clock=None, limit=256, reporter=None):
        self.clock = default_timer if clock is None else clock
        self.limit = max(1, limit)
        self.enabled = False
        self.records = {}
        self.generation = 0
        self.reporter = LOG.info if reporter is None else reporter

    def configure(self, enabled):
        enabled = bool(enabled)
        if enabled == self.enabled:
            return
        self.generation += 1
        if enabled:
            self.records.clear()
        else:
            self.report()
        self.enabled = enabled

    def _record(self, label):
        if label not in self.records and len(self.records) >= self.limit - 1:
            label = '__other__'
        if label not in self.records:
            self.records[label] = dict(calls=0, errors=0, totalMs=0.0, maxMs=0.0, count=0)
        return self.records[label]

    def count(self, label, amount=1):
        if self.enabled:
            self._record(label)['count'] += amount

    def call(self, label, function, *args, **kwargs):
        if not self.enabled:
            return function(*args, **kwargs)
        generation = self.generation
        started = self._time()
        failed = True
        try:
            result = function(*args, **kwargs)
            failed = False
            return result
        finally:
            if self.enabled and generation == self.generation:
                finished = self._time()
                elapsed = 0.0 if started is None or finished is None else max(0.0, (finished - started) * 1000.0)
                record = self._record(label)
                record['calls'] += 1
                record['errors'] += int(failed)
                record['totalMs'] += elapsed
                record['maxMs'] = max(record['maxMs'], elapsed)

    def _time(self):
        try:
            value = float(self.clock())
            return None if math.isnan(value) or math.isinf(value) else value
        except Exception:
            return None

    def snapshot(self):
        return dict(enabled=self.enabled, timing='inclusive wall time; hooks include original calls',
                    records=dict((name, dict(value)) for name, value in list(self.records.items())))

    def report(self):
        if not self.records:
            return
        for name, value in sorted(list(self.records.items()), key=lambda item: (-item[1]['totalMs'], item[0]))[:20]:
            message = '%s calls=%d errors=%d total=%.3fms max=%.3fms count=%d' % (
                name, value['calls'], value['errors'], value['totalMs'], value['maxMs'], value['count'])
            try:
                self.reporter(message)
            except Exception:
                # Observability must never prevent settings apply or cleanup.
                pass


diagnostics = Diagnostics()
