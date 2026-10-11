# Preparing for ABConnect 8_01

**Target: SDK 0.3.0. Status: migration preview.** The inventory/handling-unit and
multiple-shipment SDK changes are not implemented yet. This page records the
intended migration contract; runnable replacement calls will be added with the
implementation and validated against real responses.

## Inventory and handling units

Treat inventory as the items being handled and handling units as the units used
to pack and transport them. New integrations should use that common model for
both parcel and freight rather than maintain two independent item workflows.

Review code that creates, saves, deletes, or replaces parcel/freight items.
Record the fields and return values it depends on, especially quantities,
dimensions, weights, values, and packing relationships. Compatibility adapters
must preserve that meaning and unrelated records during an update.

## Multiple active shipments

The development SDK now accepts the optional `quote_id` keyword on
`api.jobs.form.packing_slip`, `api.jobs.form.packaging_specification`, and
`api.jobs.tracking.shipment`. These read-only selectors are validated locally
against the server contract; quote-selected live captures are still pending.
The larger booking and inventory migration remains planned.

A job can have more than one active shipment. Keep its shipping records as a
collection and retain the identifiers needed by each operation.

| Identifier | Meaning and observed server use |
|---|---|
| Job display ID | Selects the job; does not uniquely select a shipment within it. |
| `Shipping.id` / `shippingId` | Selects a shipping record; used for shipment-specific export data. |
| `quoteId` | Selects a quote; required by the V2 booking request and used by the cancellation route. |
| `shipmentId` | Returned carrier shipment identifier; keep separate from shipping-record and quote IDs. |

Review helpers that choose the first rate or shipment, store one shipment on a
job object, cancel a job's shipment implicitly, or retrieve one set of export
data. The migrated workflow must select its target explicitly when several are
possible. An ambiguous mutation must ask for the missing context before sending
a request.

## Compatibility policy

The 0.3.0 target is **supported legacy calls plus actionable warnings**. Existing
public entry points remain available through a retained server route or a
verified SDK adapter. Each warning should identify the legacy usage and the
canonical replacement, with no removal deadline attached to this release.

Not every legacy server operation survives in 8_01. The inspected source retains
legacy booking and parcel-item reads, while the old parcel write actions are
absent from the inspected controller. An adapter is a release requirement to
investigate and verify, not something the current SDK already provides.

| Area | Preparation now | Evidence needed before release |
|---|---|---|
| Parcel and freight item writes | Inventory callers, fields, and replace-all assumptions. | Lossless adapter or documented unsupported mapping; preservation of unrelated items. |
| Booking | Keep selected quote IDs and return-value expectations. | V1/V2 request and response fixtures; warning behavior; booking validation. |
| Export data | Retain the shipping-record ID. | Targeted get/save and verified legacy fallback semantics. |
| Cancellation and tracking | Separate quote, shipping, and carrier identifiers. | Operation-specific selectors and proof another active shipment is unaffected. |

## Before upgrading an application

1. Record its installed SDK version and the server release in each environment.
2. Identify uses of legacy item APIs and assumptions of one shipment per job.
3. Preserve the completed Catalog migration, including bulk-upsert `platformId`.
4. On the release candidate, exercise canonical and compatibility calls against
   approved staging data and review every compatibility warning.
5. Verify two active shipments on one job, with targeted updates that leave the
   other shipment unchanged. Confirm response models against real captures.

The final release guide must replace this preview with working Python examples,
the completed compatibility matrix, warning handling, and verified limitations.
See [What's New](whats-new.md) and the [DX goals](dx-roadmap.md).
