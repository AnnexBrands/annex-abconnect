# What's New

Use this page to decide what an upgrade changes for your application. SDK package
versions and ABConnect server versions are separate: the upcoming **SDK 0.3.0**
targets **ABConnect 8_01**.

## Upcoming: 0.3.0 — ABConnect 8_01

**Status: planned, not released.** Updating the Swagger snapshot does not add the
new SDK workflows. Implementation and certification are still required.

| Change | What it means for your integration |
|---|---|
| Inventory and handling units | A unified packing and transportation workflow replaces separate parcel-item and freight-item workflows. |
| Multiple active shipments per job | Select the intended shipment or quote explicitly; a job ID alone may no longer identify the operation's target. |
| Compatibility warnings | Supported legacy requests remain available with guidance toward their replacements. Public entry points are not scheduled for removal in this release. |
| Better developer guidance | Updated onboarding, migration examples, troubleshooting, and release documentation are release requirements. |

Start with the [8_01 migration guide](migration-8-01.md). It identifies what can be
prepared now and what depends on the new SDK implementation. The updated portal
schema contains 363 operations and 527 schemas; those counts describe the API,
not completed SDK coverage.

The development SDK now exposes optional quote selection on packing slips,
packaging specifications, and shipment tracking. These selectors pass local
transport checks; live quote-selected validation is pending. The remaining new
routes are discoverable placeholders, not implemented endpoint wrappers.

The current development branch also adds `ab token` / `abs token` to refresh and
print the access token. This is after the 0.2.3 tag; do not expect it in an
installed 0.2.3 package. Its output is a credential, not diagnostic log data.

## Current tagged release: 0.2.3

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
