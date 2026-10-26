# -*- coding: utf-8 -*-
"""Type aliases shared by the Python 2 game client and the Python 3 tools and tests."""
try:
    string_types = (basestring,)  # noqa: F821 - Python 2 client
    text_type = unicode  # noqa: F821
    integer_types = (int, long)  # noqa: F821
except NameError:
    string_types = (str,)
    text_type = str
    integer_types = (int,)

number_types = integer_types + (float,)
