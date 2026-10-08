# -*- coding: utf-8 -*-
import re

from Driftkings._constants import CAROUSEL_STATS, GLOBAL
from Driftkings.common import color_tables
from Driftkings.core import carousel as layout
from Driftkings.settings.carousel_store import CarouselStore, FILES
from Driftkings.settings.store import merge
from Driftkings.settings.template_schema import control, options, caption
from Driftkings.settings.template_schema import field as nested_field
from Driftkings.settings.templates.base import ComponentSettings


class CarouselStatsSettings(ComponentSettings):
    COMPONENT = CAROUSEL_STATS.ID


    def profileStore(self):
        from Driftkings.settings.loader import settings_loader
        return settings_loader.split_store(self.ID, CarouselStore, FILES, self.configPath)

    def loadDataJson(self, *args, **kwargs):
        return self.profileStore().load()

    def writeDataJson(self, *args, **kwargs):
        return self.profileStore().save(self.data)

    def readData(self, quiet=True):
        data = self.menuLists(self.loadDataJson())
        self.data.clear()
        self.data.update(data)

    def onApplySettings(self, settings):
        candidate = merge(self.data, settings)
        for ui, key in ((CAROUSEL_STATS.SORTING_CRITERIA, 'sorting_criteria'), (CAROUSEL_STATS.NATIONS_ORDER, 'nations_order'), (CAROUSEL_STATS.TYPES_ORDER, 'types_order')):
            if ui in settings:
                candidate[CAROUSEL_STATS.CAROUSEL][key] = [value.strip() for value in settings[ui].split(',') if value.strip()]
        self.profileStore().save(candidate)
        self.data.clear()
        self.data.update(candidate)

    @staticmethod
    def menuLists(data):
        for ui, key in ((CAROUSEL_STATS.SORTING_CRITERIA, 'sorting_criteria'), (CAROUSEL_STATS.NATIONS_ORDER, 'nations_order'), (CAROUSEL_STATS.TYPES_ORDER, 'types_order')):
            data[ui] = ', '.join(data[CAROUSEL_STATS.CAROUSEL][key])
        return data
    TRANSLATED_TITLE = False

    def getControlColumns(self):
        columns = [[options(CAROUSEL_STATS.COLOR_RATING, [x['ScaleColor'] for x in color_tables])], [control(CAROUSEL_STATS.SHOW_ICONS)]]

        def nested(path, title, kind, low=None, high=None, choices=None):
            values = [value for value, label in choices] if choices is not None else None
            labels = [label for value, label in choices] if choices is not None else None
            step = 0.1 if path[-1] in ('scale', 'scrollingSpeed') else 1
            return nested_field(path, title, kind, low, high, values, step, labels)
        columns[0].append(nested([CAROUSEL_STATS.CAROUSEL,'cellType'], 'Layout', 'Dropdown', choices=[('default','Auto'),('normal','Normal'),('small','Compact')]))
        columns[1].append(nested([CAROUSEL_STATS.CAROUSEL,'rows'], 'Rows (0 = client)', 'Slider', 0, 4))
        for index, key in enumerate(('backgroundAlpha', 'slotBackgroundAlpha', 'slotBorderAlpha', 'slotSelectedBorderAlpha', 'edgeFadeAlpha')):
            columns[index % 2].append(nested([CAROUSEL_STATS.CAROUSEL, key], key, 'Slider', 0, 100))
        columns[1].append(nested([CAROUSEL_STATS.CAROUSEL, 'scrollingSpeed'], 'Scrolling speed', 'Slider', 0.1, 10))
        for index, key in enumerate(('hideBuyTank', 'hideBuySlot', 'hideRestoreTank', 'showTotalSlots', 'showUsedSlots', 'enableLockBackground', 'suppressCarouselTooltips')):
            columns[index % 2].append(nested([CAROUSEL_STATS.CAROUSEL, key], key, 'CheckBox'))
        for index, key in enumerate(('params', 'bonus', 'favorite', 'elite', 'premium')):
            columns[index % 2].append(nested([CAROUSEL_STATS.CAROUSEL, 'filters', key, GLOBAL.ENABLED], 'Filter: ' + key, 'CheckBox'))
        for index, key in enumerate(('horizontal', 'vertical')):
            columns[index].append(nested([CAROUSEL_STATS.CAROUSEL, 'filtersPadding', key], 'Filter spacing: ' + key, 'Slider', 0, 40))
        for key, title in ((CAROUSEL_STATS.SORTING_CRITERIA, 'Sorting (comma separated; - = descending)'), (CAROUSEL_STATS.NATIONS_ORDER, 'Nation order (comma separated)'), (CAROUSEL_STATS.TYPES_ORDER, 'Vehicle type order (comma separated)')):
            columns[0].append(nested([key], title, 'TextInput'))
        for col, mode in enumerate(('normal','small')):
            profile = self.data[CAROUSEL_STATS.CAROUSEL][mode]
            target=columns[col]
            target.append(caption(mode.upper()))
            for key,low,high in (('width',80,600),('height',35,400),('gap',0,40)):
                target.append(nested([CAROUSEL_STATS.CAROUSEL,mode,key],mode+': '+key,'Slider',low,high))
            for name in layout.FIELD_NAMES:
                path=[CAROUSEL_STATS.CAROUSEL,mode,'fields',name]
                target.append(caption(name))
                target.append(nested(path+[GLOBAL.ENABLED],'Show '+name,'CheckBox'))
                for key,lo,hi in (('dx',-400,400),('dy',-400,400),('alpha',0,100),('scale',0.1,4)):
                    target.append(nested(path+[key],name+': '+key,'Slider',lo,hi))
            for i,item in enumerate(profile['extraFields'][:64]):
                # Expose properties present in each custom extra field.
                path=[CAROUSEL_STATS.CAROUSEL,mode,'extraFields',i]
                target.append(caption('Extra field '+str(i+1)))
                for key in (GLOBAL.ENABLED,'format','color','bgColor','src','x','y','width','height','fontSize','iconSize','alpha','align','layer'):
                    if key not in item: continue
                    kind='CheckBox' if key==GLOBAL.ENABLED else 'TextInput'
                    if key in ('x','y','width','height','fontSize','iconSize','alpha') and not isinstance(item[key], basestring):
                        lo,hi={'x':(-600,600),'y':(-400,400),'width':(0,600),'height':(0,400),'fontSize':(8,40),'iconSize':(8,80),'alpha':(0,100)}[key]
                        target.append(nested(path+[key],str(i+1)+': '+key,'Slider',lo,hi))
                    elif key=='align': target.append(nested(path+[key],str(i+1)+': '+key,'Dropdown',choices=[('left','Left'),('center','Center'),('right','Right')]))
                    elif key=='layer': target.append(nested(path+[key],str(i+1)+': '+key,'Dropdown',choices=[('substrate','Background'),('top','Foreground')]))
                    else:
                        if key in ('color','bgColor') and re.match(r'^(?:#|0x)?[0-9a-fA-F]{6}$',str(item[key])): kind='ColorChoice'
                        target.append(nested(path+[key],str(i+1)+': '+key,kind))
        return columns[0], columns[1]

    def init(self):
        super(CarouselStatsSettings, self).init()
        self.menuLists(self.data)

    def getSettingsDefaults(self):
        return self.menuLists(super(CarouselStatsSettings, self).getSettingsDefaults())
