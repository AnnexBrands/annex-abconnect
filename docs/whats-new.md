# What's New

SDK **0.3.x** targets **ABConnect 8_01**. SDK and server version numbers are separate.
Read the [migration guide](migration-8-01.md) before upgrading an existing integration.

## 0.3.1 — Handling-unit writes that keep what you did not mention

After 0.3.0, the 8_01 server changed how handling units are written: a write now
overwrites the whole unit, and `manage` replaces the whole job's arrangement.
0.3.0 could not send the new fields, so those writes lost data without an error.
Upgrade before writing handling units against 8_01.

| Change | What it means for your integration |
|---|---|
| Existing units keep omitted fields | `handling_units.update` and `manage` read the unit and send back every field you left out: dimensions, flags, inventory, nested units, materials. Pass `None` or `[]` to clear. |
| Lock and choice flags | `is_locked`, `is_container_changed`, `is_fill_changed` are typed, required on new units, and preserved on existing ones. A changed container type or fill turns its flag on. |
| `manage` is the whole job | The server deletes every unit the request leaves out. The SDK refuses that unless `delete_omitted` names exactly the units to delete (or is `True`). New units use negative IDs. |
| Bill-of-lading helpers | `form.bol`, `hbl`, `pbl`, `dbl` work against 8_01 again and accept `quote_id`. |
| International booking | `export.to_international_params()` turns an export-data read into the parameters `shipment.validate` and `book_v2` need for a cross-border quote. |
| Partner selection | `partner_id` setting and `api.resolve_partner_id()`: from the token for a partner login, required for a corporate login. |
| Explicit settings | `ABConnectAPI(settings=ABConnectSettings.explicit(...))` builds a client without reading process environment, so one process can hold several logins. |
| Migration mappings | Field-level mappings from the 7_11 parcel, freight-item and option-index contracts: [packing](mapping-8-01/packing.md), [quotes and booking](mapping-8-01/quotes-booking.md), [reads](mapping-8-01/reads.md). |

These were exercised by writes on staging: unit updates and whole-job `manage`, final
overrides with amounts and PRO, and rating, selecting, validating, booking and
cancelling a unit with no inventory. Three server behaviours to design for: an
inactive unit is refused only at booking validation, not at rating; a quote must be
rated with the unit exactly as stored; and per-shipping export data is empty until
saved. The bundled portal Swagger now contains 364 operations.

**Quote flow additions.** `save_new_final_override` creates a final override with its
amounts in one write. `mark_selected` makes a rate selected into a new shipping read as a
selection rather than an estimate. A stale `jobModifiedDate` now raises
`JobModifiedConflictError`, and `is_recorded_override` / `is_carrier_booked` separate an
override that was marked shipped by its PRO from a carrier booking. 8_01 has no call that
deactivates a quote or creates an empty shipping; see
[the quotes mapping](mapping-8-01/quotes-booking.md).

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
