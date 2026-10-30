# -*- coding: utf-8 -*-
"""Preserve conversion and fallback contracts across shared numeric consumers."""
import math
from support import RuntimeTest


class NumbersTests(RuntimeTest):
    def setUp(self):
        super(NumbersTests, self).setUp()
        self.convert = self.load('common.utils.numbers').finite_number

    def test_finite_values_convert_to_float(self):
        for value, expected in ((0, 0.0), (-4, -4.0), (2.5, 2.5), ('12.5', 12.5),
                                (u' -3 ', -3.0), (True, 1.0), (False, 0.0)):
            result = self.convert(value)
            self.assertEqual(result, expected)
            self.assertIsInstance(result, float)
        self.assertEqual(math.copysign(1, self.convert(-0.0)), -1)

    def test_invalid_values_preserve_the_exact_fallback(self):
        class Overflow(object):
            def __float__(self):
                raise OverflowError('too large')
        marker = object()
        for value in (None, '', 'bad', [], {}, float('nan'), float('inf'),
                      float('-inf'), 10 ** 400, Overflow()):
            self.assertIsNone(self.convert(value))
            self.assertIs(self.convert(value, marker), marker)
            self.assertEqual(self.convert(value, 0.0), 0.0)

    def test_consumer_names_and_defaults_remain_compatible(self):
        marks = self.load('core.marks_calculator')
        view = self.load('views.marks_model')
        self.assertEqual(marks.safe_number('bad'), 0.0)
        self.assertIsNone(view.finite('bad'))
        self.assertIs(view.finite, self.convert)
        self.assertEqual(marks.safe_number('bad', -1), -1)
        self.assertEqual(view.finite('bad', -1), -1)

    def test_statistical_numbers_reject_booleans_and_keep_public_aliases(self):
        convert = self.load('common.utils.numbers').nonnegative_number
        self.assertIs(self.load('core.wnx').number, convert)
        self.assertIs(self.load('core.vehicle_markers.ratings').numeric, convert)
        for value in (True, False, -1, '-2', None, 'bad', [], 10 ** 400,
                      float('nan'), float('inf'), float('-inf')):
            self.assertIsNone(convert(value))
        for value, expected in ((0, 0.0), ('12.5', 12.5), (2.5, 2.5)):
            self.assertEqual(convert(value), expected)
            self.assertIsInstance(convert(value), float)
        self.assertEqual(math.copysign(1, convert(-0.0)), -1)
