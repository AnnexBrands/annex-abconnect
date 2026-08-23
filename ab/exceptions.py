"""Custom exceptions for the ABConnect SDK."""


class ABConnectError(Exception):
    """Base exception for all ABConnect SDK errors."""


class AuthenticationError(ABConnectError):
    """Raised when authentication fails (invalid credentials, expired tokens)."""


class RequestError(ABConnectError):
    """Raised when an API request fails with an error response.

    Attributes:
        status_code: HTTP status code from the response.
        message: Error message from the API or a description of the failure.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class ConfigurationError(ABConnectError):
    """Raised when required configuration is missing or invalid."""


class ValidationError(ABConnectError):
    """Raised when data validation fails outside of Pydantic model validation."""


class CatalogSchemaMismatchError(ABConnectError):
    """Raised when a Catalog API surface call is made against an environment
    whose schema this SDK does not model.

    The Catalog schema migration (``agentCompanyIds``, a singular
    ``seller``, per-platform external IDs, ``/Platform``, ``/Bulk/upsert``)
    is deployed to **staging** only. The ``catalog``, ``lots``, ``sellers``
    and ``platforms`` endpoints target that schema, so calling them against
    production would send bodies the old API rejects and drop fields the
    old API still returns. The guard fails fast with an explanation rather
    than surfacing a confusing 400/404 or a silently empty model.
    """
