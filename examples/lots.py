"""Example: Lots operations (Catalog API).

Live SDK example — real call, real printed pydantic response. Migrated from the
deprecated runner (examples/_lots.py) to the plain-script form.

Targets the migrated Catalog schema: a lot no longer carries ``customerItemId``
— its external identity lives per-platform in ``platforms`` — and
``overridenData`` is now ``itemData``. Production had not migrated as of this
release, so this example runs against staging.

See also: https://ab-sdk.readthedocs.io/en/latest/api/lots.html
"""

from __future__ import annotations

from ab import ABConnectAPI
from ab.cli.formatter import format_result
from examples._capture import load_request, mutations_enabled, save
from examples.constants import TEST_LOT_ID


def main() -> None:
    api = ABConnectAPI(env="staging")

    # GET /Lot/{id}
    print(f"\n# api.lots.get({TEST_LOT_ID!r})")
    result = api.lots.get(TEST_LOT_ID)
    print(format_result(result))
    save("LotDto.json", result)

    # GET /Lot
    print("\n# api.lots.list(page_size=5)")
    listed = api.lots.list(page_size=5)
    print(format_result(listed))

    # GET /Lot/{id}/ClientItemData — read-only, safe to run unguarded.
    print(f"\n# api.lots.list_client_item_data({TEST_LOT_ID!r})")
    client_data = api.lots.list_client_item_data(TEST_LOT_ID)
    print(format_result(client_data))

    # POST /Lot/ItemData — a read despite the POST verb; the query travels in
    # the body because the ID list can be long.
    print("\n# api.lots.item_data(data=GetLotsItemDataQuery(...))")
    item_data = api.lots.item_data(data=load_request("GetLotsItemDataQuery.json"))
    print(format_result(item_data))

    if not mutations_enabled():
        print("\n# (mutating lot calls skipped — set AB_RUN_MUTATIONS=1 to run)")
        return

    # POST /Lot — creates a lot (mutates staging).
    print("\n# api.lots.create(data=AddLotRequest(...))")
    created = api.lots.create(data=load_request("AddLotRequest.json"))
    print(format_result(created))
    save("LotDto.json", created)

    # PUT /Lot/{id} — updates a lot (mutates staging).
    print(f"\n# api.lots.update({created.id!r}, data=UpdateLotRequest(...))")
    updated = api.lots.update(created.id, data=load_request("UpdateLotRequest.json"))
    print(format_result(updated))
    save("LotDto.json", updated)

    # POST /Lot/{id}/ClientItemData — attaches a client item data record.
    print(f"\n# api.lots.create_client_item_data({created.id!r}, data=...)")
    client_item_data = api.lots.create_client_item_data(
        created.id, data=load_request("AddLotClientItemDataRequest.json"),
    )
    print(format_result(client_item_data))
    save("LotClientItemDataDto.json", client_item_data)

    # DELETE /Lot/{lotId}/ClientItemData/{clientItemDataId} — no response model.
    print(f"\n# api.lots.delete_client_item_data({created.id!r}, {client_item_data.id!r})")
    print(format_result(api.lots.delete_client_item_data(created.id, client_item_data.id)))

    # POST /Lot/{targetId}/merge/{sourceId} — folds the source into the target
    # and deletes the source, so it needs a throwaway lot of its own.
    print("\n# api.lots.merge(target_id, source_id)")
    merge_source = api.lots.create(data=load_request("AddLotRequest.json"))
    merged = api.lots.merge(created.id, merge_source.id)
    print(format_result(merged))

    # DELETE /Lot/{id} — deletes a lot (mutates staging); no response model.
    print(f"\n# api.lots.delete({created.id!r})")
    print(format_result(api.lots.delete(created.id)))


if __name__ == "__main__":
    main()
