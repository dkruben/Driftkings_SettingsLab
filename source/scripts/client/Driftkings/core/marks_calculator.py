# -*- coding: utf-8 -*-
"""Only arithmetic proven identical in the existing Battle/Hangar paths."""
import math


def ceil_damage(value):
    return int(math.ceil(value))


def ceil_damage_tens(value):
    return int(math.ceil(math.ceil(value / 10.0)) * 10)


def combined_damage(damage, *assists):
    return damage + max(assists)
