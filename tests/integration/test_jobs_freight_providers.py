"""Live integration tests for ``api.jobs.freight_providers``."""

from __future__ import annotations

import pytest

from ab.api.endpoints.jobs.freight_providers import _SAVE
from ab.api.models.jobs import ShipmentPlanProvider
from tests.constants import TEST_JOB_DISPLAY_ID2

pytestmark = pytest.mark.live


class TestJobFreightProvidersIntegration:
    def test_final_override_returns_200(self, api):
        payload = ShipmentPlanProvider.check(
            {
                "providerCompanyName": "UPS",
                "freightAmount": 0.0,
                "accessorialAmount": 0.0,
                "proNum": f"TEST-{TEST_JOB_DISPLAY_ID2}",
                "optionIndex": 6,
                "optionActive": True,
            }
        )

        response = api.jobs.freight_providers._client.request(
            _SAVE.method,
            _SAVE.bind(jobDisplayId=TEST_JOB_DISPLAY_ID2).path,
            json=[payload],
            raw=True,
        )

        assert response.status_code == 200, response.text
