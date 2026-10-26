# -*- coding: utf-8 -*-
"""Bounded marker condition grammar, shared by validation and portable checks."""
import math
import re

COMPARISON = re.compile(r'^(.*?)\s*(<=|>=|==|!=|<|>)\s*(.*?)$')
NUMBER = re.compile(r'^-?\d+(?:\.\d+)?$')


def token(text, names, values=None):
    text = text.strip()
    if text in names:
        return None if values is None else values.get(text)
    if text in ('true', 'false'):
        return text == 'true'
    if NUMBER.match(text):
        result = float(text)
        if math.isinf(result) or math.isnan(result):
            raise ValueError('Invalid marker condition number')
        return result
    if len(text) >= 2 and text[0] in ('"', "'") and text[-1] == text[0] and text[0] not in text[1:-1]:
        return text[1:-1]
    raise ValueError('Unknown marker condition token: ' + text)


def truth(value):
    return value not in (None, False, 0, '', '--', 'false', '0')


def atom(text, names, values=None):
    text = text.strip()
    negate = False
    while text.startswith('!') and not text.startswith('!='):
        negate = not negate
        text = text[1:].strip()
    match = COMPARISON.match(text)
    if match:
        left, operator, right = match.groups()
        left, right = token(left, names, values), token(right, names, values)
        if left is None or right is None:
            result = False
        elif operator in ('==', '!='):
            equal = left == right
            if isinstance(left, bool) != isinstance(right, bool):
                equal = False
            result = equal if operator == '==' else not equal
        else:
            try:
                left, right = float(left), float(right)
                result = {'<': left < right, '>': left > right, '<=': left <= right, '>=': left >= right}[operator]
            except (TypeError, ValueError, OverflowError):
                result = False
    else:
        result = truth(token(text, names, values))
    return not result if negate else result


def condition(expression, names, values=None):
    # Evaluate every atom even during validation; do not short-circuit unknown names.
    groups = [[atom(part, names, values) for part in group.split('&&')] for group in expression.split('||')]
    return any(all(group) for group in groups)


def validate(text, names):
    for depth in range(12):
        matches = list(re.finditer(r'\{\{([^{}]*)\}\}', text))
        if not matches:
            if '{{' in text or '}}' in text:
                raise ValueError('Unbalanced marker macro')
            return
        for match in matches:
            expression = match.group(1)
            if '?' in expression:
                condition(expression.partition('?')[0], names)
            else:
                body = expression.partition('|')[0]
                key, separator, spec = body.partition('%')
                if key not in names:
                    raise ValueError('Unsupported field macro: ' + key)
                if separator and not re.match(r'^(?:d|s|0?\.[0-3]f)$', spec):
                    raise ValueError('Unsupported marker numeric format')
        text = re.sub(r'\{\{([^{}]*)\}\}', '0', text)
    if '{{' in text:
        raise ValueError('Marker macro nesting exceeds 12 levels')
