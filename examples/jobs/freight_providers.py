"""Example: api.jobs.freight_providers — list / rate-quote / save.

Live SDK example — real call, real printed pydantic response. Authored for
feature 037 (endpoint previously had no example).

The read-only :meth:`list` returns ``List[PricedFreightProvider]``; its
``option_index`` feeds the (positional) ``optionIndex`` path param on
:meth:`rate_quote`. The mutating calls (``rate_quote``/``save``) are guarded so a
default run and the verify harness exercise only the GET. Set
``AB_RUN_MUTATIONS=1`` to run them deliberately (mutates staging).

See also: https://ab-sdk.readthedocs.io/en/latest/api/jobs.html
"""

from __future__ import annotations

from ab import ABConnectAPI
from ab.cli.formatter import format_result
from examples._capture import load_request, mutations_enabled, save
from examples.constants import TEST_JOB_DISPLAY_ID


def main() -> None:
    api = ABConnectAPI(env="staging")

    # GET /job/{jobDisplayId}/freightproviders — priced provider options (read-only).
    print(f"\n# api.jobs.freight_providers.list({TEST_JOB_DISPLAY_ID})")
    providers = api.jobs.freight_providers.list(TEST_JOB_DISPLAY_ID)
    print(format_result(providers))
    save("PricedFreightProvider.json", providers)

    # Discover the optionIndex for the rate-quote path param from the list above;
    # fall back to 0 if the live result is empty / the option has no index.
    option_index = 0
    if providers and providers[0].option_index is not None:
        option_index = providers[0].option_index

    # --- state-changing calls (mutate staging) — guarded -----------------
    if mutations_enabled():
        # POST /job/{jobDisplayId}/freightproviders/{optionIndex}/ratequote
        print(
            f"\n# api.jobs.freight_providers.rate_quote({TEST_JOB_DISPLAY_ID}, "
            f"{option_index}, data=RateQuoteRequest(...))"
        )
        api.jobs.freight_providers.rate_quote(
            TEST_JOB_DISPLAY_ID,
            option_index,
            data=load_request("RateQuoteRequest.json"),
        )
        print("  (rate quote requested)")

        # POST /job/{jobDisplayId}/freightproviders
        print(f"\n# api.jobs.freight_providers.save({TEST_JOB_DISPLAY_ID}, data=ShipmentPlanProvider(...))")
        api.jobs.freight_providers.save(
            TEST_JOB_DISPLAY_ID,
            data=load_request("ShipmentPlanProvider.json"),
        )
        print("  (saved)")

        # POST /job/{jobDisplayId}/freightproviders — API 7.11 final override shape.
        print(
            f"\n# api.jobs.freight_providers.final_override("
            f"{TEST_JOB_DISPLAY_ID}, provider='FedEx 2 Day AM', pro_num=...)"
        )
        api.jobs.freight_providers.final_override(
            TEST_JOB_DISPLAY_ID,
            provider="FedEx 2 Day AM",
            provider_id="62d9c47f-fd20-e611-8b56-00505694489d",
            provider_company_code="FEDEX_2DAM",
            shipment_type="d6a05ae8-1c3b-4a0f-ba73-fabc9d496ff3",
            pro_num=f"TEST-{TEST_JOB_DISPLAY_ID}",
        )
        print("  (final override saved)")
    else:
        print(
            "\n# api.jobs.freight_providers.rate_quote / .save / .final_override skipped "
            "— set AB_RUN_MUTATIONS=1 to run (mutates staging)"
        )


if __name__ == "__main__":
    main()
