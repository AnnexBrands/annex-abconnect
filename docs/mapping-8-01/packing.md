# Packing: legacy parcel/freight items → 8_01 inventory and handling units

For the agent migrating AnnexIq/tools. Covers the reads (`jobs.parcel_items.list`) and the
packing writes (raw `POST parcelitems`, `parcel_items.delete`, `add_freight_items`).

Evidence tags used on every statement:

- **[S]** verified on staging by a read (2026-11-22, jobs 5483351 and 13829427, corporate login).
- **[C]** read in server source, `/src/ABConnect` branch `release` at `7245c94cc`; file and symbol given.
- **[A]** assumed; not checked.

**No write in this document has been run against staging.**

---

## 0. The model change in one paragraph

Legacy had three tables: job items, parcel items (a box, optionally pointing at one job item by
`jobItemId`), freight items. 8_01 has **inventory** (the goods) and **handling units** (every
box, crate, pallet, parcel package). Units nest: a unit can contain other units
(`content_handling_units`) and inventory (`inventory_items`). The server's own data migration
turned each legacy parcel item and freight item into a **top-level handling unit**, and turned a
parcel item's `jobItemId` into a **nested unit**, not into inventory on the box
[C `ABConnect.DB/Scripts/Version8.01/MigrateJobsToInventoryHandlingUnits.sql` steps 4–7].
Staging shows the same shape: on job 5483351 the `BOXES` unit 3596159 contains unit 3593096
(`Corrugated`), and that inner unit holds inventory 3927131 [S].

So a top-level transport unit with **no inventory of its own is the normal shape**, including
for jobs the portal built [S].

---

## 1. Reads: `jobs.parcel_items.list` → `jobs.handling_units.get_all`

### 1.1 What the retained endpoint returns now

`GET /job/{id}/parcelitems` is a projection of handling units
[C `ABC.Modern.Services/Services/JobParcelItemService.cs` `GetByJobId`]. It returns a unit when
all of these hold:

- `isActive` is true;
- the unit is top level (it is not the content of another unit);
- its container type code is `BOXES`, or equals a code in the parcel package type lookup
  (the carrier packages, e.g. `UPS_Tube`, `FEDEX_PAK`).

Ordered by `sequenceNo`. Everything else is absent: inactive units, nested units, and freight
units with any other container (`CRATES`, `PALLETS`, …). On job 13829427 the active top-level
`CRATES` unit 2521204 is in `get_all` and not in `parcelitems` [S].

The body is `{"parcelItems": [...], "jobModifiedDate": null}` [S]. `jobModifiedDate` is declared
but never set by the service [C `JobParcelItemsDto`, `GetByJobId`], so it is always null — do
not use it as a concurrency token. The SDK unwraps `parcelItems` and returns `list[ParcelItem]`,
and emits `LegacyRequestWarning` on every call [S].

### 1.2 Field by field

`handling_units.get_all` returns `list[JobHandlingUnitDetails]`. To reproduce the legacy list,
filter it as in 1.1 (see 1.3).

| Legacy `ParcelItem` field | 8_01 source | `JobHandlingUnit` field | Note |
|---|---|---|---|
| `id` | `unit.Id` [C] | `id` | Same integer. Legacy parcel-item ids did **not** survive the migration; this is the handling-unit id [C migration step 4]. |
| `jobItemId` | not returned | none | `ParcelItemDto` has no such property [C]; always `None` now [S]. See 2.5. |
| `description` | `unit.Name` [C] | `name` | Equal on staging [S]. |
| `quantity` | `unit.Quantity` [C] | `quantity` | |
| `jobItemPkdLength` | `unit.Length` [C] | `length` | Inches. Nullable in both. |
| `jobItemPkdWidth` | `unit.Width` [C] | `width` | |
| `jobItemPkdHeight` | `unit.Height` [C] | `height` | |
| `jobItemPkdWeight` | `unit.Weight ?? 0` [C] | `weight` | Pounds. Legacy shows `0` where the unit has `None`. |
| `jobItemParcelValue` | `unit.DeclaredValue ?? 0` [C] | `declared_value` | Legacy shows `0.0` where the unit has `None` [S]. |
| `parcelPackageTypeId` | id of the parcel package type whose code equals the container code, else null [C] | `container_type_id` | **Different id space.** Parcel package type ids (`lookup.get_parcel_package_types()`: 1–17 on staging) are not container type ids (7–23 for the same codes on staging) [S]. Join on `code`. Null for a `BOXES` unit [S]. |
| `packageTypeCode` | `unit.ContainerType.Code` [C] | none (only `container_type_id`, `container_name`) | `get_all` gives the id and display name, not the code. Resolve the code from `lookup.get_container_types()`. Present in the JSON but not a declared field of the SDK `ParcelItem` model. |
| `insureKey` | computed from the value: `≤100 → "0"`, `≤300 → "3"`, else `ceil(value/100)` [C `ParcelItemDto.InsureKey`] | none | Recompute from `declared_value` with the same rule if needed. |
| `jobModifiedDate` | never set [C] | none | Take the token from a write response (`manage` returns `job_modified_date`) or the job read [A for the job read field]. |
| `parcelItems` | wrapper key | — | Already unwrapped by the SDK. |

Fields `get_all` has that the legacy list never had, and which tools now needs: `is_active`,
`sequence_no`, `container_type_id`, `container_name`, `content_handling_units`,
`inventory_items`, `is_used_in_shipment`, `is_locked`, `is_container_changed`,
`is_fill_changed`, `freight_class_id`, `nmfc_item_no`, `has_custom_name`.

### 1.3 Equivalent read

```python
units = api.jobs.handling_units.get_all(job_id)
codes = {t.id: t.code for g in api.lookup.get_container_types() for t in (g.container_types or [])}
parcel_codes = {p.code for p in api.lookup.get_parcel_package_types()}
content_ids = {c.id for u in units for c in (u.content_handling_units or [])}

legacy_parcel_view = sorted(
    (u for u in units
     if u.is_active
     and u.id not in content_ids                      # top level
     and (codes.get(u.container_type_id) == "BOXES" or codes.get(u.container_type_id) in parcel_codes)),
    key=lambda u: u.sequence_no or 0,
)
```

For a "what is on file" view that also covers freight, drop the container-code test and keep
active top-level units whose container is in the **Parcel Packaging** or **Freight Type** group
(section 2.4): that is the set the server rates and attaches to a shipping
[C `ABC.Services/JobServices/JobShipmentPlanService.cs`, the `rateContainerTypeIds` query].

---

## 2. Writes: packing save → `jobs.handling_units.manage`

### 2.1 What the legacy calls did (7.11.1)

| Legacy call | Behaviour | Source |
|---|---|---|
| `POST /job/{id}/parcelitems` body `{parcelItems:[...], jobModifiedDate, forceUpdate}` | **Replace-all for the job.** Rows whose `id` is not in the request are deleted; rows with a known `id` are updated; rows with `id` null or ≤ 0 are inserted. When `parcelPackageTypeId` is set, the package's fixed dimensions override the ones sent. `jobItemId`, when given, must be a job item of that job. Job modified date is bumped. | [C tag `release_7.11.1`: `ABC.Services/JobServices/JobParcelItemService.cs` `SaveParcelItems`; `ABConnect.DB/job/Stored Procedures/ManageJobParcelItems.sql`] |
| `DELETE /job/{id}/parcelitems/{parcelItemId}` | Deletes one parcel row. | [C same file, `DeleteParcelItem`] |
| `POST /job/{id}/freightitems` body `{freightItems:[...], jobModifiedDate, forceUpdate}` | **Replace-all for the job**, keyed on `jobFreightID`: rows not listed are deleted, listed ones updated or inserted. Cube is recomputed from the dimensions. | [C `release_7.11.1`: `ACPortal/.../Controllers/JobController.cs` `SaveFreightItems`; `ABConnect.DB/job/Stored Procedures/ManageFreightItems.sql`] |

All three routes are gone on 8_01 [C commit `f026ef705`, AB-12593]; only the parcel `GET`
came back [C commit `f3aaf8a6b`, AB-13302].

### 2.2 Field mapping to `ManageableJobHandlingUnitModel`

Target model: `ab/api/models/packing.py`, `ManageableJobHandlingUnitModel` (extends
`JobHandlingUnitModel`), as on the SDK working tree for 0.3.1. The right-hand column is what the
server's own migration did with the same legacy column, which is the best available definition
of "equivalent".

**Parcel item (`ParcelItemSave` / raw body) → handling unit**

| Legacy field | Handling-unit field | Rule | Source |
|---|---|---|---|
| `id` | `id` | Not transferable: use the **handling-unit** id from `get_all` to update in place, or a negative temporary id to create (2.3). | [C] |
| `jobItemId` | none under D-1 | Legacy meaning "this box holds that item". 8_01 equivalent is nesting the item's packing unit via `content_handling_units` (2.5). Dropped under D-1. | [C migration step 5] |
| `description` | `name`, with `has_custom_name=True` when non-blank | Migration sets `HasCustomName` exactly when the description is non-blank. With a blank name and `has_custom_name=False` the server generates a name. Max 250 chars (SDK). | [C migration step 4; `JobHandlingUnitExtensions.GenerateHandlingUnitName`] |
| `quantity` | `quantity` | SDK requires ≥ 1. Migration turned a quantity ≤ 0 row into `quantity=1, isActive=false`. | [C] |
| `jobItemPkdLength` / `Width` / `Height` | `length` / `width` / `height` | Inches, 0–9999 (SDK). | [C] |
| `jobItemPkdWeight` | `weight` | Pounds, 0–999999 (SDK). | [C] |
| `jobItemParcelValue` | `declared_value` | The retained GET reads it back from `DeclaredValue`. | [C `JobParcelItemService`] |
| `parcelPackageTypeId` | `container_type_id` | Look up the parcel package type's `code`, then the container type with the same code in the **Parcel Packaging** group. No package type → `BOXES`. | [C migration step 4] |
| `insureKey` | none | Derived; do not send. | [C] |
| — | `is_active` (required) | `True`. | |
| — | `sequence_no` (required, 0–1000) | Position in the list. Legacy had no sequence; the legacy GET now orders by it. | [C] |
| — | `is_locked`, `is_container_changed`, `is_fill_changed` (required for new units) | See 2.6. | |
| — | `inventory_items` (required for new units) | `[]` under D-1. | |

Lost relative to the 7.11.1 behaviour: the server no longer overwrites dimensions with a carrier
package's fixed dimensions on save [A — no such code found in `HandlingUnitService`; not tested].

**Freight item (`FreightShipment` in `FreightItemsRequest.freight_items`) → handling unit**

| Legacy field | Handling-unit field | Rule | Source |
|---|---|---|---|
| `jobFreightID` (UUID) | `id` | Not transferable; use the handling-unit integer id or a negative temporary id. | [C] |
| `quantity` | `quantity` | ≥ 1. | [C migration step 6] |
| `itemLength` / `itemWidth` / `itemHeight` | `length` / `width` / `height` | Inches. | [C] |
| `itemWeight` | `weight` | Pounds, per unit. | [C] |
| `freightItemClassId` / legacy `FreightClass` (UUID) | `freight_class_id` | Same UUID (a master-constant value). The server rejects an unknown one: "Freight class with Id … is not found." | [C migration step 6; `HandlingUnitService.ValidateEntity`] |
| `nmfcItem` | `nmfc_item_no` | Max 50 chars. | [C] |
| `bolDescription` | `name`, `has_custom_name=True` when non-blank | | [C] |
| `itemID` / `freightItemId` (freight item type UUID) | `container_type_id` | Legacy type is a master-constant whose value is a code (`PALLETS`, `CRATES`, `BOXES`, …); use the container type with that code in the **Freight Type** group. Migration left the container null when there was no match. | [C migration step 6] |
| `itemValue` / `freightItemValue` | `declared_value` | Not migrated by step 6; `declared_value` is the only value field on a unit. | [A] |
| `cube`, `totalWeight`, `netCubic*`, `longestDimension`, `transportation*`, `ceilingTransportationWeight`, `freightDescription`, `freightItemClass`, `jobFreightReport`, audit fields, `jobID`, `jobDisplayId` | none | Derived or read-only; do not send. `cubic_feet` is computed by the server on read. | [C `JobHandlingUnit.CubicFeet`] |

Fields with no legacy source that the model also accepts and tools can leave unset:
`fill_id`, `fill_rate`, `inches_to_add`, `container_thickness`, `labor_minutes`,
`container_handling_unit_material_id`, `materials`, `content_handling_units`.

### 2.3 How "replace all" works in `manage` — read this before coding

`POST /job/{id}/handlingUnit/manage` [C `HandlingUnitService.ManageHandlingUnits` and its helpers
`DeleteManagedHandlingUnits`, `UpdateManagedHandlingUnits`, `CreateNewHandlingUnits`].

1. **It is a true replace-all for the whole job.** Every existing handling unit of the job whose
   id is not in the request is **hard-deleted**, together with its nesting links, its
   unit–inventory links, its materials, its documents and its **shipping-contents rows**
   [C `DeleteManagedHandlingUnits`]. There is no check for `isUsedInShipment`. This includes
   nested packing units and units that belong to another shipping. The inventory records
   themselves (`jobs.inventory`) are not deleted.
2. **Existing units**: a request unit whose `id` matches an existing unit is updated. The update
   maps the **whole** entity onto the record [C `BaseEntityService.UpdateRecord`,
   `AutoMapperProfile` `JobHandlingUnit → JobHandlingUnitRecord`], so any scalar field left out
   is written as null/false/0. To keep a unit unchanged, send every field back as read.
3. **New units**: a request unit with `id < 0` is created [C `CreateNewHandlingUnits`]. Each new
   unit needs its own **distinct negative** id (`-1`, `-2`, …); the ids are also how other units
   in the same request refer to it in `content_handling_units`.
4. **`id = 0` is invalid.** It is neither existing nor new, and the later lookup
   `newHandlingUnitsMap[handlingUnit.Id]` throws [C]. A positive id that does not exist on the
   job is silently skipped by the server [C]. SDK 0.3.1 requires `id` on every unit and rejects
   `0` and unknown positive ids before any request.
5. **An empty or missing `handlingUnits` deletes every unit on the job** [C: point 1 with an
   empty request; A that a missing list binds as empty rather than failing]. SDK 0.3.1 requires
   `handling_units`, and refuses any call that would delete existing units unless
   `delete_omitted=True` is passed.
6. **Not atomic.** The delete step commits its own transaction before the update and create
   steps run [C `DeleteManagedHandlingUnits`]. A request that fails later (for example an
   unknown freight class) has already deleted the omitted units.
7. Per unit, after create/update, the server synchronises to the request: inventory links
   (`inventoryItems`; omitted = empty), nested units (`contentHandlingUnits`; omitted = empty),
   materials (`materials`; omitted = empty) [C]. So nesting and materials of an existing unit are
   also cleared unless sent back. SDK 0.3.1 does that for you: for a unit with a positive id it
   reads the job's units once and sends back every field the entry leaves out (scalars, flags,
   inventory, nested units, materials). `{"id": unit_id}` alone therefore means "keep this unit
   exactly as it is". Pass `None` or `[]` to clear a field.
8. **Concurrency**: `jobModifiedDate` is optional. Omitted → no check. Given and older than the
   job's modified date (plus a server-side tolerance) → HTTP 400 with `refreshRequired: true`.
   `forceUpdate` does **not** override it on this route
   [C `CheckJobModificationAttribute` with `JobModificationConflictResolution.Refresh`;
   `JobService.IsJobModifiedSince`].
9. **Response**: `success`, `job_modified_date` (new token), and `handling_units` containing the
   updated and created units with their real ids [C].
10. **Access**: owner, pickup agent or packaging agent of the job [C `JobHandlingUnitController`].
11. **Standard pallet pricing** is recalculated from active `PALLETS` units when the job is not
    locked and has a pack agent [C `UpdateStandardPalletPricing`]. A packing save can therefore
    change a pricing row.

**Removing one unit**: either leave it out of a `manage` request (deleted as in point 1), or call
`handling_units.delete(job_id, unit_id)` — a hard delete of that unit, its links, materials and
documents [C `HandlingUnitService.FullDelete`]. That single delete does not remove
shipping-contents rows; whether it fails for a unit that is in a shipping is not known [A].
Setting `is_active=False` keeps the unit but excludes it from the legacy parcel view, from
rating and from job totals [C `JobParcelItemService`, `JobShipmentPlanService`, `JobSummary`].
There is no soft-delete flag beyond `isActive`.

**Consequence for the packing save.** Legacy parcel save replaced parcel rows only and freight
save replaced freight rows only. `manage` replaces **every** unit on the job in one call. The
tools packing save must therefore build one request that contains every unit that should exist
afterwards: the boxes being saved, plus any existing unit it means to keep (echoed in full).

### 2.4 Container types

Container types come in four groups [S `lookup.get_container_types()`;
C `AB.ABCEntities/AutoPack/Constants.cs`]:

| Group | `unique_id` | Codes (staging ids) | Rated / attached to a shipping |
|---|---|---|---|
| Own Packaging | `9d42e80c-…` | `CO` 1, `CR` 2, `D` 3, `FAC` 4, `SB` 5, `SC` 6 | **No** |
| Parcel Packaging | `ff3e4982-7787-4ac9-a34f-b901d392342b` | carrier packages, 7–23 | Yes |
| Freight Type | `46021a31-01c8-436b-bb5e-f61367f70eeb` | `BAGS` 24, `BOXES` 25, `CARPETS` 26, `CARTONS` 27, `CRATES` 28, `CYLINDERS` 29, `DRUMS` 30, `PAILS` 31, `PALLETS` 32, `ROLLS` 33 | Yes |
| Packed By Owner | `cbbdcbc4-…` | `PBO` 34 | **No** |

The server treats a unit as a transport unit when it is active, top level, and its container
type is in the **Parcel Packaging** or **Freight Type** group
[C `HandlingUnitService.GetTopLevelHandlingUnitsContainerTypeIds`, used by
`JobShipmentPlanService`]. A unit in Own Packaging or PBO, or with no container type, is not
picked up.

What to send:

| Legacy thing | `container_type_id` to use |
|---|---|
| Parcel box, no carrier package (`parcelPackageTypeId` null) | code `BOXES` (Freight Type group). This is what the migration used for 4,649 of 4,795 parcel items [C], and what makes the unit appear in the legacy parcel view. |
| Parcel in a carrier package | the Parcel Packaging type with the same `code` as the parcel package type. |
| Freight box / pallet / crate | the Freight Type code that matches the legacy freight item type (`PALLETS`, `CRATES`, `BOXES`, …). |

Discover ids at run time and match on **code**; do not hard-code the staging ids:

```python
groups = api.lookup.get_container_types()          # list[HandlingUnitContainerTypeGroupResult]
type_id = {t.code: t.id for g in groups for t in (g.container_types or [])}
BOXES, PALLETS = type_id["BOXES"], type_id["PALLETS"]
```

Not established here: whether the rate request treats a `BOXES` unit as parcel or freight, or
decides that from the carrier/service requested. That belongs to the quotes mapping [A].

### 2.5 Legacy `jobItemId` (UUID) → integer inventory id

- **There is no API mapping.** The inventory table has a column `TempSourceJobItemId` holding the
  legacy job-item GUID, and the handling-unit table has the same column
  [C `ABConnect.DB/job/Tables/InventoryItem.sql`, `HandlingUnit.sql`], written by the migration.
  It is not on the EF record, not on any DTO, and not referenced by any C# code
  [C: no match for `TempSourceJobItemId` in `*.cs`]. The SDK's `JobInventoryItem` cannot expose
  it because the server does not send it [S: no extra fields on `inventory.get_all`].
- A legacy job-item GUID can therefore only be translated by a database query, or by matching
  on content. The practical key the API does expose is `customer_item_id` on inventory
  (populated on both staging jobs [S]); name, dimensions and sequence are the fallbacks [A that
  tools holds the customer item id for its items].
- **What D-1 gives up.** Legacy `jobItemId` on a parcel row recorded which item is in which box.
  The 8_01 form is: box unit → `content_handling_units` → packing unit → `inventory_items` →
  inventory. Writing boxes with no content and no inventory records dimensions only. Lost: the
  item-to-box association (so a box's generated name, "contents" lines on forms and emails, and
  per-unit inventory value/weight roll-ups have nothing to draw on) [C
  `TransactionEmailsService` and `GenerateHandlingUnitName` read unit inventory; forms not
  traced]. Not lost: the inventory records themselves.
- **Because `manage` deletes unlisted units (2.3 point 1)**, a D-1 packing save that lists only
  the new boxes also deletes the existing packing units that currently hold the job's
  inventory links. After it, the job's inventory is attached to no unit. Decide deliberately
  whether to echo those units back instead.

**Export data and assumption A-2.** Export data is a JSON document stored per
(job, shipping id) [C `ABC.Services/JobServices/JobExportDataService.cs`]. `GET`/`POST
…/shipment/exportdata/{shippingId?}` read and write that document as is. Its commodities are
seeded once, at job creation, from the job's **inventory list** (name, quantity, weight, value,
Schedule B, ECCN) — not from handling units and not from inventory attached to units
[C `SaveJobExportData`, called from `JobService`]. The seed does not set `jobItemId`, and no
server code reads `jobItemId`; the property is kept only because clients use it
[C `ExportDataCommodity`, comment "used by FE/WebApp"; no other reference in services].

So for export data specifically: **empty unit inventory does not change it**, and `jobItemId`
inside commodities is an opaque value the client round-trips. A-2 holds for export data
[C, not run]. Still open under A-2: forms and customs documents produced at booking (not
traced), and the fact that export data is seeded only for jobs the server judged international
at creation.

### 2.6 The three flags

Required on new units; inferred by the SDK for existing ones. Server meaning
[C `ACPortal/ABC.ACPortal.WebClient/.../inventory-handling-units`]:
`is_locked` — a user locked the unit; `is_container_changed` / `is_fill_changed` — the container
/ fill was chosen by a user, so AutoPack must keep it. For boxes a packer measured, tools'
working assumption is `is_locked=True` (assumption A-6, undecided), with the other two `False`
because tools does not choose a packing container or fill [A].

### 2.7 Worked example — **untested against staging**

Replaces the job's transport boxes with the ones the packer entered, updating in place where a
box already exists so ids (and any shipping that references them) survive, and echoing every
other unit so `manage` does not delete it. Set `KEEP_OTHER_UNITS = False` for the literal D-1
reading (only the new boxes remain). Requires SDK 0.3.1.

```python
KEEP_OTHER_UNITS = True

def save_packing(api, job_id, boxes, job_modified_date=None):
    """boxes: [{"length":…, "width":…, "height":…, "weight":…, "quantity":…, "description":…, "value":…}]"""
    current = api.jobs.handling_units.get_all(job_id)
    type_id = {t.code: t.id for g in api.lookup.get_container_types() for t in (g.container_types or [])}
    rateable = {t.id for g in api.lookup.get_container_types()
                if str(g.unique_id) in ("ff3e4982-7787-4ac9-a34f-b901d392342b",
                                        "46021a31-01c8-436b-bb5e-f61367f70eeb")
                for t in (g.container_types or [])}
    nested = {c.id for u in current for c in (u.content_handling_units or [])}
    old_boxes = sorted((u for u in current if u.id not in nested and u.container_type_id in rateable),
                       key=lambda u: (u.sequence_no or 0, u.id))
    if any(u.is_used_in_shipment for u in old_boxes):
        raise RuntimeError("a box is part of a booked shipment; do not replace it")

    units = []
    for n, box in enumerate(boxes):
        reuse = old_boxes[n].id if n < len(old_boxes) else -(n + 1)   # update in place, else new
        units.append({
            "id": reuse,
            "quantity": box["quantity"], "is_active": True, "sequence_no": n,
            "length": box["length"], "width": box["width"], "height": box["height"],
            "weight": box["weight"], "declared_value": box.get("value"),
            "container_type_id": type_id["BOXES"],
            "name": box.get("description"), "has_custom_name": bool((box.get("description") or "").strip()),
            "is_locked": True, "is_container_changed": False, "is_fill_changed": False,   # A-6
            "inventory_items": [],                                                         # D-1
            "content_handling_units": [], "materials": [],
        })
    reused = {u["id"] for u in units}
    if KEEP_OTHER_UNITS:
        # {"id": n} alone keeps a unit exactly as it is: SDK 0.3.1 fills in the rest.
        units += [{"id": u.id} for u in current if u.id not in reused]
    # Units in `current` that are not listed are deleted by the server; the SDK refuses
    # that unless delete_omitted=True.

    request = {"handling_units": units, "delete_omitted": not KEEP_OTHER_UNITS or len(old_boxes) > len(boxes)}
    if job_modified_date is not None:
        request["job_modified_date"] = job_modified_date      # stale → HTTP 400 refreshRequired
    result = api.jobs.handling_units.manage(job_id, **request)
    if not result.success:
        raise RuntimeError(result.error_message)
    return result   # result.handling_units carry the real ids; result.job_modified_date is the new token
```

Things this example does not settle and UAT must:

- Whether reusing a box's id while clearing its `content_handling_units` is acceptable when the
  old box wrapped a packing unit; the inner unit then becomes top level (still Own Packaging, so
  still not rated).
- Whether the SDK's completion of an existing unit round-trips every material field the server
  needs (`ManageableHandlingUnitMaterialModel`).
- Freight: the same function with `type_id["PALLETS"]` (or the matching freight code) plus
  `freight_class_id` and `nmfc_item_no`; tools writes no freight class today.
- A unit with `is_locked=True` and what the portal's AutoPack then does (U-10).
