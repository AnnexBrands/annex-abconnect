# 8_01 mapping: quotes, final overrides and booking

For callers migrating from the option-index freight-provider contract (ABConnect 7_11,
SDK 0.2.x) to the quote contract (ABConnect 8_01, SDK 0.3.x).

Evidence tags used below:

- **[staging]** read on staging on 2026-11-22 (reads only).
- **[source]** read in the server source, branch `release` at `7245c94cc`; file and symbol given.
- **[assumed]** not checked.

No write in this document has been run on staging yet.

## 1. The model changed, not just the names

| 7_11 | 8_01 |
|---|---|
| A job has up to six provider *options*, addressed by `optionIndex` 1 to 6. | A job has one or more *shippings* (`jobs.shippings.get_all`). Each shipping holds handling units and any number of *quotes*. |
| Options 1, 2 freight; 3, 4 parcel; 5, 6 override. Option 6 is the "final override". **[source]** removed `JobConstants.ProviderPriceCategories` | No index. A quote is identified by its UUID `id`, belongs to `shippingId`, and carries `isOverridden`, `active` and `orderInShipping`. |
| "One active option-6 row per job." | **One active quote per shipping.** Saving a final quote or creating a final override deactivates every other quote of the same shipping. **[source]** `FinalQuoteService.DeactivateExceptFinal`, `JobShipmentPlanService.DeactivateOtherQuotesForShipping` |
| `shipmentType` is a string. | `shipmentType` is a UUID (table in section 6). |
| Booking by `quoteOptionIndex`. | Booking by quote UUID. |

A job with two active shippings has two active quotes. Code that assumed one active row per
job must select by `shippingId` first.

## 2. Reads: `freight_providers.list` → `freight_providers.get_quotes`

`jobs.freight_providers.list()` raises `UnsupportedOperationError` on 0.3.x. Use
`jobs.freight_providers.get_quotes(job_display_id, active=..., is_overridden=..., shipped=...,
shipment_types=[...], carrier_apis=[...])`, which returns `list[TransportationQuoteResult]`.
All filters are optional and combine. **[staging]** `active=True` and `is_overridden=True`
filter as expected.

| `PricedFreightProvider` (7_11) | `TransportationQuoteResult` (8_01) | Note |
|---|---|---|
| `optionIndex` | none | Derive the meaning: old option 6 = `is_overridden` and `active`; old option 4 = `active`, not overridden, `shipment_type` = Parcel. `order_in_shipping` is a display order within one shipping, not the old index. |
| `shipmentType` (str) | `shipment_type` (UUID) | Section 6. |
| `providerAPI` | `provider_api` | Same integers. 3 = UPS, 2 = FedEx, 7 = Maersk. **[staging]** |
| `providerId` | `provider_id` (UUID) | Carrier company id. |
| `providerCode` | `provider_code` | **[staging]** for example `UPS03`. |
| `providerCompanyName` | `provider_company_name` | |
| `totalSell` | none | The quote carries cost: `freight_amount` and `accessorial_amount`. Sell lives in job pricing. **[assumed]** that `totalSell` was not simply their sum; check what the 7_11 value meant before replacing it. |
| `transit` | `service_days` | |
| `quoteNo` | `quote_number` | |
| `proNum` | `pro_number` | |
| `optionActive` | `active` | |
| `shipmentAccepted`, `shipmentAcceptedDate` | `shipment_accepted`, `shipment_accepted_date` | For an overridden quote the server sets accepted = "has a PRO number". **[source]** `TransportationQuoteMappingExtensions.UpdateEditableFields` |
| `obtainNFMJobState` | `quote_snapshot` | Opaque snapshot of the units the quote was made for. |
| `usedCarrierAccountInfo` | `used_carrier_account_info` | |
| not present | `id`, `shipping_id`, `is_overridden`, `order_in_shipping`, `bill_to_franchisee_id`, `bill_to_franchisee_code`, `estimated_arrival`, audit fields | New. |

To read "what is on file for this shipping":

```python
shippings = api.jobs.shippings.get_all(job_id)          # ids, units, quote ids per shipping
shipping = select_shipping(shippings, shipping_id=...)   # ab.api.selection; rejects ambiguity
on_file = [q for q in api.jobs.freight_providers.get_quotes(job_id, active=True)
           if q.shipping_id == shipping.id]              # zero or one
```

## 3. Writes

| 7_11 call | 8_01 call | Use |
|---|---|---|
| `final_override(option_index=6, ...)` | `create_final_override` then `save_final_quote` | Record a carrier choice made outside ABConnect (section 4). |
| `rate_quote(option_index, data={ratesKey, carrierCode, ...})` | `select_rate_quote(data={ratesKey, carrierCode, shippingId, handlingUnits, ...})` | Persist a rate ABConnect returned (section 5). |
| `save(data=[providers])` | `save_final_quote(data={quote, handlingUnits?, jobModifiedDate})` | Make one quote the final one of its shipping. |
| raw `POST shipment/ratequotes` | `jobs.rates.request(...)` | Ask ABConnect for rates. |

All three 8_01 writes check the job-modified timestamp with the *refresh* policy: send the
`jobModifiedDate` you last read; a stale one is rejected and `forceUpdate` does not bypass it.
**[source]** `[CheckJobModification(JobModificationConflictResolution.Refresh)]`; verified on staging for 0.3.0.
Each response returns the new `jobModifiedDate`; carry it into the next write.
A stale stamp is HTTP 400 with `refreshRequired` in the body. From 0.3.1 the SDK raises
`ab.JobModifiedConflictError` for it (a `RequestError` subclass, so existing handlers still catch it),
with `modified_by` and `refresh_required`. Nothing was written; read the job again before retrying.
**[staging]** job 5506118, 2026-11-23.

### What each write does on the server **[source]**

**`create_final_override`** — `POST freightproviders/finaloverride`, `JobShipmentPlanService.CreateOverriddenQuoteAsync`

- Request fields: `providerID` (UUID, must be an active carrier company), `shipmentType` (UUID,
  defaults to LTL), `providerCompanyCode`, `providerCompanyName` (max 50), `proNum` (max 50),
  `shippingId`, `freightQuoteOptionsId`, `jobModifiedDate`, `forceUpdate`.
- **It does not accept amounts or an active flag.** The amounts tools wrote on option 6 cannot
  be sent here; the quote is created with no freight or accessorial amount.
- It always creates a **new** quote (new UUID), overridden and active, and deactivates the other
  quotes of that shipping. Calling it twice gives two quotes, the first inactive. It is not an update.
- `freightQuoteOptionsId` is not "the quote to update". It names the quote of an existing carrier
  task that should be re-pointed to the new quote.
- `shippingId` omitted, or not an active shipping of the job: the server **creates a new shipping**
  containing every active top-level unit with a rateable container type. Pass the existing
  `shippingId` whenever there is one, or every approval adds a shipping.
- It snapshots the job's rateable units into the quote and adds transportation fee and
  accessorial pricing rows to the job.
- Nothing in this path reads inventory. A shipping whose units have no inventory is handled the
  same as any other (answers A-17 at source level; not run).
- Returns `success`, `error_message`, `freight_quote_options_id` (the new quote id), `shipping_id`,
  `job_modified_date`.

**`save_final_quote`** — `POST freightproviders/final`, `FinalQuoteService.Save`

- `quote.shippingId` is required and must be a shipping of the job.
- `quote.id` matches a quote of that shipping: that quote is updated. Otherwise a new quote is added.
- The quote becomes the only active quote of the shipping.
- For an overridden quote these fields are **replaced with what you send**, so an omitted field
  becomes null: `providerCompanyName`, `shipmentType`, `proNumber`, `billToFranchiseeId`,
  `providerId`, `freightAmount`, `accessorialAmount`, `quoteNumber`, `serviceDays`.
  `orderInShipping` is kept when omitted. Read the quote and send it back with your change.
- An overridden quote with a non-blank `proNumber` is marked shipped (`shipmentAccepted=true`).
- It does not set the provider code; only `create_final_override` does.
- `handlingUnits`, when given, makes the shipping's contents exactly those units and quantities.
  Omit it to leave the shipping's contents alone.
- Job pricing cost follows the quote; sell price is left alone except on third-party-logistics jobs.
- Amount limits: 0 to 9,999,999.99. Service days 0 to 10,000. Quote number max 50.

## 4. The direct carrier path (label bought outside ABConnect)

Old: "approve" wrote option 6 with no PRO; "record" wrote option 6 again with the PRO.

New, grounded in section 3 but **not yet run on staging**:

```python
# --- approve: carrier chosen, no label yet ---
shipping_id = ...            # from jobs.shippings.get_all(); None only if the job has no shipping
created = api.jobs.freight_providers.create_final_override(job_id, data={
    "providerID": carrier_company_id,          # UUID
    "shipmentType": PARCEL,                    # UUID, section 6
    "providerCompanyCode": code,
    "providerCompanyName": name,               # max 50
    "shippingId": shipping_id,
    "jobModifiedDate": job_modified_date,
})
if not created.success:
    raise RuntimeError(created.error_message)
quote_id, shipping_id = created.freight_quote_options_id, created.shipping_id

# amounts cannot go on create_final_override; set them on the quote it created
quote = next(q for q in api.jobs.freight_providers.get_quotes(job_id, is_overridden=True)
             if q.id == quote_id)
body = quote.model_dump(by_alias=True, mode="json")
body.update(freightAmount=freight_amount, accessorialAmount=0.0)
saved = api.jobs.freight_providers.save_final_quote(
    job_id, data={"quote": body, "jobModifiedDate": created.job_modified_date})

# --- record: label bought, PRO known ---
quote = ...                  # read it again, same way
body = quote.model_dump(by_alias=True, mode="json")
body["proNumber"] = pro
api.jobs.freight_providers.save_final_quote(
    job_id, data={"quote": body, "jobModifiedDate": latest_job_modified_date})
```

- Read-back for verification: `get_quotes(job_id, active=True)` filtered to the shipping returns
  exactly the approved quote; check `is_overridden`, provider, amounts and `pro_number`.
- Approving a different choice: call `create_final_override` again with the same `shippingId`.
  The earlier quote stays on the job, inactive.
- `save_final_quote` validates the response model `JobModifiedDateServiceResponseResult`:
  check `success` and `error_message`, not just the HTTP status.

### One write instead of two (0.3.1) **[staging]**

`POST .../freightproviders/final` adds the posted quote when its id is not stored yet
(**[source]** `FinalQuoteService.Save`), so a complete override can be created with its amounts in
one request. `save_new_final_override` does that under an id it generates and returns:

```python
new = api.jobs.freight_providers.save_new_final_override(
    job_id, shipping_id=shipping_id, shipment_type=PARCEL, provider_id=carrier_company_id,
    provider_code=code, provider_company_name=name, freight_amount=freight_amount,
    job_modified_date=job_modified_date)          # pro_number=... to record in the same write
quote_id, next_stamp = new.quote_id, new.response.job_modified_date
```

Run on staging job 5506118 (2026-11-23): the quote was created under the client's id, active, with
freight 33.10 and accessorial 2.20, and the shipping's other quotes were deactivated. A stale stamp
was refused and created nothing. This removes the window where a failed second write leaves an
active override at 0. It needs an existing shipping; `create_final_override` is still the only
override call that creates one.

### What 8_01 does not offer **[source]**

- **No call deactivates a quote.** The API has four quote routes (`finaloverride`, `ratequote`,
  `final`, and the read). Every write leaves its own quote active and deactivates the others of the
  shipping; none leaves a shipping with no active quote, and none deletes a quote. The legacy web
  application has a manage-all-quotes save that can, but it is not exposed through the API. To
  retire an approval, make another quote of the shipping final (`mark_selected` on the earlier
  quote does it without changing that quote). To retire the last quote of a shipping there is no
  call; clear its PRO and treat it as void on the client.
- **No call creates an empty shipping.** A shipping appears only as a side effect: of
  `create_final_override` or `select_rate_quote` without `shippingId`, or of `handling_units.manage`.
- **An override with a PRO reads `shipment_accepted = true`**, and loses it when the PRO is
  cleared. `ab.api.selection.is_recorded_override(quote)` and `is_carrier_booked(quote)` tell the
  two apart.

Answers to the open assumptions in `expectations.md`:

| ID | Answer | Evidence |
|---|---|---|
| A-17 | Yes at source level: a final override can be created on a shipping whose units have no inventory, without a PRO, and the PRO added later through `save_final_quote`. | [source]; staging write not run |
| A-18 | **Not through `create_final_override`; yes through `save_new_final_override` (0.3.1, above).** `create_final_override` takes provider id, code, name, shipment type and PRO, but not freight amount, accessorial amount or the active flag. Amounts go through `save_final_quote`; the quote is always created active. | [source] `FinalOverrideProviderModel`, staging Swagger |
| A-19 | Yes, per shipping rather than per job. Both writes leave exactly one active quote in the shipping. Read back with `get_quotes(active=True)` filtered by `shipping_id`. | [source]; read filter [staging] |

## 5. The ABConnect-rated path

| Step | 7_11 | 8_01 |
|---|---|---|
| Get rates | raw `POST shipment/ratequotes` | `api.jobs.rates.request(job_id, handling_units=[...], origin_address=..., destination_address=..., ship_out_date=...)` → `rates_key`, `providers` |
| Persist a rate | `rate_quote(option_index=4, ...)` | `select_rate_quote(job_id, data={"ratesKey", "carrierCode", "carrierAccountId"?, "active": True, "shippingId"?, "handlingUnits": [{"id", "quantity"}], "jobModifiedDate"})` → `transportation_quote.id` |
| Book | raw `POST shipment/book` with `quoteOptionIndex: 4` | `shipment.validate(job_id, quote_id=..., ship_out_date=..., job_modified_date=...)` then `shipment.book_v2(...)` with the same arguments |
| Cancel | `shipment.delete(job_id)` | `shipment.cancel(job_id, quote_id, job_modified_date=..., force_delete=False)` |

- `rates.select_quote` only previews; it persists nothing. `select_rate_quote` persists.
- Omitting `shippingId` on `select_rate_quote` creates a new shipping.
  A rate selected into a shipping that had no quote is stored exactly like an estimate, so
  `is_untouched_estimate` reads it as one. Call `freight_providers.mark_selected(job_id, quote,
  job_modified_date=...)` on the returned quote: it posts the quote back unchanged as the final
  quote of its shipping, the server stamps it as modified, and the estimate test then reads it as a
  selection. **[staging]** job 5523070, shipping 1522773, 2026-11-23: amounts and state unchanged,
  `is_untouched_estimate` went from true to false.
- Only active, top-level units with quantity above zero and a transportation container type are
  rated. **[source]** `TransportationQuoteValidator`, `JobShipmentPlanService`
- `book_v2` returns `success`, `error_message`, `shipment_id` (a carrier id, not a shipping id) and
  `job_modified_date`. HTTP 200 with `success=false` is a failed booking.
- `book_v2` returns no documents. The label is filed on the job afterwards as a document of type 1
  (`Label`); read it with `api.documents.list(...)` and download it. **[staging]** job 5483351
  (reported by the annex-shipping migration)
- Staging UPS bookings return the placeholder tracking number `1ZXXXXXXXXXXXXXXXX`. **[staging]**
- **Cost and sell at rating time.** Each service in the `rates.request` response carries both
  `net_amount` (carrier cost) and `total_sell`. On 7_11 the `price` of `shipment/ratequotes` was the
  **sell** (`TotalSell`), so `total_sell` is the like-for-like figure for a rate list. Once a rate is
  saved as a quote only cost remains on it (`freight_amount`, `accessorial_amount`); see
  [reads](reads.md) section 2. **[source]** 7_11 `JobCarrierRatesModel`; **[staging]** job 5483351
- `cancel` returns `success`, `error_message`, `override_error`. When the carrier refuses,
  `force_delete=True` removes ABConnect's booking state only; the carrier still holds the booking.
- The legacy `shipment.book`, `shipment.delete` and job-level export calls still work on a job
  with exactly one active shipping and fail locally when there are two.

### Verified on staging (2026-11-22)

- A top-level `BOXES` unit with **no inventory** was rated, selected, validated and booked.
- **Rate with the unit as stored.** The `handling_units` sent to `rates.request` must carry the same
  values as the stored unit, including `declared_value`. A quote rated without the unit's declared
  value was selected without complaint and then failed validation with "Some handling units have
  been changed".
- **An inactive unit is not refused at rating.** `rates.request` returned services for an inactive
  unit and `select_rate_quote` saved the quote into a new shipping; only `shipment.validate`
  rejected it ("Requested handling units were not found"). Check `is_active` yourself before rating.
- A nested unit, or a unit with a packing-only container type, is refused at rating
  ("Requested carriers are not allowed for the selected handling units").
- Deleting a unit that is in a shipping leaves that shipping in place with no units and its quotes.

### International shipments

- `shipment.validate` and `book_v2` return "International parameters are required" for a
  cross-border quote unless `international_params` is sent.
- `shipment.get_shipping_export_data(job, shipping_id)` returns `None` until export data has been
  saved for that shipping. The job-level `shipment.get_export_data(job)` returns the job's export
  data with its commodities (seeded from the job's inventory list, not from inventory on units).
- Convert either read with `.to_international_params()` (SDK 0.3.1) and pass it on:

```python
export = api.jobs.shipment.get_export_data(job_id)       # or get_shipping_export_data(...) once saved
params = export.to_international_params().model_dump(by_alias=True, exclude_unset=True, mode="json")
check = api.jobs.shipment.validate(job_id, quote_id=quote_id, ship_out_date=ship_out,
                                   international_params=params)
```

  Validated on staging for a cross-border UPS quote on a unit with no inventory; not booked.

## 6. Shipment type UUIDs **[source]** `JobConstants.TransportationMode`

| Mode | UUID |
|---|---|
| LTL | `d6a05ae8-1c3b-4a0f-ba73-fabc9d496ff3` |
| Parcel | `778a28ef-4866-4878-a87a-9fa6333a48a6` |
| Air1 | `ee044ce4-a6e3-46bc-968b-e5c0a763f93d` |
| Air2 | `ab36ee3f-7318-4b55-abb4-e335a39afb72` |
| Air3 | `5f30c1c1-4044-4e7f-b51a-ebe02d48de39` |
| Ocean | `b7e9a7d1-863c-4202-95f6-7306b7497028` |
| Van | `2a60d1ee-914c-4363-aea0-04ac7875fbf0` |

Parcel and LTL match the values seen on staging quotes. Any other value is rejected as a wrong
shipment type.
