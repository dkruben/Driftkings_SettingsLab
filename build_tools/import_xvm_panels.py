"""Developer-only import of the local WG XVM defaults; no XC runtime dependency."""
import argparse
import ast
import copy
import json
import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"clanIcon", "xvmUserMarker", "xmqpServiceMarker"}

def uncomment(text):
    return re.sub(r'("(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/)',
                  lambda m: m[0] if m[0].startswith('"') else '', text, flags=re.S)

def read_xc(path):
    text = uncomment(path.read_text(encoding='utf-8-sig'))
    text = re.sub(r'\$\{"([^"}]+)"\}', lambda m: json.dumps({'ref': m[1].split('.')[-1]}), text)
    return json.loads(text)

def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k,v in value.items() if k not in EXCLUDED}
    if isinstance(value, list):
        return [clean(v) for v in value if not isinstance(v, dict) or v.get('ref') not in EXCLUDED]
    if isinstance(value, str):
        value = re.sub(r"<img[^>]+(?:xvm-user|icons/flags)[^>]*> ?", '', value)
        return value.replace("face='mono'", "face='$FieldFont'").replace("face='xvm'", "face='$FieldFont'").replace('&#x11E;', '*')
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('xvm', type=Path)
    args=parser.parse_args()
    base=args.xvm/'release/configs/default_wg'
    sources={name: clean(read_xc(base/(name+'.xc'))) for name in ('playersPanel','battleLoading','statisticForm')}
    panel=sources['playersPanel']['playersPanel']
    profiles={name:panel.pop(name) for name in ('none','short','medium','medium2','large')}
    templates=sources['playersPanel']['def']
    templates['enemySpottedMarker']['format']="{{spotted? <img src='img://gui/maps/Driftkings/PlayerPanelPro/spotted/dot-{{spotted}}.png' width='8' height='8' vspace='5'>}}"
    path=ROOT/'source/scripts/client/Driftkings/settings/settings_data.py'
    text=path.read_text(encoding='utf-8-sig')
    tree=ast.parse(text)
    assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFAULTS' for t in n.targets))
    node=next(v for k,v in zip(assignment.value.keys,assignment.value.values) if k.value=='PlayerPanelPro')
    old=ast.literal_eval(node)
    general={k:old[k] for k in ('enabled','statsEnabled','colorScale','rating','performance','hpEnabled','spottedEnabled')}
    general['schemaVersion']=2
    loading=sources['battleLoading']['battleLoading']
    tab=sources['statisticForm']['statisticForm']
    for screen in (panel,loading,tab):
        screen.update(enabled=True,showUnavailable=True)
    # Native badges remain visible; their XVM replacement templates are unnecessary.
    tab['removeRankBadgeIcon']=False
    tab['extraFieldsLeft']=tab['extraFieldsRight']=[]
    data=dict(general,playersPanel=panel,profiles=profiles,templates=templates,loading=loading,tab=tab)
    lines=text.splitlines(True)
    start=sum(map(len,lines[:node.lineno-1]))+node.col_offset
    end=sum(map(len,lines[:node.end_lineno-1]))+node.end_col_offset
    text=text[:start]+pprint.pformat(data,width=110,sort_dicts=False)+text[end:]
    text=re.sub(r'# Resolve the shared panel definitions once;.*?\n\n\nHOTKEYS', 'HOTKEYS', text, flags=re.S)
    text=text.replace('from Driftkings.settings.player_panel_formats import decode_profile\n','')
    path.write_text(text,encoding='utf-8')
    target=ROOT/'res/configs/Driftkings/default/player_panel_pro'
    parts={'general.json':general,'playersPanel.json':{'playersPanel':panel,'templates':templates},'battleLoading.json':loading,'statisticForm.json':tab}
    parts.update(('panel'+name.title()+'.json',value) for name,value in profiles.items())
    for name,value in parts.items():
        (target/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Imported WG defaults: %d JSON documents' % len(parts))

if __name__=='__main__': main()
