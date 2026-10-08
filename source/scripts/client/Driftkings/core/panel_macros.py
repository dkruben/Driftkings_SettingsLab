# -*- coding: utf-8 -*-
import math
import re
from xml.sax.saxutils import escape
try:
    text_type = unicode
except NameError:
    text_type = str


def truth(value):
    return value not in (None, False, '', 0, 'false', '0')


def partition(text, separator):
    depth, index = 0, 0
    while index < len(text):
        pair = text[index:index+2]
        if pair == '{{':
            depth += 1
            index += 2
        elif pair == '}}':
            depth -= 1
            index += 2
        elif not depth and text[index] == separator:
            return text[:index], True, text[index+1:]
        else:
            index += 1
    return text, False, ''


class Macros(object):
    def __init__(self, values, config=None, translations=None, dependencies=None):
        self.values = values
        self.config = config or {}
        self.translations = translations or {}
        self.dependencies = dependencies

    def value(self, name):
        if name.startswith('l10n:'):
            return self.translations.get(name[5:], name[5:])
        if name.startswith('.'):
            value=self.config
            for key in name[1:].split('.'):
                value=value.get(key) if isinstance(value,dict) else None
            return value
        if name == 'hp-ratio' or name.startswith('hp-ratio:'):
            if self.dependencies is not None: self.dependencies.update(('hp','hp-max'))
            try:
                width=float(name.partition(':')[2] or 100)
                return int(math.ceil(max(0,min(4000,width))*max(0,min(1,float(self.values['hp'])/self.values['hp-max']))))
            except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
                return None
        if self.dependencies is not None: self.dependencies.add(name)
        return self.values.get(name)

    def condition(self, expression):
        comparison=re.match(r'^([^<>=!]+)(>=|<=|!=|==|>|<|=)(.*)$',expression)
        if not comparison:
            return truth(self.value(expression))
        key,operator,right=comparison.groups()
        left=self.value(key)
        if left is None: return False
        try: left,right=float(left),float(right)
        except (TypeError,ValueError): left,right=text_type(left),right
        if operator in ('=','=='): return left == right
        if operator == '!=': return left != right
        if operator == '>': return left > right
        if operator == '<': return left < right
        if operator == '>=': return left >= right
        return left <= right

    def expression(self, text, depth, html):
        test,conditional,branches=partition(text,'?')
        if conditional:
            yes,_,no=partition(branches,'|')
            return self.render(yes if self.condition(self.render(test,depth+1,False)) else no,depth+1,html)
        body,has_fallback,fallback=partition(text,'|')
        body=self.render(body,depth+1,False)
        body,has_suffix,suffix=partition(body,'~')
        key,has_spec,spec=partition(body,'%')
        value=self.value(key)
        if value is None or value == '':
            return self.render(fallback,depth+1,html) if has_fallback else ''
        if key.startswith('.') and isinstance(value,(str,text_type)) and '{{' in value:
            return self.render(value,depth+1,html)
        if isinstance(value,bool):
            value='true' if value else ''
        try:
            if has_spec:
                if not re.match(r'^[-+0 ]?[0-9]{0,3}(?:\.[0-9]{1,3})?[sdf]$',spec): return ''
                formatted=('%'+spec)%value
                if has_suffix and (not spec.endswith('s') or len(formatted)<len(text_type(value))): formatted+=suffix
            else:
                formatted=text_type(value)+(suffix if has_suffix else '')
            return escape(formatted, {'"':'&quot;', "'":'&apos;'}) if html else formatted
        except (ValueError,TypeError,OverflowError):
            return self.render(fallback,depth+1,html) if has_fallback else ''

    def render(self,text,depth=0,html=True):
        if text is None: return ''
        if not isinstance(text,(str,text_type)): return text_type(text)
        if depth>24: return ''
        result,cursor=[],0
        while cursor<len(text):
            start=text.find('{{',cursor)
            if start<0:
                result.append(text[cursor:]); break
            result.append(text[cursor:start])
            end,nesting=start+2,1
            while end<len(text) and nesting:
                pair=text[end:end+2]
                if pair=='{{': nesting+=1; end+=2
                elif pair=='}}': nesting-=1; end+=2
                else: end+=1
            if nesting:
                result.append(text[start:]); break
            result.append(self.expression(text[start+2:end-2],depth,html))
            cursor=end
        return u''.join(result)

    def resolve(self,value,key=''):
        if isinstance(value,dict): return dict((k,self.resolve(v,k)) for k,v in value.items())
        if isinstance(value,list): return [self.resolve(v,key) for v in value]
        if isinstance(value,(str,text_type)) and '{{' in value:
            rendered=self.render(value,html=key in ('format','text') or 'Format' in key or key.startswith('format'))
            if key.startswith('remove') or key in ('enabled','visible','fixedPosition','darkenNotReadyIcon','bindToIcon','bold','italic','underline','onHold','visibleOnHotKey'):
                return truth(rendered)
            return rendered
        return value
