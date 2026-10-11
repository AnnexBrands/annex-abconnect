# Quickstart Guide

This guide takes you from a fresh Python environment to a read-only staging
request. You need Python 3.11+ and an ABConnect client and user provisioned for
the target environment. See [What's New](whats-new.md) for release status.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install annex-abconnect
python -c "from importlib.metadata import version; print(version('annex-abconnect'))"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.
For reproducible deployments, pin the version you have validated, such as
`annex-abconnect==0.2.3`. Editable installation is for SDK contributors.

## Configuration

Create a `.env.staging` file in your project root:

```ini
ABCONNECT_USERNAME=myuser
ABCONNECT_PASSWORD=mypass
ABCONNECT_CLIENT_ID=myapp
ABCONNECT_CLIENT_SECRET=my-secret-uuid
ABCONNECT_ENVIRONMENT=staging
```

Use your provisioned values in this local file and keep it out of version control.

### OAuth scopes (optional)

The SDK requests a scope set appropriate to the environment, so you normally
set nothing:

| Environment | Default scopes |
|---|---|
| `staging` | `roles portalApi customerPortalApi catalog offline_access` |
| `production` | `roles portalApi customerPortalApi offline_access` |

`catalog` is offered by the staging IdentityServer only. If your client is
provisioned differently, override the whole set:

```ini
ABCONNECT_SCOPES=roles portalApi offline_access
```

The server rejects the **entire** grant with `invalid_scope` when any one
requested scope is not provisioned for your client, so the override must be a
subset your client allows. Keep `offline_access` unless you want a password
grant on every session — it is what makes the server issue a refresh token.
A scope change applies at the next password grant; delete the cached token
under `~/.cache/ab/` to apply it immediately.

## Basic Usage

Save this as `first_request.py` beside `.env.staging`:

```python
from ab import ABConnectAPI

api = ABConnectAPI(env="staging")
me = api.contacts.get_current_user()
print(me.full_name)
```

Run `python first_request.py`. A successful call prints the current user's full
name. If it fails, start with [Troubleshooting](troubleshooting.md).

To discover endpoint groups and signatures without API credentials:

```bash
ab --help
abs contacts get_current_user --help
```

`abs` targets staging; `ab` targets production. In Python, choose explicitly with
`ABConnectAPI(env="staging")` or `ABConnectAPI(env="production")`. Editor completion
and `api.groups()` also expose the endpoint groups.

## Common Operations

The snippets below continue from `api` above. Use identifiers accessible to your
account; a sample identifier is not a provisioned test record.

### Get a Company

```python
company = api.companies.get_by_id("93179b52-3da9-e311-b6f8-000c298b59ee")
print(company.name)  # "Brightwater Interiors"

# Or use a company code
company = api.companies.get_by_id("14004OH")
```

### Get Current User's Contact

```python
me = api.contacts.get_current_user()
print(me.full_name)
```

### Search Companies

```python
results = api.companies.search(data={"searchText": "Navis"})
for r in results:
    print(r.id, r.name)
```

### List Catalogs

```python
# Basic listing
catalogs = api.catalog.list()

# With filter parameters
catalogs = api.catalog.list(title="Auction", is_completed=False, page_size=10)
for catalog in catalogs.items:
    print(catalog.id, catalog.title)
```

### Paginate Through All Results

```python
from ab import ABConnectAPI, paginate

api = ABConnectAPI(env="staging")
for page in paginate(api.catalog.list, page_size=10):
    for item in page.items:
        print(item.title)
```

### Get Lookup Data

```python
countries = api.lookup.get_countries()
statuses = api.lookup.get_job_statuses()
contact_types = api.lookup.get_contact_types()
```

### List Users and Roles

```python
users = api.users.list(data={"page": 1, "pageSize": 10})
roles = api.users.get_roles()
```

## Django Integration

```python
from ab import ABConnectAPI
from django.shortcuts import render

def my_view(request):
    api = ABConnectAPI(request=request)
    company = api.companies.get_by_id("14004OH")
    return render(request, "company.html", {"company": company})
```

When using `request=`, tokens are stored in the Django session instead of the filesystem.

For a login view, authenticate explicitly with form credentials:

```python
def login_view(request):
    api = ABConnectAPI(request=request, allow_password_fallback=False)
    api.login(request.POST["username"], request.POST["password"])
```

`allow_password_fallback=False` is recommended for user-session flows so an
expired session token cannot fall back to service-account credentials.

## Error Handling

```python
from ab.exceptions import AuthenticationError, RequestError

try:
    company = api.companies.get_by_id("nonexistent")
except RequestError as e:
    print(f"API error {e.status_code}: {e.message}")
except AuthenticationError:
    print("Invalid credentials")
```

Request-model validation raises `pydantic.ValidationError` before the HTTP call;
handle it separately from an API `RequestError`. The troubleshooting guide
explains configuration, scope, validation, and server failures.
