"""Documents API endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import IO, TYPE_CHECKING, Union

from ab.api.base import BaseEndpoint
from ab.api.models.documents import DocumentUploadRequest, DocumentUploadResponse
from ab.api.models.enums import DocumentType
from ab.api.route import Route
from ab.exceptions import UnsupportedOperationError

if TYPE_CHECKING:
    from ab.api.models.documents import Document, DocumentUpdateRequest

_UPLOAD = Route(
    "POST",
    "/documents",
    request_model="DocumentUploadRequest",
    response_model="DocumentUploadResponse",
)
_LIST = Route("GET", "/documents/list", params_model="DocumentListParams", response_model="List[Document]")
_GET = Route("GET", "/documents/get/{docPath}", response_model="bytes")
_UPDATE = Route("PUT", "/documents/update/{docId}", request_model="DocumentUpdateRequest")
_GET_THUMBNAIL = Route("GET", "/documents/get/thumbnail/{docPath}", response_model="bytes")
_HIDE = Route("PUT", "/documents/hide/{docId}")

#: A file to upload: a filesystem path, raw bytes, or a binary file-like
#: object (e.g. ``io.BytesIO``). Non-path sources require ``filename=``.
FileSource = Union[str, Path, bytes, IO[bytes]]


def _file_part(file: FileSource, filename: str | None) -> tuple[str, object]:
    """Resolve *(name, file-object/bytes)* for the multipart ``file`` part."""
    if isinstance(file, (str, Path)):
        path = Path(file)
        return filename or path.name, path.open("rb")
    if filename is None:
        raise ValueError("filename= is required when uploading bytes or a file-like object")
    return filename, file


class DocumentsEndpoint(BaseEndpoint):
    """Operations on documents (ACPortal API)."""

    def upload(
        self,
        *,
        job_display_id: str,
        file_path: FileSource,
        document_type: DocumentType | int,
        document_type_description: str | None = None,
        shared: int = 0,
        tags: list[str] | None = None,
        job_items: list[str] | None = None,
        inventory_item_ids: list[int] | None = None,
        handling_unit_ids: list[int] | None = None,
        rfq_id: int | None = None,
        filename: str | None = None,
    ) -> DocumentUploadResponse:
        """POST /documents — upload a single document of any type (multipart).

        The accompanying form fields are validated through
        :class:`~ab.api.models.documents.DocumentUploadRequest` and the file is
        streamed as the ``file`` part. This is the canonical upload primitive;
        :meth:`upload_item_photo` is a thin wrapper that fills in the
        item-photo specifics.

        Args:
            job_display_id: Job display ID the document belongs to.
            file_path: The file to upload — a filesystem path, raw ``bytes``,
                or a binary file-like object (e.g. ``io.BytesIO``).
            document_type: Document type; see :class:`~ab.api.models.enums.DocumentType`.
            document_type_description: Optional human-readable type label.
            shared: Sharing bitmask (0 = private).
            tags: Optional tags to attach.
            job_items: Integer inventory ID(s) to associate (used for item photos).
            rfq_id: Optional RFQ ID to associate.
            filename: Override the multipart filename (defaults to the file's
                name; **required** for bytes / file-like sources).

        Returns:
            DocumentUploadResponse: The parsed upload result.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/documents/upload.html
        Request model: DocumentUploadRequest
        Response model: DocumentUploadResponse
        """
        if job_items is not None:
            raise UnsupportedOperationError(
                "8_01 document associations require inventory_item_ids or handling_unit_ids; "
                "legacy item UUIDs cannot be mapped."
            )
        form = DocumentUploadRequest(
            job_display_id=job_display_id,
            document_type=document_type,
            document_type_description=document_type_description,
            shared=shared,
            tags=tags,
            inventory_item_ids=inventory_item_ids,
            handling_unit_ids=handling_unit_ids,
            rfq_id=rfq_id,
        )
        data = form.model_dump(by_alias=True, exclude_none=True)
        part_name, source = _file_part(file_path, filename)
        try:
            files = {"file": (part_name, source, "application/octet-stream")}
            return self._request(_UPLOAD, files=files, data=data)
        finally:
            if isinstance(file_path, (str, Path)):
                source.close()

    def upload_item_photo(
        self,
        *,
        job_display_id: str,
        item_ids: int | list[int],
        file_path: FileSource,
        shared: int = 0,
        tags: list[str] | None = None,
        filename: str | None = None,
    ) -> DocumentUploadResponse:
        """Upload one item photo, associated with one or more job items.

        A thin convenience wrapper over :meth:`upload` that sets
        ``document_type=DocumentType.ITEM_PHOTO`` and routes ``item_ids`` to the
        ``JobInventoryItems`` form field. Accepts a single item UUID or a list.

        Args:
            job_display_id: Job display ID the photo belongs to.
            item_ids: One item UUID, or a list of UUIDs, to attach the photo to.
            file_path: The image — a filesystem path, raw ``bytes``, or a
                binary file-like object.
            shared: Sharing bitmask (0 = private).
            tags: Optional tags to attach.
            filename: Override the multipart filename (defaults to the file's
                name; required for bytes / file-like sources).

        Returns:
            DocumentUploadResponse: The parsed upload result.
        """
        items = [item_ids] if isinstance(item_ids, (int, str)) else list(item_ids)
        if not items or any(not str(i).strip() for i in items):
            raise ValueError("item_ids must contain one or more non-empty item id(s)")
        if any(isinstance(i, bool) or not isinstance(i, int) or i <= 0 for i in items):
            raise UnsupportedOperationError("8_01 item photos require positive integer inventory item_ids, not UUIDs.")
        return self.upload(
            job_display_id=job_display_id,
            file_path=file_path,
            document_type=DocumentType.ITEM_PHOTO,
            document_type_description="Item Photo",
            shared=shared,
            tags=tags,
            inventory_item_ids=items,
            filename=filename,
        )

    def upload_item_photos(
        self,
        *,
        job_display_id: str,
        item_ids: int | list[int],
        file_paths: list[FileSource],
        filenames: list[str] | None = None,
        shared: int = 0,
        tags: list[str] | None = None,
    ) -> list[DocumentUploadResponse]:
        """Upload several item photos in one call — one request per file.

        Returns one :class:`~ab.api.models.documents.DocumentUploadResponse`
        per file, in the same order as ``file_paths`` (always a list, even for
        a single file — unlike the legacy SDK's variable return). Every file is
        attached to the same ``item_ids``.

        Args:
            job_display_id: Job display ID the photos belong to.
            item_ids: One item UUID, or a list of UUIDs, to attach every photo to.
            file_paths: The image files to upload — filesystem paths, raw
                ``bytes``, or binary file-like objects.
            filenames: Multipart filenames, one per file — required when any
                entry in ``file_paths`` is not a filesystem path.
            shared: Sharing bitmask (0 = private).
            tags: Optional tags to attach to every photo.

        Returns:
            list[DocumentUploadResponse]: One result per uploaded file, in order.
        """
        if filenames is not None and len(filenames) != len(file_paths):
            raise ValueError("filenames must have one entry per file_paths entry")
        return [
            self.upload_item_photo(
                job_display_id=job_display_id,
                item_ids=item_ids,
                file_path=file_path,
                shared=shared,
                tags=tags,
                filename=filenames[i] if filenames else None,
            )
            for i, file_path in enumerate(file_paths)
        ]

    def list(
        self,
        job_display_id: str | int,
        *,
        inventory_item_id: int | None = None,
        handling_unit_id: int | None = None,
        rfq_id: int | None = None,
        item_id: str | None = None,
    ) -> list[Document]:
        """GET /documents/list

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/documents/list.html
        Query params: DocumentListParams
        Response model: List[Document]
        """
        if item_id is not None:
            raise UnsupportedOperationError(
                "Use inventory_item_id or handling_unit_id on 8_01; item UUIDs are removed."
            )
        return self._request(
            _LIST,
            params=dict(
                job_display_id=str(job_display_id),
                inventory_item_id=inventory_item_id,
                handling_unit_id=handling_unit_id,
                rfq_id=rfq_id,
            ),
        )

    def get(self, doc_path: str) -> bytes:
        """``GET /documents/get/{docPath}`` — download a document as raw bytes.

        Args:
            doc_path: The document's storage path, as returned in
                ``Document.path`` by :meth:`list` (may contain ``/``
                separators).

        Response model: bytes

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/documents/get.html
        """
        return self._request(_GET.bind(docPath=doc_path))

    def get_thumbnail(self, doc_path: str) -> bytes:
        """``GET /documents/get/thumbnail/{docPath}`` — document thumbnail bytes.

        Args:
            doc_path: The document's storage path, as returned in ``Document.path``
                (or ``Document.thumbnail_path``) by :meth:`list`.

        Response model: bytes

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/documents/get_thumbnail.html
        """
        return self._request(_GET_THUMBNAIL.bind(docPath=doc_path))

    def hide(self, doc_id: int) -> None:
        """``PUT /documents/hide/{docId}`` — hide a document from listings.

        Args:
            doc_id: Numeric document identifier (``Document.id``).

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/documents/hide.html
        """
        return self._request(_HIDE.bind(docId=doc_id))

    def update(self, doc_id: str, *, data: DocumentUpdateRequest | dict) -> None:
        """PUT /documents/update/{docId}.

        Args:
            doc_id: Document identifier.
            data: Document update payload.
                Accepts a :class:`DocumentUpdateRequest` instance or a dict.

        Request model: :class:`DocumentUpdateRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/documents/update.html
        Request model: DocumentUpdateRequest
        """
        raw = data.model_dump(by_alias=True, exclude_unset=True) if hasattr(data, "model_dump") else data
        if any(k in raw for k in ("JobItems", "jobItems", "job_items")):
            raise UnsupportedOperationError(
                "Use jobInventoryItems or jobHandlingUnits on 8_01; item UUIDs are removed."
            )
        return self._request(_UPDATE.bind(docId=doc_id), json=data)
