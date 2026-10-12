"""Typed 8_01 inventory operations."""

from __future__ import annotations

from typing import Any

from ab.api.base import BaseEndpoint
from ab.api.models.packing import (
    JobInventoryItem,
)
from ab.api.route import Route

_GET_ALL = Route("GET", "/job/{jobDisplayId}/inventory", response_model="List[JobInventoryItem]")
_CREATE = Route(
    "POST", "/job/{jobDisplayId}/inventory", request_model="JobInventoryItemModel", response_model="JobInventoryItem"
)
_UPDATE = Route("PUT", "/job/{jobDisplayId}/inventory/{id}", request_model="JobInventoryItemModel")
_DELETE = Route("DELETE", "/job/{jobDisplayId}/inventory/{id}")


class JobInventoryEndpoint(BaseEndpoint):
    """Job inventory operations; identifiers are scoped to the job."""

    def get_all(self, job_display_id: int) -> list[JobInventoryItem]:
        """``GET /job/{jobDisplayId}/inventory``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/inventory.get_all.html
        Response model: List[JobInventoryItem]
        """
        return self._request(_GET_ALL.bind(jobDisplayId=job_display_id))

    def create(self, job_display_id: int, **kwargs: Any) -> JobInventoryItem:
        """``POST /job/{jobDisplayId}/inventory``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/inventory.create.html
        Request model: JobInventoryItemModel
        Response model: JobInventoryItem
        """
        return self._request(_CREATE.bind(jobDisplayId=job_display_id), json=kwargs)

    def update(self, job_display_id: int, inventory_item_id: int, **kwargs: Any) -> None:
        """``PUT /job/{jobDisplayId}/inventory/{id}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/inventory.update.html
        Request model: JobInventoryItemModel
        """
        return self._request(_UPDATE.bind(jobDisplayId=job_display_id, id=inventory_item_id), json=kwargs)

    def delete(self, job_display_id: int, inventory_item_id: int) -> None:
        """``DELETE /job/{jobDisplayId}/inventory/{id}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/inventory.delete.html
        """
        return self._request(_DELETE.bind(jobDisplayId=job_display_id, id=inventory_item_id))
