# What's New

SDK **0.3.0** targets **ABConnect 8_01**. SDK and server version numbers are separate.
Read the [migration guide](migration-8-01.md) before upgrading an existing integration.

## 0.3.0 — Unified packing and multiple shipments

| Change | What it means for your integration |
|---|---|
| Inventory and handling units | Describe goods separately from their packing; use one workflow for parcel and freight. |
| Company packing | Manage common inventory, discover materials and container types, and request packing suggestions and validation. |
| Multiple active shipments | Inspect all shipping records and select the intended shipping ID or quote UUID explicitly. |
| Rates and booking | Request rates for handling units, save selected quotes, validate and book V2 shipments, and inspect cancellation results. |
| Shipment-specific data | Export data targets a shipping ID; forms, tracking, documents, and add-ons expose current 8_01 contracts. |
| Supported legacy requests | Visible, filterable `LegacyRequestWarning` notices point to replacements without a removal deadline. |
| Removed server contracts | Retained method names raise `UnsupportedOperationError` before HTTP when no lossless adapter exists. |

Nested request validation rejects unknown fields before HTTP and preserves explicit
nulls. Shipping records, quote UUIDs, and carrier shipment identifiers remain distinct.
Ambiguous legacy shipping mutations fail before making a request.

The bundled portal Swagger contains 363 operations and 527 schemas. Unimplemented
schema methods remain explicit placeholders; these counts do not claim full API coverage.
Reviewed staging captures cover packing, materials, rates, booking, shipping isolation,
and company support. Normal carrier cancellation failed in the staging release test;
forced removal succeeded in ABConnect and **does not prove cancellation with the carrier**.
Callers must inspect `success`, `error_message`, and `override_error`.

The release also includes `ab token` / `abs token` to refresh and print an access
token. Treat that output as a credential. Explicit environment selection now takes
precedence over the environment named in a supplied configuration file.

Start with [Quickstart](quickstart.md), [migration examples](migration-8-01.md), and
[Troubleshooting](troubleshooting.md). The [release evidence](https://github.com/bmonson-annex/annex-abconnect/blob/main/specs/038-abconnect-8-01/validation.md)
distinguishes deterministic checks, observed staging behavior, and hosted publication.

## 0.2.3 — Catalog bulk upserts

Catalog bulk upserts now require `platformId` on every catalog, together with
`customerCatalogId`, `title`, dates, and seller data. This fixes the missing
platform context behind corporate callers' bulk-upsert 404s. Request models
reject missing required fields locally instead of sending an invalid request.

For non-corporate users, the server may resolve the platform from the bearer
claims rather than the submitted value. Verify the returned platform association
when choosing a particular platform matters.

- [Bulk upsert contract and examples](api/catalog/bulk_upsert.md)
- [Platform discovery](api/platforms.md)
- [Catalog models](models/catalog.md)

The release also adds bearer-claim helpers for inspecting roles and partner IDs.
These decode claims; they do not verify token authenticity or authorize access.

## 0.2.2 — Catalog schema cutover

Catalog, lots, sellers, and platforms use the migrated schema unconditionally.
The former production guard and `CatalogSchemaMismatchError` were removed.
Deployment compatibility must be checked against the target server; the SDK no
longer blocks a request merely because production is selected.

The release notes recorded production Catalog as not migrated at publication
time. That is historical deployment information, not a current environment
check. Confirm the schema your target runs before choosing a version.

## 0.2.1 — OAuth scope configuration

Default scopes are selected by environment. `ABCONNECT_SCOPES` can override the
whole set for differently provisioned clients. See the
[configuration instructions](quickstart.md#oauth-scopes-optional).

## Choose the right documentation

Use the Read the Docs version selector to match your installed SDK release.
`latest` follows development; `stable` should match the highest stable release.
The [release runbook](release-runbook.md) requires verifying those versions and
their build commits, along with the PyPI artifact, for each release.

For the complete history, see the repository
[changelog](https://github.com/bmonson-annex/annex-abconnect/blob/main/CHANGELOG.md).
