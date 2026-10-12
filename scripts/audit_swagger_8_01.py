"""Reproduce the 8_01 Swagger operation audit from the recorded SDK baseline."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

BASELINE = "ae87d11"
ROOT = Path(__file__).resolve().parents[1]


def operations(spec):
    return {
        (method.upper(), path): op
        for path, methods in spec["paths"].items()
        for method, op in methods.items()
        if method in ("get", "post", "put", "delete", "patch")
    }


def content_schema(value):
    return {kind: data.get("schema") for kind, data in value.get("content", {}).items()}


def main():
    old = json.loads(subprocess.check_output(["git", "show", f"{BASELINE}:ab/api/schemas/acportal.json"], cwd=ROOT))
    current = json.loads((ROOT / "ab/api/schemas/acportal.json").read_text())
    before, after = operations(old), operations(current)
    changed = []
    for method, path in sorted(before.keys() & after.keys()):
        a, b = before[(method, path)], after[(method, path)]
        if a == b:
            continue
        categories = []
        if a.get("parameters") != b.get("parameters"):
            categories.append("parameter contract")
        if content_schema(a.get("requestBody", {})) != content_schema(b.get("requestBody", {})):
            categories.append("request contract")
        ar = {k: content_schema(v) for k, v in a.get("responses", {}).items() if k.startswith("2")}
        br = {k: content_schema(v) for k, v in b.get("responses", {}).items() if k.startswith("2")}
        if ar != br:
            categories.append("response contract" if any(ar.values()) else "response metadata newly specified")
        if not categories:
            categories.append("documentation or error-response metadata")
        changed.append({"method": method, "path": path, "categories": categories})
    artifact = {
        "baseline": BASELINE,
        "server_source": "23a8a00cd3883b4e4783de76f3e5e8c8b901660a",
        "added": [{"method": m, "path": p} for m, p in sorted(after.keys() - before.keys())],
        "removed": [{"method": m, "path": p} for m, p in sorted(before.keys() - after.keys())],
        "changed": changed,
    }
    target = ROOT / "specs/038-abconnect-8-01/swagger-audit.json"
    target.write_text(json.dumps(artifact, indent=2) + "\n")
    print({k: len(artifact[k]) for k in ("added", "removed", "changed")})


if __name__ == "__main__":
    main()
