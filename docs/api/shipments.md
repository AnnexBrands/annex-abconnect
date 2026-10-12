# Shipments

Use `api.jobs.shippings.get_all(job_id)` to inspect a job's shipping records and
`api.jobs.shipment` for quote-specific booking, validation, cancellation, and
shipping-specific export data. See the [8_01 migration guide](../migration-8-01.md).

`api.shipments.get_shipment()` reads global carrier shipment details.
`get_shipment_document(doc_id, franchisee_id=...)` calls `GET /shipment/document`
with both query parameters. `get_global_accessorials()` is retained but raises
`UnsupportedOperationError`: its server implementation is unavailable.

Older job-scoped names on `api.shipments` are deprecation shims to
`api.jobs.shipment`. Supported legacy requests warn; removed rate/accessorial
contracts raise before HTTP. Prefer handling-unit rates and `api.jobs.add_ons`.

```{eval-rst}
.. autoclass:: ab.api.endpoints.shipments.ShipmentsEndpoint
   :members:
   :undoc-members:
```

## Per-endpoint reference

```{toctree}
:maxdepth: 1
:glob:

shipments/*
```
