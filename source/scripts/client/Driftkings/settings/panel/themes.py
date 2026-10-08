# -*- coding: utf-8 -*-
"""Validated theme values; preview lives only in the editing session."""
THEMES = {
    'wot': {'background': '#101113', 'textColor': '#E8E4DA', 'secondary': '#B3AE9F', 'border': '#4A463E', 'hover': '#39352B'},
    'dark': {'background': '#191C22', 'textColor': '#E6E9EF', 'secondary': '#9BA4B4', 'border': '#424A58', 'hover': '#2A3342'},
    'black': {'background': '#000000', 'textColor': '#FFFFFF', 'secondary': '#AAAAAA', 'border': '#333333', 'hover': '#202020'},
    'transparent': {'background': '#101113', 'textColor': '#FFFFFF', 'secondary': '#CECABE', 'border': '#6B6254', 'hover': '#3F382D'},
}


def describe(values):
    result = dict(values)
    result.update(THEMES.get(values.get('theme'), {}))
    if values.get('theme') == 'transparent':
        result['opacity'] = min(result.get('opacity', 96), 75)
    return result
