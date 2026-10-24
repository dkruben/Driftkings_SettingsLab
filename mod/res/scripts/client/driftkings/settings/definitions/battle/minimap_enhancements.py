# -*- coding: utf-8 -*-
import json

from driftkings._constants import GLOBAL, MINIMAP_ENHANCEMENTS
from driftkings.core import minimap as policy
from driftkings.settings.controls_schema import color, control
from driftkings.settings.controls_schema import field as nested_field
from driftkings.settings.controls_schema import hotkey, slider
from driftkings.settings.definitions.base import SectionDefinition


class MinimapEnhancementsSettings(SectionDefinition):
    NAME = MINIMAP_ENHANCEMENTS.NAME

    TRANSLATED_TITLE = True

    def normalize_loaded(self, values):
        policy.validate(values)
        return values

    def normalize_changes(self, values, changes):
        if isinstance(values.get(MINIMAP_ENHANCEMENTS.EXTRA_CIRCLES), (str, type(u''))):
            values[MINIMAP_ENHANCEMENTS.EXTRA_CIRCLES] = json.loads(values[MINIMAP_ENHANCEMENTS.EXTRA_CIRCLES])
        policy.validate(values)
        return values

    def getControlColumns(self):
        xColorDrawRange = color(MINIMAP_ENHANCEMENTS.COLOR_DRAW_CIRCLE, 'colorDrawCircleCheck')
        xColorMaxRange = color(MINIMAP_ENHANCEMENTS.COLOR_MAX_VIEW_CIRCLE, 'colorMaxViewCircleCheck')
        xColorMinSpottingRange = color(MINIMAP_ENHANCEMENTS.COLOR_MIN_SPOTTING_CIRCLE, 'colorMinSpottingCircleCheck')
        xColorViewRange = color(MINIMAP_ENHANCEMENTS.COLOR_VIEW_CIRCLE, 'colorViewCircleCheck')

        columns = (
            [
                control(MINIMAP_ENHANCEMENTS.PERMANENT_MINIMAP_DEATH),
                control(MINIMAP_ENHANCEMENTS.SHOW_NAMES),
                hotkey(MINIMAP_ENHANCEMENTS.BUTTON),
                control(MINIMAP_ENHANCEMENTS.VIEW_RADIUS),
                control(MINIMAP_ENHANCEMENTS.YAW),
                control(MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS),
                slider(MINIMAP_ENHANCEMENTS.LAST_POSITION_DURATION, 0, 300, 5, '{{value}}.s')
            ],
            [
                control(MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES),
                xColorDrawRange,
                xColorMaxRange,
                xColorMinSpottingRange,
                xColorViewRange,
                control(MINIMAP_ENHANCEMENTS.SHOW_VEHICLE_TYPES),
                slider(MINIMAP_ENHANCEMENTS.ZOOM_FACTOR_MAX, 1.0, 3.0, 0.1, '{{value}}.Px/Py')
            ]
        )

        def nested(section, key, kind='CheckBox', low=None, high=None, choices=None):
            title = self.i18n.get('UI_setting_' + section + '_' + key + '_text', key)
            labels = [self.i18n.get('UI_mode_' + value, value) for value in choices] if choices else None
            return nested_field([section, key], title, kind, low, high, choices, choice_labels=labels)
        # Centred/zoomed minimap: general options, kept together and ahead of the labels.
        for key in ('alternativeEnabled', 'zoom', 'center'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.PRESENTATION, key))
        columns[0].append(slider(MINIMAP_ENHANCEMENTS.ZOOM_FACTOR, 1.0, 3.0, 0.1, '{{value}}'))
        for key, low, high in (('sizeIndex', 0, 5), ('normalAlpha', 10, 100), ('alternativeAlpha', 10, 100), ('backgroundAlpha', 0, 100)):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.PRESENTATION, key, 'Slider', low, high))
        columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, GLOBAL.ENABLED))
        for key in ('normal', 'alternative', 'dead', 'lost'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, key, 'TextInput'))
        for key, low, high in (('fontSize', 8, 24), (GLOBAL.ALPHA, 0, 100)):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, key, 'Slider', low, high))
        for key in ('direction', 'sector'):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, key, 'Dropdown', choices=['client', 'on', 'off']))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, 'customStyle'))
        for key in ('directionColor', 'sectorColor'):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, key, 'ColorChoice'))
        for key in ('triangleAlpha', 'directionAlpha'):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, key, 'Slider', 0, 100))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, 'hull'))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, 'hullColor', 'ColorChoice'))
        marks = nested(MINIMAP_ENHANCEMENTS.LINES, 'marks', 'Slider', 0, 500)
        marks['snapInterval'] = 50
        columns[1].append(marks)
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, GLOBAL.ALPHA, 'Slider', 0, 100))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.ARTILLERY_AIM, GLOBAL.ENABLED))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.ARTILLERY_AIM, 'scale', 'Slider', 10, 200))
        paths = policy.artillery_aim_choices(self.data[MINIMAP_ENHANCEMENTS.ARTILLERY_AIM]['src'])
        aim = nested_field([MINIMAP_ENHANCEMENTS.ARTILLERY_AIM, 'src'],
                           self.i18n['UI_setting_artilleryAim_src_text'], 'Dropdown',
                           choices=paths, previewImage=True)
        for index, option in enumerate(aim['options']):
            option['image'] = paths[index]
            option['label'] = self.i18n.get('UI_minimapAim_%d' % index, paths[index].rsplit('/', 1)[-1])
        columns[1].append(aim)
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.ARTILLERY_AIM, GLOBAL.ALPHA, 'Slider', 0, 100))
        for key in policy.CIRCLES:
            for field, kind in (('mode', 'Dropdown'), (GLOBAL.ALPHA, 'Slider')):
                item = nested(MINIMAP_ENHANCEMENTS.CIRCLES, key, kind, 0 if field == GLOBAL.ALPHA else None, 100,
                               ['client', 'on', 'off'] if field == 'mode' else None)
                item['path'].append(field)
                item['varName'] += '.' + field
                item['text'] += ' / ' + self.i18n.get('UI_field_' + field, field)
                columns[1].append(item)
        for field, kind, low, high, choices in (('mode', 'Dropdown', None, None, ['on', 'off']),
                                                (GLOBAL.ALPHA, 'Slider', 0, 100, None),
                                                ('color', 'ColorChoice', None, None, None)):
            item = nested(MINIMAP_ENHANCEMENTS.CIRCLES, 'shell', kind, low, high, choices)
            item['path'].append(field)
            item['varName'] += '.' + field
            item['text'] += ' / ' + self.i18n.get('UI_field_' + field, field)
            columns[1].append(item)
        for key in ('ally', 'enemy', 'squad', 'alternativeAlly', 'alternativeEnemy', 'alternativeSquad'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, key, 'TextInput'))
        for key in ('x', 'y'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, key, 'Slider', -100, 100))
        columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, 'align', 'Dropdown', choices=['left', 'center', 'right']))
        for key in ('shadow', 'teamColors', 'customColors', 'avoidOverlap'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, key))
        for key in ('allyColor', 'enemyColor', 'squadColor', 'teamKillerColor', 'deadColor'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, key, 'ColorChoice'))
        columns[0].append(nested(MINIMAP_ENHANCEMENTS.LABELS, 'compactLength', 'Slider', 4, 40))
        for key in ('scale', 'deadScale', 'lostScale', 'selfScale'):
            item = nested(MINIMAP_ENHANCEMENTS.ICONS, key, 'Slider', .5, 3)
            item['snapInterval'] = .1
            columns[0].append(item)
        for key in (GLOBAL.ALPHA, 'deadAlpha', 'selfAlpha'):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.ICONS, key, 'Slider', 0, 100))
        columns[0].append(nested(MINIMAP_ENHANCEMENTS.ICONS, 'selfColor', 'ColorChoice'))
        columns[0].append(nested(MINIMAP_ENHANCEMENTS.HEALTH, 'visibility', 'Dropdown', choices=['never', 'key', 'always']))
        columns[0].append(nested(MINIMAP_ENHANCEMENTS.HEALTH, 'mode', 'Dropdown', choices=['value', 'percent', 'bar']))
        for key, low, high in (('x', -100, 100), ('y', -100, 100), ('width', 10, 100), ('height', 1, 10), ('fontSize', 8, 24)):
            columns[0].append(nested(MINIMAP_ENHANCEMENTS.HEALTH, key, 'Slider', low, high))
        for key in ('icon', 'showSeconds', 'fade'):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.LOST_MARKER, key))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LOST_MARKER, 'minimumAlpha', 'Slider', 0, 100))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LOST_MARKER, 'style', 'Dropdown', choices=list(policy.LOST_STYLES)))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LOST_MARKER, 'desaturate', 'Slider', 0, 100))
        for key in ('enemyColor', 'allyColor', 'squadColor'):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.LOST_MARKER, key, 'ColorChoice'))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.NEARBY, GLOBAL.ENABLED))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.NEARBY, 'range', 'Dropdown', choices=list(policy.NEARBY_RANGES)))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.NEARBY, 'distance', 'Slider', 50, 1500))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.NEARBY, 'color', 'ColorChoice'))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.NEARBY, GLOBAL.ALPHA, 'Slider', 0, 100))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.MAP_SIZE, GLOBAL.ENABLED))
        for key, low, high in (('x', -300, 300), ('y', -300, 300), ('fontSize', 8, 24)):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.MAP_SIZE, key, 'Slider', low, high))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.MAP_SIZE, 'color', 'ColorChoice'))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.MAP_SIZE, 'format', 'TextInput'))
        columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, 'geometry'))
        for key, low, high in (('length', 50, 1500), ('thickness', 1, 5), ('dash', 0, 100), ('gap', 1, 100)):
            columns[1].append(nested(MINIMAP_ENHANCEMENTS.LINES, key, 'Slider', low, high))
        for circle in policy.CIRCLES + ('shell',):
            for key, low, high in (('thickness', 1, 5), ('dash', 0, 100), ('gap', 1, 100)):
                item = nested(MINIMAP_ENHANCEMENTS.CIRCLES, circle, 'Slider', low, high)
                item['path'].append(key)
                item['varName'] += '.' + key
                item['text'] += ' / ' + self.i18n.get('UI_setting_lines_' + key + '_text', key)
                columns[1].append(item)
        columns[1].append(nested_field([MINIMAP_ENHANCEMENTS.EXTRA_CIRCLES],
                         self.i18n.get('UI_setting_extraCircles_text', 'Extra circles (JSON)'),
                         'TextInput', jsonValue=True))
        return columns
