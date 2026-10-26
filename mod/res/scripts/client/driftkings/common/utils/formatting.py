# -*- coding: utf-8 -*-
"""Small text and colour conversions, independent of the game."""
from colorsys import hsv_to_rgb
import math
import re

from driftkings.common.utils.compat import string_types


def percentToRgb(percent, saturation=0.5, brightness=1.0, **__):
    """
    Convert a percentage value to an RGB color.
    percent (float): Percentage value between 0.0 and 1.0.
    saturation (float, optional): Color saturation. Defaults to 0.5.
    brightness (float, optional): Color brightness. Defaults to 1.0.
    **__: Additional unused keyword arguments.
    str: RGB color in hex format (#RRGGBB).
    """
    position = min(0.8333, percent * 0.3333)
    r, g, b = (int(math.ceil(i * 255)) for i in hsv_to_rgb(position, saturation, brightness))
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)


def hexToDecimal(value):
    """Convert a #RRGGBB setting to the numeric colour required by native APIs."""
    if not isinstance(value, string_types) or not re.match(r'^#[0-9A-Fa-f]{6}\Z', value):
        raise ValueError('Expected #RRGGBB')
    return int(value[1:], 16)


def replaceMacros(text_format, data):
    """
    Replace macros in a text format with their corresponding values.
    text_format (str): Text containing macros to be replaced.
    data (dict): Dictionary of macro-value pairs.
    str: Text with macros replaced by their values.
    """
    for macro, value in data.items():
        text_format = text_format.replace(macro, value)
    return text_format
