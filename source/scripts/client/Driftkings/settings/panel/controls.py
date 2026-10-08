# -*- coding: utf-8 -*-
"""Control definitions: declaration checks, value validation and UI descriptions."""
import math
import re

from Driftkings.core.keycodes import valid_key_code

try:
    string_types = (basestring,)  # noqa: F821 - Python 2 client
    text_type = unicode  # noqa: F821
except NameError:
    string_types = (str,)
    text_type = str

ID_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]{0,63}$')
COLOR_PATTERN = re.compile(r'^(?:#|0x)?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$')
TEXT_LIMIT = 4096

# Controls that hold a persisted value.
VALUE_TYPES = ('switch', 'checkbox', 'dropdown', 'slider', 'number', 'text', 'password', 'color', 'hotkey', 'multiselect', 'textarea', 'file', 'directory')
# Layout and action controls; they are never persisted.
STATIC_TYPES = ('section', 'label', 'separator', 'button')
SECRET_TYPES = ('password',)


class DefinitionError(ValueError):
    """Raised to the mod author when a declaration is invalid."""


def is_text(value):
    return isinstance(value, string_types)


def check_text(value, name, allow_dict=True):
    """Labels are a string or a {language: string} dictionary."""
    if is_text(value):
        return value
    if allow_dict and isinstance(value, dict) and value and all(is_text(k) and is_text(v) for k, v in value.items()):
        return dict(value)
    raise DefinitionError('%s must be text or a {language: text} dictionary' % name)


def resolve_text(value, language):
    if isinstance(value, dict):
        for key in (language, 'en'):
            if key in value:
                return value[key]
        return value[sorted(value)[0]]
    return value


def is_number(value):
    return type(value) in (int, float) or (type(value).__name__ == 'long')


def normalize_color(value):
    if not is_text(value):
        raise ValueError('Color must be text')
    match = COLOR_PATTERN.match(value.strip())
    if match is None:
        raise ValueError('Invalid color: use #RRGGBB')
    digits = match.group(1)
    if len(digits) == 3:
        digits = ''.join(ch * 2 for ch in digits)
    return '#' + str(digits.upper())


def _check_depends(depends_on):
    if depends_on is None:
        return {}
    if not isinstance(depends_on, dict):
        raise DefinitionError('depends_on must be a dictionary {setting_id: value or [values]}')
    result = {}
    for key, expected in depends_on.items():
        if not is_text(key) or not ID_PATTERN.match(key):
            raise DefinitionError('Invalid depends_on key: %r' % (key,))
        values = list(expected) if isinstance(expected, (list, tuple)) else [expected]
        for item in values:
            if not (item is None or type(item) is bool or is_number(item) or is_text(item)):
                raise DefinitionError('depends_on values must be JSON scalars')
        result[key] = values
    return result


class Control(object):
    """One declared setting or layout element of a registered mod."""
    __slots__ = ('id', 'type', 'label', 'description', 'default', 'order', 'depends_on', 'enabled',
                 'visible', 'keywords', 'options', 'minimum', 'maximum', 'step', 'unit', 'max_length',
                 'placeholder', 'callback', 'text', 'presets', 'column', 'tab', 'preview')

    def __init__(self, kind, control_id, label=None, default=None, description=None, order=None,
                 depends_on=None, enabled=True, visible=True, keywords=None, column=-1, tab=None):
        if kind not in VALUE_TYPES + STATIC_TYPES:
            raise DefinitionError('Unknown control type: %r' % (kind,))
        if not is_text(control_id) or not ID_PATTERN.match(control_id):
            raise DefinitionError('Invalid setting id %r: use letters, digits and _' % (control_id,))
        self.column = column
        self.tab = tab
        self.id = str(control_id)
        self.type = kind
        self.label = check_text(label, 'label') if label is not None else self.id
        self.description = check_text(description, 'description') if description is not None else None
        self.order = order
        self.depends_on = _check_depends(depends_on)
        self.enabled = bool(enabled)
        self.visible = bool(visible)
        if keywords is not None and (not isinstance(keywords, (list, tuple)) or not all(is_text(k) for k in keywords)):
            raise DefinitionError('keywords must be a list of strings')
        self.keywords = list(keywords or [])
        self.options = None
        self.minimum = self.maximum = self.step = None
        self.unit = None
        self.max_length = TEXT_LIMIT
        self.placeholder = None
        self.callback = None
        self.text = None
        self.presets = None
        self.default = default
        self.preview = None

    @property
    def has_value(self):
        return self.type in VALUE_TYPES

    @property
    def secret(self):
        return self.type in SECRET_TYPES

    def finalize(self):
        """Validate type-specific attributes and the default, once configured."""
        if self.type in ('slider', 'number'):
            if not is_number(self.minimum) or not is_number(self.maximum) or self.minimum >= self.maximum:
                raise DefinitionError('%s: min_value must be lower than max_value' % self.id)
            if not is_number(self.step) or self.step <= 0:
                raise DefinitionError('%s: step must be positive' % self.id)
        if self.type in ('dropdown', 'multiselect'):
            if not self.options:
                raise DefinitionError('%s: dropdown requires values' % self.id)
            seen = []
            for value, _ in self.options:
                if value in seen:
                    raise DefinitionError('%s: duplicate dropdown value %r' % (self.id, value))
                seen.append(value)
        if self.type == 'button' and self.callback is not None and not callable(self.callback):
            raise DefinitionError('%s: callback must be callable' % self.id)
        if self.has_value:
            try:
                self.default = self.validate(self.default)
            except ValueError as error:
                raise DefinitionError('%s: invalid default (%s)' % (self.id, error))
        return self

    @property
    def integral(self):
        return all(type(v) is not float for v in (self.minimum, self.maximum, self.step))

    def validate(self, value):
        """Return the normalized value or raise ValueError; never coerces silently."""
        kind = self.type
        if kind in ('switch', 'checkbox'):
            if type(value) is not bool:
                raise ValueError('Expected true or false')
            return value
        if kind == 'hotkey':
            if not isinstance(value, list) or len(value) > 4:
                raise ValueError('Invalid hotkey')
            if any(not isinstance(group, (list, tuple)) or not 1 <= len(group) <= 4 or
                   any(not valid_key_code(code) for code in group) for group in value):
                raise ValueError('Invalid key code')
            return [list(group) for group in value]
        if kind == 'multiselect':
            if not isinstance(value, list) or len(value) != len(set(value)):
                raise ValueError('Expected unique selections')
            if any(not any(type(v) is type(option) and v == option for option, label in self.options) for v in value):
                raise ValueError('Unknown selection')
            return list(value)
        if kind == 'dropdown':
            for option, _ in self.options:
                if option == value and type(option) is type(value):
                    return option
                # JSON strings arrive as unicode in Python 2.
                if is_text(option) and is_text(value) and option == value:
                    return option
            raise ValueError('Unknown option')
        if kind in ('slider', 'number'):
            if type(value) is bool or not is_number(value):
                raise ValueError('Expected a number')
            if math.isnan(value) or math.isinf(value):
                raise ValueError('Expected a finite number')
            if value < self.minimum or value > self.maximum:
                raise ValueError('Out of range')
            if self.integral:
                if value != int(value):
                    raise ValueError('Expected an integer')
                return int(value)
            return float(value)
        if kind in ('text', 'password', 'textarea', 'file', 'directory'):
            if not is_text(value):
                raise ValueError('Expected text')
            if len(value) > self.max_length:
                raise ValueError('Text too long')
            return value
        if kind == 'color':
            return normalize_color(value)
        raise ValueError('Control has no value')

    def describe(self, language):
        """JSON-safe description for the Gameface view; callbacks stay in Python."""
        data = {'id': self.id, 'type': self.type, 'label': resolve_text(self.label, language)}
        data.update(column=self.column, tab=resolve_text(self.tab, language) if self.tab else None, keywords=self.keywords)
        if self.description is not None:
            data['description'] = resolve_text(self.description, language)
        if self.has_value and not self.secret:
            data['default'] = self.default
        if self.type in ('dropdown', 'multiselect'):
            data['options'] = [{'value': value, 'label': resolve_text(label, language)} for value, label in self.options]
        if self.type in ('slider', 'number'):
            data.update({'min': self.minimum, 'max': self.maximum, 'step': self.step})
            if self.unit:
                data['unit'] = self.unit
        if self.type in ('text', 'password', 'textarea', 'file', 'directory'):
            data['maxLength'] = self.max_length
            if self.placeholder is not None:
                data['placeholder'] = resolve_text(self.placeholder, language)
        if self.type == 'button':
            data['text'] = resolve_text(self.text, language) if self.text is not None else data['label']
        if self.type == 'color' and self.presets:
            data['presets'] = [{'value': value, 'label': resolve_text(label, language)} for value, label in self.presets]
        if self.depends_on:
            data['dependsOn'] = self.depends_on
        if self.preview:
            data['preview'] = self.preview
        return data

    def search_text(self, language):
        parts = [resolve_text(self.label, language)]
        if self.description is not None:
            parts.append(resolve_text(self.description, language))
        parts.extend(self.keywords)
        return u' '.join(text_type(part) if not isinstance(part, bytes) else part.decode('utf-8', 'replace')
                         for part in parts).lower()


def options_list(values):
    """Accept [(value, label)], [value] or {value: label}; keep author order."""
    if isinstance(values, dict):
        values = sorted(values.items())
    if not isinstance(values, (list, tuple)):
        raise DefinitionError('values must be a list')
    result = []
    for item in values:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            value, label = item
        else:
            value, label = item, item if is_text(item) else str(item)
        if not (type(value) is bool or is_number(value) or is_text(value)):
            raise DefinitionError('Dropdown values must be text or numbers')
        result.append((value, check_text(label, 'option label')))
    return result


DEFAULT_COLOR_PRESETS = (
    ('#D98219', {'en': 'WoT Orange', 'pt': 'Laranja WoT'}),
    ('#F2C14E', {'en': 'Gold', 'pt': 'Dourado'}),
    ('#D9412B', {'en': 'Red', 'pt': 'Vermelho'}),
    ('#3D8FD9', {'en': 'Blue', 'pt': 'Azul'}),
    ('#5DB346', {'en': 'Green', 'pt': 'Verde'}),
    ('#9B5DE5', {'en': 'Purple', 'pt': 'Roxo'}),
    ('#FFFFFF', {'en': 'White', 'pt': 'Branco'}),
)
