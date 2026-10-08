# -*- coding: utf-8 -*-
"""Version 2: XVM-shaped JSON, shared references, atomic multi-file saves."""
import copy
import logging
import os

from Driftkings.core.keycodes import valid_key_code
from Driftkings.settings.panel_validation import macro_issues
from Driftkings.settings.settings_data import PROFILES, defaults as component_defaults
from Driftkings.settings.store import merge, JsonDocuments, read_object as read_json

FILES = ('general.json', 'playersPanel.json', 'battleLoading.json', 'statisticForm.json') + tuple('panel%s.json' % name.title() for name in PROFILES)
LEGACY_FILES = ('panelLong.json', 'panelFull.json')
GENERAL = ('schemaVersion', 'enabled', 'statsEnabled', 'colorScale', 'rating', 'performance', 'hpEnabled', 'hpVisibility', 'hpKey', 'spottedEnabled')
try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

def defaults():
    return component_defaults('PlayerPanelPro')

def loading_settings(settings):
    return dict((key,value) for key,value in settings.items() if key!='tips')

def split(data):
    return [dict((key, data[key]) for key in GENERAL),
            dict(playersPanel=data['playersPanel'], templates=data['templates']), loading_settings(data['loading']), data['tab']] + [data['profiles'][name] for name in PROFILES]

def join(parts):
    data = dict(parts[0], **parts[1])
    data.update(loading=loading_settings(parts[2]), tab=parts[3], profiles=dict(zip(PROFILES, parts[4:])))
    return data

def resolve_fields(entries, templates):
    result = []
    if not isinstance(entries, list):
        raise ValueError('extraFields must be an array')
    for entry in entries:
        if isinstance(entry, string_types):
            entry = {'format': entry}
        if not isinstance(entry, dict):
            raise ValueError('Invalid extra field')
        entry = copy.deepcopy(entry)
        reference = entry.pop('ref', None)
        if reference is not None:
            if not isinstance(reference, string_types) or reference not in templates:
                raise ValueError('Unknown field reference: %s' % reference)
            if 'ref' in templates[reference]:
                raise ValueError('Recursive field reference')
            entry = merge(templates[reference], entry)
            entry.setdefault('id', reference)
        for key in ('format','src','id'):
            if entry.get(key) is not None and not isinstance(entry[key],string_types):
                raise ValueError('Invalid field text: '+key)
        for key in ('shadow','textFormat'):
            if entry.get(key) is not None and not isinstance(entry[key],dict):
                raise ValueError('Invalid field style: '+key)
        result.append(entry)
    return result

def validate(data):
    if data.get('schemaVersion') != 2:
        raise ValueError('PlayerPanelPro requires schemaVersion 2')
    if data.get('rating') not in ('wn8', 'eff', 'wgr', 'winrate', 'xwn8', 'xeff'):
        raise ValueError('Invalid rating')
    if type(data.get('colorScale')) is not int or data['colorScale'] < 0:
        raise ValueError('Invalid color scale')
    for key in ('enabled','statsEnabled','hpEnabled','spottedEnabled'):
        if type(data.get(key)) is not bool:
            raise ValueError('Invalid switch: ' + key)
    performance=data['performance']
    if data.get('hpVisibility') not in ('always','hold','never'):
        raise ValueError('general.json: hpVisibility: expected always, hold or never')
    keys=data.get('hpKey')
    if not isinstance(keys,list) or not 1 <= len(keys) <= 4 or any(
            not isinstance(group,list) or not 1 <= len(group) <= 4 or
            any(not valid_key_code(code) for code in group) for group in keys):
        raise ValueError('general.json: hpKey: expected key groups with native key codes 1..326')
    if type(performance.get('diagnostics',False)) is not bool:
        raise ValueError('general.json: performance.diagnostics: expected boolean')
    for key,low,high in (('requestTimeout',1,30),('cacheExpiry',1,86400),('minBattlesToShow',0,100000)):
        if type(performance.get(key)) not in (int,float) or not low <= performance[key] <= high:
            raise ValueError('Invalid performance setting: '+key)
    templates=data.get('templates')
    if not isinstance(templates,dict) or any(not isinstance(v,dict) or 'ref' in v for v in templates.values()):
        raise ValueError('Invalid field templates')
    panel=data['playersPanel']
    for key in ('startMode','altMode'):
        if panel.get(key) not in PROFILES+(None,):
            raise ValueError('Invalid panel mode')
    for name,profile in data['profiles'].items():
        if name not in PROFILES or not isinstance(profile,dict):
            raise ValueError('Invalid panel profile')
        if name != 'none':
            fields=profile.get('standardFields')
            if not isinstance(fields,list) or any(k not in ('frags','badge','nick','vehicle','prestige') for k in fields) or len(set(fields)) != len(fields):
                raise ValueError('Invalid standardFields')
            if not isinstance(profile.get('nickMinWidth'),string_types) and not isinstance(profile.get('nickMaxWidth'),string_types) and profile['nickMinWidth'] > profile['nickMaxWidth']:
                raise ValueError('nickMinWidth exceeds nickMaxWidth')
        elif profile.get('layout') not in ('vertical','horizontal'):
            raise ValueError('Invalid hidden panel layout')
    warnings=[]
    def walk(value,key='',path=''):
        if isinstance(value,dict):
            if 'ref' in value:
                try: resolve_fields([value],templates)
                except ValueError as error: raise ValueError(path+': '+str(error))
            for k,v in value.items(): walk(v,k,path+'.'+k)
        elif isinstance(value,list):
            for index,v in enumerate(value): walk(v,key,path+'[%d]'%index)
        elif key.endswith(('Alpha','alpha')):
            numeric=value
            if isinstance(value,string_types) and '{{' not in value:
                try: numeric=float(value)
                except ValueError: raise ValueError(path+': Invalid opacity')
            if not isinstance(numeric,string_types) and (type(numeric) not in (int,float) or not 0 <= numeric <= 100):
                raise ValueError(path+': Invalid opacity')
        elif ('Width' in key or 'Offset' in key or key in ('x','y','width','height')) and value is not None:
            numeric=value
            if isinstance(value,string_types) and '{{' not in value:
                try: numeric=float(value)
                except ValueError: raise ValueError(path+': Invalid field geometry')
            if not isinstance(numeric,string_types) and (type(numeric) not in (int,float) or not (0 if ('Width' in key and 'WidthDelta' not in key) or key in ('width','height') else -2000) <= numeric <= 4000):
                raise ValueError(path+': Invalid field geometry')
        if isinstance(value,string_types) and ('{{' in value or '}}' in value):
            warnings.extend(path+': '+issue for issue in macro_issues(value,data))
    for filename,part in zip(FILES,split(data)): walk(part,path=filename+':')
    for screen in [data['loading'],data['tab']] + list(data['profiles'].values()):
        if type(screen.get('enabled',True)) is not bool:
            raise ValueError('Invalid screen switch')
        for side in ('Left','Right'):
            resolve_fields(screen.get('extraFields'+side,[]),templates)
    for side in ('leftPanel','rightPanel'):
        resolve_fields(data['profiles']['none']['extraFields'][side]['formats'],templates)
    return warnings

class PlayerPanelStore(JsonDocuments):
    def __init__(self, directory, legacy_root=None):
        super(PlayerPanelStore, self).__init__(directory, FILES + LEGACY_FILES)

    def load(self):
        self.recover()
        initial=defaults()
        general=os.path.join(self.directory,FILES[0])
        # Old geometry used different semantics. Preserve it for reference, then
        # start the explicitly requested new implementation with coherent defaults.
        old=os.path.isfile(general) and read_json(general).get('schemaVersion') != 2
        if old:
            for name in FILES:
                path=os.path.join(self.directory,name)
                if os.path.isfile(path) and not os.path.isfile(path+'.v1'):
                    with open(path,'rb') as source, open(path+'.v1','wb') as backup:
                        backup.write(source.read())
            previous=read_json(general)
            for key in ('rating','colorScale','statsEnabled','performance'):
                if key in previous: initial[key]=previous[key]
        parts=[]
        obsolete_loading=False
        for name,default in zip(FILES,split(initial)):
            path=os.path.join(self.directory,name)
            saved=read_json(path) if not old and os.path.isfile(path) else {}
            if name=='general.json' and 'hpVisibility' not in saved and saved.get('hpEnabled') is False:
                saved['hpVisibility']='never'
            if name=='battleLoading.json': obsolete_loading='tips' in saved
            parts.append(merge(default,saved))
        data=join(parts)
        for message in validate(data): logging.getLogger('Driftkings.PlayerPanelPro').warning('Configuration: %s',message)
        missing=[(os.path.join(self.directory,name),value) for name,value in zip(FILES,split(data)) if old or not os.path.isfile(os.path.join(self.directory,name)) or name=='battleLoading.json' and obsolete_loading]
        self.publish(missing)
        return data

    def save(self,data):
        data=join(split(data))
        for message in validate(data): logging.getLogger('Driftkings.PlayerPanelPro').warning('Configuration: %s',message)
        self.recover()
        self.publish([(os.path.join(self.directory,name),value) for name,value in zip(FILES,split(data))])
