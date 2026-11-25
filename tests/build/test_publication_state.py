# -*- coding: utf-8 -*-
"""Publication is an explicit chain of independent facts; a signature alone never publishes."""
import binascii
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import publication_state as state
from build_tools import publish_release
from build_tools import validation_record
from build_tools.sign_release import sign_folder

PRODUCTION = dict(status='success', mode='release', profile=state.PRODUCTION_PROFILE, realm='NA',
                  version='0.1.7-beta.2', publishable=False)
CT_DEBUG = dict(status='success', mode='debug', profile=state.DEVELOPMENT_PROFILE, realm='CT',
                version='0.1.7-beta.2', publishable=False)
CT_RELEASE = dict(PRODUCTION, mode='release', profile=state.DEVELOPMENT_PROFILE, realm='CT')

REGIONAL_MISSING = ValueError('Each global distribution realm requires runtime or source evidence')
NOT_APPROVED = ValueError('Record decision is PENDING; Record has no approver')
FULLY_EVALUATED = lambda text, version: {'version': version}  # noqa: E731


class PublicationStateTests(unittest.TestCase):
    def test_ct_debug_build_is_never_eligible_or_publishable(self):
        self.assertEqual(state.classify(CT_DEBUG), state.NOT_ELIGIBLE)
        self.assertEqual(state.classify(CT_DEBUG, signed=True, validation_ok=True, approved=True), state.NOT_ELIGIBLE)

    def test_ct_release_build_is_not_eligible_for_signing(self):
        self.assertEqual(state.classify(CT_RELEASE, signed=True, validation_ok=True, approved=True), state.NOT_ELIGIBLE)
        self.assertFalse(state.eligible_for_signing(CT_RELEASE))

    def test_unsigned_production_build_is_eligible_but_not_publishable(self):
        self.assertTrue(state.eligible_for_signing(PRODUCTION))
        self.assertEqual(state.classify(PRODUCTION), state.ELIGIBLE_UNSIGNED)
        self.assertFalse(PRODUCTION['publishable'])

    def test_signed_but_unvalidated_candidate_is_not_publishable(self):
        self.assertEqual(state.classify(PRODUCTION, signed=True), state.SIGNED_UNVALIDATED)
        self.assertEqual(state.classify(PRODUCTION, signed=True, validation_ok=False, approved=True),
                         state.SIGNED_UNVALIDATED)

    def test_missing_regional_evidence_blocks_validation(self):
        def evaluate(text, version):
            raise REGIONAL_MISSING
        ok, approved, problems = state.validation_facts('record', '0.1.7-beta.2', evaluate)
        self.assertFalse(ok)
        self.assertFalse(approved)
        self.assertEqual(state.classify(PRODUCTION, True, ok, approved), state.SIGNED_UNVALIDATED)
        self.assertTrue(problems)

    def test_missing_approval_keeps_validated_candidate_unpublishable(self):
        def evaluate(text, version):
            raise NOT_APPROVED
        ok, approved, _ = state.validation_facts('record', '0.1.7-beta.2', evaluate)
        self.assertTrue(ok)
        self.assertFalse(approved)
        self.assertEqual(state.classify(PRODUCTION, True, ok, approved), state.VALIDATED_NOT_APPROVED)

    def test_fully_authorized_release_is_publishable(self):
        ok, approved, problems = state.validation_facts('record', '0.1.7-beta.2', FULLY_EVALUATED)
        self.assertEqual((ok, approved, problems), (True, True, []))
        self.assertEqual(state.classify(PRODUCTION, True, ok, approved), state.PUBLISHABLE)
        self.assertEqual(state.require_publishable(PRODUCTION, True, ok, approved), state.PUBLISHABLE)

    def test_publication_requires_every_fact(self):
        for kwargs in (dict(signed=False, validation_ok=True, approved=True),
                       dict(signed=True, validation_ok=False, approved=True),
                       dict(signed=True, validation_ok=True, approved=False)):
            with self.assertRaises(ValueError):
                state.require_publishable(PRODUCTION, **kwargs)
        with self.assertRaises(ValueError):
            state.require_publishable(CT_RELEASE, True, True, True)

    def test_blank_validation_record_is_neither_validated_nor_approved(self):
        text = validation_record.render()
        ok, approved, problems = state.validation_facts(text, '0.1.7-beta.2', validation_record.evaluate)
        self.assertFalse(ok)
        self.assertFalse(approved)
        self.assertTrue(problems)


class SigningEligibilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.key = self.folder.parent / (self.folder.name + '.key')
        self.addCleanup(lambda: self.key.exists() and self.key.unlink())
        self.key.write_text(binascii.hexlify(os.urandom(32)).decode('ascii'))
        (self.folder / 'release.json').write_text(json.dumps(dict(version='0.1.7-beta.2')), encoding='utf-8')

    def write_report(self, report):
        (self.folder / 'build-report.json').write_text(json.dumps(report), encoding='utf-8')

    def test_production_report_can_be_signed_and_stays_unpublishable(self):
        self.write_report(dict(PRODUCTION))
        output, _ = sign_folder(self.folder, self.key)
        self.assertTrue(output.is_file())
        report = json.loads((self.folder / 'build-report.json').read_text(encoding='utf-8'))
        self.assertFalse(report['publishable'])
        self.assertEqual(state.classify(report, signed=True), state.SIGNED_UNVALIDATED)

    def test_ct_debug_report_is_refused_before_any_signature(self):
        self.write_report(dict(CT_DEBUG))
        with self.assertRaises(ValueError):
            sign_folder(self.folder, self.key)
        self.assertFalse((self.folder / 'release.json.sig').exists())

    def test_missing_report_is_refused(self):
        with self.assertRaises(SystemExit):
            sign_folder(self.folder, self.key)


class PublicationGateTests(unittest.TestCase):
    def test_missing_approval_is_not_publishable_even_when_signed(self):
        self.assertEqual(publish_release.publication_gate(dict(PRODUCTION), None), state.SIGNED_UNVALIDATED)

    def test_ct_build_is_refused_by_the_gate(self):
        self.assertEqual(publish_release.publication_gate(dict(CT_RELEASE), None), state.NOT_ELIGIBLE)

    def test_blank_record_never_passes_the_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            record = Path(temp) / 'record.md'
            record.write_text(validation_record.render(), encoding='utf-8')
            result = publish_release.publication_gate(dict(PRODUCTION), record)
        self.assertNotEqual(result, state.PUBLISHABLE)


if __name__ == '__main__':
    unittest.main()
