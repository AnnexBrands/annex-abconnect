"""Read-only 8_01 checks; never mutate a job as part of routine integration tests."""

import os

import pytest

from tests.conftest import assert_no_extra_fields

pytestmark = pytest.mark.live


@pytest.mark.parametrize("group", ["inventory", "handling_units", "shippings"])
def test_packing_collections(api, group):
    job_id = os.getenv("AB_TEST_PACKING_JOB_ID")
    if not job_id:
        pytest.skip("Set AB_TEST_PACKING_JOB_ID to a provisioned 8_01 staging job")
    records = getattr(api.jobs, group).get_all(int(job_id))
    assert isinstance(records, list)
    for record in records:
        assert record.id is not None
        assert_no_extra_fields(record)
