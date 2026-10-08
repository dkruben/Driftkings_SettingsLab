# -*- coding: utf-8 -*-
"""Owned battle scene. State survives a late Flash load or view recreation."""
import logging
from copy import deepcopy

LOG = logging.getLogger('Driftkings.Overlay')


class ElementType(object):
    PANEL = 'panel'
    LABEL = 'label'
    IMAGE = 'image'


class Align(object):
    LEFT, CENTER, RIGHT = 'left', 'center', 'right'
    TOP, BOTTOM = 'top', 'bottom'


class ChangeEvent(object):
    def __init__(self):
        self.listeners = []

    def __iadd__(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)
        return self

    def __isub__(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)
        return self

    def emit(self, *args):
        for callback in tuple(self.listeners):
            try:
                callback(*args)
            except Exception:
                LOG.exception('Overlay position callback failed')


class OverlayScene(object):
    def __init__(self):
        self.elements = {}
        self.view = None
        self.updated = ChangeEvent()

    def attach(self, view):
        self.view = view
        view.reset([dict(alias=alias, kind=kind, props=deepcopy(props))
                    for alias, (kind, props) in sorted(self.elements.items(), key=lambda item: (item[0].count('.'), item[0]))])

    def detach(self, view):
        if self.view is view:
            self.view = None

    def create(self, alias, kind, props):
        if kind not in (ElementType.PANEL, ElementType.LABEL, ElementType.IMAGE):
            raise ValueError('Unsupported overlay type: ' + str(kind))
        rebuild = alias in self.elements or any(key.startswith(alias + '.') for key in self.elements)
        self.elements[alias] = (kind, deepcopy(props))
        if self.view is not None:
            if rebuild:
                self.attach(self.view)
            else:
                self.view.createElement(alias, kind, deepcopy(props))

    def update(self, alias, props, animation=None):
        if alias not in self.elements:
            return False
        self.elements[alias][1].update(deepcopy(props))
        if self.view is not None:
            self.view.update(alias, deepcopy(props), float((animation or {}).get('duration', 0)))
        return True

    def animate(self, alias, duration, props, replace=True):
        return self.update(alias, props, {'duration': max(0, duration)})

    def remove(self, alias):
        for key in list(self.elements):
            if key == alias or key.startswith(alias + '.'):
                del self.elements[key]
        if self.view is not None:
            self.view.remove(alias)

    def moved(self, view, alias, x, y):
        # Ignore callbacks from disposed views and locked/nonexistent elements.
        if view is not self.view or alias not in self.elements:
            return
        props = self.elements[alias][1]
        if not props.get('drag'):
            return
        import math
        x, y = float(x), float(y)
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            return
        delta = {'x': x, 'y': y}
        props.update(delta)
        self.updated.emit(alias, delta)


overlays = OverlayScene()
