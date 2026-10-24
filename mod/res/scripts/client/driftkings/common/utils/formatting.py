# -*- coding: utf-8 -*-
"""Small text and colour conversions, independent of the game."""
from colorsys import hsv_to_rgb
import math


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


def hexToDecimal(*args):
    """
    Convert a hexadecimal string to a decimal integer.
    *args: First argument should be a string containing hexadecimal digits.
    int: Decimal representation of the hexadecimal string.
    """
    hex_decimal_conversion = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'A': 10, 'a': 10, 'B': 11, 'b': 11, 'C': 12, 'c': 12, 'D': 13, 'd': 13, 'E': 14, 'e': 14, 'F': 15, 'f': 15
    }
    p = len(args[0]) - 1
    decimal = 0
    for color in args[0]:
        decimal += hex_decimal_conversion[color] * (16 ** p)
        p -= 1
    return decimal


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
