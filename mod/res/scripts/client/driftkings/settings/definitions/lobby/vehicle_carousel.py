# -*- coding: utf-8 -*-
import re

from driftkings._constants import GLOBAL, VEHICLE_CAROUSEL
from driftkings.common.utils.colorratting import color_tables
from driftkings.core import carousel as layout
from driftkings.settings.controls_schema import caption, control
from driftkings.settings.controls_schema import field as nested_field
from driftkings.settings.controls_schema import options
from driftkings.settings.definitions.base import SectionDefinition
from driftkings.settings.vehicle_carousel_store import CarouselStore, FILES


class VehicleCarouselSettings(SectionDefinition):
    NAME = VEHICLE_CAROUSEL.NAME


    STORAGE_CLASS = CarouselStore
    STORAGE_FILES = FILES

    def normalize_loaded(self, values):
        return self.menuLists(values)

    def normalize_changes(self, values, changes):
        for ui, key in ((VEHICLE_CAROUSEL.SORTING_CRITERIA, 'sorting_criteria'), (VEHICLE_CAROUSEL.NATIONS_ORDER, 'nations_order'), (VEHICLE_CAROUSEL.TYPES_ORDER, 'types_order')):
            if ui in changes:
                values[VEHICLE_CAROUSEL.CAROUSEL][key] = [value.strip() for value in changes[ui].split(',') if value.strip()]
        return values

    @staticmethod
    def menuLists(data):
        for ui, key in ((VEHICLE_CAROUSEL.SORTING_CRITERIA, 'sorting_criteria'), (VEHICLE_CAROUSEL.NATIONS_ORDER, 'nations_order'), (VEHICLE_CAROUSEL.TYPES_ORDER, 'types_order')):
            data[ui] = ', '.join(data[VEHICLE_CAROUSEL.CAROUSEL][key])
        return data
    TRANSLATED_TITLE = True

    def getControlColumns(self):
        columns = [[options(VEHICLE_CAROUSEL.COLOR_RATING, [x['ScaleColor'] for x in color_tables])], [control(VEHICLE_CAROUSEL.SHOW_ICONS)]]

        def tr(key):
            return self.i18n.get('UI_carousel_' + key, key)

        def nested(path, title, kind, low=None, high=None, choices=None):
            values = [value for value, label in choices] if choices is not None else None
            labels = [label for value, label in choices] if choices is not None else None
            step = 0.1 if path[-1] in ('scale', 'scrollingSpeed') else 1
            return nested_field(path, title, kind, low, high, values, step, labels)
        columns[0].append(nested([VEHICLE_CAROUSEL.CAROUSEL,'cellType'], tr('layout'), 'Dropdown', choices=[('default',tr('auto')),('normal',tr('normal')),('small',tr('small'))]))
        columns[1].append(nested([VEHICLE_CAROUSEL.CAROUSEL,'rows'], tr('rows'), 'Slider', 0, 4))
        for index, key in enumerate(('backgroundAlpha', 'slotBackgroundAlpha', 'slotBorderAlpha', 'slotSelectedBorderAlpha', 'edgeFadeAlpha')):
            columns[index % 2].append(nested([VEHICLE_CAROUSEL.CAROUSEL, key], tr(key), 'Slider', 0, 100))
        columns[1].append(nested([VEHICLE_CAROUSEL.CAROUSEL, 'scrollingSpeed'], tr('scrollingSpeed'), 'Slider', 0.1, 10))
        for index, key in enumerate(('hideBuyTank', 'hideBuySlot', 'hideRestoreTank', 'showTotalSlots', 'showUsedSlots', 'enableLockBackground', 'suppressCarouselTooltips')):
            columns[index % 2].append(nested([VEHICLE_CAROUSEL.CAROUSEL, key], tr(key), 'CheckBox'))
        for index, key in enumerate(('params', 'bonus', 'favorite', 'elite', 'premium')):
            columns[index % 2].append(nested([VEHICLE_CAROUSEL.CAROUSEL, 'filters', key, GLOBAL.ENABLED], tr('filter') + ': ' + tr('filterFavorite' if key == 'favorite' else key), 'CheckBox'))
        for index, key in enumerate(('horizontal', 'vertical')):
            columns[index].append(nested([VEHICLE_CAROUSEL.CAROUSEL, 'filtersPadding', key], tr('filterSpacing') + ': ' + tr(key), 'Slider', 0, 40))
        for key, title in ((VEHICLE_CAROUSEL.SORTING_CRITERIA, tr('sortingCriteria')), (VEHICLE_CAROUSEL.NATIONS_ORDER, tr('nationsOrder')), (VEHICLE_CAROUSEL.TYPES_ORDER, tr('typesOrder'))):
            columns[0].append(nested([key], title, 'TextInput'))
        for col, mode in enumerate(('normal','small')):
            profile = self.data[VEHICLE_CAROUSEL.CAROUSEL][mode]
            target=columns[col]
            target.append(caption(tr(mode)))
            for key,low,high in (('width',80,600),('height',35,400),('gap',0,40)):
                target.append(nested([VEHICLE_CAROUSEL.CAROUSEL,mode,key],tr(mode)+': '+tr(key),'Slider',low,high))
            for name in layout.FIELD_NAMES:
                path=[VEHICLE_CAROUSEL.CAROUSEL,mode,'fields',name]
                target.append(caption(tr(name)))
                target.append(nested(path+[GLOBAL.ENABLED],tr('show')+' '+tr(name),'CheckBox'))
                for key,lo,hi in (('dx',-400,400),('dy',-400,400),('alpha',0,100),('scale',0.1,4)):
                    target.append(nested(path+[key],tr(name)+': '+tr(key),'Slider',lo,hi))
            for i,item in enumerate(profile['extraFields'][:64]):
                # Expose properties present in each custom extra field.
                path=[VEHICLE_CAROUSEL.CAROUSEL,mode,'extraFields',i]
                target.append(caption(tr('extraField')+' '+str(i+1)))
                for key in (GLOBAL.ENABLED,'format','color','bgColor','src','x','y','width','height','fontSize','iconSize','alpha','align','layer'):
                    if key not in item: continue
                    kind='CheckBox' if key==GLOBAL.ENABLED else 'TextInput'
                    if key in ('x','y','width','height','fontSize','iconSize','alpha') and not isinstance(item[key], basestring):
                        lo,hi={'x':(-600,600),'y':(-400,400),'width':(0,600),'height':(0,400),'fontSize':(8,40),'iconSize':(8,80),'alpha':(0,100)}[key]
                        target.append(nested(path+[key],str(i+1)+': '+tr(key),'Slider',lo,hi))
                    elif key=='align': target.append(nested(path+[key],str(i+1)+': '+tr(key),'Dropdown',choices=[('left',tr('left')),('center',tr('center')),('right',tr('right'))]))
                    elif key=='layer': target.append(nested(path+[key],str(i+1)+': '+tr(key),'Dropdown',choices=[('substrate',tr('background')),('top',tr('foreground'))]))
                    else:
                        if key in ('color','bgColor') and re.match(r'^(?:#|0x)?[0-9a-fA-F]{6}$',str(item[key])): kind='ColorChoice'
                        target.append(nested(path+[key],str(i+1)+': '+tr(key),kind))
        return columns[0], columns[1]
