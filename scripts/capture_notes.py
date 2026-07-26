"""Discover global-note association semantics by empirical trial-and-error.

The swagger for ``/note`` does not pin down how the association fields
interact. Three asymmetries make the behaviour non-obvious:

* **Create** (``NoteRequest``) accepts ``crmContactId`` (int) + ``companyId``
  (UUID), but **not** ``franchiseId`` — the server derives ``franchiseID`` on
  the response, the caller cannot set it.
* **List** (``NotesListParams``) filters by ``contactId`` (**int**) +
  ``companyId`` — the contact filter is named differently from the create field
  (``crmContactId``), so whether they are the same axis is unverified.
* The response ``GlobalNote`` carries **both** ``crmContactId`` (int) and
  ``contactId`` (str UUID), plus a server-stamped ``franchiseID``.

This script resolves all of that by building an **association truth table**
against a provider you own (a company + its CRM contact):

    A = note created with crmContactId only
    B = note created with companyId  only
    C = note created with both

then probing each ``list(...)`` filter and recording which of {A, B, C}
surface. The presence pattern tells you whether the contact/company axes are
independent, unioned, or intersected, and the per-note ``franchiseID`` tells
you whether every provider note is stamped with an owning franchise (your
"is this note about a franchise/agent" signal).

Because the API exposes **no DELETE route**, every created note persists.
Comments are tagged ``ZZ-DISCOVERY-<ts>`` so they are easy to find, and
``--cleanup`` marks each created note ``isCompleted`` with a ``[CLOSED]``
prefix (the closest thing to a delete this API offers).

Usage::

    AB_RUN_MUTATIONS=1 python -m scripts.capture_notes \\
        --company-id <company-uuid> --crm-contact-id <int> [--env staging]

    # neutralise the notes created by the most recent run:
    AB_RUN_MUTATIONS=1 python -m scripts.capture_notes --cleanup [--env staging]

Artifacts land in ``tests/fixtures/notes/``:

* ``create_<A|B|C>.json`` — the raw ``GlobalNote`` returned by each create.
* ``probe_<label>.json``   — the raw list result for each filter probe.
* ``truth_table.json``     — the run manifest (inputs, note IDs, presence grid).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from examples._capture import mutations_enabled, to_jsonable

ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = ROOT / "tests" / "fixtures" / "notes"
MANIFEST = NOTES_DIR / "truth_table.json"


def _write(name: str, payload: object) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    path = NOTES_DIR / name
    path.write_text(json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"    wrote {path.relative_to(ROOT)}")


def _resolve_category(api, override: str | None) -> str:
    """A note requires a category UUID from the JobNoteCategory master constant.

    (Not ``get_refer_categories`` — those are RFQ referral categories and are
    rejected by ``POST /note``.) In that lookup the UUID lives in ``id`` and
    ``value`` is null, so ``id`` is what the note create expects.
    """
    if override:
        return override
    from ab.api.models.enums import MasterConstantKey

    cats = api.lookup.get_by_key(MasterConstantKey.JOB_NOTE_CATEGORY)
    if not cats:
        raise SystemExit("No JobNoteCategory values returned — pass --category <uuid> explicitly.")
    chosen = cats[0]
    cat = chosen.id or chosen.value
    print(f"  category: {cat}  ({chosen.name!r}) — override with --category")
    return str(cat)


# ---------------------------------------------------------------------------
# Capture: create the A/B/C matrix, then probe list filters
# ---------------------------------------------------------------------------

def capture(env: str, company_id: str, crm_contact_id: int, category: str | None) -> None:
    from ab import ABConnectAPI
    from ab.api.models.notes import NoteRequest

    api = ABConnectAPI(env=env)
    category = _resolve_category(api, category)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tag = f"ZZ-DISCOVERY-{stamp}"

    # --- create the three association variants -----------------------------
    variants = {
        "A": dict(crm_contact_id=crm_contact_id),                       # contact only
        "B": dict(company_id=company_id),                               # company only
        "C": dict(crm_contact_id=crm_contact_id, company_id=company_id),  # both
    }
    created: dict[str, dict] = {}
    print(f"\nCreating notes tagged {tag} ...")
    for label, assoc in variants.items():
        req = NoteRequest(comments=f"{tag} variant={label}", category=category, **assoc)
        note = api.notes.create(data=req)
        dumped = to_jsonable(note)
        created[label] = dumped
        _write(f"create_{label}.json", note)
        print(
            f"  {label}: noteID={dumped.get('noteID')} "
            f"crmContactId={dumped.get('crmContactId')} "
            f"contactId={dumped.get('contactId')} "
            f"companyId={dumped.get('companyId')} "
            f"franchiseID={dumped.get('franchiseID')}"
        )

    ids = {label: created[label].get("noteID") for label in variants}

    # --- probe each list filter, record which variants surface -------------
    probes = {
        "by_contact": dict(contact_id=crm_contact_id),
        "by_company": dict(company_id=company_id),
        "by_both": dict(contact_id=crm_contact_id, company_id=company_id),
    }
    presence: dict[str, dict[str, bool]] = {}
    print("\nProbing list filters ...")
    for label, kwargs in probes.items():
        rows = api.notes.list(**kwargs)
        _write(f"probe_{label}.json", rows)
        seen_ids = {r.note_id for r in rows}
        presence[label] = {v: (ids[v] in seen_ids) for v in variants}
        hits = ",".join(v for v in variants if presence[label][v]) or "—"
        print(f"  {label:<12} {dict(kwargs)!s:<48} n={len(rows):<3} surfaced: {hits}")

    # --- render the truth table -------------------------------------------
    print("\nAssociation truth table (rows=filter, cols=which created note appeared):")
    print(f"    {'filter':<12} " + "  ".join(f"{v}" for v in variants))
    for label in probes:
        cells = "  ".join(("✓" if presence[label][v] else "·") for v in variants)
        print(f"    {label:<12} " + "  ".join(f"{c}" for c in cells.split("  ")))
    print("\nfranchiseID per created note (server-derived — you cannot set it):")
    for label in variants:
        print(f"    {label}: {created[label].get('franchiseID')}")

    manifest = {
        "env": env,
        "capturedAt": stamp,
        "tag": tag,
        "inputs": {"companyId": company_id, "crmContactId": crm_contact_id, "category": category},
        "created": {label: created[label].get("noteID") for label in variants},
        "franchiseID": {label: created[label].get("franchiseID") for label in variants},
        "presence": presence,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n  manifest -> {MANIFEST.relative_to(ROOT)}")
    print("  (no DELETE route — run with --cleanup to mark these notes completed)")


# ---------------------------------------------------------------------------
# Cleanup: no delete endpoint exists, so neutralise via update()
# ---------------------------------------------------------------------------

def cleanup(env: str) -> None:
    from ab import ABConnectAPI
    from ab.api.models.notes import NoteRequest

    if not MANIFEST.exists():
        raise SystemExit(f"No manifest at {MANIFEST} — nothing to clean up.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    category = manifest["inputs"]["category"]
    api = ABConnectAPI(env=env)
    print(f"Closing {len(manifest['created'])} discovery note(s) from {manifest['tag']} ...")
    for label, note_id in manifest["created"].items():
        if note_id is None:
            continue
        req = NoteRequest(
            comments=f"[CLOSED] {manifest['tag']} variant={label}",
            category=category,
            is_completed=True,
        )
        api.notes.update(str(note_id), data=req)
        print(f"  closed noteID={note_id} (variant {label})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", default="staging", help="API environment (default: staging)")
    parser.add_argument("--company-id", help="Provider company UUID (companyId)")
    parser.add_argument("--crm-contact-id", type=int, help="Provider CRM contact ID (int)")
    parser.add_argument("--category", help="Note category UUID (default: first JobNoteCategory lookup id)")
    parser.add_argument("--cleanup", action="store_true", help="Mark last run's notes isCompleted (no DELETE)")
    args = parser.parse_args()

    if not mutations_enabled():
        raise SystemExit("This script creates real notes. Set AB_RUN_MUTATIONS=1 to run it deliberately.")

    if args.cleanup:
        cleanup(args.env)
        return

    if not args.company_id or args.crm_contact_id is None:
        raise SystemExit("Provide --company-id and --crm-contact-id (or use --cleanup).")
    capture(args.env, args.company_id, args.crm_contact_id, args.category)


if __name__ == "__main__":
    main()
