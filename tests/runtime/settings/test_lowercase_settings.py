import os
import tempfile
import shutil
from support import RuntimeTest


class LowercaseSettingsTests(RuntimeTest):
    def test_old_json_spelling_is_read_without_resetting_its_contents(self):
        api = self.load('common.utils.filesystem')
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        old = os.path.join(folder, 'panelLarge.json')
        current = os.path.join(folder, 'panellarge.json')
        data = b'{"enabled":false,"format":"{{v.WinRate}}"}'
        with open(old, 'wb') as stream:
            stream.write(data)
        api.recover_file(current)
        with open(current, 'rb') as stream:
            self.assertEqual(stream.read(), data)
        self.assertEqual(len(os.listdir(folder)), 1)
