# -*- coding: utf-8 -*-
import math

__all__ = ('color_tables', 'getRatingColors', 'getColor', 'getStatisticColor',
           'getRatingPaletteColor', 'getComparisonColor', 'getMoeDamageColor', 'getRelativePerformanceColor')


# color_tables stays importable from here for the settings definitions (checked by tests/core/test_colors.py).
from driftkings.common.utils.color_rating_data import color_tables, MOE_LEVELS
from driftkings.core.tomato_colors import color as gradient_color


def getRatingColors(index=0):
    """Return a configured palette, falling back to NoobMeter for invalid settings."""
    try:
        index = int(index)
    except (TypeError, ValueError, OverflowError):
        index = 0
    if not 0 <= index < len(color_tables):
        index = 0
    return color_tables[index]['colors']


def getColor(data, ratting_color, value=None, kwargs=None):
    """
    Get a color based on a rating value from a color configuration.
    data (dict): Color configuration data.
    ratting_color (str): Rating category key.
    value (float, optional): Value to compare against thresholds. Defaults to None.
    kwargs (float, optional): Alternative value for 'x' category. Defaults to None.
    str: Color in hex format or None if not found.
    """
    aliases = {'xwn8': 'x', 'xeff': 'x', 'xte': 'x', 'dmg': 'tdb',
               'winRate': 'winrate', 't_winrate': 'winrate', 'hitRate': 'hitsRatio',
               'avgDamage': 'tdb', 'avgFrags': 'tfb', 'avgSpotted': 'tsb',
               'marks': 'mog', 'battles': 'kb'}
    category = ratting_color if ratting_color in data else aliases.get(ratting_color, ratting_color)
    if category == 'wnx' and 'wnx' not in data:
        category = 'wn8'  # Existing palettes reuse their own rating bands for WNX.
    if value is None and kwargs is not None:
        category, value = 'x', kwargs
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    if ratting_color == 'battles' and category == 'kb':
        value /= 1000.0
    bands = data.get(category)
    if not isinstance(bands, (list, tuple)) or not bands:
        return None
    gradient = data.get('gradient', {})
    if category in gradient.get('metrics', ()):
        return gradient_color(bands, gradient['hsl'], value)
    if category == 'diff':
        return formatColor(bands[0 if value < 0 else 2 if value > 0 else 1]['color'])
    if category == 'mog':
        for item in reversed(bands):
            if value >= item['value']:
                return formatColor(item['color'])
        return formatColor(bands[0]['color'])
    for item in bands:
        if value < item['value']:
            return formatColor(item['color'])
    # The last source limit is a sentinel, not a reason to lose the rating color.
    return formatColor(bands[-1]['color'])


def formatColor(color):
    """
    Format a color string to a standard hex format.
    color (str): Color string, possibly starting with '0x'.
    str: Color in standard hex format (#RRGGBB).
    """
    return '#' + color[2:] if color.startswith('0x') else color


def getRatingPaletteColor(name, index=0):
    """Resolve named statistical colors and missing-data colors centrally."""
    palette = getRatingColors(index)['colorRating']
    name = {'super_unique': 's_unique', 'not_available': 'nocolor'}.get(name, name)
    if name == 's_unique':
        return palette.get(name, palette['unique'])
    return palette.get(name, palette.get('nocolor', '#CCCCCC'))


def getStatisticColor(metric, value, index=0):
    """Public mod API: always returns a valid color, including missing statistics."""
    return getColor(getRatingColors(index), metric, value) or getRatingPaletteColor('nocolor', index)


def getComparisonColor(value, reference, index=0):
    """Color a statistical comparison using the selected palette."""
    try:
        difference = float(value) - float(reference)
    except (TypeError, ValueError, OverflowError):
        difference = None
    return getStatisticColor('diff', difference, index)


def getRelativePerformanceColor(value, reference, index=0):
    """Compare against a positive expected value using the Driftkings ratio scale."""
    ratio = None
    try:
        reference = float(reference)
        if reference > 0 and not math.isinf(reference):
            ratio = float(value) / reference
    except (TypeError, ValueError, OverflowError):
        pass  # Missing or invalid statistics use the palette's no-data colour.
    return getStatisticColor('relativePerformance', ratio, index)


def getMoeDamageColor(damage, targets, index=0):
    """Color damage against the seven calculated MoE targets (20 through 100)."""
    try:
        damage = float(damage)
    except (TypeError, ValueError, OverflowError):
        return getRatingPaletteColor('nocolor', index)
    if math.isnan(damage) or math.isinf(damage) or len(targets) != 7:
        return getRatingPaletteColor('nocolor', index)
    for percent, target in zip(MOE_LEVELS[1:], targets):
        if damage <= target:
            return getStatisticColor('mog', percent, index)
    return getStatisticColor('mog', 100, index)
