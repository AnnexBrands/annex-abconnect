"""Live staging verification for the 0.2.3 ``platformId`` work.

Runs the cases the change is meant to cover, against real staging, with three
real accounts out of ``.env.staging``:

  1. each platform user uploads a catalog naming their own ``platformId`` and
     gets that platform back;
  2. every caller — platform users included — fails **locally** when
     ``platformId`` is missing, with no HTTP call leaving the process;
  3. a corporate user uploading with ``platformId`` gets the platform they
     named, for both platforms in one payload;
  4. two controls posted raw, past the model, to record what the API itself
     does: a corporate payload with no ``platformId``, and a platform user
     naming a platform their ``partnerIds`` claim does not cover.

Every external ID is prefixed with a per-run UUID so nothing collides with
real data or with a previous run. Nothing here prints a credential, a token,
or a claim value. Created catalogs — and the sellers the upserts created —
are removed in ``finally`` with the corporate account.
"""

from __future__ import annotations

import json
import uuid

from dotenv import dotenv_values
from pydantic import ValidationError

from ab import ABConnectAPI
from ab.auth.memory import MemoryTokenStorage

ENV = dotenv_values(".env.staging")
RUN = uuid.uuid4().hex[:8]

#: partner ID (from the bearer's claim) -> the platform staging maps it to.
EXPECTED_PLATFORM = {1: 11, 5: 15}

created_catalogs: list[int] = []
created_sellers: list[int] = []
results: list[str] = []


def log(line: str) -> None:
    print(line)
    results.append(line)


def session(user_key: str, pass_key: str) -> ABConnectAPI:
    """Log in with an isolated in-memory token, so accounts never share one."""
    api = ABConnectAPI(env="staging", token_storage=MemoryTokenStorage())
    api.login(ENV[user_key], ENV[pass_key])
    return api


def body(tag: str, *, platform_id: int | None = None, seller_display_id: int) -> dict:
    """A minimal valid catalog entry. ``platform_id=None`` omits the key."""
    catalog: dict = {
        "customerCatalogId": f"SDK-{RUN}-{tag}",
        "title": f"SDK 0.2.3 verification {RUN} {tag}",
        "startDate": "2026-09-01T00:00:00Z",
        "endDate": "2026-09-02T00:00:00Z",
        "lots": [{
            "customerItemId": f"SDK-{RUN}-{tag}-L1",
            "lotNumber": "1",
            "data": {"Qty": 1, "L": 10, "W": 5, "H": 3, "Wgt": 2, "Description": f"lot {tag}"},
        }],
        "seller": {
            "name": f"SDK verification seller {RUN} {tag}",
            "customerDisplayId": seller_display_id,
            "isActive": True,
        },
    }
    if platform_id is not None:
        catalog["platformId"] = platform_id
    return catalog


def record(catalogs) -> None:
    for catalog in catalogs:
        created_catalogs.append(catalog.id)
        if catalog.seller is not None:
            created_sellers.append(catalog.seller.id)


def associations(catalog) -> list[tuple[int, str]]:
    return [(p.platform_id, p.platform_catalog_id) for p in (catalog.platforms or [])]


class CountingClient:
    """Wraps a client's ``request`` so a case can prove nothing went out."""

    def __init__(self, client) -> None:
        self._client = client
        self.count = 0
        self._real = client.request

    def __enter__(self) -> "CountingClient":
        def counted(*args, **kwargs):
            self.count += 1
            return self._real(*args, **kwargs)

        self._client.request = counted
        return self

    def __exit__(self, *exc) -> None:
        self._client.request = self._real


try:
    corp = session("ABCONNECT_USERNAME", "ABCONNECT_PASSWORD")
    users = {
        "live": session("ABC_LIVE_USER", "ABC_LIVE_PASS"),
        "rago": session("ABC_RAGO_USER", "ABC_RAGO_PASS"),
    }

    corp_claims = corp._catalog.bearer_claims()
    log(f"[claims] corporate     {corp_claims.describe()}")
    for label, api in users.items():
        log(f"[claims] {label:<13} {api._catalog.bearer_claims().describe()}")

    # -- 1: each platform user names their own platform ----------------------
    for index, (label, api) in enumerate(users.items()):
        claims = api._catalog.bearer_claims()
        (partner_id,) = claims.partner_ids
        expected = EXPECTED_PLATFORM[partner_id]

        upserted = api.catalog.bulk_upsert(data={
            "catalogs": [
                body(f"{label}-own", platform_id=expected, seller_display_id=990100 + index)
            ],
        })
        record(upserted)
        got = associations(upserted[0])
        ok = [p for p, _ in got] == [expected]
        log(
            f"[case 1] {label} upload with own platformId {expected} -> associations {got} "
            f"{'PASS' if ok else 'FAIL'}"
        )

    # -- 2: platformId is required of everyone, before any HTTP ---------------
    for label, api in {"corporate": corp, **users}.items():
        with CountingClient(api._catalog) as counter:
            try:
                api.catalog.bulk_upsert(
                    data={"catalogs": [body(f"{label}-missing", seller_display_id=990200)]}
                )
                log(f"[case 2] {label} upload without platformId -> NO ERROR RAISED  FAIL")
            except ValidationError as exc:
                errors = [(e["loc"], e["type"]) for e in exc.errors()]
                log(
                    f"[case 2] {label} upload without platformId -> ValidationError "
                    f"{errors}, http calls={counter.count} "
                    f"{'PASS' if counter.count == 0 else 'FAIL'}"
                )

    # -- 3: corporate names both platforms in one payload ----------------------
    upserted = corp.catalog.bulk_upsert(data={
        "catalogs": [
            body("corp-p11", platform_id=11, seller_display_id=990201),
            body("corp-p15", platform_id=15, seller_display_id=990202),
        ],
    })
    record(upserted)
    got = [associations(c) for c in upserted]
    ok = [[p for p, _ in c] for c in got] == [[11], [15]]
    log(
        f"[case 3] corporate upload with platformId 11 and 15 -> associations {got} "
        f"{'PASS' if ok else 'FAIL'}"
    )

    # -- controls: what the API itself does, with the model stepped around ----
    def raw_post(api, label, catalog):
        payload = {"catalogs": [catalog]}
        try:
            raw = api._catalog.request("POST", "/Bulk/upsert", json=payload)
            if isinstance(raw, list):
                created_catalogs.extend(c["id"] for c in raw if "id" in c)
                created_sellers.extend(
                    c["seller"]["id"] for c in raw if isinstance(c.get("seller"), dict)
                )
                platforms = [
                    [(pl.get("platformId"), pl.get("platformCatalogId")) for pl in c.get("platforms", [])]
                    for c in raw
                ]
                log(f"[control] {label} -> HTTP 200, associations {platforms}")
            else:
                log(f"[control] {label} -> {json.dumps(raw)[:200]}")
        except Exception as exc:  # noqa: BLE001 - the control records what comes back
            log(f"[control] {label} -> {type(exc).__name__}: {str(exc)[:220]}")

    # The model would refuse these, so build the raw dicts by hand.
    corp_missing = json.loads(json.dumps(body("corp-control", seller_display_id=990203)))
    corp_missing.pop("platformId", None)
    corp_missing["startDate"] = "2026-09-01T00:00:00Z"
    corp_missing["endDate"] = "2026-09-02T00:00:00Z"
    raw_post(corp, "corporate raw POST with no platformId", corp_missing)

    mismatched = json.loads(json.dumps(body("live-mismatch", platform_id=15, seller_display_id=990204)))
    raw_post(
        users["live"],
        "platform user A (partner 1) raw POST naming platform 15",
        mismatched,
    )

finally:
    log(f"[cleanup] catalogs to delete: {created_catalogs}")
    for catalog_id in created_catalogs:
        try:
            corp.catalog.delete(catalog_id)
            log(f"[cleanup] deleted catalog {catalog_id}")
        except Exception as exc:  # noqa: BLE001
            log(f"[cleanup] catalog {catalog_id} FAILED: {type(exc).__name__}: {str(exc)[:200]}")
    for seller_id in dict.fromkeys(created_sellers):
        try:
            corp.sellers.delete(seller_id)
            log(f"[cleanup] deleted seller {seller_id}")
        except Exception as exc:  # noqa: BLE001
            log(f"[cleanup] seller {seller_id} FAILED: {type(exc).__name__}: {str(exc)[:200]}")
