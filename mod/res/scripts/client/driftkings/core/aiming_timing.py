# -*- coding: utf-8 -*-
"""Numerical aiming/flight timing, independent of either presentation technology."""
from math import ceil, log


def dispersion_timing(minimum, angle, aiming_time):
    minimum = min(minimum, angle)
    ratio = minimum / angle
    return minimum, int(ceil(ratio * 100)), round(aiming_time * abs(log(ratio)), 2)


def flight_time(distance, horizontal_speed):
    return distance / horizontal_speed
