"""Views/Grids models for the ACPortal API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel


class GridViewDetails(ResponseModel):
    """Full view configuration — GET /views/{viewId} and GET /views/all."""

    view_id: Optional[str] = Field(None, alias="viewId", description="View ID")
    name: Optional[str] = Field(None, description="View name")
    dataset_sp: Optional[str] = Field(None, alias="datasetSp", description="Dataset stored procedure")
    columns: Optional[List[dict]] = Field(None, description="Column definitions")
    filters: Optional[List[dict]] = Field(None, description="Filter configurations")
    access: Optional[dict] = Field(None, description="Access control settings")


class GridViewAccessEntry(ResponseModel):
    """One grant on a view — an element of GET /views/{viewId}/accessinfo.

    The GET answers "who can see this view" and returns a flat row per grant,
    which is a different shape from the nested ``{users, roles}`` payload
    ``PUT /views/{viewId}/access`` accepts. They were one class, so the GET
    could not validate: every field it returns was undeclared and the response
    was a list where a single object was expected.
    """

    id: Optional[int] = Field(None, description="Access grant ID")
    company_id: Optional[str] = Field(None, alias="companyId", description="Company ID")
    role_id: Optional[str] = Field(None, alias="roleId", description="Role ID")
    user_id: Optional[str] = Field(None, alias="userId", description="User ID")
    company_name: Optional[str] = Field(None, alias="companyName", description="Company name")
    role_name: Optional[str] = Field(None, alias="roleName", description="Role name")
    user_login: Optional[str] = Field(None, alias="userLogin", description="User login")
    user_email: Optional[str] = Field(None, alias="userEmail", description="User email")


class GridViewAccess(ResponseModel):
    """View access control payload — body of PUT /views/{viewId}/access.

    Request-side only. The matching GET returns
    :class:`GridViewAccessEntry` rows.
    """

    view_id: Optional[str] = Field(None, alias="viewId", description="View ID")
    users: Optional[List[dict]] = Field(None, description="User access list")
    roles: Optional[List[dict]] = Field(None, description="Role access list")


class StoredProcedureColumn(ResponseModel):
    """Dataset stored procedure column — GET /views/datasetsps and /views/datasetsp/{spName}."""

    name: Optional[str] = Field(None, description="Column name")
    data_type: Optional[str] = Field(None, alias="dataType", description="Column data type")
    is_sortable: Optional[bool] = Field(None, alias="isSortable", description="Whether column is sortable")


class GridViewCreateRequest(RequestModel):
    """Body for POST /views."""

    name: Optional[str] = Field(None, description="View name")
    dataset_sp: Optional[str] = Field(None, alias="datasetSp", description="Dataset stored procedure")
    columns: Optional[List[dict]] = Field(None, description="Column definitions")
