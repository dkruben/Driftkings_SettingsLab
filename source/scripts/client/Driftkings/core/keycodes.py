# -*- coding: utf-8 -*-
"""Native BigWorld key codes, shared by configuration validators."""
try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)

# Keys.py includes keyboard, mouse (256..263), joystick and LCD keys.
MAX_KEY_CODE = 326


def valid_key_code(code):
    return isinstance(code, integer_types) and not isinstance(code, bool) and 1 <= code <= MAX_KEY_CODE
