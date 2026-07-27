# `api.jobs.timeline.create_task` — certification evidence

**Classification: `circular_restored`.** Certified 2026-07-27 against staging
job 4000000 (`TEST_JOB_DISPLAY_ID2`), the dedicated staging test job.

Machine-readable evidence lives in `tests/example_run_results.json` under
`api.jobs.timeline.create_task`. This file is the human-readable record.

## Baseline (precondition, verified before mutating)

```json
{"status": "1 - New Job", "tasks": []}
```

The session refuses to proceed unless both hold: status `1 - New Job` and
`tasks: []`.

## Request

Model `BaseTimelineTaskRequest`, resolved from the route's `request_model`.

Wire payload:

```json
{"id": null, "modifiedDate": null, "taskCode": "PU",
 "plannedStartDate": "2026-08-01T09:00:00",
 "workTimeLogs": null, "initialNote": null}
```

`PU` rather than `PK`: `PATCH .../timeline/{id}` rejects `PK` outright —
`HTTP 400 "Task of a such type (PK) can not be updated. Allowed types are
Pickup - (PU) or Delivery - (DE)"` — so `PU` is the code that can be exercised
end to end by both endpoints in this batch.

## Created state

`HTTP 200 TimelineSaveResponse`, `taskExists=false`, new task id `687970`.

```
diff [create]:
   status: '1 - New Job' -> '2 - Scheduled'
   + task 687970 {taskCode: PU, status: null, scheduledDate: null,
                  completedDate: null, comments: null}
```

The status transition is the part worth noting: creating a `PU` task advances
the job's sub-management status. Restoration therefore has to return **both**
the task list and the status, not just delete the row.

## Teardown

`DELETE /job/4000000/timeline/687970`, via `api.jobs.tasks.delete(JOB, "PU")`.

## Final baseline verification

```json
{"status": "1 - New Job", "tasks": []}
```

Identical to the captured baseline — the status transition reversed on its own
when the task was deleted. `final_state_verified: true`.

## Checks

```
✅ request-model validation   BaseTimelineTaskRequest accepted
✅ response-model validation  TimelineSaveResponse
✅ undeclared response fields none
✅ fixture match              structure matches
✅ restoration                complete
```

## Scope

`api.jobs.timeline.update_task` is **not** certified here. Its investigation is
in `timeline-update-task-investigation.md`; the SDK defect it uncovered is fixed
and its controlled session now passes, but certifying it is a separate operator
decision.

Job notes (`api.jobs.note.create` / `update`) remain `manual_cleanup`: there is
no delete in the SDK surface, so creation can be proven but restoration cannot.
