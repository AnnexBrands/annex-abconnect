"""Interactive certification workbench (issue #71).

Reusable core behind ``notebooks/certify_endpoint.ipynb``. The notebook is a
thin UI: every step it performs is a function or method here, so pytest drives
the identical code path and the two cannot drift apart.

Typical session::

    from ab.progress.certify import CertificationSession

    s = CertificationSession("api.address.validate")
    s.validate_request({"line1": "...", "city": "...", "state": "CA", "zip": "92108"})
    s.expect_validation_error(data, omit="line1")
    s.execute(api.address.validate, **data)      # bound SDK method
    print(s.summary)                              # bounded, never a raw dump
    print(s.checks)                               # green/red panel
    report = s.propose_fixture()                  # sanitized diff for review
    s.approve_fixture(confirm=True)               # explicit operator approval
    s.write_evidence()                            # schema-2, no manual JSON
    s.regenerate_report()
"""

from ab.progress.certify.session import (
    CertificationSession,
    Check,
    CheckReport,
    MutationNotClassified,
    approved_constants,
    compare_to_fixture,
    list_endpoints,
    load_request_fixture,
    load_response_fixture,
    resolve_model,
    resolve_route,
)
from ab.progress.certify.summarize import (
    ResponseSummary,
    extra_fields,
    select_path,
    summarize,
)
from ab.progress.sanitize import (
    SanitizeReport,
    payload_sha256,
    sanitize,
)

__all__ = [
    "CertificationSession",
    "Check",
    "CheckReport",
    "MutationNotClassified",
    "ResponseSummary",
    "SanitizeReport",
    "approved_constants",
    "compare_to_fixture",
    "extra_fields",
    "list_endpoints",
    "load_request_fixture",
    "load_response_fixture",
    "payload_sha256",
    "resolve_model",
    "resolve_route",
    "sanitize",
    "select_path",
    "summarize",
]
