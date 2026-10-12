# 0.3.0 release validation

Validated 2026-10-11. SDK baseline: v0.2.3 plus main's CLI token addition.
Server source: `origin/release` at `23a8a00cd3883b4e4783de76f3e5e8c8b901660a`.
Staging deployment commit is not exposed; source decisions were cross-checked
against live responses. See [compatibility.md](compatibility.md) and the complete
[Swagger operation audit](swagger-audit.json).

## Deterministic and packaging checks

- Python 3.14.8: **1,554 passed, 39 skipped, 71 deselected**; live tests are excluded
  from the deterministic command. Fourteen expected legacy warnings remain visible.
- Ruff, whitespace checks, route/stub inventory, generated-reference freshness,
  and the unchanged gate baseline pass.
- Strict Sphinx HTML build succeeds, including Python/Pydantic reference inventories.
- Wheel and source distribution for **0.3.0** build and pass `twine check --strict`.
- `uv lock --check --offline` passes with the corrected package version.
- Fresh temporary environment installed the wheel outside the checkout, imported
  typed workflows, ran CLI discovery, and made the quickstart's authenticated
  read-only staging contact request. Total automated install-to-call time: **2.13 s**.
  No credential or contact value is in this report. This is an automated smoke
  check, not an independent first-time developer study.
- CI now runs Python 3.11, 3.12, 3.13, and 3.14 before tag publication.
  Hosted run URLs and final publication evidence will be recorded in the GitHub release.

## Staging discovery and packing

All calls explicitly selected staging with git-ignored credentials. The user
explicitly authorized all staging data as disposable. Production was not mutated.
Company LIVE home grids supplied estimates (234564), inbound (1495), in-house
(909), and outbound (765) candidates; these are observed counts, not fixture expectations.

On empty estimate **9165707**, inventory and handling-unit create/read/update/delete,
inventory association changes, nested unit relationships, explicit nulls, and
cleanup all passed. Only test-created records were removed. A subsequent empty
`manage` request succeeded and preserved the empty collection.

Company inventory create/update/delete passed; deletion is soft deletion, so the
new row remains visible as inactive. Existing rows remained unchanged. Nonempty
material add, replacement, container assignment/clear, and deletion passed.
Container assignment uses the material association row ID.

Company pack-inventory, combined-inventories, hierarchy packing, handling-unit
packing, and material suggestions succeeded. A negative container validation
correctly reported that the container did not fit. Staging-only `fill` and
`containerMaterial` metadata (observed null) are preserved as optional opaque
objects; their non-null schema has not been inferred. Editable invoice and USAR
returned typed JSON successfully.

## Rates, booking, conflicts, and shipment isolation

- Job **13829427** has two active shipping records, **619100** and **619101**.
  Explicit export reads and a write targeting 619100 left 619101 and the shipping
  collection unchanged. The marked `SDK-8_01-ISOLATION-CHECK` export is retained;
  no export-delete operation exists.
- A new handling unit on **5483351** used the transportation `BOXES` container
  (observed ID 25), distinct from packing `Stock Box` (ID 5). Its rate request
  returned five UPS providers, no errors, and a billable-weight warning.
- Persisted rate selection created new shipping records and preserved existing
  quotes and shipping relationships. Legacy source rows with null CreatedDate
  are projected with the current time by `JobShipmentPlanService`; only this
  source-confirmed volatile field was excluded from quote comparisons.
- A stale job modification timestamp was rejected with HTTP 400 and refresh
  guidance with both `forceUpdate=false` and `true`; existing shippings were unchanged.
- V2 validation returned `valid=true`; booking returned `success=true` for quote
  **664ee852-119d-4870-7c2f-08df27f6a737**, shipping **1513059**.
  Other shipping records remained unchanged. Negative validation of an already
  shipped quote also returned its expected business error without mutations.
- Normal cancellation failed on repeated attempts with `override_error=true`.
  The server reported that the carrier must also be notified. The SDK retained
  this business failure; HTTP success was not treated as cancellation success.
- Explicit **forced deletion succeeded in ABConnect**, again preserving the other
  shipments. **Carrier cancellation remains unconfirmed.** No carrier notification
  was sent. Forced deletion is not evidence that UPS cancelled the booking.

Marked test units/quotes remain on disposable job 5483351: units 6330561–6330563,
shipping records 1513057–1513059 (the last booking was force-removed). Earlier
attempts stopped at isolation assertions before booking. These records are retained
for inspection rather than silently erasing the validation trail.

## CI fixture-safety correction

The first hosted run caught contact data embedded in editable-form HTML. The
capture sanitizer now redacts entire HTML/CSS leaf strings, preserving the real
response structure and types. The fixture was re-proposed, reviewed, and approved.
The safety gate now includes untracked, non-ignored files so local checks catch
new fixtures before the first commit. A regression test verifies blob redaction
and sanitizer idempotence. The exposed implementation revision was replaced on
both branch heads before tagging; no package was published from that revision.

## Fixture review and limits

Twenty-seven new real response fixtures were sanitized, reviewed through
`CertificationSession.propose_fixture`, explicitly approved, and validated with
no extra fields. Pending raw/sanitized bundles remain git-ignored. Historical DTO
fixtures remain for compatible imports and for the contracts now rejected before HTTP.
The empty add-ons capture proves the empty-list shape only.

Transport tests cover every retained unsupported Route and item helper, asserting
zero HTTP calls. Canonical selectors, nested arrays, exact query aliases, optional
nulls, concurrency data, and legacy-warning behavior have deterministic coverage.
Not every endpoint or carrier is live-certified: payment exchange, final override,
final quote edits, document uploads, and carrier-specific document/history variants
have contract/source coverage rather than a claimed live mutation result. No financial
transaction or outbound email was performed for this release.

## Publication

Local verification does not establish hosted publication. The release process
must verify both PyPI and Read the Docs against the final tag. The GitHub release
records the exact commit, CI run, artifact names, clean PyPI installation, RTD build,
and version/stable URLs after those checks complete.
