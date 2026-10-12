# 8_01 compatibility decisions

Server source: release `23a8a00cd3883b4e4783de76f3e5e8c8b901660a`.
The complete reproducible operation inventory is [swagger-audit.json](swagger-audit.json).
Generate it with `python scripts/audit_swagger_8_01.py`.

Supported legacy requests use `LegacyRequestWarning` (`UserWarning`), with no
removal deadline. Removed contracts retain their Python entry points and raise
`UnsupportedOperationError` before HTTP. Existing DTO imports remain available.
Old flat-name aliases retain their pre-existing `DeprecationWarning`; that is
separate from this release's compatibility warning.

| Existing operation | Server evidence and SDK decision | Evidence |
|---|---|---|
| `jobs.parcel_items.list` | JobParcelItemsController retains GET as JobParcelItemsDto. Warn and unwrap parcelItems into the established list. | Wrapped-response transport test; source controller. |
| Parcel create/delete/materials list | Controller has GET only. No lossless UUID-to-integer packing adapter; fail locally and point to inventory/handling_units. | Every removed Route is tested for zero HTTP calls. |
| `jobs.add_freight_items`, old `update_item`, `add_item_notes`, item mutation helpers | JobController removes freightitems, replaces item UUID with inventory integer, and explicitly rejects old notes. Use inventory CRUD, handling units, or update_inventory_info. Helpers reject before read/merge/write. | Parameterized helper/route guard tests. |
| `jobs.shipment.book` | JobShipmentController retains V1; quoteOptionIndex was removed. Warn, reject that field, require exactly one active shipping. | Legacy-warning and ambiguity tests. |
| `jobs.shipment.delete` | Legacy DELETE retained with ForceDelete DTO. Warn, require exactly one active shipping, send forceDelete=false. | Transport/selection tests. |
| Legacy export read/save | Optional `shippingId:int?` remains in source although Swagger changes the path. Warn; legacy save requires one active shipping; retain jobItemId. | Round-trip tests; two-shipment export isolation. |
| Explicit export, V2 booking/validation/cancel | Integer shipping IDs for export; quote UUIDs for booking/cancel. Strict nested requests, no legacy warnings. | Staging captures and contract tests; see validation.md for carrier outcome. |
| Legacy ratequotes/accessorials | Actions absent from JobShipmentController. Error before HTTP; use rates, freight_providers, add_ons and lookup.get_addons. | Route/raw-helper guard tests. |
| `get_rates_state` | LegacyJobRatesStateDto retained. Warn; preserve raw response additions in tolerant model. | Warning tests; source. |
| Old freight list/save/final_override/rate_quote | JobFreightProvidersController now returns TransportationQuote and uses finaloverride/ratequote/final routes. Old option indexes/provider arrays cannot preserve semantics; error locally. | Guard tests. |
| New freight quote methods | get_quotes filters use Active/IsOverridden/CarrierAPIs/Shipped; create_final_override, select_rate_quote and save_final_quote preserve shipping IDs and concurrency. | Exact-alias/nested-request tests; live selection and stale-conflict checks. |
| Forms | JobFormController uses quoteId for BOL, packing slip/specification, operations. Missing optional quote warns; old BOL option index errors. Ambiguous convenience selection errors. Editable forms return typed JSON, not a PDF wrapper. | Query tests; typed DTOs; editable-form capture check. |
| Tracking | JobTrackingController has shipment/history/documents with QuoteId and PRO. Unversioned job GET removed; error points to v3. | Source and transport tests. |
| Global shipment document | ShipmentController uses GET /shipment/document with DocId and FranchiseeId. Require franchisee_id before HTTP, return typed ShippingDocument. | Query/required-selector tests. |
| Global accessorials | ShipmentController action throws NotImplementedException. Error locally with lookup replacement. | Source and guard test. |
| Documents list/upload/update/photos | DocumentsController replaces JobItems/itemId with integer inventory and handling-unit associations. Current selectors supported; old UUID association errors before file opening/HTTP. Item-photo helpers accept integer inventory IDs. | Multipart/filter/negative-selector tests. |
| Job email send | POST email now creates a draft by template, not a send operation. Reject old send body; direct callers to current full-send contract. Sending is deliberately not part of live release validation. | JobEmailController source; no-HTTP tests. |
| Payment methods | JobPaymentController retains only jobSubKey exchange. Old financial operations error; exchange returns the payment application URL (sensitive). | Source and no-HTTP tests. |
| Dashboard feeds | Company UUID is a query parameter; body is load options. Old data={companyId:...} is losslessly adapted and warns. | Five feed tests and company LIVE staging discovery. |
| Reports / contact search / timeline | Reports already return lists; contact search's LoadResult is unwrapped by the established list adapter; timeline uses tolerant BaseTimelineTask response. | Existing fixture/transport tests retained. |

## Every removed Swagger operation

The following classification covers all 30 removed entries, including entries
that were placeholders rather than implemented SDK calls. Swagger absence alone
was not used to infer removal.

| Removed path and methods | Source disposition |
|---|---|
| POST `/email/{jobDisplayId}/labelrequest` | JobEmailController explicitly retains `/api/email/{jobDisplayId}/labelRequest`; casing change, same server action. |
| POST `/job/{jobDisplayId}/freightitems` | Absent from JobController; explicit SDK unsupported error. |
| PUT `/job/{jobDisplayId}/item/{itemId}` | JobController now constrains inventoryItemId to int and accepts JobInventoryItemInfoData. New typed method; old UUID method errors. |
| POST `/job/{jobDisplayId}/freightproviders` | Absent from JobFreightProvidersController; use explicit final/ratequote/override contracts. |
| POST `/job/{jobDisplayId}/freightproviders/{optionIndex}/ratequote` | Replaced by ratequote without optionIndex. |
| POST `/job/{jobDisplayId}/parcelitems` | JobParcelItemsController retains GET only. |
| GET `/job/{jobDisplayId}/parcel-items-with-materials` | Absent; handling-unit materials replace it. |
| DELETE `/job/{jobDisplayId}/parcelitems/{parcelItemId}` | Absent; handling-unit deletion uses integer ID. |
| GET `/job/{jobDisplayId}/payment/create`, `/payment`, `/payment/sources` | JobPaymentController has only exchange; three unsupported reads. |
| POST `/job/{jobDisplayId}/payment/ACHPaymentSession`, `/ACHCreditTransfer`, `/attachCustomerBank`, `/verifyJobACHSource`, `/cancelJobACHVerification`, `/bysource`, `/banksource` | Seven removed financial operations; no automatic adapter. |
| GET and POST `/job/{jobDisplayId}/shipment/ratequotes` | Both absent from JobShipmentController. New rates/quote selection contracts. |
| GET `/job/{jobDisplayId}/shipment/accessorials`, POST `/shipment/accessorial`, DELETE `/shipment/accessorial/{addOnId}` | Three absent shipment actions; current job add-ons use different identifiers and arrays. |
| GET and POST `/job/{jobDisplayId}/shipment/exportdata` | Both retained by optional shippingId controller route. |
| GET `/job/{jobDisplayId}/tracking` | JobTrackingController has shipment-specific actions; V3 controller remains. |
| GET `/shipment/document/{docId}` | ShipmentController moves DocId to query and requires franchisee context. |
| GET `/SmsTemplate/notificationTokens` | Legacy unimplemented placeholder remains explicit NotImplementedError; no claim of SDK compatibility. |
| POST `/webhooks/stripe/checkout.session.completed` | Legacy unimplemented webhook placeholder; not an SDK business-operation adapter. |
| GET `/Values` | Legacy unimplemented placeholder; not counted as current schema coverage. |

## Changed-operation audit

The 221 changed operation definitions are individually listed with change
categories in swagger-audit.json. Most add response/error metadata to previously
unspecified Swagger operations; that is not evidence of a changed request.
Existing unrelated fixture-backed wrappers remain in place, and current schema
gaps remain visible as unimplemented placeholders.

Actual request/selector changes affecting the existing SDK are resolved above.
The gridsettings, jobAccessLevel, and admin hierarchy changes apply to existing
unimplemented placeholders. They remain explicitly unimplemented. Reports' new
array annotations already match SDK list responses. Editable forms, freight
quotes, dashboard envelopes, document associations, and email creation required
runtime changes. Form/tracking selectors use the server's exact casing.

Regression reporting does not certify unsupported contracts. The historical
gate baseline is retained; removed contracts are checked by no-HTTP migration
tests instead of being counted as working operations. Historical request and
response fixtures stay available to validate retained imports.
