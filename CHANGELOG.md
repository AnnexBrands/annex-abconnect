# Changelog

All notable changes to `annex-abconnect` are documented here. This project
adheres to [Semantic Versioning](https://semver.org/) (pre-1.0: minor/patch
per 0.x pragmatics). The package is imported as `ab`.

## [0.3.0] - Unreleased — targeting ABConnect 8_01

Release scope is defined in [specs/038-abconnect-8-01/spec.md](specs/038-abconnect-8-01/spec.md).
The implementation and certification are pending; these are release requirements,
not claims of shipped SDK support. The baseline is v0.2.3 plus the current main
branch's CLI token-refresh addition.

### Prepared

- Refreshed the bundled ACPortal Swagger from staging: 363 operations and 527
  component schemas. This updates discovery evidence, not endpoint compatibility.
- Added What's New, an 8_01 migration preview, troubleshooting, and measurable
  developer-experience goals. Reworked the docs home and quickstart around package
  installation and a first read-only call; corrected outdated example arguments.
- Added a release runbook requiring verified publication on both PyPI and Read
  the Docs. Read the Docs now fails on build warnings, and the PyPI workflow
  checks distribution metadata and description rendering before upload.
- Corrected the package repository link to `bmonson-annex/annex-abconnect`.

### Planned

- Unified inventory and handling-unit operations replace the parcel-item versus
  freight-item split as the primary SDK workflow.
- Multiple active shipments per job, with explicit selection of the appropriate
  shipping record, quote, and carrier shipment for each operation.
- Preserve supported legacy requests through verified server compatibility or
  explicit SDK adapters. Emit actionable compatibility warnings; do not remove
  public methods or announce a removal deadline in this release.
- Updated typed models, runnable examples, real fixtures, migration guidance,
  and certification evidence for the 8_01 core-app changes.

## [0.2.3] - 2026-08-28

Every bulk-upserted catalog now states the platform it belongs to, and the SDK
can read the bearer token's own claims to help a caller work out which that is.

### Added

- **`BulkUpsertCatalogRequest.platform_id`** (`platformId`), **required on
  every catalog**. The property is real but absent from swagger — the API
  declares it `[SwaggerIgnore]`, which hides it from the generated document and
  changes nothing about the binder.

  Requiring it of everyone is stricter than the API, deliberately:

  - **corporate users** (`CorporateAdmin`, `CorporateAccounting`) have no
    choice — those roles intentionally carry no `partnerIds` claim, so the API
    has nothing to resolve a platform from and answers `404` without one;
  - **non-corporate users** *could* omit it and be resolved through their own
    `partnerIds`. It is required anyway so one payload shape works for every
    caller and the intended platform is recorded in the body rather than left
    implicit in whoever held the token.

  Caveat, verified on staging 2026-08-28: the API **ignores** the value for
  non-corporate bearers rather than validating it. A platform user on partner 1
  who names platform 15 is silently given platform 11 — their own — with a
  `200`. The value is authoritative only for corporate callers. Confirm the
  landing platform from the `platforms` association on the response when it
  matters.

  A caller who does not know their platform ID can derive it from their token:
  `bearer_claims().partner_ids` maps to platforms via
  `api.platforms.list(partner_id=...)`. `partnerIds` stays a claim and never
  becomes a body field.

- **`ab.auth.claims`** — `BearerClaims`, `decode_jwt_payload`,
  `is_corporate_role`, `CORPORATE_ROLES`, and `HttpClient.bearer_claims()`.
  Reads `role` and `partnerIds` off the access token, normalising each whether
  the token carries a scalar or an array. No signature verification: nothing
  security-bearing is decided here, and the API validates the request again for
  real. Corporate status is decided from the **role** and never from an absent
  `partnerIds` — a claim can be missing for reasons that have nothing to do
  with being corporate.

- `api.catalog.bulk_upsert` rejects a payload missing `platformId` with a
  `pydantic.ValidationError` located at `catalogs.<i>.platformId`, listing every
  offending index at once, before any HTTP request goes out. The rule is
  unconditional, so it needs no knowledge of the bearer and holds for clients
  that cannot report claims at all.

### Fixed

- **The `404` from `POST /Bulk/upsert` is explained and gone.** 0.2.0 through
  0.2.2 recorded the route as answering `404` for any non-empty `catalogs`
  list, certified as an unverified gap. The cause was the missing `platformId`:
  the certification runs used a corporate account. With one supplied the route
  answers `200` and returns each catalog with its platform association —
  verified against staging on 2026-08-27 with a corporate account and two
  platform accounts, and re-verified on 2026-08-28 once `platformId` became
  required of every caller.

### Breaking

Request models now match what the API source requires, rather than what swagger
declares. Payloads that were accepted locally and rejected over the wire now
fail at construction:

- `BulkUpsertCatalogRequest`: `customer_catalog_id`, `title` and `platform_id`
  are required (joining `start_date`, `end_date` and `seller`).
- `BulkUpsertLotRequest`: `customer_item_id`, `lot_number` and `data` are
  required.
- `BulkUpsertSellerRequest`: `name` is required (joining `customer_display_id`
  and `is_active`).
- `AddCatalogRequest.title` — and so `UpdateCatalogRequest.title` — is required.
- `CatalogPlatformDto.platform_catalog_id` is required. The association exists
  to carry that external ID; a platform entry without one associates a catalog
  under no external identity at all.
- Collections default to `[]` instead of `None`, so "none of them" has exactly
  one representation: `BulkUpsertRequest.catalogs`,
  `BulkUpsertCatalogRequest.lots`, `BulkUpsertLotRequest.image_links`,
  `AddCatalogRequest.agent_company_ids` and `AddCatalogRequest.platforms`.
  Passing an explicit `None` for any of these is now an error. Serialization is
  unchanged: `check()` excludes unset fields, so an untouched default still
  adds nothing to the body.

## [0.2.2] - 2026-08-25

Completes the Catalog schema cutover. The SDK now models the migrated schema
unconditionally; environment skew is handled by pinning, not by a runtime guard.

### Breaking

- **`CatalogSchemaMismatchError` is removed, along with the guard that raised
  it.** 0.2.0 and 0.2.1 refused every `catalog`, `lots`, `sellers` and
  `platforms` call when the client targeted production, because the migrated
  Catalog schema was deployed to staging only. That guard is gone: catalog-surface
  calls now go out against whatever environment the client targets.

  Production had not migrated as of this release, so those calls fail against it
  — with the API's own 400/404 rather than a guard message. **Pin
  `annex-abconnect==0.1.15` for production catalog access** until the Catalog API
  migrates there; 0.1.15 is the last release modelling the pre-migration schema.
  Code that caught `CatalogSchemaMismatchError` must drop the handler; the name
  no longer exists in `ab.exceptions`.

### Notes

- `_DEFAULT_SCOPES` is deliberately unchanged. `login.abconnect.co` still does
  not advertise the `catalog` scope, and one unavailable scope fails the whole
  grant with `invalid_scope`, so adding it to the production default would break
  every production login.
  `tests/integration/test_oauth_scopes.py::test_catalog_scope_is_staging_only`
  fails when production gains the scope — that is the signal to make the change.
- The two gaps 0.2.0 certified as unverified are still unverified: `POST
  /Bulk/upsert` answers `404` on staging for any non-empty `catalogs` list, and
  `POST /Lot/ItemData` answers `200 []` for every query shape tried.

## [0.2.1] - 2026-08-23

OAuth scopes are configurable, and the requested set now matches what each
IdentityServer actually offers.

### Fixed

- The token grant hardcoded `scope=offline_access`, so every token the SDK
  minted carried that one scope and never the `catalog` scope the staging
  IdentityServer offers. Neither API enforces scopes today, which is why
  nothing had broken; the day the Catalog API starts enforcing, every call
  would have returned 403.

### Added

- `ABCONNECT_SCOPES` (`ABConnectSettings.scopes`) overrides the requested
  scopes; `ABConnectSettings.oauth_scopes` resolves the effective value.
- Per-environment defaults, because the servers differ and one unavailable
  scope fails the *whole* grant with `invalid_scope`:
  - staging: `roles portalApi customerPortalApi catalog offline_access`
  - production: `roles portalApi customerPortalApi offline_access`
  Both verified against the live discovery documents and real grants on
  2026-08-23. `catalog` exists on staging only; `openid` and `profile` are
  advertised by both servers but rejected for the `toolsApp` client.
- A failed grant returning `invalid_scope` now reports the scopes requested,
  the client ID, the environment, and the setting to change — the server
  rejects the whole grant without naming the offending scope.
- `tests/integration/test_oauth_scopes.py` pins each environment's default
  against that server's advertised scopes, so a default that drifts from the
  server fails loudly. One test deliberately fails when production gains the
  `catalog` scope, as the prompt to move it into the production default.

### Notes

- The refresh grant deliberately sends no `scope`: the refresh token replays
  the scopes it was granted. A scope change therefore takes effect at the next
  password grant — clear the stored token to apply it immediately.
- `offline_access` stays in every default; without it the server issues no
  refresh token and every session falls back to a password grant.

## [0.2.0] - 2026-08-23

Catalog schema migration. The Catalog API's database schema changed and the SDK
now models the **migrated schema, which is deployed to staging only**.
Production still serves the pre-migration schema, so the `catalog`, `lots`,
`sellers` and `platforms` endpoints raise `CatalogSchemaMismatchError` when the
client targets production. Pin `annex-abconnect==0.1.15` to keep calling
production's catalog surface until it migrates.

Every route below was exercised against live staging on 2026-08-23; the two
exceptions are called out under "Known gaps".

### Breaking — retired routes

- `POST /Bulk/insert` is gone, replaced by `POST /Bulk/upsert`.
  `api.catalog.bulk_insert()` -> `api.catalog.bulk_upsert()`. The new route
  returns `list[CatalogWithLotsDto]` (the old one returned nothing) and matches
  rows on `customerCatalogId` / `customerItemId`, so re-sending a payload now
  updates instead of duplicating.
- `POST /Lot/get-overrides` is gone, replaced by `POST /Lot/ItemData`.
  `api.lots.get_overrides(ids)` -> `api.lots.item_data(data=...)`, which takes a
  `GetLotsItemDataQuery` (a required `partnerId` plus the ID list) and returns
  `list[LotItemDataDto]` in place of `list[LotOverrideDto]`.

### Breaking — retired fields, matching the database's `Obsolete*` columns

- `Catalogs.Agent` -> `agentCompanyIds`. `CatalogDto.agent` (a single string) is
  now `agent_company_ids` (a list), backed by the `CatalogAgentCompanies` join.
  `api.catalog.list(agent=...)` -> `api.catalog.list(agent_company_id=...)`.
- `Catalogs.CustomerCatalogId` is retired. A catalog's external identity lives
  per-platform on `CatalogPlatformDto.platform_catalog_id`.
  `api.catalog.list(customer_catalog_id=...)` ->
  `api.catalog.list(platform_catalog_id=...)`.
- `Lots.CustomerItemId` is retired. A lot's external identity lives per-platform
  on `LotPlatformDto.platform_item_id`.
  `api.lots.list(customer_item_id=...)` -> `api.lots.list(platform_item_id=...)`.
- A catalog now has **one** seller (`Catalogs.SellerId`), not a list.
  `CatalogWithSellersDto` is deleted; reads return a singular `seller` and
  `AddCatalogRequest`/`UpdateCatalogRequest` take a required `sellerId` in place
  of `sellerIds`. Both also now require `isCompleted`.
- `overridenData` is renamed `itemData` on `LotDto`, `AddLotRequest` and
  `UpdateLotRequest`.
- `LotDataDto.value` is gone — the migrated swagger no longer declares it.
- Response model changes: `GET /Catalog` and `GET /Catalog/{id}` return
  `CatalogWithLotsDto`; `POST /Catalog` and `PUT /Catalog/{id}` return
  `CatalogExpandedDto` (previously `CatalogWithSellersDto`).

### Added

- `api.platforms` — full CRUD over the new `/Platform` surface (`PlatformDto`,
  `AddPlatformRequest`, `UpdatePlatformRequest`, `PlatformListParams`), plus the
  `CatalogPlatformDto` / `LotPlatformDto` association models.
- `api.catalog.merge(target_id, source_id)` and
  `api.lots.merge(target_id, source_id)` — destructive; the source does not
  survive the call.
- Lot client item data: `api.lots.create_client_item_data()`,
  `api.lots.list_client_item_data()`, `api.lots.delete_client_item_data()`
  (`LotClientItemDataDto`, `AddLotClientItemDataRequest`).
- `CatalogSchemaMismatchError`, raised before any request leaves the client when
  the catalog surface is called against an environment running the old schema.

### Fixed — contract corrections found against live staging

- `BulkUpsertCatalogRequest.seller` is required, though swagger declares it
  nullable: the API answers `400 Catalogs[0].Seller: The Seller field is
  required` without it.

### Known gaps — certified as unverified, not as working

- `POST /Bulk/upsert` answers `404 Resource not found` on staging for any
  non-empty `catalogs` list (an empty list returns `200 []`). The request shape
  is confirmed by the API's own model binding; the handler fails downstream.
  Unverified end to end.
- `POST /Lot/ItemData` answers `200 []` for every query shape tried, including
  one matching a freshly created lot on a matching partner's platform. The route
  is reachable and the empty-array contract holds, but `LotItemDataDto`'s shape
  is asserted from swagger rather than from a captured response.

## [0.1.15] - 2026-07-27

Certification infrastructure release. The SDK surface changes are corrections
found by running every read-only endpoint against live staging, so several are
breaking for callers relying on the previous (wrong) types.

### Fixed — model contracts, all verified against live staging

- `Commodity.id` and `Partner.id` were `str`; the API returns an integer primary
  key. `Commodity` also gained `code`, `name`, `isActive` and the four `parent*`
  fields it denormalizes into every search row, none of which were declared.
- `DashboardItem.step` was `int`. Live sends `"1 "`, `"2 "`, `"2."`, `"10"` —
  padded labels, and `"2."` does not parse as an integer, so it was never an int
  arriving as text.
- `GET /views/{viewId}/accessinfo` returns `List[GridViewAccessEntry]`, not a
  single `GridViewAccess`. One class was serving both this response and the
  `PUT /views/{viewId}/access` request body; every field the GET returns was
  undeclared *and* the list could not validate against an object.
- `GET /lookup/referCategoryHeirachy` returns `List[ReferCategoryHierarchy]`. It
  lives under `/lookup` but returns a 21-field referral record, and shared
  `LookupValue` with `/lookup/referCategory`, which genuinely is a plain lookup.
- `PATCH /job/{jobDisplayId}/timeline/{timelineTaskId}` sent a body no field of
  which existed in Swagger's `UpdateTaskModel`. The API answered **204** and
  applied nothing — indistinguishable from success at the call site. The request
  model now mirrors the contract (`truckId`, `plannedStartDate`,
  `preferredStartDate`, `plannedEndDate`, `preferredEndDate`, each a
  `{"value": ...}` override wrapper) and accepts a bare scalar, wrapping it.
  Its route also declared `response_model="TimelineTask"` where the API returns
  204 No Content.

### Added

- `ab.progress.compare` — one structural comparator shared by the harness and
  the certification workbench. Committed fixtures are sanitized, so comparing by
  value reported every sanitized endpoint as permanently failing;
  `api.address.validate` was "failing" purely because its fixture held the
  sanitizer's synthetic coordinates. Comparison is now model parse, undeclared
  fields, keys, nested structure, JSON value types and merged list element
  shapes — never values.
- `ab.progress.certify` — interactive certification workbench, and
  `notebooks/certify_endpoint.ipynb`, generated from
  `scripts/generate_certify_notebook.py` and held to it by a test.
- `fixture_sha256` on every passing run result, pinning evidence to the exact
  fixture bytes verified, with staleness/refresh regression tests.
- `docs/known-model-defects.md` — every read-only endpoint carries exactly one
  explicit blocking state, keeping HTTP 400/401/404/500 distinct.

### Security

- Example captures can no longer write the committed fixture tree.
  `_capture.save()` defaulted to `tests/fixtures/`, so an ordinary
  `python -m examples.companies` overwrote fixtures with the raw live response;
  a single run put carrier secrets and real UUIDs, emails, phone numbers and
  street addresses into the working tree. Captures now go to a git-ignored
  scratch tree, are sanitized before reaching disk, and refuse the committed
  tree outright. `examples/_runner.py` held a second copy of the same write.
  A committed fixture now changes through one path only: the workbench's
  `propose_fixture()` → operator review → `approve_fixture()`.

### Certification

- `api.jobs.timeline.create_task` and `api.jobs.timeline.update_task` certified
  as `circular_restored` with full restoration evidence.
- live_verified 36, certified 36.

## [0.1.13] - 2026-07-12

### Added

- `scripts/capture_notes.py` — discovery harness that builds an association
  truth table for global notes (contact/company/franchise) by creating the
  A/B/C variants and probing each `GET /note` filter. Gated behind
  `AB_RUN_MUTATIONS=1`; no DELETE route exists, so `--cleanup` closes the
  created notes via `update()`.
- `scripts/capture_lookups.py` + generated `ab/api/lookup_constants.py` —
  capture master-constant lookups as fixtures and typed per-group enums.

### Fixed

- Note `category` sourcing corrected across the SDK docstrings, CLI help
  (`ab notes create --help`), and `examples/notes.py`: use the
  `JobNoteCategory` master constant
  (`api.lookup.get_by_key(MasterConstantKey.JOB_NOTE_CATEGORY)`, UUID in
  `LookupValue.id`) — the RFQ `referCategory` lookups are a different set and
  are rejected by `POST /note`.

### Changed

- `LookupValue.id` widened to `str | int` — the `ContactTypes` lookup returns
  integer ids.

## [0.1.12] - 2026-07-05

### Added

- Added discoverable `NotImplementedError` stubs for all 93 schema routes that
  are still missing typed SDK wrappers. The registry is tested against the
  checked-in Swagger snapshots so future route coverage drift is explicit.
- Added full `JobCarrierRates` parsing for job shipment rate quotes via
  `get_rate_quotes_result()` / `request_rate_quotes_result()`, while keeping
  the existing list-returning `get_rate_quotes()` / `request_rate_quotes()`
  compatibility methods.

### Fixed

- `api.jobs.freight_providers.save()` now sends the API 7.11 array body for
  `POST /job/{jobDisplayId}/freightproviders` and parses `ServiceBaseResponse`.
- `DocumentUpdateRequest` now serializes the current 7.11 `FileName`,
  `TypeId`, `Shared`, `Tags`, and `JobItems` contract, while still accepting
  older `docType` / `sharingLevel` input keys.
- `DocumentUploadResponse.amazonException` is now the confirmed boolean flag,
  and `documentDetails` is typed.
- AutoPrice V2 quote requests now parse the live
  `SubmitNewQuoteRequestV2Result` wrapper.

## [0.1.11] - 2026-07-05

### Added

- **`api.jobs.freight_providers.final_override()` supports the API 7.11 final
  override flow through `POST /job/{jobDisplayId}/freightproviders`.** The
  helper posts a one-item `ShipmentPlanProvider` array and always includes
  `optionIndex=6` unless a different index is explicitly supplied.

### Fixed

- `CodeResolver.resolve()` now accepts `uuid.UUID` objects and other
  stringifiable identifiers without raising `TypeError`.
- `api.jobs.parcel_items.list()` still unwraps the API's
  `{jobModifiedDate, parcelItems}` response shape, but no longer emits the
  generic wrapped-list warning for this known contract.
- `DocumentUploadResponse` declares the live upload/storage fields
  `successfully`, `amazonException`, `amazonErrorMessage`, `amazonErrorCode`,
  and `documentDetails`, removing production drift warnings for those fields.

## [0.1.10] - 2026-06-27

### Added

- **`api.jobs.tasks.clear_pack_finish()` reopens packaging without deleting
  the PK timeline task.** The helper fetches the current PK task and posts it
  back with explicit JSON `null` values for `timeLog.end` and `completedDate`,
  preserving the task id, `modifiedDate`, work logs, and `timeLog.start`. When
  the job is below Packaging Completed, it returns a successful no-op response
  without touching the API.

## [0.1.9] - 2026-06-26

### Added

- **`api.jobs.get_feedback()` and `api.jobs.save_feedback()` now expose
  `/job/feedback/{jobDisplayId}`.** `save_feedback()` accepts a `feedback_id`
  and `cancel_job` flag and sends the API's `feedbackId` / `cancelJob` payload.

## [0.1.8] - 2026-06-25

A model-correctness patch. Backward-compatible with `0.1.7`.

### Fixed

- **`Job` nested contacts no longer reject integer ID values.** In the
  `ContactDetails` model nested under `Job` (`customerContact` / `pickupContact`
  / `deliveryContact`), `jobTitleId` and `rootContactId` were typed
  `Optional[str]`, but the API (and both OpenAPI schemas) declare them as
  nullable **integers**, and the standalone `contacts.py` models already typed
  them as `int`. Because Pydantic v2 does not coerce `int → str`, any
  `api.jobs.get()` on a job whose contact carried a non-null `jobTitleId` /
  `rootContactId` (e.g. a warehouse pickup contact with `jobTitleId=83`) raised
  `ValidationError` and the whole job fetch failed. Both fields are now
  `Optional[int]`, matching the schema and the `contacts.py` twin.

A packaging-hygiene release plus a small model completion. The `ab` import
surface is backward-compatible with `0.1.6`.

### Changed

- **The published package now ships only the `ab` library.** Previous releases
  bundled the entire `examples/` tree (demo/dev scripts, including
  internal/Acme-specific and harness tooling) into both the wheel and sdist.
  `[tool.setuptools.packages.find]` now includes `ab*` only, and a new
  `MANIFEST.in` prunes `examples/`, `scripts/`, `tests/`, `docs/`, and other
  dev trees from the sdist. Installed size drops and no internal scripts leak to
  PyPI consumers. (`ab` package-data — `py.typed`, `api/schemas/*.json` — is
  unchanged.)

### Fixed

- **`BookedDocument` now models the full book-response document object.** Added
  `documentPath`, `documentDescription`, `documentTypeName`, and `errorMessage`
  (alongside the existing `documentId` / `docType` / `byteCode`). On a normal
  book the label is a **path reference** — `documentPath` + `documentDescription`,
  keyed off the PRO in `ServiceBaseResponse.shipmentId` — and `byteCode` is only
  populated when the request sets `documentByteCodeRequired=True`. The missing
  fields previously surfaced as `extra="allow"` warnings (accessible but
  untyped). Verified live (UPS book of job 7107421, PRO `1ZK430390306149813`).

## [0.1.6] - 2026-06-18

A correctness release for shipment booking. Backward-compatible with `0.1.5`
for client construction, auth, and config; the single **Fixed** item changes
the *wire payload* of `api.jobs.shipment.book()` (not its signature).

### Fixed

- **`ShipmentBookRequest` now sends `quoteOptionIndex`/`shipOutDate` (was
  `providerOptionIndex`/`shipDate`) so `shipment.book()` succeeds.** The portal's
  `BookShipmentRequest` schema binds `quoteOptionIndex` for the chosen rate
  option and requires `shipOutDate` for non-UPS carriers; the old aliases were
  never read, so `quoteOptionIndex` defaulted to `0`, the selected provider was
  never set, and every Ready-to-Ship book was rejected with "Specified provider
  was not set or it is not active" (callers saw a phantom success with no
  PRO/label). The Python attributes are renamed to `quote_option_index` /
  `ship_out_date` (construction by attribute or alias both still work). The body
  also gains the schema's optional `internationalParams`,
  `carrierSpecificParams`, and `documentByteCodeRequired` fields. Downstream
  apps that posted a raw dict to work around this can drop the workaround and
  call the typed `book()` again.
- **`ServiceBaseResponse.documents` now accepts document objects, not just
  strings.** A *successful* book returns `documents` as a list of objects
  (`{documentId, docType, byteCode}` — the label byte codes), but the field was
  typed `list[str]`, so the typed `book()` raised a `ValidationError` parsing
  its own success envelope (surfaced live booking UPS job 7036373, PRO
  `1ZK430390312572326`). The field is now `list[str | BookedDocument]`
  (new `BookedDocument` model), so `book()` returns the success envelope
  instead of throwing. Backward-compatible with operations that return
  document URL/reference strings.

## [0.1.5] - 2026-06-15

An example-coverage + ergonomics + correctness release. **Every routed endpoint
now has a canonical plain-script example** (`215 / 215`), six new endpoints and
several SDK ergonomics land, and three correctness fixes harden job-item and
timeline handling. The client-construction, auth, and config surface is
backward-compatible with `0.1.4`; the three **Fixed** items below change
*behavior* (not signatures) — see the notes there. Downstream consumers pinning
`0.1.4` are unaffected until they bump.

### Added

- **`api.jobs.items` — lenient parcel/freight item helpers.** Create / replace /
  update / delete for parcel and freight items with loose-keyword input (unknown
  kwargs are dropped, not rejected) and get-merge-write *replace-all* semantics
  for freight, so editing one item never wipes the others.
- **Six new routed endpoints** — an account group, `jobs.book`, per-shipment
  tracking (`jobs.tracking.shipment`), and document thumbnail / hide.
- **`MasterConstantKey` enum** — discoverable master-constant keys for
  `lookup.get_by_key`.
- **SDK ergonomics** — `MemoryTokenStorage`, raw-`bytes` document uploads,
  anonymous `AccessKey` autoprice quotes, and per-request header injection
  (`extra_headers`).
- **Completed freight item models** — `JobFreightItem` (response) and
  `FreightShipment` (request) now mirror the full swagger `FreightShimpment`
  (31 fields), so a populated freight item validates without drift warnings and a
  get-modify-replace round-trip is lossless. Added `ParcelItemSave`,
  `ParcelItemsRequest`, and `ParcelItemsResponse`.
- **Examples for every routed endpoint** — canonical coverage rises to
  **215 / 215**; `uncovered_endpoints()` and `legacy_only_endpoints()` are both
  empty and the `STRICT_COVERAGE` + `STRICT_NO_LEGACY` gates are `True`. Includes
  examples for the previously-uncovered dashboard reads, `jobs.transfer`,
  `jobs.status`, and the job subgroups (`email`, `sms`, `note`, `on_hold`,
  `parcel_items`, `payment`, `shipment`, `rfq`, `tracking`, `timeline`, `form`,
  `freight_providers`).

### Changed

- **All 114 legacy-only endpoints migrated to canonical examples** — the
  deprecated `examples/_X.py` runner files are superseded by plain-`main()`
  scripts (`catalog`, `commodities`, `commodity_maps`, `companies`(+`_extended`),
  `contacts`(+`_extended`), `documents`, `jobs/core`, `lookup`, `lots`, `notes`,
  `reports`, `rfq`, `shipments`, `views`).

### Fixed

- **Pickup-and-pack agents no longer get a spurious 403 on status-with-note.**
  The timeline status helpers (`api.jobs.tasks.*`) no longer issue a redundant
  `POST /note`: the ABConnect job-management endpoint now records the Job History
  note itself when the task is saved. The old second call required top-level
  note-write permission an agent lacks, so it 403'd and masked an otherwise-
  successful pickup status change. *Behavior change:* the helpers no longer make
  that call; `TimelineHelpers._create_job_history_note` is a deprecated no-op.
- **`api.jobs.parcel_items.create` is now non-destructive (ACID).** `POST
  /job/{id}/parcelitems` is a replace-all (`SaveAllParcelItemsRequest`); the SDK
  previously modeled it as a single-item create, so `create` **wiped the entire
  parcel set**. It now reads the current items, appends, and saves the full set,
  returning the newly added item (`api.jobs.items` builds on this).
- **Empty `2xx` responses no longer raise.** A success response with an empty
  body (common for `DELETE` and replace-all saves) returned "Response was not
  valid JSON"; it now resolves to `None`. *Behavior change:* affected calls (e.g.
  `parcel_items.delete`) return `None` instead of raising.

[0.1.5]: https://github.com/AnnexBrands/ab/compare/v0.1.4...v0.1.5

## [0.1.4] - 2026-06-05

A documents + discoverability release. The `help()` → Read the Docs rollout now
covers every route-backed group, and the Documents endpoint gains a
swagger-faithful item-photo upload. The client-construction, auth, config,
exceptions, and model-import surface relied on by downstream consumers is
unchanged from `0.1.3`.

### Added

- **Item-photo upload for the Documents endpoint** — `documents.upload` is now a
  typed, route-backed `POST /documents` multipart primitive
  (`DocumentUploadRequest` / `DocumentUploadResponse`), with
  `documents.upload_item_photo` and `documents.upload_item_photos` (batch;
  always returns a list) convenience wrappers.
- **`help()` → Read the Docs for every group** — the per-endpoint page + `Docs:`
  footer mechanism (jobs-only in `0.1.3`) now covers all 21 route-backed groups,
  each with generated per-endpoint pages and a `:glob:` toctree.

### Changed

- **`DocumentType` enum corrected to swagger-truth** — values now mirror the live
  `GET /lookup/documentTypes` lookup (e.g. `BOL = 4`, `ITEM_PHOTO = 6`,
  `OTHER = 7`); the previous values were incorrect. Code referencing the old
  members (`UNKNOWN`, `INVOICE`, `PHOTO`, `CLAIM`, `POD`) or their old integer
  values must update.

### Fixed

- Generated per-endpoint pages now escape pipes in the parameter *type* column,
  so Union types (`DocumentType | int`, `str | None`) no longer break the
  Markdown tables under MyST.
- `jobs.tracking.v3` documents `historyAmount` as a **path** parameter (not a
  query parameter) in both its page heading and its docstring footer.

### CI

- Hardened the PyPI publish job: a tag↔`pyproject` version guard, token-based
  auth, and `skip-existing: true`.

[0.1.4]: https://github.com/AnnexBrands/ab/compare/v0.1.3...v0.1.4

## [0.1.3] - 2026-06-05

A quality & discoverability release. No breaking changes — the public API
surface (client construction, auth, config, exceptions, and models) is
backward compatible with `0.1.2`.

### Added

- **Statically discoverable endpoint groups** — `ABConnectAPI` now carries
  class-level annotations for every endpoint group, so `api.<TAB>` completion
  works in editors and REPLs. Adds public `ABConnectAPI.groups()` and
  `__repr__()`.
- **`help()` → Read the Docs links** — route-backed jobs-group methods now
  carry a `Docs:` footer linking to a rich per-endpoint documentation page,
  plus generated per-endpoint pages for the jobs group.
- **`contacts.get_did` accepts integer display IDs** — the parameter is
  widened from `str` to `str | int` (backward compatible; existing string
  callers are unaffected).

### Changed

- Internal quality gates are now enforced in CI: zero `ruff` violations, a
  green deterministic test suite (`pytest -m "not live"`), and no-drift gates
  for the progress report and generated endpoint docs.

[0.1.3]: https://github.com/AnnexBrands/ab/compare/v0.1.2...v0.1.3
