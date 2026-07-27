"""Import-surface regression tests.

These guard the failure mode that shipped as a production blocker for
downstream consumers: an endpoint module top-level-imports a name that the
corresponding models module does not define, so merely *constructing*
``ABConnectAPI`` raises ``ImportError``. Nothing else in the suite imports
every endpoint module, so a stale endpoint/model pair could reach a wheel
undetected.

Deliberately dependency-free: no fixtures, no ``tests/`` data files, no
network. That lets this exact file be copied next to an *installed* wheel and
run in a throwaway virtualenv, which is the only way to catch packaging
mistakes (a module missing from the wheel imports fine in the source checkout
and fails in site-packages).
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest


def test_documents_import_surface() -> None:
    """The exact imports whose absence broke ``ABConnectAPI`` construction."""
    from ab.api.endpoints.documents import DocumentsEndpoint
    from ab.api.models.documents import (
        DocumentUploadRequest,
        DocumentUploadResponse,
    )

    assert DocumentsEndpoint is not None
    assert DocumentUploadRequest is not None
    assert DocumentUploadResponse is not None


def test_document_upload_request_is_not_an_empty_stub() -> None:
    """Guard against 'fixing' the ImportError with a hollow placeholder class.

    A bare ``class DocumentUploadRequest(RequestModel): pass`` would satisfy
    the import test above while silently serializing to ``{}`` on the wire, so
    assert the required fields and their PascalCase multipart aliases.
    """
    from ab.api.models.documents import DocumentUploadRequest

    fields = DocumentUploadRequest.model_fields
    aliases = {name: f.alias for name, f in fields.items()}

    assert aliases["job_display_id"] == "JobDisplayId"
    assert aliases["document_type"] == "DocumentType"
    assert aliases["shared"] == "Shared"
    assert aliases["job_items"] == "JobItems"

    # Required fields must stay required — the multipart contract rejects both.
    assert fields["job_display_id"].is_required()
    assert fields["document_type"].is_required()

    # Round-trip by alias: this is what actually goes over the wire.
    dumped = DocumentUploadRequest(
        JobDisplayId="2000000", DocumentType=6, JobItems=["item-uuid"]
    ).model_dump(by_alias=True, exclude_none=True)
    assert dumped["JobDisplayId"] == "2000000"
    assert dumped["DocumentType"] == 6
    assert dumped["JobItems"] == ["item-uuid"]


def test_document_upload_response_is_not_an_empty_stub() -> None:
    """Same guard for the response model's camelCase aliases."""
    from ab.api.models.documents import DocumentUploadResponse

    aliases = {n: f.alias for n, f in DocumentUploadResponse.model_fields.items()}
    assert aliases["uploaded_files"] == "uploadedFiles"
    assert aliases["document_details"] == "documentDetails"
    assert aliases["file_name"] == "fileName"

    parsed = DocumentUploadResponse.model_validate(
        {"success": True, "fileName": "packing-list.pdf", "id": 42}
    )
    assert parsed.success is True
    assert parsed.file_name == "packing-list.pdf"
    assert parsed.id == 42


def _endpoint_module_names() -> list[str]:
    import ab.api.endpoints as endpoints_pkg

    return sorted(
        f"ab.api.endpoints.{m.name}"
        for m in pkgutil.iter_modules(endpoints_pkg.__path__)
        if not m.ispkg
    )


def test_endpoint_package_is_discoverable() -> None:
    """Sanity check so an empty walk can't make the sweep below vacuously pass."""
    names = _endpoint_module_names()
    assert len(names) > 15, f"suspiciously few endpoint modules: {names}"
    assert "ab.api.endpoints.documents" in names


@pytest.mark.parametrize("module_name", _endpoint_module_names())
def test_every_endpoint_module_imports(module_name: str) -> None:
    """Package-wide sweep: every endpoint module must import on its own."""
    importlib.import_module(module_name)


def test_client_constructs_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """``ABConnectAPI`` wires up every endpoint — the reported crash site.

    Construction is what triggered the original ``ImportError``, so exercise it
    directly. Credentials are injected as env vars (they outrank any ``.env``
    in cwd) purely to get past config validation; ``anonymous=True`` means no
    token is fetched and no request is made. Without this the test would pass
    in the repo only because a developer ``.env`` happens to be present, and
    fail against an installed wheel.
    """
    monkeypatch.setenv("ABCONNECT_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ABCONNECT_CLIENT_SECRET", "test-client-secret")

    from ab import ABConnectAPI

    api = ABConnectAPI(anonymous=True)
    assert api.documents is not None
    assert api.docs is api.documents  # back-compat alias still wired
