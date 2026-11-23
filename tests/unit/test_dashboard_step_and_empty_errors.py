"""Dashboard ``step`` arriving as a number, and HTTP errors with no body."""

from unittest.mock import MagicMock

import pytest

from ab.api.models.dashboard import DashboardSummary
from ab.exceptions import RequestError
from ab.http import HttpClient


@pytest.mark.parametrize(
    ("sent", "expected"),
    [(1, "1"), (10, "10"), (2.0, "2"), ("2.", "2."), ("1 ", "1"), (None, None)],
)
def test_step_is_kept_as_a_label(sent, expected):
    summary = DashboardSummary.model_validate({"data": [{"jobDisplayID": 1, "step": sent}]})
    assert summary.data[0].step == expected


def _response(status, text, url="https://host.example/api/dashboard?viewId=43"):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.content = text.encode()
    resp.url = url
    resp.request.method = "GET"
    resp.json.side_effect = ValueError("no json")
    return resp


def test_error_with_empty_body_names_the_call():
    with pytest.raises(RequestError) as caught:
        HttpClient._handle_response(_response(500, ""))
    assert caught.value.status_code == 500
    assert "empty response body from GET /api/dashboard" in str(caught.value)
    assert "viewId" not in str(caught.value)


def test_error_with_a_body_is_unchanged():
    with pytest.raises(RequestError) as caught:
        HttpClient._handle_response(_response(500, "boom"))
    assert "boom" in str(caught.value)
