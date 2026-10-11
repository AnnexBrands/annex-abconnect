# Release preparation validation

Status: local release preparation, not a published or certified 0.3.0 release.
Validated 2026-10-11 using Python 3.14.8 in an isolated temporary environment.

## Passed

- `ruff check .` and `git diff --check`.
- Sphinx HTML build with `-E -b html -W --keep-going`, including external Python
  and Pydantic reference inventories. Build completed without warnings.
- Rendered HTML checks for home, quickstart, What's New, migration preview,
  troubleshooting, DX goals, and release runbook: 1,026 local links/anchors
  resolve; the home page links directly to all six guides.
- Parsed all 13 Python snippets in home, quickstart, and troubleshooting;
  checked corrected method signatures and the local validation-error example.
- Built wheel and source distribution; both passed `twine check --strict`.
  Verified the wheel includes the portal Swagger and corrected repository URL.
  These are temporary validation artifacts carrying the unchanged 0.2.3 package
  version, not release artifacts to publish or overwrite on PyPI.
- ACPortal Swagger parses; all 1,960 internal references resolve. Saved bytes
  match the staging download.

## Targeted regression result

Command scope: `tests/test_example_params.py`,
`tests/unit/test_schema_stubs.py`,
`tests/unit/test_timeline_update_transport.py`, and
`tests/unit/test_token_refresh.py`.

Result: **108 passed, 7 skipped, 5 xfailed, 1 failed**.

The failure is `test_schema_stub_registry_matches_current_route_gaps`: the
refreshed Swagger differs from the existing route/stub registry. FR-007 requires
reconciling this during 8_01 implementation. The test remains intact.

## Pending release evidence

- The full CI matrix and API implementation/certification remain release gates.
- No timed onboarding review or two-active-shipment live test was performed.
- At validation time, no tag, package upload, GitHub release publication, or
  hosted-doc deployment had been performed. This report describes local checks;
  subsequent commit/push operations do not establish publication success.
- The RTD project uses `AnnexBrands/annex-abconnect`. Synchronize reviewed commits
  and release tags to that upstream and verify the actual build commit and version
  URLs before release completion. PyPI upload runs only in the origin repository.

## CI repair after the preparation commit

Both repositories failed on commit `7c8b5d4` with the same four checks: two stale
progress-report assertions, the schema-stub inventory, and the parameter-routing
regression gate. The latter found missing quote parameters on packing-slip,
packaging-specification, and shipment-tracking GETs.

The repair keeps the gate baseline and schema equality check intact:

- Register 183 current-schema placeholders, retaining three removed-from-schema
  placeholders without counting them as current coverage. They all still raise
  `NotImplementedError`; no route is presented as implemented by adding a stub.
- Add validated optional quote parameters using `quoteId` for the forms and
  `QuoteId` for tracking, as confirmed in the 8_01 controllers and DTOs.
- Regenerate endpoint docs and the progress report.
- Remove the notebook generator's hard-coded checkout path so the existing
  generator consistency test validates this repository on local machines too.

Local deterministic suite after repair: **1,331 passed, 39 skipped, 68 deselected,
5 xfailed**. New tests cover correct query aliases, omitted selectors, rejection
before HTTP, legacy-placeholder preservation, and unique stub names/routes.
The three new read-only live tests are opt-in and were not executed; quote-selected
capture status remains pending in `FIXTURES.md`.
