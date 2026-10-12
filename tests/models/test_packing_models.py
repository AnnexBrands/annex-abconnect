"""Validate real packing captures when they have been reviewed and committed."""

import pytest

from ab.api import models
from tests.conftest import assert_no_extra_fields, require_fixture


@pytest.mark.parametrize(
    "name",
    [
        "JobInventoryItem",
        "JobHandlingUnit",
        "JobHandlingUnitDetails",
        "HandlingUnitMaterial",
        "Shipping",
        "ManageHandlingUnitsResponse",
    ],
)
def test_packing_response_fixture(name):
    data = require_fixture(name)
    for row in data if isinstance(data, list) else [data]:
        result = getattr(models, name).model_validate(row)
        assert_no_extra_fields(result)
