# Release specification: ABConnect 8_01 core-app support

**Status**: Draft release scope; implementation pending
**Created**: 2026-10-11
**Target SDK release**: 0.3.0
**Target server release**: ABConnect 8_01 (8.01)
**Latest tagged SDK baseline**: v0.2.3, `9ecd129d5b60933932f54aaca5ff9fe4f078f0e3`
**Working baseline**: main, `ae87d11a5b2a8d45b87b4ed112a1d45f234b4b8d`
**SDK repository**: https://github.com/bmonson-annex/annex-abconnect

## Release intent

The preceding release round migrated Catalog API support. This release targets
the larger core-app change in 8_01. Inventory describes the items being handled;
handling units provide the unified packing and transportation experience that
replaces separate parcel-item and freight-item workflows. Jobs can have multiple
active shipments. The SDK must represent those relationships explicitly.

Backward compatibility is part of the release: supported older requests remain
usable, with warnings directing callers toward the new requests. This release
does not remove legacy public entry points or set a removal deadline. New
canonical requests should not emit a legacy-compatibility warning.

The SDK version is distinct from the server version. 0.3.0 is the next planned
minor release after the verified 0.2.3 baseline. Package metadata remains at the
current version until implementation and release validation are complete.

## User scenarios and acceptance criteria

### 1. Unified inventory and handling units (P1)

A caller creates inventory, packs it into handling units, and manages those units
without choosing separate parcel-item or freight-item mutation APIs.

- Create, read, update, and delete inventory and handling units through typed
  models matching the server. Cover company inventory where needed by job flows.
- Associate inventory with handling units and support content units, materials,
  container selection, and the packing operations needed by this workflow.
- Preserve identifiers, quantities, dimensions, weight, values, and supported
  packing relationships. Updating one item must preserve unrelated items.
- Demonstrate the same public workflow for parcel and freight use cases.
- Validate request aliases and requiredness against server DTOs and behavior;
  validate responses against real captured fixtures.

### 2. Multiple active shipments on one job (P1)

A caller can inspect and operate on two active shipments for the same job without
one replacing the other or a helper silently choosing the first shipment.

- Expose the job's shipping collection, including archive state and relationships
  to handling units and freight quote options.
- Support the current rate-selection, validation, booking, cancellation, export,
  tracking, and document flows with their actual operation-specific identifiers.
- Keep `Shipping.id`, `quoteId`, and returned carrier `shipmentId` distinct.
  Export data uses `shippingId`; V2 booking requires `quoteId`.
- A targeted mutation of shipment A must leave shipment B unaffected. Verify
  this through suitable evidence, not merely a successful HTTP status.
- If a legacy call lacks enough context to identify a shipment, require that
  context before a mutation. A warning cannot justify guessing a target.
- Cover zero, one, and multiple active shipments, archived records, invalid
  selectors, and job-modification conflicts.

### 3. Compatibility with actionable warnings (P1)

An existing SDK consumer can migrate gradually while retaining supported legacy
method names, imports, and request forms.

- Build a compatibility matrix for existing item, rate, booking, cancellation,
  export, tracking, and document entry points before changing them.
- For each entry, record the old SDK method and shape, the 8_01 replacement,
  whether the server still accepts it, any SDK adapter, warning behavior, and
  fixture/test evidence. Distinguish verified support from unresolved mappings.
- Supported legacy calls continue to work and issue an actionable compatibility
  warning identifying the old usage and replacement. Use a caller-visible,
  filterable warning category; do not equate this with scheduled removal.
- Warn once per public invocation under an always-warn filter, with caller
  location attribution; internal helpers must not multiply the same warning.
- Adapters preserve all meaningful data and established return contracts, or
  explicitly surface an unsupported/ambiguous mapping before sending a mutation.
  Never drop fields or pretend a removed server route still works.
- Tests must cover both a retained server route and an adapted request, plus
  the absence of compatibility warnings on canonical 8_01 usage.

## Functional requirements

- **FR-001**: Add inventory and handling-unit models and endpoint groups using
  the shared request/response bases and explicit API aliases.
- **FR-002**: Make handling units the primary packing and transportation workflow
  in examples and documentation, replacing the parcel/freight item split there.
- **FR-003**: Model a job's multiple active shipments and all required identifiers
  without flattening the collection to one implicit shipment.
- **FR-004**: Expose the current booking and validation contracts and preserve
  supported legacy booking behavior with compatibility warnings.
- **FR-005**: Preserve supported legacy public entry points through verified
  routes or explicit adapters; removal is outside this release's scope.
- **FR-006**: Classify every removed or changed Swagger operation affecting an
  existing SDK route using server source, fixtures, and the compatibility matrix.
  Absence from Swagger alone is not evidence of server removal.
- **FR-007**: Reconcile route discovery and schema-stub coverage with the refreshed
  specification, with explicit treatment of retained compatibility routes.
- **FR-008**: Deliver model validation, transport/selector regression tests,
  safe staging integration coverage, real fixtures, and `FIXTURES.md` updates
  for new and changed endpoint contracts.
- **FR-009**: Preserve the completed Catalog API changes, including required
  `platformId` for bulk upsert, and the current auth and CLI behavior.
- **FR-010**: Publish migration examples showing old calls, their warnings, and
  canonical replacement calls, including a job with multiple active shipments.
- **FR-011**: Publish and verify the release on both PyPI and Read the Docs using
  the [release runbook](../../docs/release-runbook.md). Record artifact versions,
  release/build commits, and public URLs; neither destination alone completes
  the release.
- **FR-012**: Meet the [DX acceptance measures](../../docs/dx-roadmap.md), including
  a timed first-call review, discoverable What's New and migration guidance,
  complete validated examples, and actionable error and compatibility guidance.

## Evidence and limits

Follow the repository source-of-truth hierarchy: server implementation, then
captured responses, then Swagger. The server checkout is `~/src/abconnect`;
inspect `origin/release` rather than assuming its checked-out `dev` is 8_01.
The inspected release commit is `23a8a00cd`.

Observed server source under `ACPortal/ABC.ACPortal.WebAPI/Controllers/`:

- `JobControllers/JobInventoryController.cs` and
  `JobControllers/JobHandlingUnitController.cs` expose the new item/unit APIs.
- `JobControllers/JobShippingController.cs` returns `List<Shipping>` from
  `GET /api/job/{jobDisplayId}/shippings`.
- `JobControllers/JobShipmentController.cs` retains `/shipment/book`, adds
  `/shipment/v2/book` and `/shipment/validate`, and accepts optional `shippingId`
  on export-data routes. V1 booking returns documents; V2's response differs.
- `JobControllers/JobParcelItemsController.cs` still exposes a legacy GET.
  The inspected controller does not retain the old parcel write actions.

The refreshed `ab/api/schemas/acportal.json` comes from
https://portal.staging.abconnect.co/swagger/v1/swagger.json. Its SHA-256 is
`fef44a69f42597b8a1058bed4216c7cd31f5ea9e934011e3e53c328ed3fc7fcd`.
It contains 308 paths, 363 operations, and 527 component schemas. Compared with
the SDK baseline, 94 operations are added, 30 removed, and 221 existing operation
definitions differ. These counts include changes beyond the release's three
major themes and are an investigation inventory, not completed SDK work.

The source inspection proves route availability, not end-to-end compatibility.
In particular, optional export identifiers demonstrate why a path appearing
removed from Swagger need not mean the old call is gone. Removed writes need
service/DTO investigation before promising an adapter. The deployed staging
commit has not been matched to the inspected server commit.

The initial refresh exposed schema-stub, query-parameter, and generated-report
drift. The CI repair reconciles 183 current-schema placeholders, preserves three
older placeholders, adds the three missing quote selectors, and regenerates the
report. The full local deterministic suite now passes; see [validation.md](validation.md).
These discovery/selector fixes are not the complete 8_01 implementation.

## Release gates

- [x] Establish the correct SDK repository and update to current main containing v0.2.3.
- [x] Refresh the ACPortal schema; validate JSON and its 1,960 internal references.
- [x] Reconcile current schema-stub coverage, quote-selector routing, and generated progress for CI.
- [ ] Complete the compatibility matrix and resolve ambiguous or lossy mappings.
- [ ] Implement typed inventory/handling-unit and multiple-shipment workflows.
- [ ] Implement and verify compatibility warnings and adapters.
- [ ] Capture and validate real fixtures; update fixture status and certification.
- [ ] Verify multi-shipment isolation, selectors, and conflict behavior on staging.
- [ ] Update examples, migration documentation, endpoint docs, and progress data.
- [ ] Pass deterministic tests, Ruff, progress no-drift checks, and Sphinx with warnings as errors.
- [ ] Complete safe live integration checks with documented results and gaps resolved.
- [ ] Finalize 0.3.0 package metadata and release notes from implemented behavior.
- [ ] Complete the DX review and replace the migration preview with verified examples.
- [ ] Publish and verify the exact release on PyPI and Read the Docs, including stable routing.

## Handoff

This document is the next release's scope for the FR round. Detailed planning
and implementation follow the repository's Claude/speckit workflow. No runtime
8_01 support, certification, tag, or published package is claimed by this draft.
