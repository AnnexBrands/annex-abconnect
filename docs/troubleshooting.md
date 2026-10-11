# Troubleshooting

Start by recording your SDK version and chosen environment:

```bash
python -c "from importlib.metadata import version; print(version('annex-abconnect'))"
```

In Python, use `ABConnectAPI(env="staging")` or `env="production"` explicitly.
The CLI uses `abs` for staging and `ab` for production. Method help works without
credentials: `abs contacts get_current_user --help`.

| Symptom | What to check next |
|---|---|
| `ModuleNotFoundError: ab` | Install `annex-abconnect` using the same interpreter: `python -m pip install annex-abconnect`. The package name and import name differ. |
| `ConfigurationError` at client creation | Follow the quickstart credentials and environment-file setup. Default file-backed service accounts need username, password, client ID, and client secret. |
| `invalid_scope` during authentication | Check the scopes provisioned for your OAuth client. `ABCONNECT_SCOPES` replaces the whole default set. A single unavailable scope can reject the grant. |
| `AuthenticationError` or HTTP 401 | Verify the environment, client/user credentials, token validity, and provisioning. Use the authentication error detail to distinguish these causes. |
| HTTP 403 | Check the account's roles and access to the requested company, job, or resource. |
| `pydantic.ValidationError` | Inspect `errors()` for missing fields, aliases, and types. Request-model validation happens before sending the request. |
| `TypeError` about arguments | Open the installed method's help. Many mutations and searches require `data=...`; catalog listing takes named filter arguments. |
| Bulk-upsert 404 or wrong platform | Supply each catalog's required `platformId` and check the returned association. See What's New for corporate versus platform-user behavior. |
| Other `RequestError` | Record `status_code` and `message`, then compare the method and model to the server release. A missing route and an inaccessible record can both appear as a 404. |
| Multiple active shipments | Keep shipping-record, quote, and carrier shipment IDs separate. Use the operation's actual selector; see the 8_01 migration preview. |

## Inspect validation errors

```python
from pydantic import ValidationError
from ab.api.models.catalog import BulkUpsertRequest

try:
    request = BulkUpsertRequest.model_validate({"catalogs": [{}]})
except ValidationError as exc:
    for error in exc.errors():
        print(error["loc"], error["msg"])
```

This deliberately incomplete payload demonstrates local validation; it makes no
API request. Use [bulk upsert](api/catalog/bulk_upsert.md) for the full contract.

## Reproduce a problem clearly

Include the SDK version, environment, endpoint/method, exception class, status,
and a minimal sanitized payload or response shape. For shipment problems, state
which identifier type was supplied and how many active shipments the job has.
Exclude passwords, client secrets, access tokens, and customer data from shared
diagnostics. A passing HTTP status alone does not prove a mutation took effect;
check the resulting record when investigating a silent no-op.

Continue with [Quickstart](quickstart.md), [What's New](whats-new.md), or the
[API reference](index.md#api-reference).
