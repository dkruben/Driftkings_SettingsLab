# -*- coding: utf-8 -*-
"""Finite float conversion shared by calculations and presentation."""
import math


def finite_number(value, default=None):
    """Convert to float, preserving the caller's fallback for invalid input."""
    try:
        value = float(value)
        return default if math.isnan(value) or math.isinf(value) else value
    except (ValueError, TypeError, OverflowError):
        return default


def nonnegative_number(value):
    """Finite statistical value; booleans and negative inputs are unavailable."""
    if isinstance(value, bool):
        return None
    value = finite_number(value)
    return value if value is not None and value >= 0 else None
