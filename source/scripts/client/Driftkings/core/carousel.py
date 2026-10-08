# -*- coding: utf-8 -*-
"""Gameface carousel configuration and field rendering, independent of the client."""
import math
import re

from Driftkings.settings.settings_data import defaults as component_defaults

try:
    text_type = unicode
    string_types = (basestring,)
except NameError:
    text_type = str
    string_types = (str,)

FIELD_NAMES = ('flag', 'tankIcon', 'tankType', 'level', 'xp', 'tankName', 'info', 'favorite', 'progressionPoints')
ALIASES = {'tdb': 'avgDamage', 'winrate': 'winRate', 't_battles': 'battles', 'damageRating': 'marks', 'name': 'vehicle', 'tier': 'level', 'tfb': 'avgFrags', 'hitsRatio': 'hitRate', 'markOfMastery': 'mastery'}
MACRO = re.compile(r'\{\{([^{}]+)\}\}')
EXPR = re.compile(r'^(?P<key>(?:v\.)?(?:c:|c_|icon:)?[A-Za-z][\w-]*)(?P<fmt>%[-0-9.]*[dfs]|:\.[0-3]f|:d)?(?:~(?P<suffix>[^|]*))?(?:\|(?P<fallback>.*))?$')


def bounded(value, low, high, default):
    try:
        value = float(value)
        return max(low, min(high, value)) if not (math.isnan(value) or math.isinf(value)) else default
    except (ValueError, TypeError, OverflowError):
        return default


def defaults():
    return component_defaults('CarouselStats')['carousel']


def config_defaults():
    return component_defaults('CarouselStats')


def row_count(carousel, native):
    rows = carousel.get('rows', 0)
    if rows in (1, 2, 3, 4):
        return rows
    return {'normal': 1, 'small': 2}.get(carousel.get('cellType'), native)


def render(template, values, color, icon):
    if not isinstance(template, string_types):
        return ''
    if isinstance(template, bytes) and text_type is not str:
        template = template.decode('utf-8')
    def replace(match):
        body = match.group(1)
        if '?' in body:
            test, branches = body.split('?', 1)
            condition = re.match(r'^((?:v\.)?[A-Za-z][\w-]*)(?:(==|!=)([\w-]+))?$', test)
            if condition is None:
                return '--'
            yes, separator, no = branches.partition('|')
            key, operator, operand = condition.groups()
            key = key[2:] if key.startswith('v.') else key
            key = ALIASES.get(key, key)
            value = values.get(key)
            if operator:
                value = (text_type(value) == operand) if operator == '==' else (text_type(value) != operand)
            return (yes if yes else text_type(value)) if value else no if separator else ''
        expression = EXPR.match(body)
        if expression is None:
            return '--'
        key, fmt, suffix, fallback = [expression.group(x) for x in ('key','fmt','suffix','fallback')]
        if key.startswith('v.'): key = key[2:]
        if key in ('c_type', 'c:type'):
            return values.get('classColor', fallback or '#FFFFFF')
        if key.startswith(('c:', 'c_')):
            key = ALIASES.get(key[2:], key[2:])
            return text_type(color(key, values.get(key))) if values.get(key) is not None else (fallback or '#FFFFFF')
        if key.startswith('icon:'): return text_type(icon(key[5:]))
        key = ALIASES.get(key, key)
        value = values.get(key)
        if isinstance(value, bytes) and text_type is not str:
            value = value.decode('utf-8', 'replace')
        if value is None:
            return fallback if fallback is not None else '--'
        try:
            if fmt:
                if len(fmt) > 12 or any(int(n) > 100 for n in re.findall(r'\d+', fmt)): return '--'
                if fmt.startswith(':'): result = format(value, fmt[1:])
                else: result = fmt % value
            elif isinstance(value, string_types): result = value
            elif key in ('winRate','hitRate','damageRatio','damageHP','avgFrags','marks'): result = '%.2f' % value
            else: result = str(int(value))
            return text_type(result) + (suffix or '')
        except (TypeError, ValueError, OverflowError):
            return fallback if fallback is not None else '--'
    result = template[:2048]
    for unused in range(8):
        updated = MACRO.sub(replace, result)
        if updated == result:
            break
        result = updated
    return result


def profile_shadow(profile, shadow):
    """Local reusable shadow, with per-field overrides (no cross-file loading)."""
    reference = shadow if isinstance(shadow, string_types) else shadow.get('$ref') if isinstance(shadow, dict) else None
    result = {}
    if reference is not None:
        if reference not in ('$ref:textFieldShadow', 'textFieldShadow',
                             'carouselNormal.textFieldShadow', 'carouselSmall.textFieldShadow'):
            raise ValueError('Unknown carousel shadow reference: %s' % reference)
        result.update(profile.get('textFieldShadow', {}))
    if isinstance(shadow, dict):
        result.update((key, value) for key, value in shadow.items() if key != '$ref')
    return result


def build_profile(profile, renderer, show_icons):
    result = {'width': bounded(profile.get('width'),80,600,160),
              'height': bounded(profile.get('height'),35,400,100), 'fields': {}, 'extraFields': []}
    for name in FIELD_NAMES:
        item = profile.get('fields', {}).get(name, {})
        result['fields'][name] = {'enabled': item.get('enabled',True) is not False,
            'dx': bounded(item.get('dx'),-400,400,0), 'dy': bounded(item.get('dy'),-400,400,0),
            'alpha': bounded(item.get('alpha'),0,100,100), 'scale': bounded(item.get('scale'),0.1,4,1)}
    for item in profile.get('extraFields', [])[:64]:
        if not isinstance(item, dict) or item.get('enabled',True) is False: continue
        field = {}
        for key in ('format','color','bgColor','src'):
            field[key] = renderer(item.get(key, ''))
        if not show_icons: field['src'] = ''
        field['showIcons'] = bool(show_icons)
        for key,low,high,default in (('x',-600,600,0),('y',-400,400,0),('width',0,600,0),('height',0,400,0),('alpha',0,100,100),('fontSize',8,40,12),('iconSize',8,80,14)):
            value=item.get(key,default)
            if isinstance(value,string_types): value=renderer(value)
            field[key]=bounded(value,low,high,default)
        field['align']=item.get('align') if item.get('align') in ('left','center','right') else 'left'
        field['layer']='substrate' if item.get('layer') == 'substrate' else 'top'
        shadow=profile_shadow(profile, item.get('shadow',{}))
        shadow = dict((key, renderer(value) if isinstance(value, string_types) else value) for key, value in shadow.items())
        field['shadow']={'enabled': shadow.get('enabled',True) is not False, 'color':renderer(shadow.get('color','#000000')),
                         'alpha':bounded(shadow.get('alpha'),0,100,80),'blur':bounded(shadow.get('blur'),0,20,2),
                         'distance':bounded(shadow.get('distance'),0,20,1),
                         'angle':bounded(shadow.get('angle'),-360,360,45),
                         'strength':bounded(shadow.get('strength'),0,5,1)}
        result['extraFields'].append(field)
    return result
