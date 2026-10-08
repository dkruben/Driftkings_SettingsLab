# -*- coding: utf-8 -*-
"""Declarative controls with shared construction and explicit numeric limits."""
import copy

from Driftkings._constants import GLOBAL
from Driftkings.settings.service import settings_service


class ControlSpec(object):
    def __init__(self, method, *args, **kwargs):
        self.method, self.args, self.kwargs = method, args, kwargs
        self.metadata = {}

    def build(self, builder):
        result = getattr(builder, self.method)(*copy.deepcopy(self.args), **copy.deepcopy(self.kwargs))
        result.update(copy.deepcopy(self.metadata))
        return result


def metadata(spec, **values):
    spec.metadata.update(values)
    return spec


class ColorSpec(ControlSpec):
    def __init__(self, key, label):
        super(ColorSpec, self).__init__('createControl', key, 'ColorChoice')
        self.key, self.label = key, label

    def build(self, builder):
        result = super(ColorSpec, self).build(builder)
        result['text'] = builder.getLabel(self.label)
        result['tooltip'] %= {self.key: builder.getValue(self.key, None)}
        return result


def color(key, label):
    return ColorSpec(key, label)


def label(*args, **kwargs):
    return ControlSpec('createLabel', *args, **kwargs)


def caption(text):
    """Literal heading for dynamically named profiles and fields."""
    return {'type': 'Label', 'text': text}


def images(*args, **kwargs):
    return ControlSpec('createImageOptions', *args, **kwargs)


def control(*args, **kwargs):
    return ControlSpec('createControl', *args, **kwargs)


def slider(*args, **kwargs):
    return ControlSpec('createSlider', *args, **kwargs)


def options(*args, **kwargs):
    return ControlSpec('createOptions', *args, **kwargs)


def hotkey(*args, **kwargs):
    return ControlSpec('createHotKey', *args, **kwargs)


def field(path, title, kind='CheckBox', low=None, high=None, choices=None,
          step=1, choice_labels=None, **metadata):
    """Define a nested setting without duplicating path/option conversions."""
    path = list(path)
    if not path:
        raise ValueError('Empty control path')
    item = {'varName': '.'.join(str(part) for part in path), 'path': path,
            'text': title, 'type': kind}
    if low is not None:
        if high is None or low > high or step <= 0:
            raise ValueError('Invalid slider limits: ' + item['varName'])
        item.update(minimum=low, maximum=high, snapInterval=step, canManualInput=True)
    if choices is not None:
        values = list(choices)
        labels = list(choice_labels) if choice_labels is not None else values
        if not values or len(values) != len(labels):
            raise ValueError('Invalid options: ' + item['varName'])
        item.update(options=[{'label': label} for label in labels], optionValues=values)
    item.update(metadata)
    return item


def build_template(config):
    result = {
        'modDisplayName': config.i18n['UI_description'] if config.TRANSLATED_TITLE else config.ID,
        'enabled': settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True)}
    columns = config.getControlColumns()
    if len(columns) != 2:
        raise ValueError('Expected two settings columns: ' + config.ID)
    for index, definitions in enumerate(columns):
        result['column%d' % (index + 1)] = [definition.build(config.tb) if isinstance(definition, ControlSpec) else copy.deepcopy(definition) for definition in definitions]
    return result
