"""8_01 rates for explicit handling units and addresses."""

from typing import Any

from ab.api.base import BaseEndpoint
from ab.api.models.transportation import HandlingUnitRates, SelectedQuoteResult
from ab.api.route import Route

_GET_RATES = Route(
    "POST", "/job/{jobDisplayId}/rates", request_model="HandlingUnitRateRequest", response_model="HandlingUnitRates",
)
_SELECT_QUOTE = Route(
    "POST", "/job/{jobDisplayId}/rates/select-quote", request_model="SelectQuoteRequest",
    response_model="SelectedQuoteResult",
)


class JobRatesEndpoint(BaseEndpoint):
    """Rate and select transportation for an explicit set of handling units."""

    def request(self, job_display_id: int, **kwargs: Any) -> HandlingUnitRates:
        """Get carrier rates for handling units, origin, destination, and requested date.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/rates.request.html
        Request model: HandlingUnitRateRequest
        Response model: HandlingUnitRates
        """
        return self._request(_GET_RATES.bind(jobDisplayId=job_display_id), json=kwargs)

    def select_quote(self, job_display_id: int, **kwargs: Any) -> SelectedQuoteResult:
        """Preview a carrier quote from ``rates_key`` without saving a shipping record.

        Persist selection with ``jobs.freight_providers.select_rate_quote``.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/rates.select_quote.html
        Request model: SelectQuoteRequest
        Response model: SelectedQuoteResult
        """
        return self._request(_SELECT_QUOTE.bind(jobDisplayId=job_display_id), json=kwargs)
