# -*- coding: utf-8 -*-
import threading
import time

from support import RuntimeTest


class Stream(object):
    def close(self):
        pass


class FakeProcess(object):
    def __init__(self, exits_after=None):
        self.stdin, self.stdout, self.stderr = Stream(), Stream(), Stream()
        self.killed = False
        self.exit_time = None if exits_after is None else time.time() + exits_after

    def poll(self):
        if self.killed or (self.exit_time is not None and time.time() >= self.exit_time):
            return 0
        return None

    def kill(self):
        self.killed = True

    def wait(self):
        return self.poll()


class CloseTests(RuntimeTest):
    def validator(self, process):
        api = self.load('core.updater.windows_files')
        client = api.WindowsPathValidator('helper.exe', '.', 'x' * 64)
        client.process = process
        return client

    def test_close_waits_for_a_helper_that_exits_and_starts_no_thread(self):
        before = threading.active_count()
        process = FakeProcess(exits_after=0.1)
        client = self.validator(process)
        client.close()
        self.assertFalse(process.killed)
        self.assertTrue(client.failed)
        self.assertEqual(threading.active_count(), before)

    def test_close_kills_a_stuck_helper_after_the_grace_period(self):
        process = FakeProcess()
        client = self.validator(process)
        started = time.time()
        client.close()
        self.assertTrue(process.killed)
        self.assertGreaterEqual(time.time() - started, 2.9)


if __name__ == '__main__':
    import unittest
    unittest.main()
