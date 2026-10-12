# AB SDK

Python SDK for the ABConnect API ecosystem — ACPortal, Catalog, and ABC APIs.

Start with a read-only request, then use the task guides and typed API reference
to build your integration. Requires Python 3.11 or newer.

## Start here

```{toctree}
:maxdepth: 1

quickstart
whats-new
migration-8-01
troubleshooting
```

| I want to… | Start here |
|---|---|
| Install, authenticate, and make my first request | [Quickstart](quickstart.md) |
| Understand the current and upcoming releases | [What's New](whats-new.md) |
| Prepare for inventory, handling units, and multiple shipments | [8_01 migration](migration-8-01.md) |
| Fix a configuration, validation, or API error | [Troubleshooting](troubleshooting.md) |
| Work with catalogs and lots | [Catalog](api/catalog.md), [Lots](api/lots.md) |
| Inspect jobs and shipping operations | [Jobs](api/jobs.md), [Shipments](api/shipments.md) |

## Install and make a first request

```bash
python -m pip install annex-abconnect
```

Configure credentials using the [quickstart](quickstart.md), then:

```python
from ab import ABConnectAPI

api = ABConnectAPI(env="staging")

me = api.contacts.get_current_user()
print(me.full_name)
```

**SDK 0.3.0 targets ABConnect 8_01:** unified inventory and handling units,
explicit shipment selection, and migration notices for supported legacy calls.
Read [What's New](whats-new.md) and the [migration guide](migration-8-01.md) before upgrading.

## API Reference

```{toctree}
:maxdepth: 2

api/account
api/companies
api/contacts
api/jobs
api/documents
api/address
api/lookup
api/users
api/catalog
api/lots
api/sellers
api/platforms
api/autoprice
api/web2lead
api/commodities
api/payments
api/shipments
api/views
api/commodity_maps
api/dashboard
api/notes
api/partners
api/reports
api/rfq
```

## Model Reference

```{toctree}
:maxdepth: 2

models/base
models/common
models/companies
models/contacts
models/jobs
models/documents
models/address
models/lookup
models/users
models/catalog
models/lots
models/sellers
models/platforms
models/autoprice
models/web2lead
models/commodities
models/payments
models/shipments
models/packing
models/transportation
models/release_support
models/rfq
models/views
models/dashboard
models/forms
models/notes
```

## Maintainer and validation guides

```{toctree}
:maxdepth: 1

release-runbook
dx-roadmap
certification-evidence
known-model-defects
mutation-batch-1-proposal
evidence/timeline-create-task-certification
evidence/timeline-update-task-investigation
FIXTURES
```

Source: [bmonson-annex/annex-abconnect](https://github.com/bmonson-annex/annex-abconnect).
