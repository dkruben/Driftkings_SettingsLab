"""Explicit publication states for a build.

Each fact is independent and is never inferred from another one:

* production build: the build used the verified production profile of a real client (not CT);
* eligible for signing: a successful release-mode production build; it may be signed offline;
* signed: `release.json.sig` verifies against a trusted key (checked by the signing and publishing tools);
* runtime and regional evidence: the validation record passes every automated and in-game check,
  and each advertised production realm is RUNTIME VERIFIED or SOURCE VERIFIED;
* approved: the validation record decision is APPROVED by the release owner.

A signature alone never makes a build publishable. The compiler writes `publishable: false` into every
report: only the full chain of facts yields PUBLISHABLE, and that decision is made outside the compiler.
"""
from build_tools.validate_build_data import require

NOT_ELIGIBLE = 'NOT_ELIGIBLE'
ELIGIBLE_UNSIGNED = 'ELIGIBLE_UNSIGNED'
SIGNED_UNVALIDATED = 'SIGNED_UNVALIDATED'
VALIDATED_NOT_APPROVED = 'VALIDATED_NOT_APPROVED'
PUBLISHABLE = 'PUBLISHABLE'
STATES = (NOT_ELIGIBLE, ELIGIBLE_UNSIGNED, SIGNED_UNVALIDATED, VALIDATED_NOT_APPROVED, PUBLISHABLE)

PRODUCTION_PROFILE = 'production'
DEVELOPMENT_PROFILE = 'ct-development'

# Problems that only the approval decision can raise; any other validation problem is missing evidence.
APPROVAL_PROBLEMS = ('Record decision is ', 'Record has no approver', 'Record has no valid approval date',
                     'Approval predates', 'Approved commit differs', 'Approved version differs')


def eligible_for_signing(report):
    """Only a successful release build from the production profile may be signed."""
    return (report.get('status') == 'success' and report.get('mode') == 'release'
            and report.get('profile') == PRODUCTION_PROFILE and report.get('realm') != 'CT')


def classify(report, signed=False, validation_ok=False, approved=False):
    """Return the single state that the independent facts support; PUBLISHABLE needs every fact."""
    if not eligible_for_signing(report):
        return NOT_ELIGIBLE
    if not signed:
        return ELIGIBLE_UNSIGNED
    if not validation_ok:
        return SIGNED_UNVALIDATED
    if not approved:
        return VALIDATED_NOT_APPROVED
    return PUBLISHABLE


def validation_facts(record_text, version, evaluate):
    """(validation_ok, approved, problems) for a validation record, using the record's own evaluator.

    `evaluate` is `build_tools.validation_record.evaluate`; it raises ValueError listing every problem.
    """
    try:
        evaluate(record_text, version)
        return True, True, []
    except ValueError as error:
        problems = [item.strip() for item in str(error).split(';') if item.strip()]
    evidence = [item for item in problems if not item.startswith(APPROVAL_PROBLEMS)]
    return not evidence, False, problems


def require_signable(report):
    require(eligible_for_signing(report),
            'Only a successful release build from the production profile can be signed (state %s)'
            % classify(report))


def require_publishable(report, signed, validation_ok, approved):
    state = classify(report, signed, validation_ok, approved)
    require(state == PUBLISHABLE, 'Publication blocked: state is %s' % state)
    return state


# Candidate lifecycle. Two states only matter for mutation:
#   STAGING: the working release distribution in a run output. Its inventory may be rebuilt or extended (an installer
#            is attached here). A SHA256SUMS.txt on disk does NOT freeze it.
#   FROZEN:  the candidate was stamped by `promote_release.py build` and/or signed (`release.json.sig`). Its bytes are
#            immutable; no installer, report or checksum may change, and only the explicit promotion copies it.
# INCOMPLETE means the staging inventory does not exist yet.
CANDIDATE_INCOMPLETE = 'INCOMPLETE'
CANDIDATE_STAGING = 'STAGING'
CANDIDATE_FROZEN = 'FROZEN'
FREEZE_MARKERS = ('release.json.sig', '.promotion-build.json', '.official-build-attestation.json')


def candidate_state(folder):
    from pathlib import Path
    folder = Path(folder)
    if any((folder / name).is_file() for name in FREEZE_MARKERS):
        return CANDIDATE_FROZEN
    if (folder / 'release.json').is_file() and (folder / 'SHA256SUMS.txt').is_file():
        return CANDIDATE_STAGING
    return CANDIDATE_INCOMPLETE


def require_mutable(folder):
    state = candidate_state(folder)
    require(state != CANDIDATE_FROZEN,
            'The candidate is frozen (stamped or signed) and cannot change; attach installers while it is staging')
    return state
