# 8_01 mapping: reading what is on file

Answers to four read-side questions from callers migrating off the option-index contract.
Companion to [quotes and booking](quotes-booking.md) and [packing](packing.md).

Evidence tags:

- **[staging]** read on staging on 2026-11-22 (jobs 5483351 and 13829427, corporate login; reads only).
- **[source]** read in the server source, branch `release` at `7245c94cc`; file and symbol given.
- **[assumed]** not checked.

## 1. Initial versus final options

**Answer.** "Initial" no longer exists as a concept. 8_01 dropped the option index: the column
is renamed `ObsoleteOptionIndex` and no code reads it. A shipping has one *current* quote and a
*history* of earlier ones. The current quote is the shipping's active quote; if none is active,
it is the one with the highest `order_in_shipping`. Everything else in that shipping is history.
A client cannot tell from 8_01 data whether a historical quote was once an "initial" estimate.

| Question | What to read | Evidence |
|---|---|---|
| Which quote is on file for a shipping? | `get_quotes(job)` filtered by `shipping_id`; take `active`, else highest `order_in_shipping`. | [source] web client `transportation-quotes.selector.ts` `selectCurrentQuotes`, `isPreferredCurrentQuote` |
| Which quote will ABConnect treat as the one to book when none is named? | The active, not-yet-accepted quote of the non-archived shipping with the highest id. Name the quote instead: `book_v2(quote_id=...)`. | [source] `FreightQuoteOptionsRepository.SelectBookingShipmentProviderAsync` |
| Was it booked or shipped? | `shipment_accepted` (and `shipment_accepted_date`). For an overridden quote this means "has a PRO number". | [source] `TransportationQuoteMappingExtensions.UpdateEditableFields` |
| Is it a manual override (old 5 and 6)? | `is_overridden`. | [source] |
| Parcel or freight family (old 3, 4 versus 1, 2)? | `shipment_type` (Parcel UUID versus LTL and the others). | [staging] |
| Initial versus final (old 1 versus 2, 3 versus 4)? | Not recoverable. | [source] no reader of `ObsoleteOptionIndex` |

**`order_in_shipping`.** A sequence within one shipping, 1 upward, capped at 255. A new quote
gets the highest value in its shipping plus one. The portal lists a shipping's quotes by it,
descending, so the highest is the newest. It is not the old option index.
[source] `TransportationQuoteMappingExtensions.NextOrderInShipping`; web client `nextOrderInShipping`, `selectQuoteHistory`

**How migrated jobs look.** [source] `ABConnect.DB/Scripts/Version8.01/MigrateJobsToInventoryHandlingUnits.sql`, steps 17 to 19a

- Each active non-override quote got a shipping of its own. Inactive quotes went to the shipping of
  the newest active one. Both override quotes (5 and 6) share one shipping with no contents.
- Within a shipping the order was assigned by active last, then old option index, then created
  date. So where an initial and a final quote of one family landed in the same shipping, the
  final has the higher `order_in_shipping`. That is the only trace of the old distinction, and it
  holds for migrated rows only.
- Shippings were created in old option order, so on a migrated job ascending `Shipping.id` reads
  freight, then parcel, then override.

**Consequences for a caller that used "lowest active option index" as what is on file.**

- There can be several active quotes on a job, one per shipping. Decide per shipping.
- A shipping can have no active quote. [staging] job 13829427, shipping 756679 has one inactive quote.
- An active quote that is not accepted is a selection, not a booking. Use `shipment_accepted` for "booked".
- `jobs.get(...).freight_providers` lists the job's **active** quotes only, across all shippings,
  in the old row shape. Its `optionIndex` is still serialised and is always 0. [staging]; [source] `JobService.GetOwnerJobPortalInfo`

## 2. `totalSell`

**Answer.** On 7_11 `totalSell` was the **sell price of the job's transportation pricing rows**
for that option's family (fee plus accessorial), and 0 for an inactive option. It was never the
carrier amount. On 8_01 the Portal API does not return that figure anywhere, per quote or per
shipping, so the SDK cannot provide it. The per-quote amounts that are returned
(`freight_amount`, `accessorial_amount`) are **cost**.

| | 7_11 | 8_01 |
|---|---|---|
| Source | `job.Pricing` rows with parent Transportation and service category = the option family's fee or accessorial; `SellPrice` summed. Inactive option → 0. [source] `JobShipmentPlanService.SelectPricedFreightProviders` at `e7cdde1c1~1` | Pricing rows carry `FreightQuoteId` linking them to a quote; categories are `FreightFee` and `FreightAccessorial`. [source] `JobPricing.FreightQuoteId`, `TransportationPricingService` |
| Returned by the API | `totalSell` on each `freightproviders` row | Not returned. No schema in the staging Swagger has `freightQuoteId`, `sellPrice` or `costPrice` for job pricing. [staging] Swagger |

What a client can read today:

| SDK call | Field | Meaning | Evidence |
|---|---|---|---|
| `jobs.freight_providers.get_quotes(job)` | `freight_amount`, `accessorial_amount` | Carrier cost of that quote. | [staging] |
| `jobs.get(job)` | `total_sell_price` | Sell total of the **whole job**, all services, from the job summary snapshot. Owner or customer access only. | [staging]; [source] `JobService.GetOwnerJobPortalInfo` |
| `jobs.get_price(job)` | `total_sell_price`, `prices` | Same whole-job total. `prices` is a per-category breakdown only for third-party-logistics jobs; null otherwise. | [staging]; [source] `JobService.GetJobPriceAsync` |
| `jobs.get(job)` | `prices` | Empty list on both staging jobs. | [staging] |

**What would be needed.** A server endpoint (or fields on the quote) exposing the transportation
pricing rows for a quote: sell price, cost price and `freightQuoteId`. Until then a caller that
showed `totalSell` as "the on-file price" has no equivalent figure. Showing
`freight_amount + accessorial_amount` instead would show cost where sell used to be.

## 3. The job read

**Answer.** `GET /job/{id}` on 8_01 no longer returns `items` or `freightItems` at all. The keys
are absent from the response, and the SDK's `Job.items` and `Job.freight_items` are `None`.
They were removed from the Portal API in July 2026. Read goods from `jobs.inventory.get_all` and
packed units from `jobs.handling_units.get_all`.

Top-level keys returned for both staging jobs [staging]:

`accessLevel`, `activeOnHoldInfo`, `agentPaymentInfo`, `bookedDate`, `customerContact`,
`deliveryContact`, `documents`, `expectedDeliveryDate`, `expectedPickupDate`, `freightInfo`,
`freightProviders`, `isCancelled`, `jobDisplayId`, `jobMgmtSubId`, `jobSummarySnapshot`,
`jobType`, `labelRequestSentDate`, `modifiedDate`, `notes`, `ownerCompanyId`, `paymentInfo`,
`pickupContact`, `prices`, `slaInfo`, `statusId`, `timelineTasks`, `totalSellPrice`, `writeAccess`.

| 7_11 field on the job read | 8_01 | Read instead | Evidence |
|---|---|---|---|
| `freightItems` (freight finals) | absent | `jobs.handling_units.get_all(job)`: active top-level units with a freight container type. See [packing](packing.md) section 1. | [staging]; [source] commit `f026ef705` "Remove legacy Portal API: parcel/fright items" |
| `items` with `jobItemID` | absent | `jobs.inventory.get_all(job)`: integer `id`. The legacy item UUID is not exposed by any API. | [staging]; [packing](packing.md) section 2.5 |
| `freightProviders` | present | Active quotes only, old row shape plus `shippingId`, `orderInShipping`, `isOverridden`; `optionIndex` always 0. Prefer `get_quotes`, which also returns inactive quotes. | [staging] |
| `freightInfo` | present | `proNum`, `providerCompanyCode`, `providerCompanyName`, `shippingName`, `transportationState`, `transportationStateDescription`. One summary for the job. | [staging] |
| `modifiedDate` | present | The value to send as `jobModifiedDate` on writes. | [staging] |
| no inventory or handling-unit collections | | Not embedded in the job read; use the two endpoints above. | [staging] |

The SDK's `Job` model parses the 8_01 response with no unknown fields. [staging]

## 4. Bill-of-lading helpers

**Answer.** Without a quote id the server does not pick a shipping at all. It renders a
**non-carrier** BOL: no carrier, no PRO, and the item lines are the job's whole inventory list,
whatever the shippings contain. With `quoteId` it renders a carrier BOL for that quote, and the
item lines are the handling units of that quote's shipping. So on a job with two active shippings
the unselected call returns neither shipping's document. Name the quote.

| Call | Server behaviour | Evidence |
|---|---|---|
| `bill-of-lading` with `quoteId` | Carrier BOL. Carrier, PRO and bill-to come from that quote. Lines: units in the quote's shipping that are active, quantity above zero, rateable container type. | [source] `BillOfLadingDbMappingExtensions.ToBOLJobModel`, `BillOfLadingJobFormGenerator.FillJobItemsForBOL` |
| `bill-of-lading` without `quoteId` | Non-carrier BOL. Lines: the job's active top-level inventory items. No quote or shipping is consulted. | [source] same |
| `shipmentPlanId` | Chooses the leg (addresses and parties), independent of the quote. The house plan id selects the house BOL. | [source] `ToBOLJobModel` |

Under the empty-inventory decision this matters twice: a carrier BOL lists handling units, so it
is unaffected; a non-carrier BOL lists inventory, so it shows the job's inventory records and
nothing about the boxes.

**`form.shipments` on 8_01.** Returns one row per leg plus a `House` row. The carrier leg's row
carries `freight_quote_options_id`, the active quote it was joined to. [staging]

| Job | Rows (`transport_type`, quote id present) |
|---|---|
| 5483351 | `PickUp` (no), `PickUp (PARCEL)` (yes), `House` (no) |
| 13829427 | `PickUp` (no), `PickUp (LTL)` (yes), `House` (no) |

The procedure joins the carrier leg to **every** active quote of the job, with no shipping
filter, so a job with two active quotes gets that leg twice, once per quote.
[source] `job.SelectFormsShipmentPlanByJobID`. Not seen on staging: job 13829427 has two active
shippings but only one active quote.

**The SDK helpers `form.bol`, `hbl`, `pbl`, `dbl` do not work against 8_01.** [staging]

| Helper | Result on both staging jobs | Cause |
|---|---|---|
| `bol` | `ValueError: Expected one shipment plan` | Looks for `transport_type` `LTL` or `Delivery`; 8_01 returns `PickUp (LTL)`, `PickUp (PARCEL)`. |
| `dbl` | `ValueError: No LTL shipment plan exists` | Same. |
| `hbl`, `pbl` | `ValidationError` on `shipment_plan_id` | The helper passes the plan's UUID object where the params model requires a string. Fails before any request. |

None of them warns, and none can pass a quote id. They never reach the unselected-shipping case
because they fail first.

**Call instead** (both forms return a PDF on staging job 13829427) [staging]:

```python
plans = api.jobs.form.shipments(job_id)
carrier_leg = next(p for p in plans if p.freight_quote_options_id == quote_id)   # or choose by leg
pdf = api.jobs.form.bill_of_lading(
    job_id,
    shipment_plan_id=str(carrier_leg.job_shipment_id),
    quote_id=str(quote_id),
)
# House BOL: shipment_plan_id=str(house_plan.job_shipment_id), with or without quote_id.
```

`bill_of_lading(job_id, quote_id=...)` alone also works and emits no warning;
`bill_of_lading(job_id)` emits `LegacyRequestWarning` and returns the non-carrier document.

## 5. Telling an estimate from a selected rate

**Answer.** No field marks a quote as "the estimate the job came with" or as "a rate someone
selected". Both are ordinary quotes. What the data does record is whether a quote has been
**superseded, touched or acted on** since it was created, and that is enough to recognise an
untouched estimate in every case except one: a rate selected into a brand-new shipping looks
exactly like an estimate until something else happens to it. A client that needs that case must
keep its own record of what it selected.

### What exists before anyone selects a rate

| Job | State | Evidence |
|---|---|---|
| Created on 8_01 from a quote | One shipping, holding one **active, non-overridden** quote: the carrier and amounts the job was priced with. Created by the server during job creation, stamped with the creating user. | [source] `JobService` (job creation builds a `TransportationQuote` with `Active = true`, `IsOverridden = false`, then `SaveQuoteAsync`). No natively created 8_01 job was available on staging to confirm. |
| Migrated from 7_11, initial option only | One shipping with that quote active, `order_in_shipping` 1. | [staging] jobs 5506118, 5523070 before any write |
| Migrated from 7_11, initial and final of one family | Same shipping; the final is active with the higher `order_in_shipping`, the initial inactive below it. | [source] migration step 19a; [staging] jobs 14423857, 12679699 (order 1 inactive, order 2 active and shipped) |

### What each field can and cannot tell you

| Field | Meaning | Use |
|---|---|---|
| `shipment_accepted` | Booked, or an override with a PRO. | True: not an estimate. |
| `is_overridden` | Entered by hand (final override). | True: not an estimate. |
| `order_in_shipping` | Sequence within the shipping; each new quote is max + 1. | Greater than 1: this quote replaced an earlier one in the same shipping, so it is a selection. |
| other quotes in the same shipping | History. | Any present: the active one is a selection. |
| `modified_date` versus `created_date` | `save_final_quote` updates the quote in place and restamps `modified_by` / `modified_date`. A new quote has both stamps set at the same moment. | Modified later than created: someone saved it as final. [staging] job 5506118 |
| `created_by` | User who created the quote through the 8_01 API. **Null on every quote migrated from 7_11.** | Null means "migrated", nothing more. |
| `created_date` on a migrated quote | The server substitutes the **current time** on every read when the stored value is null. | Never compare it for a quote whose `created_by` is null. [staging]: the value changed between reads. |
| `quote_snapshot`, `active`, amounts | Same on an estimate and a selection. | No use. |
| old option index | Kept in the database as `ObsoleteOptionIndex`; not returned by any endpoint. | Not available. |

### What a write leaves behind

| Write | Trace |
|---|---|
| `select_rate_quote` with `shippingId` | A new quote, `order_in_shipping` = previous max + 1; the others in the shipping become inactive. [staging] job 12679699 |
| `select_rate_quote` without `shippingId` | A new shipping with one quote, `order_in_shipping` 1. **Indistinguishable from an estimate.** [staging] job 5523070 |
| `save_final_quote` on an existing quote | Same quote id; `modified_by` and `modified_date` restamped; the others inactive. [staging] job 5506118 |
| `create_final_override` | A new quote with `is_overridden` true, next order. [staging] job 5506118 |
| `book_v2` | `shipment_accepted` true and a PRO. [staging] job 5523070 |

### A rule that follows from this

Treat the active quote of a shipping as an **untouched estimate** only when all of these hold;
otherwise it is a selection:

- it is the only quote in its shipping, with `order_in_shipping` 1;
- `is_overridden` is false and `shipment_accepted` is false;
- it has not been modified after creation: `modified_by` is null (migrated quote), or
  `modified_date` equals `created_date` to within a few seconds (quote created on 8_01).

SDK 0.3.1 implements this rule as `ab.api.selection.is_untouched_estimate(quote, quotes)`.

Known blind spot: a rate selected into a **new** shipping satisfies all three. The portal's rates
window passes the shipping it was opened for when it has one, so a person re-selecting a rate for
an existing shipping produces `order_in_shipping` above 1 and is recognised; it sends no
`shippingId` only when the shipping does not exist yet. On jobs that are not third-party-logistics
the portal previews the rate and persists the quote with the job save instead.
[source] `rates-window.component.ts`, `transportation-quotes.service.ts`. A client's own
selections into new shippings are the case it must record for itself.
