"""Document models for the ACPortal API."""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import AliasChoices, Field

from ab.api.models.base import RequestModel, ResponseModel
from ab.api.models.enums import DocumentType
from ab.api.models.mixins import IdentifiedModel


class DocumentListParams(RequestModel):
    """Query parameters for GET /documents/list."""

    job_display_id: Optional[str] = Field(None, alias="jobDisplayId", description="Job display identifier")


class Document(ResponseModel, IdentifiedModel):
    """Document record — GET /documents/list and embedded in Job response.

    Live API field names differ from swagger: ``path`` not ``docPath``,
    ``typeName`` not ``docType``, ``shared`` not ``sharingLevel``.
    """

    path: Optional[str] = Field(None, description="Document storage path")
    thumbnail_path: Optional[str] = Field(None, alias="thumbnailPath", description="Thumbnail path")
    description: Optional[str] = Field(None, description="Document description")
    type_name: Optional[str] = Field(None, alias="typeName", description="Document type name")
    type_id: Optional[int] = Field(None, alias="typeId", description="Document type ID")
    file_name: Optional[str] = Field(None, alias="fileName", description="Original file name")
    shared: Optional[int] = Field(None, description="Sharing level (0=private)")
    tags: Optional[List] = Field(None, description="Document tags")
    job_items: Optional[List] = Field(None, alias="jobItems", description="Associated job items")


class DocumentUpdateRequest(RequestModel):
    """Body for PUT /documents/update/{docId}.

    API 7.11 binds the PascalCase ACPortal model (``FileName``,
    ``TypeId``, ``Shared``, ``Tags``, ``JobItems``). The older SDK names
    ``docType`` and ``sharingLevel`` are still accepted as input aliases but
    serialize to the current wire contract.
    """

    file_name: Optional[str] = Field(
        None,
        alias="FileName",
        validation_alias=AliasChoices("FileName", "fileName"),
        serialization_alias="FileName",
        description="Updated file name",
    )
    type_id: Optional[int] = Field(
        None,
        alias="TypeId",
        validation_alias=AliasChoices("TypeId", "typeId", "docType", "doc_type"),
        serialization_alias="TypeId",
        description="Updated document type ID",
    )
    shared: Optional[int] = Field(
        None,
        alias="Shared",
        validation_alias=AliasChoices("Shared", "shared", "sharingLevel", "sharing_level"),
        serialization_alias="Shared",
        description="Updated sharing level",
    )
    tags: Optional[List[str]] = Field(
        None,
        alias="Tags",
        validation_alias=AliasChoices("Tags", "tags"),
        serialization_alias="Tags",
        description="Free-form tags to attach to the document.",
    )
    job_items: Optional[List[str]] = Field(
        None,
        alias="JobItems",
        validation_alias=AliasChoices("JobItems", "jobItems", "job_items"),
        serialization_alias="JobItems",
        description="Associated job item UUIDs.",
    )


class DocumentUploadRequest(RequestModel):
    """Multipart form fields for ``POST /documents``.

    The file itself is sent as a separate ``file`` multipart part — this model
    carries only the accompanying form fields. Aliases are **PascalCase** to
    match the swagger multipart contract exactly (``JobDisplayId``,
    ``DocumentType``, ``Shared``, ``JobItems`` …), which differs from the
    camelCase convention used elsewhere, so each alias is declared explicitly.

    An *item photo* is just this request with ``document_type=DocumentType.ITEM_PHOTO``
    and ``job_items`` set to the target item UUID(s); the
    :meth:`~ab.api.endpoints.documents.DocumentsEndpoint.upload_item_photo`
    helper fills those in for you.
    """

    job_display_id: str = Field(
        ..., alias="JobDisplayId",
        description="Job display ID the document belongs to (e.g. '2000000').",
    )
    document_type: Union[DocumentType, int] = Field(
        ..., alias="DocumentType",
        description="Document type ID; see DocumentType (6 = Item Photo).",
    )
    document_type_description: Optional[str] = Field(
        None, alias="DocumentTypeDescription",
        description="Human-readable label for the document type.",
    )
    shared: int = Field(
        0, alias="Shared",
        description="Sharing bitmask (0 = private); controls portal visibility.",
    )
    tags: Optional[List[str]] = Field(
        None, alias="Tags",
        description="Free-form tags to attach to the document.",
    )
    job_items: Optional[List[str]] = Field(
        None, alias="JobItems",
        description="Item UUID(s) to associate the document with (required for item photos).",
    )
    rfq_id: Optional[int] = Field(
        None, alias="RfqId",
        description="RFQ ID to associate the document with, if applicable.",
    )


class UploadedFile(ResponseModel):
    """A single file entry within a :class:`DocumentUploadResponse`.

    The upload response shape is not described in swagger; fields mirror the
    document records the live API has been observed to return and are all
    optional so deserialization stays resilient (``ResponseModel`` allows and
    warns on unknown fields).
    """

    id: Optional[int] = Field(None, description="Server-assigned document/file ID.")
    file_name: Optional[str] = Field(None, alias="fileName", description="Stored file name.")
    file_size: Optional[int] = Field(None, alias="fileSize", description="File size in bytes.")
    document_type: Optional[str] = Field(
        None, alias="documentType",
        description="Document type name as echoed by the server.",
    )
    item_id: Optional[int] = Field(None, alias="itemId", description="Associated job item ID, if any.")
    thumbnail_url: Optional[str] = Field(
        None, alias="thumbnailUrl",
        description="URL to the generated thumbnail, if any.",
    )


class DocumentDetails(ResponseModel):
    """Document detail payload embedded in ``DocumentUploadResponse``.

    Owner source: ``SaveDocumentResponse.DocumentDetails`` in AB.ABCEntities.
    The live API usually emits camelCase, while the C# model is PascalCase, so
    both forms are accepted.
    """

    id: Optional[Union[str, int]] = Field(
        None,
        alias="id",
        validation_alias=AliasChoices("id", "Id"),
        serialization_alias="id",
        description="Server-assigned document ID.",
    )
    path: Optional[str] = Field(
        None,
        alias="path",
        validation_alias=AliasChoices("path", "Path"),
        serialization_alias="path",
        description="Document storage path.",
    )
    thumbnail_path: Optional[str] = Field(
        None,
        alias="thumbnailPath",
        validation_alias=AliasChoices("thumbnailPath", "ThumbnailPath"),
        serialization_alias="thumbnailPath",
        description="Thumbnail path.",
    )
    description: Optional[str] = Field(
        None,
        alias="description",
        validation_alias=AliasChoices("description", "Description"),
        serialization_alias="description",
        description="Document description.",
    )
    type_name: Optional[str] = Field(
        None,
        alias="typeName",
        validation_alias=AliasChoices("typeName", "TypeName"),
        serialization_alias="typeName",
        description="Document type name.",
    )
    type_id: Optional[int] = Field(
        None,
        alias="typeId",
        validation_alias=AliasChoices("typeId", "TypeId"),
        serialization_alias="typeId",
        description="Document type ID.",
    )
    file_name: Optional[str] = Field(
        None,
        alias="fileName",
        validation_alias=AliasChoices("fileName", "FileName"),
        serialization_alias="fileName",
        description="Original file name.",
    )
    shared: Optional[int] = Field(
        None,
        alias="shared",
        validation_alias=AliasChoices("shared", "Shared"),
        serialization_alias="shared",
        description="Sharing level.",
    )
    tags: Optional[List] = Field(
        None,
        alias="tags",
        validation_alias=AliasChoices("tags", "Tags"),
        serialization_alias="tags",
        description="Document tags.",
    )
    job_items: Optional[List] = Field(
        None,
        alias="jobItems",
        validation_alias=AliasChoices("jobItems", "JobItems"),
        serialization_alias="jobItems",
        description="Associated job items.",
    )


class DocumentUploadResponse(ResponseModel):
    """Response body for ``POST /documents``.

    Provisional shape (no swagger schema / live capture yet); all fields are
    optional and ``ResponseModel`` tolerates drift, so this never breaks
    deserialization even if the server adds or renames fields.
    """

    success: Optional[bool] = Field(None, description="Whether the upload succeeded.")
    successfully: Optional[bool] = Field(None, description="Legacy success flag returned by some upload paths.")
    message: Optional[str] = Field(None, description="Human-readable status or error message.")
    amazon_exception: Optional[bool] = Field(
        None, alias="amazonException", description="Whether an Amazon/S3 storage exception occurred."
    )
    amazon_error_message: Optional[str] = Field(
        None, alias="amazonErrorMessage", description="Amazon/S3 error message when upload storage fails."
    )
    amazon_error_code: Optional[Union[str, int]] = Field(
        None, alias="amazonErrorCode", description="Amazon/S3 error code when upload storage fails."
    )
    document_details: Optional[DocumentDetails] = Field(
        None, alias="documentDetails", description="Document detail payload returned by the server."
    )
    uploaded_files: Optional[List[UploadedFile]] = Field(
        None, alias="uploadedFiles",
        description="Per-file results for the upload.",
    )
    id: Optional[int] = Field(None, description="Document ID when a single file was uploaded.")
    file_name: Optional[str] = Field(
        None, alias="fileName",
        description="Stored file name when a single file was uploaded.",
    )
