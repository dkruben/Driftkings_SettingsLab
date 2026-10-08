import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('updates', Path(__file__).resolve().parents[1] / 'check_tool_updates.py')
updates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updates)


class UpdateCheckTests(unittest.TestCase):
    def test_numeric_version_order(self):
        self.assertEqual(updates.compare_versions('v1.9.0', 'v1.10.0'), 'ATUALIZACAO DISPONIVEL')
        self.assertEqual(updates.compare_versions('1.8', 'v1.8.0'), 'MESMA VERSAO')
        self.assertEqual(updates.compare_versions('1.9.0', 'v1.8.0'), 'LOCAL MAIS RECENTE')

    def test_releases_ignore_prerelease_and_upcoming(self):
        release = updates.latest_release([
            {'tag_name': 'v2.0.0-rc1'}, {'tag_name': 'v2.0.0', 'upcoming_release': True},
            {'tag_name': 'v1.9.0'}, {'tag_name': 'v1.10.0'},
        ])
        self.assertEqual(release['tag_name'], 'v1.10.0')

    def test_empty_releases_do_not_report_current(self):
        with self.assertRaises(ValueError):
            updates.latest_release([])

    def test_failure_is_isolated(self):
        def fail():
            raise TimeoutError('timeout')
        result = updates.safely_check('ModList', fail)
        self.assertEqual(result['status'], 'ERRO')
        self.assertEqual(result['error'], 'timeout')

    def test_partial_mod_extraction_not_reported_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ModList' / 'mods-list-v1.8.0').mkdir(parents=True)
            with patch.object(updates, 'request_json', return_value=[{'tag_name': 'v1.8.0'}]):
                result = updates.check_mod(root, 5, *updates.MODS[0])
            self.assertEqual(result['status'], 'LOCAL INCOMPLETO')

    def test_wot_archive_does_not_claim_commit_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / 'wot-src-EU' / 'sources'
            sources.mkdir(parents=True)
            (sources.parent / '.version_name').write_text('2.4.0.5473', encoding='utf-8')
            xml = '<version.xml><version>v.2.4.0.2 #966</version></version.xml>'
            (sources / 'version.xml').write_text(xml, encoding='utf-8')
            branch = {'commit': {'sha': 'abc', 'commit': {'committer': {'date': '2026-10-02'}}}}
            with patch.object(updates, 'request_json', return_value=branch), \
                    patch.object(updates, 'request_text', side_effect=['2.4.0.5473', xml]):
                result = updates.check_wot(root, 5)
            self.assertEqual(result['status'], 'MESMA VERSAO')
            self.assertIsNone(result['local_commit'])
            self.assertTrue(any('sem Git' in note for note in result['notes']))


if __name__ == '__main__':
    unittest.main()
