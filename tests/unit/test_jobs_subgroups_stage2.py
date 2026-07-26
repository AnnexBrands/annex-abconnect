"""Unit tests for the Stage-2 ``api.jobs.<subgroup>`` additions.

Covers the 10 subgroups added in Stage 2:

* In-jobs: ``timeline``, ``email``, ``sms``, ``freight_providers``,
  ``parcel_items``, ``tracking``, ``status``.
* Cross-endpoint moves: ``payment`` (from ``api.payments``),
  ``shipment`` (from ``api.shipments``), ``rfq`` (job-scoped methods
  that were on ``api.jobs.*``).

For each subgroup we check one representative route + verify the
deprecation shim on the legacy surface still works and emits a warning.
"""

from __future__ import annotations

import logging
import warnings
from unittest.mock import MagicMock

import pytest

from ab.api.endpoints.jobs import (
    JobEmailEndpoint,
    JobFreightProvidersEndpoint,
    JobParcelItemsEndpoint,
    JobPaymentEndpoint,
    JobRfqEndpoint,
    JobsEndpoint,
    JobShipmentEndpoint,
    JobSmsEndpoint,
    JobStatusEndpoint,
    JobTimelineEndpoint,
    JobTrackingEndpoint,
)
from ab.api.endpoints.payments import PaymentsEndpoint
from ab.api.endpoints.shipments import ShipmentsEndpoint


@pytest.fixture
def acportal():
    return MagicMock(name="acportal")


@pytest.fixture
def abc():
    return MagicMock(name="abc")


@pytest.fixture
def resolver():
    return MagicMock(name="resolver")


@pytest.fixture
def jobs(acportal, abc, resolver):
    return JobsEndpoint(acportal, abc, resolver)


# ---------------------------------------------------------------------------
# Structural — every Stage-2 subgroup is wired and the right type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("attr", "cls"),
    [
        ("timeline", JobTimelineEndpoint),
        ("email", JobEmailEndpoint),
        ("sms", JobSmsEndpoint),
        ("freight_providers", JobFreightProvidersEndpoint),
        ("parcel_items", JobParcelItemsEndpoint),
        ("tracking", JobTrackingEndpoint),
        ("status", JobStatusEndpoint),
        ("payment", JobPaymentEndpoint),
        ("shipment", JobShipmentEndpoint),
        ("rfq", JobRfqEndpoint),
    ],
)
def test_subgroup_wired(jobs, attr, cls):
    assert isinstance(getattr(jobs, attr), cls), f"api.jobs.{attr} should be a {cls.__name__}"


# ---------------------------------------------------------------------------
# Wire-level — one method per subgroup
# ---------------------------------------------------------------------------


class TestTimelineSubgroup:
    def test_response_route(self, jobs, acportal):
        acportal.request.return_value = {"tasks": []}
        jobs.timeline.response(42)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/timeline")

    def test_increment_status_route(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.timeline.increment_status(42, data={})
        args, _ = acportal.request.call_args
        assert args == ("POST", "/job/42/timeline/incrementjobstatus")


class TestEmailSubgroup:
    def test_send_template_binds_guid(self, jobs, acportal):
        acportal.request.return_value = None
        jobs.email.send_template(42, "abc-template")
        args, _ = acportal.request.call_args
        assert args == ("POST", "/job/42/email/abc-template/send")


class TestSmsSubgroup:
    def test_list_route(self, jobs, acportal):
        acportal.request.return_value = []
        jobs.sms.list(42)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/sms")


class TestFreightProvidersSubgroup:
    def test_save_wraps_single_provider_in_array(self, jobs, acportal):
        acportal.request.return_value = {"success": True}
        result = jobs.freight_providers.save(
            42,
            data={
                "providerCompanyName": "FedEx 2 Day AM",
                "providerCompanyCode": "FEDEX_2DAM",
                "optionIndex": 6,
            },
        )

        args, kwargs = acportal.request.call_args
        assert args == ("POST", "/job/42/freightproviders")
        assert kwargs["json"] == [
            {
                "providerCompanyName": "FedEx 2 Day AM",
                "providerCompanyCode": "FEDEX_2DAM",
                "optionIndex": 6,
            }
        ]
        assert result.success is True

    def test_rate_quote_binds_option_index(self, jobs, acportal):
        acportal.request.return_value = None
        jobs.freight_providers.rate_quote(42, 3, data={})
        args, _ = acportal.request.call_args
        assert args == ("POST", "/job/42/freightproviders/3/ratequote")

    def test_final_override_uses_v711_save_route_with_array_body(self, jobs, acportal):
        acportal.request.return_value = None
        jobs.freight_providers.final_override(
            42,
            provider="FedEx 2 Day AM",
            provider_id="62d9c47f-fd20-e611-8b56-00505694489d",
            provider_company_code="FEDEX_2DAM",
            shipment_type="d6a05ae8-1c3b-4a0f-ba73-fabc9d496ff3",
            pro_num="123456967897",
        )

        args, kwargs = acportal.request.call_args
        assert args == ("POST", "/job/42/freightproviders")
        assert kwargs["json"] == [
            {
                "providerID": "62d9c47f-fd20-e611-8b56-00505694489d",
                "providerCompanyName": "FedEx 2 Day AM",
                "providerCompanyCode": "FEDEX_2DAM",
                "proNum": "123456967897",
                "shipmentType": "d6a05ae8-1c3b-4a0f-ba73-fabc9d496ff3",
                "optionIndex": 6,
            }
        ]

    def test_final_override_wraps_data_and_defaults_option_index(self, jobs, acportal):
        acportal.request.return_value = None
        jobs.freight_providers.final_override(
            42,
            data={
                "providerCompanyName": "FedEx 2 Day AM",
                "providerCompanyCode": "FEDEX_2DAM",
            },
        )

        _args, kwargs = acportal.request.call_args
        assert kwargs["json"] == [
            {
                "providerCompanyName": "FedEx 2 Day AM",
                "providerCompanyCode": "FEDEX_2DAM",
                "optionIndex": 6,
            }
        ]


class TestParcelItemsSubgroup:
    def test_list_route(self, jobs, acportal):
        acportal.request.return_value = []
        jobs.parcel_items.list(42)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/parcelitems")

    def test_list_parses_wrapped_response_without_generic_warning(self, jobs, acportal, caplog):
        acportal.request.return_value = {
            "jobModifiedDate": "2026-07-05T17:15:12Z",
            "parcelItems": [{"id": 1, "description": "Packed item"}],
        }

        with caplog.at_level(logging.WARNING, logger="ab.api.base"):
            result = jobs.parcel_items.list(42)

        assert result[0].id == 1
        assert result[0].description == "Packed item"
        assert "response wrapped in dict" not in caplog.text

    def test_delete_binds_id(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.parcel_items.delete(42, "pi-1")
        args, _ = acportal.request.call_args
        assert args == ("DELETE", "/job/42/parcelitems/pi-1")

    def test_create_is_acid_and_preserves_existing_items(self, jobs, acportal):
        """POST /parcelitems is replace-all; create must merge, not wipe.

        Regression guard for the destructive bug where a single-item create
        body (no parcelItems array) cleared the whole set.
        """
        existing = {
            "jobModifiedDate": "2026-01-01",
            "parcelItems": [
                {"id": 1, "jobItemId": "A", "description": "Existing", "quantity": 1, "jobItemPkdWeight": 10.0}
            ],
        }
        saved = {
            "jobModifiedDate": "2026-01-02",
            "parcelItems": [
                {"id": 1, "jobItemId": "A", "description": "Existing", "quantity": 1, "jobItemPkdWeight": 10.0},
                {"id": 2, "jobItemId": "B", "description": "New crate", "quantity": 1, "jobItemPkdWeight": 40.0},
            ],
        }
        captured = {}

        def fake(method, path, **kwargs):
            if method == "GET":
                return existing
            if method == "POST":
                captured["body"] = kwargs.get("json")
                return saved
            return {}

        acportal.request.side_effect = fake

        created = jobs.parcel_items.create(42, data={"description": "New crate", "weight": 40})

        body = captured["body"]
        assert body["forceUpdate"] is True
        # The POST carried the FULL set: the existing item is preserved...
        assert any(p.get("id") == 1 for p in body["parcelItems"])
        # ...and the new item was appended.
        assert any(p.get("description") == "New crate" for p in body["parcelItems"])
        assert len(body["parcelItems"]) == 2
        # create returns the newly added item.
        assert created.id == 2 and created.description == "New crate"


class TestTrackingSubgroup:
    def test_get_route(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.tracking.get(42)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/tracking")

    def test_v3_route_binds_history_amount(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.tracking.v3(42, 5)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/v3/job/42/tracking/5")


class TestStatusSubgroup:
    def test_set_quote_route(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.status.set_quote(42)
        args, _ = acportal.request.call_args
        assert args == ("POST", "/job/42/status/quote")


class TestPaymentSubgroup:
    def test_get_route(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.payment.get(42)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/payment")

    def test_pay_by_source_posts_body(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.payment.pay_by_source(42, data={})
        args, _ = acportal.request.call_args
        assert args == ("POST", "/job/42/payment/bysource")


class TestShipmentSubgroup:
    def test_get_rate_quotes_keeps_legacy_list_view_over_envelope(self, jobs, acportal):
        acportal.request.return_value = {
            "ratesKey": "rates-key",
            "rates": [{"carrierName": "FedEx", "carrierCode": "FEDEX", "price": 25.0}],
            "errors": ["ignored by list view"],
        }

        result = jobs.shipment.get_rate_quotes(42)

        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/shipment/ratequotes")
        assert len(result) == 1
        assert result[0].carrier_name == "FedEx"
        assert result[0].price == 25.0

    def test_get_rate_quotes_result_returns_full_envelope(self, jobs, acportal):
        acportal.request.return_value = {
            "ratesKey": "rates-key",
            "rates": [{"carrierName": "FedEx", "carrierCode": "FEDEX", "price": 25.0}],
            "requestSnapshot": {"shipOutDate": "2026-07-05"},
            "errors": [],
        }

        result = jobs.shipment.get_rate_quotes_result(42)

        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/shipment/ratequotes")
        assert result.rates_key == "rates-key"
        assert result.request_snapshot == {"shipOutDate": "2026-07-05"}
        assert result.rates and result.rates[0].carrier_code == "FEDEX"

    def test_delete_route(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.shipment.delete(42)
        args, _ = acportal.request.call_args
        assert args == ("DELETE", "/job/42/shipment")

    def test_remove_accessorial_binds_id(self, jobs, acportal):
        acportal.request.return_value = {}
        jobs.shipment.remove_accessorial(42, "add-1")
        args, _ = acportal.request.call_args
        assert args == ("DELETE", "/job/42/shipment/accessorial/add-1")


class TestRfqSubgroup:
    def test_list_route(self, jobs, acportal):
        acportal.request.return_value = []
        jobs.rfq.list(42)
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/rfq")

    def test_status_binds_three_params(self, jobs, acportal):
        acportal.request.return_value = 0
        jobs.rfq.status(42, "3", "company-uuid")
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/rfq/statusof/3/forcompany/company-uuid")


# ---------------------------------------------------------------------------
# Deprecation shims — one per subgroup
# ---------------------------------------------------------------------------


def _expect_deprecation(call, msg_contains: str):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        call()
    matching = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert matching, "expected a DeprecationWarning"
    assert any(msg_contains in str(w.message) for w in matching), (
        f"expected a warning containing {msg_contains!r}; got {[str(w.message) for w in matching]}"
    )


class TestJobsLegacyShims:
    """The flat method names on ``JobsEndpoint`` still work and warn."""

    def test_get_timeline_response(self, jobs, acportal):
        acportal.request.return_value = {"tasks": []}
        _expect_deprecation(lambda: jobs.get_timeline_response(42), "api.jobs.timeline.response")

    def test_send_email(self, jobs, acportal):
        acportal.request.return_value = None
        _expect_deprecation(lambda: jobs.send_email(42, data={}), "api.jobs.email.send")

    def test_list_sms(self, jobs, acportal):
        acportal.request.return_value = []
        _expect_deprecation(lambda: jobs.list_sms(42), "api.jobs.sms.list")

    def test_get_tracking(self, jobs, acportal):
        acportal.request.return_value = {}
        _expect_deprecation(lambda: jobs.get_tracking(42), "api.jobs.tracking.get")

    def test_set_quote_status(self, jobs, acportal):
        acportal.request.return_value = {}
        _expect_deprecation(lambda: jobs.set_quote_status(42), "api.jobs.status.set_quote")

    def test_list_rfqs(self, jobs, acportal):
        acportal.request.return_value = []
        _expect_deprecation(lambda: jobs.list_rfqs(42), "api.jobs.rfq.list")


class TestPaymentsStandaloneShim:
    """``api.payments.*`` is now a thin shim forwarding to ``api.jobs.payment``."""

    def test_get_warns_and_forwards(self, acportal):
        acportal.request.return_value = {}
        payments = PaymentsEndpoint(acportal)
        _expect_deprecation(lambda: payments.get(42), "api.jobs.payment.get")
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/payment")

    def test_pay_by_source_warns(self, acportal):
        acportal.request.return_value = {}
        payments = PaymentsEndpoint(acportal)
        _expect_deprecation(
            lambda: payments.pay_by_source(42, data={}),
            "api.jobs.payment.pay_by_source",
        )


class TestShipmentsStandaloneShim:
    """Job-scoped methods on ``api.shipments`` warn and forward.
    Non-job-scoped methods (``get_shipment`` etc.) stay canonical here.
    """

    def test_job_scoped_warns(self, acportal):
        acportal.request.return_value = []
        shipments = ShipmentsEndpoint(acportal)
        _expect_deprecation(
            lambda: shipments.get_rate_quotes(42),
            "api.jobs.shipment.get_rate_quotes",
        )
        args, _ = acportal.request.call_args
        assert args == ("GET", "/job/42/shipment/ratequotes")

    def test_global_get_shipment_does_not_warn(self, acportal):
        acportal.request.return_value = {}
        shipments = ShipmentsEndpoint(acportal)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            shipments.get_shipment(pro_number="1234")
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert not deprecations, "non-job-scoped get_shipment should not warn"
        args, _ = acportal.request.call_args
        assert args == ("GET", "/shipment")


# ---------------------------------------------------------------------------
# CLI discovery — all 13 subgroups discoverable
# ---------------------------------------------------------------------------


def test_all_subgroups_discoverable():
    from ab.cli.discovery import discover_endpoints_from_class

    reg = discover_endpoints_from_class()
    expected = {
        "jobs.note", "jobs.on_hold", "jobs.form",
        "jobs.timeline", "jobs.email", "jobs.sms",
        "jobs.freight_providers", "jobs.parcel_items",
        "jobs.tracking", "jobs.status",
        "jobs.payment", "jobs.shipment", "jobs.rfq",
    }
    missing = expected - set(reg)
    assert not missing, f"missing subgroups: {missing}"
