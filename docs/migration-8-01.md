# Migrating to ABConnect 8_01

SDK **0.3.0** targets ABConnect **8_01**. Inventory describes the goods, handling
units describe their packing, and each job can have multiple active shipments.
The examples below use provisioned staging credentials and operator-selected IDs.

## Inventory and handling units

Inventory describes the goods. Handling units describe how those goods are packed
and transported. The same handling-unit model covers parcel and freight.

```python
import os
from ab import ABConnectAPI

api = ABConnectAPI(env="staging")
job_id = int(os.environ["AB_TEST_PACKING_JOB_ID"])
inventory = api.jobs.inventory.get_all(job_id)
handling_units = api.jobs.handling_units.get_all(job_id)
```

`inventory.create()` and `inventory.update()` require `quantity`, `is_active`,
and `sequence_no`. Inventory sequence numbers start at 1; handling-unit sequence
numbers may start at 0. Model validation checks the server's dimension, quantity,
value, and text limits before HTTP.

For an approved test job, create a unit containing existing inventory:

```python
unit = api.jobs.handling_units.create(
    job_id,
    quantity=1,
    is_active=True,
    sequence_no=0,
    inventory_items=[{
        "id": int(os.environ["AB_TEST_INVENTORY_ITEM_ID"]),
        "count": 1,
    }],
)
```

Use `add_inventory`, `update_inventory`, and `delete_inventory` to change one
content relationship. The corresponding `*_content_unit` methods manage nested
handling units. `add_materials` adds material rows; `update_material` and
`delete_material` target one existing row. **`replace_materials` replaces the whole
material list, and `manage` submits a complete handling-unit arrangement.** Read
and retain the current arrangement before using those operations.

Nullable write fields preserve explicit `None`, allowing a relationship or value
to be cleared. Omitted fields stay omitted in the JSON body. A server PUT can
still replace fields: consult its contract and include the values to retain.
The SDK does not perform a hidden read/merge/write or force a concurrency override.

## Select the intended shipping record

| Identifier | Use |
|---|---|
| Job display ID | Identifies the job, not an individual shipment. |
| `Shipping.id` / `shippingId` | Integer shipping-record ID; used for export data. |
| `quoteId` | UUID used for booking, validation, cancellation, and selected forms/tracking. |
| `shipmentId` | Carrier identifier returned by booking; never substitute it for either selector above. |

The collection preserves active and archived records and their handling-unit and
quote relationships. This selection works when a job has two or more active
shipments and does not pick the first result:

```python
from ab.api.selection import select_shipping

shippings = api.jobs.shippings.get_all(job_id)
selected = select_shipping(
    shippings,
    shipping_id=int(os.environ["AB_TEST_SHIPPING_ID"]),
    quote_id=os.environ["AB_TEST_QUOTE_ID"],
)
```

`select_shipping` rejects zero matches, multiple matches, archived records,
unknown IDs, and conflicting shipping/quote pairs. Without selectors it succeeds
only for exactly one explicitly active record. This is a local check against the
supplied collection; server-side authorization and concurrency checks still apply.

## Rates, booking, and cancellation

`api.jobs.rates.request()` accepts explicit `handling_units`, `origin_address`,
`destination_address`, and `ship_out_date`. Preserve its opaque `rates_key` and
the chosen provider's `carrier_code` and account ID.

`rates.select_quote()` previews a quote; it does **not** persist a shipping record.
Save the chosen rate with `freight_providers.select_rate_quote()`:

```python
saved = api.jobs.freight_providers.select_rate_quote(
    job_id,
    data={
        "ratesKey": os.environ["AB_TEST_RATES_KEY"],
        "carrierCode": os.environ["AB_TEST_CARRIER_CODE"],
        "active": True,
        "shippingId": selected.id,
        "handlingUnits": [{
            "id": int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            "quantity": 1,
        }],
        "jobModifiedDate": os.environ["AB_TEST_JOB_MODIFIED_DATE"],
    },
)
if not saved.success:
    raise ValueError(saved.error_message)
quote_id = str(saved.transportation_quote.id)
```

Supply the selected provider's `carrierAccountId` when required by that rate.
Omit `shippingId` intentionally to create a new shipping record. Retain unrelated
shipping records and use the returned quote ID for booking and cancellation.
Use `lookup.get_container_types()` to discover transportation containers:
packing container type IDs and transportation container type IDs are different.
For example, staging transportation `BOXES` is ID 25; packing `Stock Box` is ID 5.
Discover them in your environment instead of hard-coding these observed values.

Validate an explicit quote before booking:

```python
request = {
    "quote_id": os.environ["AB_TEST_QUOTE_ID"],
    "ship_out_date": os.environ["AB_TEST_SHIP_OUT_DATE"],
    "job_modified_date": os.environ["AB_TEST_JOB_MODIFIED_DATE"],
}
validation = api.jobs.shipment.validate(job_id, **request)
if not validation.valid:
    raise ValueError(validation.errors)
# Execute only when the selected shipment is ready to book:
# booking = api.jobs.shipment.book_v2(job_id, **request)
```

`book_v2()` returns `success`, `error_message`, `shipment_id`, and
`job_modified_date`; this response does not contain V1's document collection.
Do not assume an HTTP 200 means booking succeeded: inspect `success`.

`shipment.cancel(job_id, quote_id, job_modified_date=...)` targets the quote UUID
in its path. Inspect `success` and `override_error` even after HTTP 200. If carrier
cancellation fails, `force_delete=True` can remove ABConnect's booking state;
it does **not** confirm that the carrier cancelled it. The staging release test
exercised this failure and forced-removal path.

Supply a fresh modification timestamp for writes. A refresh-policy conflict
requires re-reading the job and reconciling the edit; `force_update=True` does
not bypass that policy. A local selector check cannot prevent a concurrent change.

## Shipment-specific export data

```python
export = api.jobs.shipment.get_shipping_export_data(job_id, selected.id)
if export is not None:
    edit = export.to_request()
    edit.invoice_number = os.environ["AB_TEST_INVOICE_NUMBER"]
    # Save only after reviewing the complete replacement export body:
    # api.jobs.shipment.save_shipping_export_data(
    #     job_id, selected.id, **edit.model_dump(by_alias=True, exclude_unset=True)
    # )
```

`to_request()` retains commodity `jobItemId`, packing information, and explicit
nulls. It removes only the computed `fullDescription`; unknown future fields
raise validation errors rather than being silently lost from a replacement write.

Packing-slip and packaging-specification methods accept `quote_id`; shipment
tracking accepts the same selector alongside the carrier PRO number.

## Compatibility notices

Supported legacy calls emit `LegacyRequestWarning`, a visible `UserWarning` with
a replacement call. It announces no removal schedule. Canonical explicit calls
emit no compatibility notice.

```python
import warnings
from ab import LegacyRequestWarning

# Optional, after reviewing and migrating affected callers:
warnings.filterwarnings("ignore", category=LegacyRequestWarning)
```

Legacy job-level booking, deletion, and export writes first require exactly one
active shipping record. They fail before mutation when selection is ambiguous.
Booking's old `quoteOptionIndex` field is rejected with guidance to `book_v2`;
8_01 no longer reads that field. Legacy export saves now preserve `jobItemId`.

Removed parcel/freight writes, item helpers, rate/accessorial routes, old payment
routes, and email sending raise `UnsupportedOperationError` before HTTP. Their
names and legacy DTO imports remain available, but the server no longer supports
their contracts. See the complete [compatibility matrix](https://github.com/bmonson-annex/annex-abconnect/blob/main/specs/038-abconnect-8-01/compatibility.md).

| Previous usage | 8_01 replacement |
|---|---|
| Parcel/freight item writes and item helpers | `jobs.inventory` and `jobs.handling_units` |
| Freight-provider list returning legacy providers | `jobs.freight_providers.get_quotes()` returning transportation quotes |
| Provider option indexes and provider-list saves | `select_rate_quote`, `create_final_override`, and `save_final_quote` with explicit identifiers |
| Shipment accessorial writes | `jobs.add_ons.get_all/save/delete` |
| Document `job_items` / item UUIDs | Integer `inventory_item_ids` and `handling_unit_ids` |
| Global shipment document path parameter | `shipments.get_shipment_document(doc_id, franchisee_id=...)` |
| Editable invoice/USAR assumed to be PDF | Typed JSON `EditableFormContent` |
| Legacy payment operations | `jobs.payment.exchange()` for the current payment-app URL |

Older flat-method alias `DeprecationWarning`s predate this release and are distinct
from the supported-request notices. Never ignore `UnsupportedOperationError` as
if a write had succeeded.

## Reproduce staging validation


For the authorized disposable staging environment, discover candidates from
company LIVE's home grids with:

```bash
python scripts/discover_staging_jobs.py --company LIVE --scan 10
```

The script requests estimates, inbound, in-house, and outbound grids, then prints
job IDs and inventory/handling-unit/shipping counts. It performs reads only and
requires staging authentication. An explicit `--env-file` can select the local
credential file; the environment remains staging.

The runnable examples are `examples/jobs/inventory.py`, `handling_units.py`,
`shippings.py`, and `transportation.py`. Reads require operator-selected staging
IDs. Writes additionally require `AB_RUN_MUTATIONS=1`, an operation name, and a
reviewed request JSON file; each invocation performs one chosen mutation.

Reviewed captures and the mutation/isolation results are recorded in the
[release validation report](https://github.com/bmonson-annex/annex-abconnect/blob/main/specs/038-abconnect-8-01/validation.md).
The scripts under `scripts/verify_*_8_01.py` are release verification tools;
read their targets and effects before running them. The booking script creates
a carrier booking and reports failure if normal cancellation fails.
The completed Catalog migration still requires bulk-upsert `platformId`.
