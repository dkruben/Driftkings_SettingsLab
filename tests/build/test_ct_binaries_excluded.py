# -*- coding: utf-8 -*-
"""The eight tracked CT SWC binaries never enter a production distribution plan (K7, conditional acceptance)."""
import unittest
from pathlib import Path

from build_tools.validate_build_data import ROOT, build_plan

CT_SWC_NAMES = {
    'base_app-1.0-snapshot.swc', 'battle.swc', 'common-1.0-snapshot.swc', 'common_i18n_library-1.0-snapshot.swc',
    'gui_base-1.0-snapshot.swc', 'gui_battle-1.0-snapshot.swc', 'gui_lobby-1.0-snapshot.swc', 'lobby.swc',
}
SEPARATOR = chr(92)


def normal(value):
    return value.replace(SEPARATOR, '/')


class CtBinariesExcludedTests(unittest.TestCase):
    def test_tracked_ct_swc_binaries_are_preserved_not_deleted(self):
        # Conditional acceptance: the files stay in the repository until redistribution rights are clarified.
        present = {p.name for p in (Path(ROOT) / 'flash_source/shared/swc').glob('*.swc')}
        self.assertTrue(CT_SWC_NAMES <= present)

    def test_production_plan_never_packages_a_ct_swc(self):
        plan = build_plan(ROOT)
        entries = []
        for value in plan.values():
            if isinstance(value, list):
                entries.extend(value)
        for item in entries:
            values = [item.get(key) for key in ('source', 'target', 'path')] if isinstance(item, dict) else [item]
            for value in values:
                if not isinstance(value, str):
                    continue
                path = normal(value)
                self.assertNotIn(path.rsplit('/', 1)[-1], CT_SWC_NAMES, value)


if __name__ == '__main__':
    unittest.main()
