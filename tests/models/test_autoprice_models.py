"""Fixture validation tests for AutoPrice models."""


from ab.api.models.autoprice import QuickQuoteResponse, QuoteRequestModel, QuoteRequestResponse
from tests.conftest import assert_no_extra_fields, load_request_fixture, require_fixture


class TestAutoPriceModels:
    def test_quick_quote_response(self):
        data = require_fixture("QuickQuoteResponse", "POST", "/AutoPrice/QuickQuote", required=True)
        model = QuickQuoteResponse.model_validate(data)
        assert isinstance(model, QuickQuoteResponse)
        assert_no_extra_fields(model)

    def test_quote_request_response(self):
        data = require_fixture("QuoteRequestResponse", "POST", "/AutoPrice/QuoteRequest")
        model = QuoteRequestResponse.model_validate(data)
        assert isinstance(model, QuoteRequestResponse)
        assert_no_extra_fields(model)

    def test_quote_request_response_accepts_v2_wrapper(self):
        data = {
            "SubmitNewQuoteRequestV2Result": {
                "JobID": "036229d8-b3b4-ee11-ac1c-0a15ce13c9bf",
                "JobDisplayID": "1974309",
                "JobFailed": False,
                "JobMessage": None,
                "QuoteCertified": True,
                "TotalAmount": 179.71,
                "PriceBreakdown": {
                    "Pickup": 15.0,
                    "Packaging": 93.83,
                    "Transportation": 65.48,
                    "Insurance": 5.4,
                    "Delivery": 0.0,
                    "Miscellaneous": 0.0,
                },
                "RequestErrors": [],
                "Warning": "",
                "Owner": {"AgentName": "Liveauctioneers.com"},
                "BookingKey": "booking-key",
            }
        }

        model = QuoteRequestResponse.model_validate(data)

        assert model.result is not None
        assert model.result.job_display_id == "1974309"
        assert model.result.quote_certified is True
        assert model.result.price_breakdown is not None
        assert model.result.price_breakdown.transportation == 65.48
        assert_no_extra_fields(model)

    def test_quote_request_model_accepts_v2_pascal_payload(self):
        data = load_request_fixture("QuoteRequestModel")

        model = QuoteRequestModel.model_validate(data)
        serialized = QuoteRequestModel.check(data)

        assert model.job_info.owner_code == "Live"
        assert model.items[0].length == "1"
        assert serialized["AccessKey"] == data["AccessKey"]
        assert serialized["JobInfo"]["OwnerCode"] == "Live"
        assert serialized["PickupService"]["Accessorials"] == []
        assert serialized["CarrierService"]["Accessorials"] == []
        assert serialized["Items"][0]["L"] == "1"
        assert "jobInfo" not in serialized

    def test_quote_request_model_accepts_swagger_lower_camel_payload(self):
        data = {
            "accessKey": "00000000-0000-0000-0000-000000000000",
            "jobInfo": {
                "ownerCode": "Live",
                "customerComments": "417034",
                "jobType": "Regular",
                "useOnlyOwnerTariffs": False,
            },
            "pickupService": {
                "date": "",
                "doneBy": "",
                "accessorials": [],
            },
            "carrierService": {
                "accessorials": [],
            },
            "items": [
                {
                    "lengthParam": "1",
                    "widthParam": "5.8",
                    "heightParam": "8",
                    "weightParam": "1",
                    "value": 384,
                    "cpack": "2",
                    "description": "0397 Salvador Dali Signed Book",
                    "customerItemId": "231986645",
                    "forceCrate": False,
                    "qtyParam": "1",
                    "doNotTip": False,
                    "commodityId": "25910",
                }
            ],
        }

        serialized = QuoteRequestModel.check(data)

        assert serialized["AccessKey"] == data["accessKey"]
        assert serialized["JobInfo"]["UseOnlyOwnerTariffs"] is False
        assert serialized["PickupService"]["Accessorials"] == []
        assert serialized["Items"][0]["L"] == "1"
        assert serialized["Items"][0]["Value"] == 384.0
        assert serialized["Items"][0]["CommodityId"] == "25910"
