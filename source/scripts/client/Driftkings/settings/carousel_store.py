# -*- coding: utf-8 -*-
"""Independent JSON documents for general, normal and compact carousel options."""
import copy
import os

from Driftkings.core.carousel import config_defaults, profile_shadow
from Driftkings.core.carousel_options import from_carousel, SORT_KEYS
from Driftkings.settings.store import merge, recover_file, read_object, JsonDocuments

FILES = ('carousel.json', 'carouselNormal.json', 'carouselSmall.json')


def documents(data):
    carousel = data['carousel']
    general = from_carousel(carousel)
    general.update(enabled=data['enabled'], colorRating=data['colorRating'], showIcons=data['showIcons'], cellType=carousel['cellType'], rows=carousel['rows'])
    return general, carousel['normal'], carousel['small']


def validate(parts):
    if any(not isinstance(part, dict) for part in parts):
        raise ValueError('Carousel JSON must contain objects')
    general = parts[0]
    if general.get('cellType') not in ('default', 'normal', 'small') or type(general.get('rows')) is not int or general['rows'] not in (0, 1, 2, 3, 4):
        raise ValueError('Invalid carousel layout or row count')
    if any(type(general.get(key)) is not bool for key in ('enabled', 'showIcons')):
        raise ValueError('Carousel toggles must be boolean')
    if type(general.get('colorRating')) is not int or general['colorRating'] < 0:
        raise ValueError('Invalid carousel color table')
    for key in ('hideBuyTank', 'hideBuySlot', 'hideRestoreTank', 'showTotalSlots', 'showUsedSlots', 'enableLockBackground', 'suppressCarouselTooltips'):
        if type(general[key]) is not bool:
            raise ValueError('Invalid carousel switch: ' + key)
    for key in ('backgroundAlpha', 'slotBackgroundAlpha', 'slotBorderAlpha', 'slotSelectedBorderAlpha', 'edgeFadeAlpha'):
        if type(general[key]) not in (int, float) or not 0 <= general[key] <= 100:
            raise ValueError('Invalid carousel opacity: ' + key)
    if type(general['scrollingSpeed']) not in (int, float) or not 0.1 <= general['scrollingSpeed'] <= 10:
        raise ValueError('Invalid scrolling speed')
    for key in ('nations_order', 'types_order', 'sorting_criteria'):
        if not isinstance(general[key], list) or any(not isinstance(v, type(u'')) and not isinstance(v, str) for v in general[key]):
            raise ValueError('Expected a list of names: ' + key)
        if len(set(general[key])) != len(general[key]):
            raise ValueError('Duplicate names: ' + key)
    if any((value[1:] if value.startswith('-') else value) not in SORT_KEYS for value in general['sorting_criteria']):
        raise ValueError('Unsupported carousel sorting criterion')
    if not isinstance(general['filters'], dict) or not isinstance(general['filtersPadding'], dict):
        raise ValueError('Invalid carousel filter settings')
    for key in ('params', 'bonus', 'favorite', 'elite', 'premium'):
        if not isinstance(general['filters'].get(key), dict) or type(general['filters'][key].get('enabled')) is not bool:
            raise ValueError('Invalid filter visibility')
    for key in ('horizontal', 'vertical'):
        value = general['filtersPadding'][key]
        if type(value) not in (int, float) or not 0 <= value <= 40:
            raise ValueError('Invalid filter spacing')
    for profile in parts[1:]:
        for key, low, high in (('width', 80, 600), ('height', 35, 400), ('gap', 0, 40)):
            if type(profile.get(key)) not in (int, float) or not low <= profile[key] <= high:
                raise ValueError('Invalid carousel cell dimensions: ' + key)
        if not isinstance(profile.get('fields'), dict) or not isinstance(profile.get('extraFields'), list):
            raise ValueError('Invalid carousel fields')
        if any(not isinstance(field, dict) for field in list(profile['fields'].values()) + profile['extraFields']):
            raise ValueError('Carousel fields must contain objects')
        if not isinstance(profile.get('textFieldShadow', {}), dict):
            raise ValueError('Carousel textFieldShadow must be an object')
        for field in profile['extraFields']:
            shadow = field.get('shadow', {})
            if not isinstance(shadow, (dict, str, type(u''))):
                raise ValueError('Carousel shadow must be an object or local reference')
            profile_shadow(profile, shadow)


class CarouselStore(JsonDocuments):
    def __init__(self, directory):
        super(CarouselStore, self).__init__(directory, FILES)

    def load(self):
        self.recover()
        parts = []
        missing = []
        for name, default in zip(FILES, documents(config_defaults())):
            path = os.path.join(self.directory, name)
            recover_file(path)
            if os.path.isfile(path):
                value = read_object(path)
                parts.append(merge(default, value))
            else:
                missing.append((path, default))
                parts.append(copy.deepcopy(default))
        validate(parts)
        # Do not overwrite malformed user documents or read old slot settings.
        self.publish(missing)
        general, normal, small = parts
        carousel = from_carousel(general)
        carousel.update(cellType=general['cellType'], rows=general['rows'], normal=normal, small=small)
        return {'enabled': general['enabled'], 'showIcons': general['showIcons'], 'colorRating': general['colorRating'], 'carousel': carousel}

    def save(self, data):
        parts = documents(data)
        validate(parts)
        self.recover()
        updates = []
        for name, part in zip(FILES, parts):
            path = os.path.join(self.directory, name)
            recover_file(path)
            if not os.path.isfile(path) or read_object(path) != part:
                updates.append((path, part))
        self.publish(updates)
        return copy.deepcopy(data)
