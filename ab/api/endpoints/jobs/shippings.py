"""Typed 8_01 shippings operations."""

from __future__ import annotations

from ab.api.base import BaseEndpoint
from ab.api.models.packing import (
    Shipping,
)
from ab.api.route import Route

_GET_ALL = Route("GET", "/job/{jobDisplayId}/shippings", response_model="List[Shipping]")


class JobShippingsEndpoint(BaseEndpoint):
    """Job shippings operations; identifiers are scoped to the job."""

    def get_all(self, job_display_id: int) -> list[Shipping]:
        """``GET /job/{jobDisplayId}/shippings``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shippings.get_all.html
        Response model: List[Shipping]
        """
        return self._request(_GET_ALL.bind(jobDisplayId=job_display_id))
