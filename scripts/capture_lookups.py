"""Capture master-constant lookups as fixtures + a generated constants module.

Two artifacts, one source of truth:

1. ``tests/fixtures/lookups/<wire-key>.json`` — one fixture per
   :class:`~ab.api.models.enums.MasterConstantKey`, the ``model_dump`` of
   ``GET /lookup/{masterConstantKey}`` (byte-identical to
   ``examples/_capture.save``).
2. ``ab/api/lookup_constants.py`` — a ``str``/``int`` ``Enum`` per group whose
   members map a value's display name to its GUID, e.g.
   ``CancelledTypes.NO_LONGER_NEEDS_OUR_SERVICE``. Generated *from the fixtures*
   so it is deterministic and reproducible without API access.

Usage::

    python -m scripts.capture_lookups --capture          # live: refresh fixtures, then regen consts
    python -m scripts.capture_lookups --capture --env prod
    python -m scripts.capture_lookups                     # offline: regen consts from existing fixtures

The constants module is derived from the committed fixtures, so the offline
form lets anyone regenerate it after a fixture refresh. The matching tests
(``tests/integration/test_lookup_masterconstants.py`` /
``tests/models/test_lookup_constants.py``) pin both artifacts.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from ab.api.models.enums import MasterConstantKey

ROOT = Path(__file__).resolve().parent.parent
LOOKUPS_DIR = ROOT / "tests" / "fixtures" / "lookups"
CONSTANTS_FILE = ROOT / "ab" / "api" / "lookup_constants.py"


# ---------------------------------------------------------------------------
# Identifier helpers (deterministic — fixtures in, valid Python out)
# ---------------------------------------------------------------------------

def member_name(label: str) -> str:
    """Turn a lookup value's display label into an UPPER_SNAKE enum member name."""
    s = html.unescape(label)
    s = s.replace("'", "").replace("’", "")  # drop apostrophes: didn't -> didnt
    s = re.sub(r"[^0-9A-Za-z]+", "_", s).strip("_").upper()
    if not s:
        return "UNKNOWN"
    if s[0].isdigit():  # identifiers cannot start with a digit
        s = "N_" + s
    return s


def class_name(key: MasterConstantKey) -> str:
    """PascalCase class name derived from the MasterConstantKey member name.

    Uses the SDK member name (not the wire value) so e.g. the DB typo
    ``OnHoldRecolvedCode`` surfaces as ``OnHoldResolvedCode``.
    """
    return "".join(part.capitalize() for part in key.name.split("_"))


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def capture_fixtures(env: str) -> None:
    from ab import ABConnectAPI
    from examples._capture import to_jsonable

    api = ABConnectAPI(env=env)
    LOOKUPS_DIR.mkdir(parents=True, exist_ok=True)
    for key in MasterConstantKey:
        result = api.lookup.get_by_key(key)
        data = to_jsonable(result)
        out = LOOKUPS_DIR / f"{key.value}.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  captured {key.value:<24} {len(data):>4} value(s)")


# ---------------------------------------------------------------------------
# Constants generation (from fixtures)
# ---------------------------------------------------------------------------

def _load_fixture(key: MasterConstantKey) -> list[dict]:
    path = LOOKUPS_DIR / f"{key.value}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing lookup fixture: {path} — run with --capture first")
    return json.loads(path.read_text(encoding="utf-8"))


def _render_enum(key: MasterConstantKey) -> str:
    rows = _load_fixture(key)
    cls = class_name(key)
    # int-valued ids (ContactTypes) -> IntEnum-style; else str.
    base = "int" if rows and all(isinstance(r.get("id"), int) for r in rows) else "str"

    lines = [
        f"class {cls}({base}, Enum):",
        f'    """{key.value} — GET /lookup/{key.value} (MasterConstantKey.{key.name})."""',
        "",
    ]
    if not rows:
        lines.append("    # No values returned by the API at capture time.")
        lines.append("    pass")
        lines.append("")
        return "\n".join(lines)

    for row in rows:
        label = row.get("name") or row.get("value") or ""
        ident = member_name(str(label))
        raw_id = row.get("id")
        literal = repr(raw_id) if base == "str" else raw_id
        lines.append(f"    {ident} = {literal}  # {html.unescape(str(label))}")
    lines.append("")
    return "\n".join(lines)


def generate_constants() -> None:
    blocks = [_render_enum(key) for key in MasterConstantKey]

    registry_lines = ["LOOKUP_CONSTANTS: dict[MasterConstantKey, type[Enum]] = {"]
    for key in MasterConstantKey:
        registry_lines.append(f"    MasterConstantKey.{key.name}: {class_name(key)},")
    registry_lines.append("}")

    all_names = [class_name(key) for key in MasterConstantKey] + ["LOOKUP_CONSTANTS"]
    all_block = "__all__ = [\n" + "".join(f'    "{n}",\n' for n in all_names) + "]"

    header = '''"""Master-constant lookup values as enums (GENERATED — do not edit by hand).

Each enum mirrors one ``GET /lookup/{masterConstantKey}`` group: members map a
value's display name to its id (a GUID, or an int for ContactTypes). Use these
instead of pasting GUIDs, e.g.::

    api.jobs.save_feedback(job_id, CancelledTypes.NO_LONGER_NEEDS_OUR_SERVICE, cancel_job=True)

Regenerate from the committed fixtures with::

    python -m scripts.capture_lookups            # offline, from tests/fixtures/lookups/
    python -m scripts.capture_lookups --capture  # refresh fixtures from the live API first
"""

# ruff: noqa: E501  (generated data table — value labels kept inline as comments)

from __future__ import annotations

from enum import Enum

from ab.api.models.enums import MasterConstantKey

'''

    body = "\n\n".join(blocks)
    content = header + "\n" + body + "\n\n" + "\n".join(registry_lines) + "\n\n\n" + all_block + "\n"
    CONSTANTS_FILE.write_text(content, encoding="utf-8")
    print(f"  generated {CONSTANTS_FILE.relative_to(ROOT)} ({len(MasterConstantKey)} enums)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="hit the live API and refresh fixtures first")
    parser.add_argument("--env", default="staging", help="API environment for --capture (default: staging)")
    args = parser.parse_args()

    if args.capture:
        capture_fixtures(args.env)
    generate_constants()


if __name__ == "__main__":
    main()
