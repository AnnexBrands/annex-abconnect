# Certification & Run Evidence

How the progress artifact decides an endpoint is *certified* rather than merely
*present*. The model lives in `ab/progress/certification.py`; evidence is
committed to `tests/example_run_results.json`.

## Why the distinction exists

An earlier version of the report counted an endpoint as done when a `Route`
object existed, and rendered "100% Done" while a single endpoint in the
repository had ever been verified to run. Fixture files, Markdown pages, and
static references to `api.<group>.<method>()` were all treated as completion.

Presence and proof are now separate, and the report shows both.

## The ladder

Each level is reported independently. Nothing below is collapsed into a single
percentage.

| Level | Means | Evidence |
|---|---|---|
| **Implemented** | A public SDK method with a `Route` | Live registry |
| **Structurally complete** | Example + fixture + model test + Sphinx page present | Files on disk |
| **Operator ready** | Example uses an approved shared constant, or needs no record identifier | Static parse of the example |
| **Live verified** | The example completed successfully against a named environment | Committed run evidence |
| **Restoration verified** | A mutating example is idempotent or restored the record | Mutation evidence block |
| **Certified** | Every *applicable* level passes | All of the above |

Read-only endpoints do not require restoration. Mutating ones do.

**Structural completeness is not proof of execution.** Only *Live verified* and
*Certified* reflect a call that actually ran.

## Staleness is content-derived, never clock-derived

Evidence records `fixture_sha256` — the SHA-256 of the fixture it was captured
against. Evidence goes stale when the committed fixture no longer matches.

A date-based rule ("evidence older than N days") was rejected: it would make the
rendered HTML change without any code change, and the no-drift gate strips only
the generation timestamp, so every stale-by-clock transition would show up as
spurious drift. Content hashing also answers the question that actually matters
— *was this evidence captured against the fixture we ship today?*

Evidence written under schema 1 has no hash and is reported as **stale**, not
fresh. It cannot be proven current, so it is not counted as verified.

## Evidence schema (version 2)

```json
{
  "schema": 2,
  "results": {
    "api.<group>.<method>": {
      "status": "passing",
      "checked": "2026-06-06",
      "source": "live",
      "environment": "staging",
      "mutation_class": "read_only",
      "fixture": "SomeModel.json",
      "fixture_sha256": "0bfe9977…",
      "detail": null
    }
  }
}
```

`status` is `passing` or `failing`. Anything else is treated as missing.

## Mutation classes

Set `mutation_class` explicitly; otherwise a non-GET method is conservatively
assumed to be `manual_cleanup`.

| Class | Meaning | Restoration evidence |
|---|---|---|
| `read_only` | GET / no state change | Not required |
| `idempotent` | Re-running leaves the same end state | Self-restoring |
| `circular_restored` | Example restores the original value before finishing | **Required** |
| `destructive_with_cleanup` | Creates then deletes within the same run | **Required** |
| `manual_cleanup` | Cleanup exists but an operator must perform it | **Required** |
| `unsafe_for_automation` | Irreversible or customer-visible side effects | Can never certify |

## Mutation evidence block

Required for `circular_restored`, `destructive_with_cleanup`, and
`manual_cleanup`. All fields below must be present **and**
`final_state_verified` must be `true` — a filled-in narrative with nobody
re-reading the record does not count.

```json
"evidence": {
  "record_identifier": "TEST_JOB_DISPLAY_ID",
  "environment": "staging",
  "precondition": "job 2000000 has no note with body 'sdk-smoke'",
  "mutation": "POST /job/2000000/note body='sdk-smoke'",
  "expected_result": "201, note created with a new id",
  "observed_result": "201, note id 8842 created",
  "restoration": "DELETE /job/2000000/note/8842",
  "final_state_verified": true,
  "timestamp": "2026-07-26T14:02:11Z",
  "evidence_ref": "tests/fixtures/JobNote.json"
}
```

| Field | Purpose |
|---|---|
| `record_identifier` | The approved shared constant or record the operator sanctioned for mutation |
| `environment` | Which environment the call ran against |
| `precondition` | Starting state, so the mutation is interpretable |
| `mutation` | What was performed |
| `expected_result` / `observed_result` | What should have happened, and what did |
| `restoration` | The operation that returned the record to its original state |
| `final_state_verified` | The record was re-read after restoration |
| `timestamp` | When the run happened |
| `evidence_ref` | Fixture or response backing the claim |

## Fixture safety

Live responses must be sanitized before they are committed. This repository is
public; see the tracking issue for the mandatory deterministic sanitization
requirement. Endpoints lacking operator data should remain visibly *awaiting*
in the report rather than being unblocked with raw production responses.
