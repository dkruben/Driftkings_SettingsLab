# -*- coding: utf-8 -*-
"""Tomato.gg percentile/HSL interpolation using its bundled 100-point reference."""
import colorsys
import math


def color(bands, gradient, value):
    position = 1.0
    if value >= bands[-1]['value']:
        position = float(len(bands))
    elif value > bands[0]['value']:
        for index in range(len(bands) - 1):
            lo, hi = bands[index]['value'], bands[index + 1]['value']
            if lo <= value < hi:
                position = index + 1 + (value - lo) / float(hi - lo)
                break
    index = min(len(gradient) - 1, int(math.floor(position)) - 1)
    fraction = position - (index + 1)
    lo, hi = gradient[index], gradient[min(index + 1, len(gradient) - 1)]
    h, s, l = [a + (b - a) * fraction for a, b in zip(lo, hi)]
    h = math.floor(h * 100 + .5) / 100.0
    s = math.floor(s * 100 + .5) / 100.0
    l = math.floor(l * 100 + .5) / 100.0
    return '#' + ''.join('%02X' % int(math.floor(channel * 255 + .5))
                          for channel in colorsys.hls_to_rgb(h / 360.0, l, s))
