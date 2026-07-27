"""Generate notebooks/certify_endpoint.ipynb."""
import json
import pathlib

md, code = "markdown", "code"
C = []


def cell(kind, src):
    src = src.strip("\n").split("\n")
    lines = [ln + "\n" for ln in src[:-1]] + [src[-1]]
    cid = f"cell-{len(C):02d}"
    if kind == md:
        C.append({"id": cid, "cell_type": "markdown", "metadata": {}, "source": lines})
    else:
        C.append({
            "id": cid, "cell_type": "code", "metadata": {}, "source": lines,
            "execution_count": None, "outputs": [],
        })


cell(md, """
# Endpoint Certification Workbench

Interactive approval for one endpoint at a time. **This notebook holds no logic** —
every step calls `ab.progress.certify`, which pytest drives through the identical
code path (`tests/test_certify_workbench.py`). Cells here cannot drift from tests.

Certification model: see `docs/certification-evidence.md` (issue #69).

## Safety

- Mutating endpoints refuse to execute until you `classify(...)` them.
- `unsafe_for_automation` can never be executed or certified.
- **No raw live response is ever committed.** `propose_fixture()` shows a
  deterministic sanitized diff; nothing is written until `approve_fixture(confirm=True)`.

## Prerequisites

```bash
uv sync --group notebook
cp .env.staging .env   # or export ABCONNECT_* credentials
uv run jupyter lab notebooks/certify_endpoint.ipynb
```
""")

cell(code, """
from ab import ABConnectAPI
from ab.progress.certification import MutationClass
from ab.progress.certify import (
    CertificationSession,
    approved_constants,
    list_endpoints,
    load_request_fixture,
)

api = ABConnectAPI(env="staging")
ENVIRONMENT = "staging"
print(f"{len(list_endpoints())} public endpoints available")
""")

cell(md, "---\n# Slice 1 — read-only: `api.address.validate`\n\n### 1. Select the endpoint")

cell(code, """
list_endpoints("address")
""")

cell(code, """
s = CertificationSession("api.address.validate", environment=ENVIRONMENT)
print(f"{s.route.method} {s.route.path}")
print("request model :", s.request_model().__name__ if s.request_model() else "plain kwargs")
print("response model:", s.response_model_name)
print("classified as :", s.mutation_class.value)   # GET -> read_only automatically
""")

cell(md, "### 2. Approved shared constants")

cell(code, """
consts = approved_constants()
print(f"{len(consts)} approved constants")
{k: v for k, v in list(consts.items())[:8]}
""")

cell(md, "### 3–4. Load (or create) the request fixture and inspect the raw data")

cell(code, """
request_data = load_request_fixture("AddressValidateParams") or {
    "line1": "7580 Metropolitan Dr", "city": "San Diego", "state": "CA", "zip": "92108",
}
request_data
""")

cell(md, "### 5–6. Cast into the Pydantic model, then show the validated wire payload")

cell(code, """
instance = s.validate_request(request_data)
print("wire payload (aliased — what the API receives):")
print(s.request_payload)
print()
print("call kwargs (snake_case — what the SDK method signature takes):")
print(s.call_kwargs)
print()
print("bound to this method's signature:", list(s.bind_arguments(api.address.validate)))
""")

cell(md, """
### 7. Negative test — omit a required field

`required_fields()` tells you what is safe to omit. `AddressValidateParams`
declares everything `Optional`, so this reports *not applicable* rather than a
false green — the model enforces nothing at the boundary, which is worth knowing.
""")

cell(code, """
print("required fields:", s.required_fields() or "none — every field is Optional")
print()
print(s.expect_validation_error(request_data, omit="line1"))
""")

cell(md, "### 8–10. Execute against staging, then read a bounded summary")

cell(code, """
summary = s.execute(api.address.validate)   # arguments bound from the validated request
summary            # compact: model type, identifiers, populated count, extra-field warnings
""")

cell(code, """
# Expand only what you need — never a page of uncontrolled repr.
print(summary.full_json())          # bounded; pass max_chars=None for everything
print()
print("selected path:", summary.path("countryCode"))
""")

cell(md, "### 11–12. Fixture comparison and the green/red panel")

cell(code, """
s.checks           # request validation · execution · response model · undeclared · fixture match
""")

cell(md, """
### 13. Sanitize, review the diff, then approve

Sanitization is deterministic — re-running produces byte-identical output, so an
unchanged response never shows up as a spurious diff.

The sanitizer rewrites only what it can classify with confidence. Anything
ambiguous — a bare `name` that could be a person, a company, or a lookup label —
is reported as **needs review** and left in the payload **unchanged**. Those are
the lines to read carefully: they are still real data until you say otherwise.
""")

cell(code, """
report = s.propose_fixture()
print(f"{report.changed_count} values rewritten, {len(report.review)} flagged for review")
print("live hash     :", report.live_sha256[:16], "...")
print("sanitized hash:", report.sanitized_sha256[:16], "...")
print()
for line in report.diff_lines():
    print("  ", line)
""")

cell(code, """
# Nothing is written without this. Uncomment to save.
# Flagged values block the write until you confirm they identify no one:
# s.approve_fixture(confirm=True)                       # clean captures
# s.approve_fixture(confirm=True, accept_review=True)   # after reading the flags
""")

cell(md, "### 14–15. Write schema-2 evidence, then regenerate the HTML artifact")

cell(code, """
# entry = s.write_evidence()
# entry
""")

cell(code, """
# s.regenerate_report()
# s.certification_state().levels()
""")

cell(md, """
---
# Slice 2 — request body with required fields: `api.contacts.search`

A POST that does not mutate. Classify it `read_only` explicitly: the workbench
infers `manual_cleanup` for any non-GET until you say otherwise.
""")

cell(code, """
s2 = CertificationSession("api.contacts.search", environment=ENVIRONMENT)
print(f"{s2.route.method} {s2.route.path}")
print("request model  :", s2.request_model().__name__)
print("required fields:", s2.required_fields())
print("inferred class :", s2.mutation_class)     # None -> must classify before executing
""")

cell(code, """
body = load_request_fixture("ContactSearchRequest") or {
    "load_options": {"skip": 0, "take": 5},
}
s2.validate_request(body)
print("wire payload:", s2.request_payload)
print("call kwargs :", s2.call_kwargs)
""")

cell(md, "Negative test: omitting a genuinely required field must raise.")

cell(code, """
print(s2.expect_validation_error(body, omit=s2.required_fields()[0])[:400])
""")

cell(code, """
s2.classify(MutationClass.READ_ONLY)     # a search POST changes nothing
summary2 = s2.execute(api.contacts.search)  # body endpoint -> bound as data=<model>
summary2
""")

cell(code, """
s2.checks
""")

cell(md, """
---
# Slice 3 — circular mutation: `api.jobs.note.create`

**Not executed here.** This cell documents the required shape; run it only against
an approved constant on staging with `AB_RUN_MUTATIONS=1`.

A `circular_restored` endpoint cannot write evidence — and therefore cannot
certify — until `record_restoration(...)` is complete *and* `final_state_verified`
is `True`. A filled-in narrative where nobody re-read the record does not count.
""")

cell(code, """
s3 = CertificationSession("api.jobs.note.create", environment=ENVIRONMENT)
s3.classify(MutationClass.CIRCULAR_RESTORED)
print(f"{s3.route.method} {s3.route.path}")
print("required fields:", s3.required_fields())
""")

cell(code, """
# Refuses to write evidence: restoration is required for this classification.
try:
    s3.write_evidence()
except ValueError as exc:
    print("blocked as designed:", exc)
""")

cell(code, """
# After genuinely running the create + delete cycle against an approved job:
#
# note = api.jobs.note.create(job_display_id=consts["ACME_JOB_DISPLAY_ID"], ...)
# api.jobs.note.delete(job_display_id=..., note_id=note.id)
#
# s3.record_restoration(
#     record_identifier="ACME_JOB_DISPLAY_ID",
#     precondition="job has no note with body 'sdk-smoke'",
#     mutation="POST /job/{jobDisplayId}/note comments='sdk-smoke'",
#     expected_result="201, note created with a new id",
#     observed_result="201, note id 8842 created",
#     restoration="DELETE /job/{jobDisplayId}/note/8842",
#     final_state_verified=True,      # re-read the job; note is gone
# )
# s3.checks
# s3.write_evidence()
""")

cell(md, """
---
## What certification now says

`certification_state()` returns the live record for the endpoint, including which
levels it has reached and what still blocks it.
""")

cell(code, """
state = s.certification_state()
print("levels  :", [level.value for level in state.levels()])
print("blockers:", state.blockers() or "none — certified")
""")

nb = {
    "cells": C,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = pathlib.Path("/opt/packages/ab/notebooks/certify_endpoint.ipynb")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
print("wrote", out, f"({len(C)} cells)")
