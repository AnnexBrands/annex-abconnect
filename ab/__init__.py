"""ABConnect SDK — typed Python client for ABConnect APIs."""

from ab.api.pagination import paginate
from ab.client import ABConnectAPI
from ab.exceptions import (
    ABConnectError,
    AuthenticationError,
    ConfigurationError,
    RequestError,
    ValidationError,
)
from ab.warnings import LegacyRequestWarning

__all__ = [
    "LegacyRequestWarning",
    "ABConnectAPI",
    "ABConnectError",
    "AuthenticationError",
    "ConfigurationError",
    "RequestError",
    "ValidationError",
    "paginate",
]
