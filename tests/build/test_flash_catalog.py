"""Generated Flash catalog identities and unchanged shared generator outputs."""
import re
import unittest

from build_tools import generate_ui_catalog as catalog


class FlashCatalogTests(unittest.TestCase):
    def test_catalog_class_maps_and_case_sensitive_output(self):
        data = catalog.read_catalog()['FLASH_COMPONENTS']
        output = catalog.outputs()
        self.assertTrue(catalog.AS3.endswith('/ComponentCatalog.as'))
        folder = catalog.ROOT / catalog.AS3
        self.assertIn('ComponentCatalog.as', [path.name for path in folder.parent.iterdir()])
        self.assertNotIn('componentcatalog.as', [path.name for path in folder.parent.iterdir()])
        text = output[catalog.AS3]
        self.assertEqual(folder.read_text(encoding='utf-8'), text)
        self.assertIn('public class ComponentCatalog', text)
        self.assertIn('public static function classes(surface:String):Object', text)
        self.assertNotIn('function ComponentCatalog(', text)
        self.assertEqual(re.findall(r'import ([\w.]+);', text), sorted({spec['as3'] for spec in data.values()}))
        for surface in ('battle', 'ratings'):
            block = text.split('if (surface == "' + surface + '") return {', 1)[1].split('};', 1)[0]
            expected = [(alias, spec['as3'].rsplit('.', 1)[1]) for alias, spec in sorted(data.items())
                        if surface in spec['surfaces']]
            self.assertEqual(re.findall(r'(\w+):(\w+)', block), expected)
        self.assertEqual(len(data), 7)

    def test_only_as3_output_identity_changes_and_shared_outputs_are_current(self):
        output = catalog.outputs()
        self.assertEqual(output, catalog.outputs())
        self.assertEqual(len(output), 4)
        self.assertFalse(any(path.endswith('/componentcatalog.as') for path in output))
        for path, content in output.items():
            if path != catalog.AS3:
                self.assertEqual((catalog.ROOT / path).read_text(encoding='utf-8'), content, path)


if __name__ == '__main__':
    unittest.main()
