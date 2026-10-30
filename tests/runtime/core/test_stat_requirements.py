# -*- coding: utf-8 -*-
"""Recursive statistic detection preserves the former JSON-search semantics."""
import copy
import json
import os

from support import ROOT, RuntimeTest


class StatisticRequirementTests(RuntimeTest):
    def setUp(self):
        super(StatisticRequirementTests, self).setUp()
        self.uses_tdv = self.load('core.panel_macros').uses_tdv

    def test_nested_templates_keys_and_escaped_tabs_match_legacy_search(self):
        values = ('{{tdv}}', '{{v.tdv%d}}', '\tdv', 'TDV', 'damage', u'Ol\u00e1 {{tdv}}', '', None, False, 123)
        for value in values:
            for document in (value, {'field': value}, {'fields': [{'format': value}]}, (None, [value])):
                self.assertEqual(self.uses_tdv(document), 'tdv' in json.dumps(document), repr(document))
        for document in ({'tdv': None}, {'prefix-tdv': {'enabled': False}}, {'fields': [{'label': '\tdv'}]},
                         {'t': 'dv'}, {'TDV': 'tDv'}):
            self.assertEqual(self.uses_tdv(document), 'tdv' in json.dumps(document), repr(document))

    def test_all_canonical_default_documents_preserve_detection_and_values(self):
        folder = os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default')
        checked = 0
        for directory, _, names in os.walk(folder):
            for name in names:
                if name.endswith('.json'):
                    with open(os.path.join(directory, name), 'rb') as stream:
                        document = json.loads(stream.read().decode('utf-8-sig'))
                    previous = copy.deepcopy(document)
                    self.assertEqual(self.uses_tdv(document), 'tdv' in json.dumps(document), name)
                    self.assertEqual(document, previous, name)
                    checked += 1
        self.assertGreater(checked, 0)
