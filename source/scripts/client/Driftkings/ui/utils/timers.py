# -*- coding: utf-8 -*-


from Driftkings.common import cancelCallback, callback

__all__ = ('Timer', 'CyclicTimerEvent',)


class Timer(object):
    __slots__ = ('_callback',)

    def __init__(self):
        self._callback = None

    def cancelCallback(self):
        if self._callback is not None:
            cancelCallback(self._callback)
            self._callback = None

    def stop(self):
        self.cancelCallback()

    def start(self, *_):
        self.cancelCallback()


class CyclicTimerEvent(Timer):
    __slots__ = ('_interval', '_callback', '_function')

    def __init__(self, updateInterval, function):
        super(CyclicTimerEvent, self).__init__()
        self._interval = float(updateInterval)
        self._function = function

    def update(self):
        self._callback = callback(self._interval, self.update)
        self._function()

    def start(self):
        super(CyclicTimerEvent, self).start()
        self.update()