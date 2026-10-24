# -*- coding: utf-8 -*-
import json
import re

from driftkings._constants import TEAM_PANELS
from driftkings.settings.controls_schema import field as nested_field
from driftkings.settings.definitions.base import SectionDefinition
from driftkings.settings.service import settings_service
from driftkings.settings.team_panel_store import FILES, PlayerPanelStore


class TeamPanelsSettings(SectionDefinition):
    NAME = TEAM_PANELS.NAME

    TRANSLATED_TITLE = True

    STORAGE_CLASS = PlayerPanelStore
    STORAGE_FILES = FILES

    def normalize_changes(self, values, changes):
        if TEAM_PANELS.HP_VISIBILITY in changes:
            values[TEAM_PANELS.HP_ENABLED] = values[TEAM_PANELS.HP_VISIBILITY] != 'never'
        def decode(value, base):
            if isinstance(base, (dict, list)) and isinstance(value, (str, type(u''))):
                return json.loads(value)
            if isinstance(value, dict) and isinstance(base, dict):
                return dict((key, decode(item, base.get(key))) for key, item in value.items())
            return value
        return decode(values, self.data)

    def getControlColumns(self):
        return player_panel_columns(self)


def player_panel_columns(config):
    """Expose the actual v2 keys; no parallel name/layout configuration."""
    import json

    from driftkings.settings.settings_data import PROFILES
    columns=[[],[]]
    labels=config.i18n
    def add(path,value,tab,column=None):
        key=path[-1]
        column=(1 if key.endswith('Right') else 0) if column is None else column
        if isinstance(value,dict):
            for child,setting in sorted(value.items()):
                add(path+[child],setting,tab,column)
            return
        title='.'.join(path[1:]) if path[0]==TEAM_PANELS.TEMPLATES else key
        item=nested_field(path, labels.get('UI_panel_'+key,title), 'TextInput', tab=tab)
        if key==TEAM_PANELS.HP_VISIBILITY:
            choices=['always','hold','never']
            item.update(type='Dropdown',options=[{'label':labels.get('UI_panel_hp_'+mode,fallback)} for mode,fallback in
                        zip(choices,('Always visible','While the key is held','Never visible'))],optionValues=choices)
        elif key==TEAM_PANELS.HP_KEY: item['type']='HotKey'
        elif isinstance(value,bool): item['type']='CheckBox'
        elif isinstance(value,(int,float)):
            item.update(type='Slider',minimum=0 if 'Width' in key or 'Alpha' in key else -2000,
                        maximum=100 if 'Alpha' in key else 4000,snapInterval=.01 if isinstance(value,float) else 1,canManualInput=True)
        elif isinstance(value,(list,dict)) or value is None and key not in ('startMode','altMode'):
            item.update(type='TextInput',value=json.dumps(value,ensure_ascii=False),jsonValue=True)
        elif key in ('startMode','altMode'):
            choices=[None]+list(PROFILES)
            item.update(type='Dropdown',options=[{'label':name or labels['UI_panel_clientDefault']} for name in choices],optionValues=choices)
        elif isinstance(value,(str,type(u''))) and re.match(r'^(?:#|0x)[0-9a-fA-F]{6}$',value):
            item['type']='ColorChoice'
        else: item['type']='TextInput'
        columns[column].append(item)
    general=labels['UI_panel_generalTab']
    for key in (TEAM_PANELS.STATS_ENABLED,TEAM_PANELS.HP_VISIBILITY,TEAM_PANELS.HP_KEY,TEAM_PANELS.SPOTTED_ENABLED,TEAM_PANELS.RATING,TEAM_PANELS.COLOR_SCALE):
        add([key],settings_service.getComponentDict(config)[key],general)
    add([TEAM_PANELS.PERFORMANCE,'diagnostics'],settings_service.getComponentDict(config)[TEAM_PANELS.PERFORMANCE].get('diagnostics',False),general)
    from driftkings.common.utils.colorratting import color_tables
    for item in columns[0]:
        if item['varName']==TEAM_PANELS.COLOR_SCALE:
            item.update(type='Dropdown',options=[{'label':entry['ScaleColor']} for entry in color_tables])
        elif item['varName']==TEAM_PANELS.RATING:
            choices=['wn8','eff','wgr','winrate','xwn8','xeff']
            item.update(type='Dropdown',options=[{'label':name} for name in choices],optionValues=choices)
    for key,value in sorted(settings_service.getComponentDict(config)[TEAM_PANELS.PLAYERS_PANEL].items()): add([TEAM_PANELS.PLAYERS_PANEL,key],value,general)
    for path,title in (([TEAM_PANELS.LOADING],labels['UI_panel_loadingTab']),([TEAM_PANELS.TAB],'TAB')):
        settings=settings_service.getComponentDict(config)[path[0]]
        for key,value in sorted(settings.items()):
            add(path+[key],value,title)
    for profile in PROFILES:
        for key,value in sorted(settings_service.getComponentDict(config)[TEAM_PANELS.PROFILES][profile].items()):
            add([TEAM_PANELS.PROFILES,profile,key],value,profile)
    for key,value in sorted(settings_service.getComponentDict(config)[TEAM_PANELS.TEMPLATES].items()): add([TEAM_PANELS.TEMPLATES,key],value,labels['UI_panel_templatesTab'])
    return columns
