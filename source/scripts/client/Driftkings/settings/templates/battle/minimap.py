# -*- coding: utf-8 -*-
import json

from Driftkings._constants import GLOBAL, MINIMAP_PLUGINS
from Driftkings.core import minimap as policy
from Driftkings.settings.store import merge
from Driftkings.settings.template_schema import color, control, hotkey, slider
from Driftkings.settings.template_schema import field as nested_field
from Driftkings.settings.templates.base import ComponentSettings


class MinimapPluginsSettings(ComponentSettings):
    COMPONENT = MINIMAP_PLUGINS.ID

    TRANSLATED_TITLE = True

    def readData(self, quiet=True):
        super(MinimapPluginsSettings, self).readData(quiet)
        self.data[MINIMAP_PLUGINS.ARTILLERY_AIM].pop('color', None)
        policy.migrate_artillery_aim(self.data)
        if not self.data.get(MINIMAP_PLUGINS.MINIMAP_SCHEMA):
            for item in self.data[MINIMAP_PLUGINS.CIRCLES].values():
                item['alpha'] = self.data[GLOBAL.ALPHA]
            self.data[MINIMAP_PLUGINS.MINIMAP_SCHEMA] = 1
        policy.validate(self.data)

    def onApplySettings(self, settings):
        settings = dict(settings)
        if isinstance(settings.get(MINIMAP_PLUGINS.EXTRA_CIRCLES), (str, type(u''))):
            settings[MINIMAP_PLUGINS.EXTRA_CIRCLES] = json.loads(settings[MINIMAP_PLUGINS.EXTRA_CIRCLES])
        candidate = merge(self.data, settings)
        policy.validate(candidate)
        super(MinimapPluginsSettings, self).onApplySettings(settings)

    def getControlColumns(self):
        xColorDrawRange = color(MINIMAP_PLUGINS.COLOR_DRAW_CIRCLE, 'colorDrawCircleCheck')
        xColorMaxRange = color(MINIMAP_PLUGINS.COLOR_MAX_VIEW_CIRCLE, 'colorMaxViewCircleCheck')
        xColorMinSpottingRange = color(MINIMAP_PLUGINS.COLOR_MIN_SPOTTING_CIRCLE, 'colorMinSpottingCircleCheck')
        xColorViewRange = color(MINIMAP_PLUGINS.COLOR_VIEW_CIRCLE, 'colorViewCircleCheck')

        columns = (
            [
                control(MINIMAP_PLUGINS.PERMANENT_MINIMAP_DEATH),
                control(MINIMAP_PLUGINS.SHOW_NAMES),
                hotkey(MINIMAP_PLUGINS.BUTTON),
                control(MINIMAP_PLUGINS.VIEW_RADIUS),
                control(MINIMAP_PLUGINS.YAW),
                control(MINIMAP_PLUGINS.SHOW_LAST_POSITIONS),
                slider(MINIMAP_PLUGINS.LAST_POSITION_DURATION, 0, 300, 5, '{{value}}.s')
            ],
            [
                control(MINIMAP_PLUGINS.CHANGE_COLOR_CIRCLES),
                xColorDrawRange,
                xColorMaxRange,
                xColorMinSpottingRange,
                xColorViewRange,
                control(MINIMAP_PLUGINS.SHOW_VEHICLE_TYPES),
                slider(MINIMAP_PLUGINS.ZOOM_FACTOR_MAX, 1.0, 3.0, 0.1, '{{value}}.Px/Py')
            ]
        )

        def nested(section, key, kind='CheckBox', low=None, high=None, choices=None):
            title = self.i18n.get('UI_setting_' + section + '_' + key + '_text', key)
            labels = [self.i18n.get('UI_mode_' + value, value) for value in choices] if choices else None
            return nested_field([section, key], title, kind, low, high, choices, choice_labels=labels)
        columns[0].append(slider(MINIMAP_PLUGINS.ZOOM_FACTOR, 1.0, 3.0, 0.1, '{{value}}'))
        columns[0].append(nested(MINIMAP_PLUGINS.LABELS, GLOBAL.ENABLED))
        for key in ('normal', 'alternative', 'dead', 'lost'):
            columns[0].append(nested(MINIMAP_PLUGINS.LABELS, key, 'TextInput'))
        for key, low, high in (('fontSize', 8, 24), (GLOBAL.ALPHA, 0, 100)):
            columns[0].append(nested(MINIMAP_PLUGINS.LABELS, key, 'Slider', low, high))
        for key in ('direction', 'sector'):
            columns[1].append(nested(MINIMAP_PLUGINS.LINES, key, 'Dropdown', choices=['client', 'on', 'off']))
        columns[1].append(nested(MINIMAP_PLUGINS.LINES, 'customStyle'))
        for key in ('directionColor', 'sectorColor'):
            columns[1].append(nested(MINIMAP_PLUGINS.LINES, key, 'ColorChoice'))
        columns[1].append(nested(MINIMAP_PLUGINS.LINES, GLOBAL.ALPHA, 'Slider', 0, 100))
        columns[1].append(nested(MINIMAP_PLUGINS.ARTILLERY_AIM, GLOBAL.ENABLED))
        columns[1].append(nested(MINIMAP_PLUGINS.ARTILLERY_AIM, 'scale', 'Slider', 10, 200))
        paths = policy.artillery_aim_choices(self.data[MINIMAP_PLUGINS.ARTILLERY_AIM]['src'])
        aim = nested_field([MINIMAP_PLUGINS.ARTILLERY_AIM, 'src'],
                           self.i18n['UI_setting_artilleryAim_src_text'], 'Dropdown',
                           choices=paths, previewImage=True)
        for index, option in enumerate(aim['options']):
            option['image'] = paths[index]
            option['label'] = self.i18n.get('UI_minimapAim_%d' % index, paths[index].rsplit('/', 1)[-1])
        columns[1].append(aim)
        columns[1].append(nested(MINIMAP_PLUGINS.ARTILLERY_AIM, GLOBAL.ALPHA, 'Slider', 0, 100))
        for key in policy.CIRCLES:
            for field, kind in (('mode', 'Dropdown'), (GLOBAL.ALPHA, 'Slider')):
                item = nested(MINIMAP_PLUGINS.CIRCLES, key, kind, 0 if field == GLOBAL.ALPHA else None, 100,
                               ['client', 'on', 'off'] if field == 'mode' else None)
                item['path'].append(field)
                item['varName'] += '.' + field
                item['text'] += ' / ' + self.i18n.get('UI_field_' + field, field)
                columns[1].append(item)
        for key in ('alternativeEnabled', 'zoom', 'center'):
            columns[0].append(nested(MINIMAP_PLUGINS.PRESENTATION, key))
        for key, low, high in (('sizeIndex', 0, 5), ('normalAlpha', 10, 100), ('alternativeAlpha', 10, 100), ('backgroundAlpha', 0, 100)):
            columns[0].append(nested(MINIMAP_PLUGINS.PRESENTATION, key, 'Slider', low, high))
        for key in ('ally', 'enemy', 'squad', 'alternativeAlly', 'alternativeEnemy', 'alternativeSquad'):
            columns[0].append(nested(MINIMAP_PLUGINS.LABELS, key, 'TextInput'))
        for key in ('x', 'y'):
            columns[0].append(nested(MINIMAP_PLUGINS.LABELS, key, 'Slider', -100, 100))
        columns[0].append(nested(MINIMAP_PLUGINS.LABELS, 'align', 'Dropdown', choices=['left', 'center', 'right']))
        for key in ('shadow', 'customColors', 'avoidOverlap'):
            columns[0].append(nested(MINIMAP_PLUGINS.LABELS, key))
        for key in ('allyColor', 'enemyColor', 'squadColor', 'deadColor'):
            columns[0].append(nested(MINIMAP_PLUGINS.LABELS, key, 'ColorChoice'))
        columns[0].append(nested(MINIMAP_PLUGINS.LABELS, 'compactLength', 'Slider', 4, 40))
        for key in ('scale', 'selfScale'):
            item = nested(MINIMAP_PLUGINS.ICONS, key, 'Slider', .5, 3)
            item['snapInterval'] = .1
            columns[0].append(item)
        for key in (GLOBAL.ALPHA, 'selfAlpha'):
            columns[0].append(nested(MINIMAP_PLUGINS.ICONS, key, 'Slider', 0, 100))
        columns[0].append(nested(MINIMAP_PLUGINS.ICONS, 'selfColor', 'ColorChoice'))
        columns[0].append(nested(MINIMAP_PLUGINS.HEALTH, 'visibility', 'Dropdown', choices=['never', 'key', 'always']))
        columns[0].append(nested(MINIMAP_PLUGINS.HEALTH, 'mode', 'Dropdown', choices=['value', 'percent', 'bar']))
        for key, low, high in (('x', -100, 100), ('y', -100, 100), ('width', 10, 100), ('height', 1, 10), ('fontSize', 8, 24)):
            columns[0].append(nested(MINIMAP_PLUGINS.HEALTH, key, 'Slider', low, high))
        for key in ('showSeconds', 'fade'):
            columns[1].append(nested(MINIMAP_PLUGINS.LOST_MARKER, key))
        columns[1].append(nested(MINIMAP_PLUGINS.LOST_MARKER, 'minimumAlpha', 'Slider', 0, 100))
        columns[1].append(nested(MINIMAP_PLUGINS.MAP_SIZE, GLOBAL.ENABLED))
        for key, low, high in (('x', -300, 300), ('y', -300, 300), ('fontSize', 8, 24)):
            columns[1].append(nested(MINIMAP_PLUGINS.MAP_SIZE, key, 'Slider', low, high))
        columns[1].append(nested(MINIMAP_PLUGINS.MAP_SIZE, 'color', 'ColorChoice'))
        columns[1].append(nested(MINIMAP_PLUGINS.MAP_SIZE, 'format', 'TextInput'))
        columns[1].append(nested(MINIMAP_PLUGINS.LINES, 'geometry'))
        for key, low, high in (('length', 50, 1500), ('thickness', 1, 5), ('dash', 0, 100), ('gap', 1, 100)):
            columns[1].append(nested(MINIMAP_PLUGINS.LINES, key, 'Slider', low, high))
        for circle in policy.CIRCLES:
            for key, low, high in (('thickness', 1, 5), ('dash', 0, 100), ('gap', 1, 100)):
                item = nested(MINIMAP_PLUGINS.CIRCLES, circle, 'Slider', low, high)
                item['path'].append(key)
                item['varName'] += '.' + key
                item['text'] += ' / ' + self.i18n.get('UI_setting_lines_' + key + '_text', key)
                columns[1].append(item)
        columns[1].append(nested_field([MINIMAP_PLUGINS.EXTRA_CIRCLES],
                         self.i18n.get('UI_setting_extraCircles_text', 'Extra circles (JSON)'),
                         'TextInput', jsonValue=True))
        return columns
