# -*- coding: utf-8 -*-
"""Declarative control metadata, independent of storage and panel construction."""
import copy
import re


def metadata(spec, **values):
    spec.update(values)
    return spec


def label(key, ctx='setting'):
    return {'type': 'Label', 'labelKey': key, 'labelContext': ctx}


def caption(text):
    return {'type': 'Label', 'text': text}


def control(key, kind='CheckBox', width=200, empty=False, button=None, value=None):
    item = {'type': kind, 'varName': key, 'width': width}
    if not empty:
        item['labelKey'] = key
    if button is not None:
        item['button'] = button
    return item


def options(key, choices, kind='Dropdown', width=200, empty=False, button=None, value=None):
    item = control(key, kind, width, empty, button, value)
    item['options'] = [{'label': choice} for choice in choices]
    return item


def images(key, icons, kind='Dropdown', width=200, empty=False, button=None, value=None):
    item = control(key, kind, width, empty, button, value)
    item.update(options=[{'label': name[:-4], 'image': 'gui/maps/icons/sixthsense/' + name} for name in icons], previewImage=True)
    return item


def hotkey(key, empty=False, value=None):
    return control(key, 'HotKey', empty=empty)


def slider(key, low, high, step, format_str='{{value}}', width=200, empty=False, button=None, value=None):
    if low > high or step <= 0:
        raise ValueError('Invalid slider limits: ' + key)
    item = control(key, 'Slider', width, empty, button, value)
    item.update(minimum=low, maximum=high, snapInterval=step, format=format_str)
    return item


def color(key, label_key):
    item = control(key, 'ColorChoice')
    item['colorLabelKey'] = label_key
    return item


def resolve(item, labels, values):
    """Resolve translations at panel-open time; declarations contain no live values."""
    item = copy.deepcopy(item)
    key = item.pop('labelKey', None)
    context = item.pop('labelContext', 'setting')
    if key is not None:
        prefix = 'UI_' + context + '_' + key
        item['text'] = labels[prefix + '_text']
        body = labels.get(prefix + '_tooltip', '')
        item['tooltip'] = '{HEADER}%s{/HEADER}{BODY}%s{/BODY}' % (item['text'], body) if body else ''
    color_key = item.pop('colorLabelKey', None)
    if color_key is not None:
        item['text'] = labels['UI_setting_' + color_key + '_text']
        # Both the caption and tooltip may contain the legacy colour placeholder.
        # Stored colours already include '#'; avoid producing '##RRGGBB'.
        for name in ('text', 'tooltip'):
            text = item.get(name, '')
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            if '%(' in text:
                try:
                    value = values[item['varName']]
                    if value is not None and str(value).startswith('#'):
                        text = text.replace('#%(' + item['varName'] + ')s', '%(' + item['varName'] + ')s')
                    text = text % {item['varName']: value}
                except (KeyError, TypeError, ValueError):
                    pass
            item[name] = text
    # Resolve colour captions as well as explicitly declared colourLabelKey controls.
    for name in ('text', 'tooltip'):
        text = item.get(name, '')
        if '%(' in text:
            for key, value in values.items():
                if isinstance(value, (str, type(u''))) and value.startswith('#'):
                    text = text.replace('#%(' + key + ')s', '%(' + key + ')s')
            try:
                item[name] = text % values
            except (KeyError, TypeError, ValueError):
                pass
    return item


def description_keys(path):
    """Catalog keys for a nested field, most specific first.

    Repeated fields (carousel slots, panel sides, extra fields) share one text per
    property: ``UI_tooltip_<parent>_<name>``, then ``UI_tooltip_<name>``. Left/Right
    variants fall back to their common name.
    """
    names = [str(part) for part in path if not isinstance(part, int)]
    if not names:
        return []
    last = names[-1]
    variants = [last]
    common = re.sub(r'(Left|Right)$', '', last)
    if common and common != last:
        variants.append(common)
    keys = []
    for name in variants:
        keys.extend('UI_tooltip_%s_%s' % (parent, name) for parent in reversed(names[-3:-1]))
        keys.append('UI_tooltip_' + name)
    return keys


def nested_description(path, labels):
    for key in description_keys(path):
        value = labels.get(key)
        if value:
            return value
    return ''


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
