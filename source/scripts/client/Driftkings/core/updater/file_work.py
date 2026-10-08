# -*- coding: utf-8 -*-
"""Bounded file jobs owned by UpdaterService; delivery uses Core callbacks."""
import logging
import threading

LOG = logging.getLogger('Driftkings.Updater')


class FileWork(object):
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.closed = False
        self.jobs = []

    def submit(self, task, completed, cleanup=None):
        if self.closed or len(self.jobs) >= 4:
            raise RuntimeError('Updater file work unavailable')
        job = dict(done=threading.Event(), cancelled=threading.Event(), lock=threading.Lock(),
                   value=None, error=None, cleaned=False, token=None)
        self.jobs.append(job)
        def discard():
            with job['lock']:
                if not job['cancelled'].is_set() or not job['done'].is_set() or job['cleaned']:
                    return
                job['cleaned'] = True
                value = job['value']
            if cleanup is not None and value is not None:
                try:
                    cleanup(value)
                except Exception:
                    LOG.exception('Could not discard cancelled file preparation')
        job['discard'] = discard
        def worker():
            try:
                if not job['cancelled'].is_set():
                    job['value'] = task()
            except Exception as error:
                job['error'] = error
                LOG.exception('Updater background file job failed')
            finally:
                job['done'].set()
                discard()
        def pump():
            job['token'] = None
            if self.closed or job['cancelled'].is_set():
                return
            if not job['done'].is_set():
                job['token'] = self.callbacks.schedule(0.05, pump)
                return
            if job in self.jobs:
                self.jobs.remove(job)
            completed(job['value'], job['error'])
        thread = threading.Thread(target=worker, name='Driftkings.Updater.Files')
        thread.daemon = True
        try:
            job['token'] = self.callbacks.schedule(0.05, pump)
            thread.start()
        except Exception:
            job['cancelled'].set()
            if job['token'] is not None:
                self.callbacks.cancel(job['token'])
            self.jobs.remove(job)
            raise
        return job

    def close(self):
        self.closed = True
        for job in self.jobs:
            job['cancelled'].set()
            if job['token'] is not None:
                self.callbacks.cancel(job['token'])
            job['discard']()
        self.jobs = []
