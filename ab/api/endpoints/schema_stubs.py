"""Not-yet-implemented swagger route stubs.

These methods make missing schema routes visible without marking them as
implemented. They intentionally do not use :class:`ab.api.route.Route`, so
docs/progress coverage stays honest until each route gets typed request and
response models.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import Any

from ab.api.base import BaseEndpoint


@dataclass(frozen=True)
class SchemaStubSpec:
    """A schema route that is visible in the SDK but not implemented yet."""

    method_name: str
    http_method: str
    path: str
    api_surface: str


class SchemaStubEndpoint(BaseEndpoint):
    """Base for endpoint groups that currently contain schema stubs only."""


class AdminEndpoint(SchemaStubEndpoint):
    """Administrative ACPortal routes not yet implemented by the SDK."""


class LogBufferEndpoint(SchemaStubEndpoint):
    """ABC log buffer routes not yet implemented by the SDK."""


class NotificationsEndpoint(SchemaStubEndpoint):
    """Notification routes not yet implemented by the SDK."""


class SmsTemplatesEndpoint(SchemaStubEndpoint):
    """SMS template routes not yet implemented by the SDK."""


class TestEndpoint(SchemaStubEndpoint):
    """ABC test routes not yet implemented by the SDK."""


class ValuesEndpoint(SchemaStubEndpoint):
    """Values routes not yet implemented by the SDK."""


class WebhooksEndpoint(SchemaStubEndpoint):
    """Webhook routes not yet implemented by the SDK."""


SCHEMA_STUBS: dict[str, tuple[SchemaStubSpec, ...]] = {
    "account": (
        SchemaStubSpec("post_account_register", "POST", "/account/register", "acportal"),
        SchemaStubSpec("post_account_send_confirmation", "POST", "/account/sendConfirmation", "acportal"),
        SchemaStubSpec("post_account_confirm", "POST", "/account/confirm", "acportal"),
        SchemaStubSpec("post_account_forgot", "POST", "/account/forgot", "acportal"),
        SchemaStubSpec("get_account_verifyresettoken", "GET", "/account/verifyresettoken", "acportal"),
        SchemaStubSpec("post_account_resetpassword", "POST", "/account/resetpassword", "acportal"),
        SchemaStubSpec("post_account_setpassword", "POST", "/account/setpassword", "acportal"),
        SchemaStubSpec("put_account_paymentsource_source_id", "PUT", "/account/paymentsource/{sourceId}", "acportal"),
        SchemaStubSpec(
            "delete_account_paymentsource_source_id",
            "DELETE",
            "/account/paymentsource/{sourceId}",
            "acportal",
        ),
    ),
    "address": (
        SchemaStubSpec("post_address_address_id_validated", "POST", "/address/{addressId}/validated", "acportal"),
        SchemaStubSpec(
            "post_address_address_id_avoid_validation",
            "POST",
            "/address/{addressId}/avoidValidation",
            "acportal",
        ),
    ),
    "admin": (
        SchemaStubSpec("get_admin_advancedsettings_all", "GET", "/admin/advancedsettings/all", "acportal"),
        SchemaStubSpec("get_admin_advancedsettings_id", "GET", "/admin/advancedsettings/{id}", "acportal"),
        SchemaStubSpec("delete_admin_advancedsettings_id", "DELETE", "/admin/advancedsettings/{id}", "acportal"),
        SchemaStubSpec("post_admin_advancedsettings", "POST", "/admin/advancedsettings", "acportal"),
        SchemaStubSpec(
            "get_admin_carriererrormessage_all",
            "GET",
            "/admin/carriererrormessage/all",
            "acportal",
        ),
        SchemaStubSpec("post_admin_carriererrormessage", "POST", "/admin/carriererrormessage", "acportal"),
        SchemaStubSpec(
            "get_admin_globalsettings_companyhierarchy",
            "GET",
            "/admin/globalsettings/companyhierarchy",
            "acportal",
        ),
        SchemaStubSpec(
            "get_admin_globalsettings_companyhierarchy_company_company_id",
            "GET",
            "/admin/globalsettings/companyhierarchy/company/{companyId}",
            "acportal",
        ),
        SchemaStubSpec(
            "post_admin_globalsettings_getinsuranceexceptions",
            "POST",
            "/admin/globalsettings/getinsuranceexceptions",
            "acportal",
        ),
        SchemaStubSpec(
            "post_admin_globalsettings_approveinsuranceexception",
            "POST",
            "/admin/globalsettings/approveinsuranceexception",
            "acportal",
        ),
        SchemaStubSpec("post_admin_globalsettings_intacct", "POST", "/admin/globalsettings/intacct", "acportal"),
        SchemaStubSpec("post_admin_logbuffer_flush", "POST", "/admin/logbuffer/flush", "acportal"),
        SchemaStubSpec("post_admin_logbuffer_flush_all", "POST", "/admin/logbuffer/flushAll", "acportal"),
    ),
    "companies": (
        SchemaStubSpec(
            "get_company_company_id_calendar_date",
            "GET",
            "/company/{companyId}/calendar/{date}",
            "acportal",
        ),
        SchemaStubSpec(
            "get_company_company_id_calendar_date_baseinfo",
            "GET",
            "/company/{companyId}/calendar/{date}/baseinfo",
            "acportal",
        ),
        SchemaStubSpec(
            "get_company_company_id_calendar_date_startofday",
            "GET",
            "/company/{companyId}/calendar/{date}/startofday",
            "acportal",
        ),
        SchemaStubSpec(
            "get_company_company_id_calendar_date_endofday",
            "GET",
            "/company/{companyId}/calendar/{date}/endofday",
            "acportal",
        ),
        SchemaStubSpec("get_companies_search", "GET", "/companies/search", "acportal"),
        SchemaStubSpec("post_companies_simplelist", "POST", "/companies/simplelist", "acportal"),
        SchemaStubSpec("get_companies_info_from_key", "GET", "/companies/infoFromKey", "acportal"),
        SchemaStubSpec("post_companies_filtered_customers", "POST", "/companies/filteredCustomers", "acportal"),
        SchemaStubSpec(
            "get_companies_company_id_capabilities",
            "GET",
            "/companies/{companyId}/capabilities",
            "acportal",
        ),
        SchemaStubSpec(
            "post_companies_company_id_capabilities",
            "POST",
            "/companies/{companyId}/capabilities",
            "acportal",
        ),
        SchemaStubSpec(
            "get_companies_company_id_franchisee_addresses",
            "GET",
            "/companies/{companyId}/franchiseeAddresses",
            "acportal",
        ),
        SchemaStubSpec(
            "get_company_company_id_accounts_stripe_connecturl",
            "GET",
            "/company/{companyId}/accounts/stripe/connecturl",
            "acportal",
        ),
        SchemaStubSpec(
            "post_company_company_id_accounts_stripe_completeconnection",
            "POST",
            "/company/{companyId}/accounts/stripe/completeconnection",
            "acportal",
        ),
        SchemaStubSpec(
            "delete_company_company_id_accounts_stripe",
            "DELETE",
            "/company/{companyId}/accounts/stripe",
            "acportal",
        ),
        SchemaStubSpec(
            "get_company_company_id_document_templates",
            "GET",
            "/company/{companyId}/document-templates",
            "acportal",
        ),
        SchemaStubSpec(
            "post_company_company_id_document_templates",
            "POST",
            "/company/{companyId}/document-templates",
            "acportal",
        ),
        SchemaStubSpec(
            "put_company_company_id_document_templates_document_id",
            "PUT",
            "/company/{companyId}/document-templates/{documentId}",
            "acportal",
        ),
        SchemaStubSpec(
            "delete_company_company_id_document_templates_document_id",
            "DELETE",
            "/company/{companyId}/document-templates/{documentId}",
            "acportal",
        ),
        SchemaStubSpec("get_company_company_id_setupdata", "GET", "/company/{companyId}/setupdata", "acportal"),
        SchemaStubSpec(
            "get_company_company_id_gridsettings",
            "GET",
            "/company/{companyId}/gridsettings",
            "acportal",
        ),
        SchemaStubSpec(
            "post_company_company_id_gridsettings",
            "POST",
            "/company/{companyId}/gridsettings",
            "acportal",
        ),
        SchemaStubSpec(
            "get_company_company_id_containerthicknessinches",
            "GET",
            "/company/{companyId}/containerthicknessinches",
            "acportal",
        ),
        SchemaStubSpec(
            "post_company_company_id_containerthicknessinches",
            "POST",
            "/company/{companyId}/containerthicknessinches",
            "acportal",
        ),
        SchemaStubSpec(
            "delete_company_company_id_containerthicknessinches",
            "DELETE",
            "/company/{companyId}/containerthicknessinches",
            "acportal",
        ),
        SchemaStubSpec("get_company_company_id_material", "GET", "/company/{companyId}/material", "acportal"),
        SchemaStubSpec("post_company_company_id_material", "POST", "/company/{companyId}/material", "acportal"),
        SchemaStubSpec(
            "put_company_company_id_material_material_id",
            "PUT",
            "/company/{companyId}/material/{materialId}",
            "acportal",
        ),
        SchemaStubSpec(
            "delete_company_company_id_material_material_id",
            "DELETE",
            "/company/{companyId}/material/{materialId}",
            "acportal",
        ),
        SchemaStubSpec("get_company_company_id_planner", "GET", "/company/{companyId}/planner", "acportal"),
        SchemaStubSpec("get_company_company_id_truck", "GET", "/company/{companyId}/truck", "acportal"),
        SchemaStubSpec("post_company_company_id_truck", "POST", "/company/{companyId}/truck", "acportal"),
        SchemaStubSpec(
            "put_company_company_id_truck_truck_id",
            "PUT",
            "/company/{companyId}/truck/{truckId}",
            "acportal",
        ),
        SchemaStubSpec(
            "delete_company_company_id_truck_truck_id",
            "DELETE",
            "/company/{companyId}/truck/{truckId}",
            "acportal",
        ),
    ),
    "contacts": (
        SchemaStubSpec("post_contacts_search", "POST", "/contacts/search", "acportal"),
        SchemaStubSpec("post_contacts_customers", "POST", "/contacts/customers", "acportal"),
    ),
    "jobs.email": (
        SchemaStubSpec(
            "post_email_job_display_id_labelrequest",
            "POST",
            "/email/{jobDisplayId}/labelrequest",
            "acportal",
        ),
    ),
    "jobs": (
        SchemaStubSpec(
            "get_job_job_display_id_submanagementstatus",
            "GET",
            "/job/{jobDisplayId}/submanagementstatus",
            "acportal",
        ),
        SchemaStubSpec("get_job_job_access_level", "GET", "/job/jobAccessLevel", "acportal"),
        SchemaStubSpec("get_job_document_config", "GET", "/job/documentConfig", "acportal"),
        SchemaStubSpec(
            "post_job_job_display_id_copy_document_id",
            "POST",
            "/job/{jobDisplayId}/copy/{documentId}",
            "acportal",
        ),
        SchemaStubSpec("get_jobintacct_job_display_id", "GET", "/jobintacct/{jobDisplayId}", "acportal"),
        SchemaStubSpec("post_jobintacct_job_display_id", "POST", "/jobintacct/{jobDisplayId}", "acportal"),
        SchemaStubSpec(
            "post_jobintacct_job_display_id_draft",
            "POST",
            "/jobintacct/{jobDisplayId}/draft",
            "acportal",
        ),
        SchemaStubSpec(
            "delete_jobintacct_job_display_id_franchisee_id",
            "DELETE",
            "/jobintacct/{jobDisplayId}/{franchiseeId}",
            "acportal",
        ),
        SchemaStubSpec(
            "post_jobintacct_job_display_id_apply_rebate",
            "POST",
            "/jobintacct/{jobDisplayId}/applyRebate",
            "acportal",
        ),
        SchemaStubSpec(
            "get_e_sign_job_display_id_booking_key",
            "GET",
            "/e-sign/{jobDisplayId}/{bookingKey}",
            "acportal",
        ),
        SchemaStubSpec("get_e_sign_result", "GET", "/e-sign/result", "acportal"),
    ),
    "sms_templates": (
        SchemaStubSpec(
            "get_sms_template_notification_tokens",
            "GET",
            "/SmsTemplate/notificationTokens",
            "acportal",
        ),
        SchemaStubSpec("get_sms_template_list", "GET", "/SmsTemplate/list", "acportal"),
        SchemaStubSpec("get_sms_template_template_id", "GET", "/SmsTemplate/{templateId}", "acportal"),
        SchemaStubSpec("delete_sms_template_template_id", "DELETE", "/SmsTemplate/{templateId}", "acportal"),
        SchemaStubSpec("post_sms_template_save", "POST", "/SmsTemplate/save", "acportal"),
    ),
    "jobs.tracking": (
        SchemaStubSpec(
            "get_v2_job_job_display_id_tracking_history_amount",
            "GET",
            "/v2/job/{jobDisplayId}/tracking/{historyAmount}",
            "acportal",
        ),
    ),
    "notifications": (
        SchemaStubSpec("get_notifications", "GET", "/notifications", "acportal"),
    ),
    "webhooks": (
        SchemaStubSpec("post_webhooks_stripe_handle", "POST", "/webhooks/stripe/handle", "acportal"),
        SchemaStubSpec(
            "post_webhooks_stripe_connect_handle",
            "POST",
            "/webhooks/stripe/connect/handle",
            "acportal",
        ),
        SchemaStubSpec(
            "post_webhooks_stripe_checkout_session_completed",
            "POST",
            "/webhooks/stripe/checkout.session.completed",
            "acportal",
        ),
        SchemaStubSpec(
            "post_webhooks_twilio_sms_status_callback",
            "POST",
            "/webhooks/twilio/smsStatusCallback",
            "acportal",
        ),
        SchemaStubSpec(
            "post_webhooks_twilio_body_sms_inbound",
            "POST",
            "/webhooks/twilio/body-sms-inbound",
            "acportal",
        ),
        SchemaStubSpec(
            "post_webhooks_twilio_form_sms_inbound",
            "POST",
            "/webhooks/twilio/form-sms-inbound",
            "acportal",
        ),
    ),
    "users": (
        SchemaStubSpec("get_users_pocusers", "GET", "/users/pocusers", "acportal"),
    ),
    "values": (
        SchemaStubSpec("get_values", "GET", "/Values", "acportal"),
    ),
    "autoprice": (
        SchemaStubSpec("post_autoprice_quoterequest", "POST", "/autoprice/quoterequest", "abc"),
    ),
    "log_buffer": (
        SchemaStubSpec("post_logbuffer_flush", "POST", "/logbuffer/flush", "abc"),
    ),
    "reports": (
        SchemaStubSpec("get_report_webrevenue", "GET", "/report/webrevenue", "abc"),
    ),
    "test": (
        SchemaStubSpec("get_test_renderedtemplate", "GET", "/Test/renderedtemplate", "abc"),
        SchemaStubSpec("get_test_recentestimates", "GET", "/Test/recentestimates", "abc"),
        SchemaStubSpec("get_test_contact", "GET", "/Test/contact", "abc"),
    ),
    "web2lead": (
        SchemaStubSpec("post_web2_lead_postv2", "POST", "/Web2Lead/postv2", "abc"),
    ),
}


def install_schema_stubs() -> None:
    """Install all schema-visible stubs onto their endpoint classes."""
    from ab.api.endpoints.account import AccountEndpoint
    from ab.api.endpoints.address import AddressEndpoint
    from ab.api.endpoints.autoprice import AutoPriceEndpoint
    from ab.api.endpoints.companies import CompaniesEndpoint
    from ab.api.endpoints.contacts import ContactsEndpoint
    from ab.api.endpoints.jobs import JobsEndpoint
    from ab.api.endpoints.jobs.email import JobEmailEndpoint
    from ab.api.endpoints.jobs.tracking import JobTrackingEndpoint
    from ab.api.endpoints.reports import ReportsEndpoint
    from ab.api.endpoints.users import UsersEndpoint
    from ab.api.endpoints.web2lead import Web2LeadEndpoint

    target_classes: dict[str, type[BaseEndpoint]] = {
        "account": AccountEndpoint,
        "address": AddressEndpoint,
        "admin": AdminEndpoint,
        "autoprice": AutoPriceEndpoint,
        "companies": CompaniesEndpoint,
        "contacts": ContactsEndpoint,
        "jobs": JobsEndpoint,
        "jobs.email": JobEmailEndpoint,
        "jobs.tracking": JobTrackingEndpoint,
        "log_buffer": LogBufferEndpoint,
        "notifications": NotificationsEndpoint,
        "reports": ReportsEndpoint,
        "sms_templates": SmsTemplatesEndpoint,
        "test": TestEndpoint,
        "users": UsersEndpoint,
        "values": ValuesEndpoint,
        "web2lead": Web2LeadEndpoint,
        "webhooks": WebhooksEndpoint,
    }

    for group, specs in SCHEMA_STUBS.items():
        cls = target_classes[group]
        for spec in specs:
            _install_stub(cls, spec)


def _install_stub(cls: type[BaseEndpoint], spec: SchemaStubSpec) -> None:
    existing = getattr(cls, spec.method_name, None)
    if existing is not None and not getattr(existing, "__schema_stub__", False):
        raise RuntimeError(f"{cls.__name__}.{spec.method_name} already exists")

    def stub(self: BaseEndpoint, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{spec.http_method} {spec.path} ({spec.api_surface}) is not implemented in annex-abconnect yet"
        )

    stub.__name__ = spec.method_name
    stub.__qualname__ = f"{cls.__name__}.{spec.method_name}"
    stub.__doc__ = (
        f"``{spec.http_method} {spec.path}``\n\n"
        f"Schema route on the ``{spec.api_surface}`` API surface. This SDK method is a placeholder and raises "
        f":class:`NotImplementedError` until request/response models and dispatch behavior are implemented."
    )
    stub.__signature__ = _signature_for(spec)  # type: ignore[attr-defined]
    stub.__schema_stub__ = True  # type: ignore[attr-defined]
    setattr(cls, spec.method_name, stub)


def _signature_for(spec: SchemaStubSpec) -> inspect.Signature:
    parameters = [
        inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        *(
            inspect.Parameter(_to_snake(name), inspect.Parameter.POSITIONAL_OR_KEYWORD)
            for name in _path_params(spec.path)
        ),
    ]
    if spec.http_method in {"POST", "PUT", "PATCH"}:
        parameters.append(
            inspect.Parameter(
                "data",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Any,
            )
        )
    return inspect.Signature(parameters=parameters, return_annotation=Any)


def _path_params(path: str) -> list[str]:
    return re.findall(r"\{([^}]+)\}", path)


def _to_snake(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^0-9A-Za-z_]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_").lower()

