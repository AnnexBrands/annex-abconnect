# `api.jobs.timeline.update_task` — silent no-op investigation

**Verdict: SDK defect, corrected.** Not an `api_behavior_defect`, and not
environment-blocked. No issue filed against the API — the payload never matched
the documented contract, so the server had nothing to apply.

## Symptom

`PATCH /job/{jobDisplayId}/timeline/{timelineTaskId}` returned **HTTP 204** and
changed nothing observable. Every field the SDK offered was ignored:

```
PATCH scheduledDate = '2026-08-05T14:00:00' -> read-back None   SILENT NO-OP
PATCH completedDate = '2026-08-06T10:00:00' -> read-back None   SILENT NO-OP
PATCH comments      = 'probe'               -> read-back None   SILENT NO-OP
```

A 204 is indistinguishable from success at the call site. The endpoint looked
healthy while discarding every payload.

## Preserved evidence

Captured live on 2026-07-27 against job 4000000, task 687968.

**Route:** `PATCH /api/api/job/4000000/timeline/{timelineTaskId}`

**Exact serialized payload the SDK sent:**

```json
{"scheduledDate": "2026-08-05T14:00:00", "comments": "probe"}
```

**Request headers** (authorization redacted): `Content-Type: application/json`,
`Accept: */*`, `Accept-Encoding: gzip, deflate`, `Connection: keep-alive`.

**Response:** `204 No Content`, empty body.

**Before / after the PATCH** (`GET /job/4000000/timeline/{id}`):

| Field | Before | After | Changed |
| --- | --- | --- | --- |
| `modifiedDate` | `null` | `2026-07-27T14:24:03.320000` | **yes** |
| `scheduledDate` | `null` | `null` | no |
| `completedDate` | `null` | `null` | no |
| `comments` | `null` | `null` | no |
| `plannedStartDate` | `2026-08-01T09:00:00` | `2026-08-01T09:00:00` | no |
| `status` | `null` | `null` | no |

`modifiedDate` moving proves the request reached the record and the server
committed a write — it simply had no recognized values to apply.

## Root cause

Swagger `UpdateTaskModel` (`ab/api/schemas/acportal.json`):

```json
{
  "type": "object",
  "properties": {
    "truckId":            {"$ref": "#/components/schemas/UpdateTruckModel"},
    "plannedStartDate":   {"$ref": "#/components/schemas/UpdateDateModel"},
    "preferredStartDate": {"$ref": "#/components/schemas/UpdateDateModel"},
    "plannedEndDate":     {"$ref": "#/components/schemas/UpdateDateModel"},
    "preferredEndDate":   {"$ref": "#/components/schemas/UpdateDateModel"}
  },
  "additionalProperties": false
}
```

`UpdateDateModel` and `UpdateTruckModel` are both override wrappers —
`{"value": <scalar-or-null>}`.

The SDK's `TimelineTaskUpdateRequest` declared `status`, `scheduledDate`,
`completedDate`, `comments`. **Not one appears in the schema.** With
`additionalProperties: false` and a 204 response, a body of entirely unknown
keys is accepted and dropped without an error to notice.

Two related metadata defects in the same routes:

- `_POST_TIMELINE` declared no `request_model`, so the workbench resolved the
  *query-params* model (`TimelineCreateParams`) as the request body and refused
  a valid `taskCode`. This blocked certification of `create_task`.
- `_PATCH_TASK` declared `response_model="TimelineTask"` where Swagger says
  204 No Content. The method claimed to return a task it never receives.

## Fix

`TimelineTaskUpdateRequest` now mirrors `UpdateTaskModel` exactly, with a
`model_validator` that accepts a bare scalar and wraps it — the wrapper is the
wire shape, not something a caller should have to remember, and silently sending
an unwrapped scalar is the very failure this model exists to prevent.

`tests/unit/test_timeline_update_transport.py` asserts on the **serialized
request body** against the checked-in Swagger schema, offline and
deterministically. A test that mocked the transport and asserted "204 was
returned" would have passed throughout the entire regression.

## Re-run of the controlled session

```
wire  : {"plannedStartDate": {"value": "2026-08-05T14:00:00"}}
diff [update]:
   plannedStartDate: '2026-08-01T09:00:00' -> '2026-08-05T14:00:00'
   modifiedDate:     None -> '2026-07-27T14:25:27.840000'
UPDATE VERIFIED — value actually persisted

wire  : {"plannedStartDate": {"value": "2026-08-01T09:00:00"}}
diff [restore]:
   plannedStartDate: '2026-08-05T14:00:00' -> '2026-08-01T09:00:00'
RESTORATION VERIFIED

teardown: {"status": "1 - New Job", "tasks": []}   SESSION: PASS
```

The endpoint is correct once the payload matches the contract. It is **not
certified in this change** — certification of `update_task` is left for the
operator to authorize separately.
