"""Example: Catalog operations.

Live SDK example — real call, real printed pydantic response. Migrated from the
deprecated runner (examples/_catalog.py) to the plain-script form.

Targets the migrated Catalog schema (staging only): a catalog carries
``agentCompanyIds``, exactly one ``seller``, and per-platform external IDs in
``platforms``. Against production these calls raise
:class:`~ab.exceptions.CatalogSchemaMismatchError`.

The read-only calls (``get``, ``list``) run by default. The state-changing calls
(create / update / merge / bulk_upsert / delete) mutate staging, so they are
guarded: set ``AB_RUN_MUTATIONS=1`` (or tick "confirm" in the progress app) to
run them.

See also: https://ab-sdk.readthedocs.io/en/latest/api/catalog.html
"""

from __future__ import annotations

from ab import ABConnectAPI
from ab.cli.formatter import format_result
from examples._capture import load_request, mutations_enabled, save
from examples.constants import TEST_CATALOG_ID


def main() -> None:
    api = ABConnectAPI(env="staging")

    # GET /Catalog/{id}
    print(f"\n# api.catalog.get({TEST_CATALOG_ID})")
    result = api.catalog.get(TEST_CATALOG_ID)
    print(format_result(result))
    save("CatalogWithLotsDto.json", result)

    # GET /Catalog
    print("\n# api.catalog.list(page_size=5)")
    listed = api.catalog.list(page_size=5)
    print(format_result(listed))

    # The remaining calls write to staging — guarded behind AB_RUN_MUTATIONS=1.
    if not mutations_enabled():
        print("\n# (mutating catalog calls skipped — set AB_RUN_MUTATIONS=1 to run)")
        return

    # POST /Catalog
    print("\n# api.catalog.create(data=AddCatalogRequest(...))")
    created = api.catalog.create(data=load_request("AddCatalogRequest.json"))
    print(format_result(created))
    save("CatalogExpandedDto.json", created)

    # PUT /Catalog/{id}
    print(f"\n# api.catalog.update({created.id}, data=UpdateCatalogRequest(...))")
    updated = api.catalog.update(created.id, data=load_request("UpdateCatalogRequest.json"))
    print(format_result(updated))
    save("CatalogExpandedDto.json", updated)

    # POST /Catalog/{targetId}/merge/{sourceId} — folds the source into the
    # target and deletes the source, so it needs a throwaway catalog of its own.
    print("\n# api.catalog.merge(target_id, source_id)")
    merge_source = api.catalog.create(data=load_request("AddCatalogRequest.json"))
    merged = api.catalog.merge(created.id, merge_source.id)
    print(format_result(merged))

    # POST /Bulk/upsert
    print("\n# api.catalog.bulk_upsert(data=BulkUpsertRequest(...))")
    bulk_result = api.catalog.bulk_upsert(data=load_request("BulkUpsertRequest.json"))
    print(format_result(bulk_result))

    # DELETE /Catalog/{id} — no response model to diff.
    print(f"\n# api.catalog.delete({created.id})")
    delete_result = api.catalog.delete(created.id)
    print(format_result(delete_result))


if __name__ == "__main__":
    main()
