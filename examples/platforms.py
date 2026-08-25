"""Example: Platform operations (Catalog API).

Live SDK example — real call, real printed pydantic response.

Platforms are new in the migrated Catalog schema. A platform is an external
marketplace a catalog or lot is published to; the platform ID plus an external
ID is what replaced the retired ``customerCatalogId`` / ``customerItemId``
columns. Production had not migrated as of this release, so this example runs
against staging.

The read-only ``list`` call runs by default. Everything else mutates staging and
is guarded behind ``AB_RUN_MUTATIONS=1``; ``get``/``update``/``delete`` operate
on a platform this example creates, because staging ships with none.

See also: https://ab-sdk.readthedocs.io/en/latest/api/platforms.html
"""

from __future__ import annotations

from ab import ABConnectAPI
from ab.cli.formatter import format_result
from examples._capture import load_request, mutations_enabled, save


def main() -> None:
    api = ABConnectAPI(env="staging")

    # GET /Platform
    print("\n# api.platforms.list(page_size=5)")
    listed = api.platforms.list(page_size=5)
    print(format_result(listed))

    if not mutations_enabled():
        print("\n# (mutating platform calls skipped — set AB_RUN_MUTATIONS=1 to run)")
        return

    # POST /Platform
    print("\n# api.platforms.create(data=AddPlatformRequest(...))")
    created = api.platforms.create(data=load_request("AddPlatformRequest.json"))
    print(format_result(created))
    save("PlatformDto.json", created)

    # GET /Platform/{id}
    print(f"\n# api.platforms.get({created.id})")
    fetched = api.platforms.get(created.id)
    print(format_result(fetched))
    save("PlatformDto.json", fetched)

    # PUT /Platform/{id}
    print(f"\n# api.platforms.update({created.id}, data=UpdatePlatformRequest(...))")
    updated = api.platforms.update(created.id, data=load_request("UpdatePlatformRequest.json"))
    print(format_result(updated))
    save("PlatformDto.json", updated)

    # DELETE /Platform/{id} — no response model to diff.
    print(f"\n# api.platforms.delete({created.id})")
    print(format_result(api.platforms.delete(created.id)))


if __name__ == "__main__":
    main()
