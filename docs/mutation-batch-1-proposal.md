# Mutation batch 1 — proposal for operator review

**Nothing here has been run.** This is the batch I would certify first, with the
restoration path for each, for approval before anything touches staging state.

All 116 mutating endpoints are currently classified `manual_cleanup`, which is
the safe default and means none can be certified. The goal of a first batch is
to reclassify a *small* set to `circular_restored` — create, verify, restore,
verify the restoration — and prove the workflow end to end before widening.

## Why these four

Each satisfies three properties:

1. **Self-contained.** It creates or edits a record this repository created; it
   never edits a pre-existing production record.
2. **Verifiable restoration.** A read-only call afterwards proves the record is
   gone or back to its prior value — not merely that a delete returned 200.
3. **Already demonstrated.** The timeline pair is exercised today by
   `tests/helpers/test_timeline_helpers.py`, which passes 14/14 including its
   own `delete_all` teardown and an explicit rollback test. That is a working
   precedent, not a hope.

| # | Endpoint | Verb | Restoration | Precondition |
| --- | --- | --- | --- | --- |
| 1 | `api.jobs.timeline.create_task` | POST | `delete_task`, then `timeline.response` shows `tasks: []` | Test job at baseline |
| 2 | `api.jobs.timeline.update_task` | PATCH | Re-PATCH to the captured prior value, then re-read | Task created by #1 |
| 3 | `api.jobs.note.create` | POST | Note is scoped to the test job; verify by `notes.list` | Test job |
| 4 | `api.jobs.note.update` | PUT | Re-PUT the captured prior body, then re-read | Note created by #3 |

Ordering matters: 2 depends on 1, and 4 on 3. Each pair is one session.

## Explicitly excluded from batch 1

| Endpoint | Why not |
| --- | --- |
| `api.contacts.merge` | Irreversible. Merging two contacts cannot be undone. |
| `api.companies.update_fulldetails` | Edits a real company record; no capture-and-restore that is safe to get wrong. |
| `api.documents.hide` | No `unhide` in the SDK surface — restoration path unproven. |
| `api.jobs.timeline.increment_status` / `undo_increment_status` | Looks like a natural pair, but the undo's semantics are unverified and job status drives downstream workflow. |
| Everything `DELETE` | Nothing is deleted before we can create it and prove restoration first. |

## Preconditions before running any of it

- The staging test job (`TEST_JOB_DISPLAY_ID2`, 4000000) at baseline: `tasks: []`,
  status "1 - New Job".
- `AB_RUN_MUTATIONS=1` set deliberately, for that session only.
- Each capture goes through the workbench, so the fixture is sanitized and any
  REVIEW-tier value blocks the write pending your decision.
- A transient staging fault was observed on 2026-07-26 (HTTP 500, empty body, on
  every timeline task creation). It cleared. If it recurs mid-batch, the correct
  classification is `environment_blocked`, not a failed certification.

## What I need from you

1. Approve or amend the four above.
2. Confirm the test job is the right target, or name a different one.
3. Confirm you want `circular_restored` as the target classification rather than
   leaving these `manual_cleanup`.
