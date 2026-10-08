# -*- coding: utf-8 -*-
"""Static macro diagnostics; unknown data is reported, never evaluated as code."""
import re

from Driftkings.core.panel_macros import partition

KNOWN=set(('name nick clan clannb veh-id vehicle vehicle-short vehiclename level rlevel vtype vtype-key vtype-l nation '
           'premium special alive ally player anonym ready hp hp-max spotted c:spotted a:spotted c:system sys-color-key '
           'xvm-stat pp.mode pp.widthLeft pp.widthRight squad-num rankBadgeId bp-stage tk squad selected friend ignored '
           'muted chatban hasBadges r xr r_size kb t-kb t-hb frags region battletype-key wins battles winrate wn8 eff wgr '
           'xwn8 xeff xwgr xwr tdv tdb tfb tsb t-battles t-winrate t-wins').split())

def macro_issues(text,config):
    issues=[]
    stack=[]
    expressions=[]
    for match in re.finditer(r'\{\{|\}\}',text):
        if match.group()=='{{': stack.append(match.end())
        elif stack: expressions.append(text[stack.pop():match.start()])
        else: issues.append('Unexpected }}')
    if stack: issues.append('Unclosed {{ macro')
    for expression in expressions:
        key,conditional,_=partition(expression,'?')
        if conditional: key=re.split(r'[<>=!]',key,maxsplit=1)[0]
        else:
            key=partition(partition(partition(key,'|')[0],'~')[0],'%')[0]
        if '{{' in key: continue  # Dynamic macro names are checked at runtime.
        if key.startswith('.'):
            value=config
            for part in key[1:].split('.'):
                if not isinstance(value,dict) or part not in value:
                    issues.append('Unknown configuration reference: '+key); break
                value=value[part]
            continue
        if key.startswith('l10n:'): continue
        if key=='hp-ratio' or key.startswith('hp-ratio:'): continue
        if key.startswith('my-'): key=key[3:]
        if key in KNOWN: continue
        if key.startswith(('c:','a:')) and key[2:] in KNOWN: continue
        issues.append('Unknown macro: '+key)
    return sorted(set(issues))
