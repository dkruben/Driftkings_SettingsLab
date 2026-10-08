# -*- coding: utf-8 -*-
import copy
import json
import re

from Driftkings._constants import PLAYER_PANEL_PRO
from Driftkings.common.config.utils import processHotKeys
from Driftkings.settings.loader import settings_loader
from Driftkings.settings.player_panel_store import PlayerPanelStore, FILES
from Driftkings.settings.service import settings_service
from Driftkings.settings.store import merge
from Driftkings.settings.template_schema import field as nested_field
from Driftkings.settings.templates.base import ComponentSettings


class PlayerPanelProSettings(ComponentSettings):
    COMPONENT = PLAYER_PANEL_PRO.ID

    TRANSLATED_TITLE = False

    def profileStore(self):
        return settings_loader.split_store(self.ID,PlayerPanelStore,FILES,self.configPath)

    def registerHotkeys(self):
        pass

    def loadDataJson(self,*args,**kwargs):
        return self.profileStore().load()

    def writeDataJson(self,*args,**kwargs):
        saved=copy.deepcopy(self.data)
        processHotKeys(saved,self.defaultKeys,'write')
        self.profileStore().save(saved)

    def onApplySettings(self,settings):
        candidate=merge(self.data,settings)
        if PLAYER_PANEL_PRO.HP_VISIBILITY in settings:
            candidate[PLAYER_PANEL_PRO.HP_ENABLED]=candidate[PLAYER_PANEL_PRO.HP_VISIBILITY]!='never'
        # The visual editor presents arrays/extra fields as JSON when there is
        # no scalar control; validation happens before publication.
        def decode(value,base):
            if isinstance(base,(dict,list)) and isinstance(value,(str,type(u''))):
                return json.loads(value)
            if isinstance(value,dict) and isinstance(base,dict):
                return dict((k,decode(v,base.get(k))) for k,v in value.items())
            return value
        candidate=decode(candidate,self.data)
        saved=copy.deepcopy(candidate)
        processHotKeys(saved,self.defaultKeys,'write')
        self.profileStore().save(saved)
        self.data.clear(); self.data.update(candidate)

    def getControlColumns(self):
        return player_panel_columns(self)


def player_panel_columns(config):
    """Expose the actual v2 keys; no parallel name/layout configuration."""
    import json
    from Driftkings.settings.settings_data import PROFILES
    columns=[[],[]]
    labels=config.i18n
    def add(path,value,tab,column=None):
        key=path[-1]
        column=(1 if key.endswith('Right') else 0) if column is None else column
        if isinstance(value,dict):
            for child,setting in sorted(value.items()):
                add(path+[child],setting,tab,column)
            return
        title='.'.join(path[1:]) if path[0]==PLAYER_PANEL_PRO.TEMPLATES else key
        item=nested_field(path, labels.get('UI_panel_'+key,title), 'TextInput', tab=tab)
        if key==PLAYER_PANEL_PRO.HP_VISIBILITY:
            choices=['always','hold','never']
            item.update(type='Dropdown',options=[{'label':labels.get('UI_panel_hp_'+mode,fallback)} for mode,fallback in
                        zip(choices,('Always visible','While the key is held','Never visible'))],optionValues=choices)
        elif key==PLAYER_PANEL_PRO.HP_KEY: item['type']='HotKey'
        elif isinstance(value,bool): item['type']='CheckBox'
        elif isinstance(value,(int,float)):
            item.update(type='Slider',minimum=0 if 'Width' in key or 'Alpha' in key else -2000,
                        maximum=100 if 'Alpha' in key else 4000,snapInterval=.01 if isinstance(value,float) else 1,canManualInput=True)
        elif isinstance(value,(list,dict)) or value is None and key not in ('startMode','altMode'):
            item.update(type='TextInput',value=json.dumps(value,ensure_ascii=False),jsonValue=True)
        elif key in ('startMode','altMode'):
            choices=[None]+list(PROFILES)
            item.update(type='Dropdown',options=[{'label':name or 'Cliente'} for name in choices],optionValues=choices)
        elif isinstance(value,(str,type(u''))) and re.match(r'^(?:#|0x)[0-9a-fA-F]{6}$',value):
            item['type']='ColorChoice'
        else: item['type']='TextInput'
        columns[column].append(item)
    general='Geral'
    for key in (PLAYER_PANEL_PRO.STATS_ENABLED,PLAYER_PANEL_PRO.HP_VISIBILITY,PLAYER_PANEL_PRO.HP_KEY,PLAYER_PANEL_PRO.SPOTTED_ENABLED,PLAYER_PANEL_PRO.RATING,PLAYER_PANEL_PRO.COLOR_SCALE):
        add([key],settings_service.getComponentDict(config)[key],general)
    add([PLAYER_PANEL_PRO.PERFORMANCE,'diagnostics'],settings_service.getComponentDict(config)[PLAYER_PANEL_PRO.PERFORMANCE].get('diagnostics',False),general)
    from Driftkings.common import color_tables
    for item in columns[0]:
        if item['varName']==PLAYER_PANEL_PRO.COLOR_SCALE:
            item.update(type='Dropdown',options=[{'label':entry['ScaleColor']} for entry in color_tables])
        elif item['varName']==PLAYER_PANEL_PRO.RATING:
            choices=['wn8','eff','wgr','winrate','xwn8','xeff']
            item.update(type='Dropdown',options=[{'label':name} for name in choices],optionValues=choices)
    for key,value in sorted(settings_service.getComponentDict(config)[PLAYER_PANEL_PRO.PLAYERS_PANEL].items()): add([PLAYER_PANEL_PRO.PLAYERS_PANEL,key],value,general)
    for path,title in (([PLAYER_PANEL_PRO.LOADING],'Loading'),([PLAYER_PANEL_PRO.TAB],'TAB')):
        settings=settings_service.getComponentDict(config)[path[0]]
        for key,value in sorted(settings.items()):
            add(path+[key],value,title)
    for profile in PROFILES:
        for key,value in sorted(settings_service.getComponentDict(config)[PLAYER_PANEL_PRO.PROFILES][profile].items()):
            add([PLAYER_PANEL_PRO.PROFILES,profile,key],value,profile)
    for key,value in sorted(settings_service.getComponentDict(config)[PLAYER_PANEL_PRO.TEMPLATES].items()): add([PLAYER_PANEL_PRO.TEMPLATES,key],value,'Campos comuns')
    return columns
