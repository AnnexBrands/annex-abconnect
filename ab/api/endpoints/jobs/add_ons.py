"""Job service add-ons for 8_01."""

from ab.api.base import BaseEndpoint
from ab.api.models.release_support import (
    JobServiceAddOnEntityListServiceResponseResult,
    JobServiceAddOnResult,
    SaveJobServiceAddOnRequestInput,
)
from ab.api.route import Route

_CURRENT_GET_ALL = Route("GET", "/job/{jobDisplayId}/addOns", response_model="List[JobServiceAddOnResult]")
_CURRENT_SAVE = Route(
    "POST",
    "/job/{jobDisplayId}/addOns",
    request_model="List[SaveJobServiceAddOnRequestInput]",
    response_model="JobServiceAddOnEntityListServiceResponseResult",
)
_CURRENT_DELETE = Route("DELETE", "/job/{jobDisplayId}/addOns/{addonId}")


class JobAddOnsEndpoint(BaseEndpoint):
    """Read and save service add-ons using current integer IDs."""

    def get_all(self, job_display_id: int) -> list[JobServiceAddOnResult]:
        """GET /job/{jobDisplayId}/addOns.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/add_ons.get_all.html
        Response model: List[JobServiceAddOnResult]
        """
        return self._request(_CURRENT_GET_ALL.bind(jobDisplayId=job_display_id))

    def save(
        self, job_display_id: int, *, data: list[SaveJobServiceAddOnRequestInput] | list[dict]
    ) -> JobServiceAddOnEntityListServiceResponseResult:
        """POST /job/{jobDisplayId}/addOns.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/add_ons.save.html
        Request model: List[SaveJobServiceAddOnRequestInput]
        Response model: JobServiceAddOnEntityListServiceResponseResult
        """
        return self._request(_CURRENT_SAVE.bind(jobDisplayId=job_display_id), json=data)

    def delete(self, job_display_id: int, addon_id: int) -> None:
        """DELETE /job/{jobDisplayId}/addOns/{addonId}.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/add_ons.delete.html
        """
        return self._request(_CURRENT_DELETE.bind(jobDisplayId=job_display_id, addonId=addon_id))
