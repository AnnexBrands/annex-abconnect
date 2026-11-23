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


class JobModifiedConflictError(RequestError):
    """The job changed after the ``jobModifiedDate`` the request carried.

    Raised for the HTTP 400 that 8_01 returns from a write guarded by the job's
    modified stamp (handling units, quote selection, final quote, booking).
    Nothing was written. Read the job again, take its new modified date and
    decide whether to repeat the write.

    Attributes:
        modified_by: Name of the user who changed the job, when the server gives one.
        modified_by_system: Whether the change was made by the system.
        refresh_required: The server refuses the write outright.
        force_update_required: The server would accept the write with ``forceUpdate``.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        modified_by: str | None = None,
        modified_by_system: bool | None = None,
        refresh_required: bool = False,
        force_update_required: bool = False,
    ) -> None:
        super().__init__(status_code, message)
        self.modified_by = modified_by
        self.modified_by_system = modified_by_system
        self.refresh_required = refresh_required
        self.force_update_required = force_update_required


class ConfigurationError(ABConnectError):
    """Raised when required configuration is missing or invalid."""


class ValidationError(ABConnectError):
    """Raised when data validation fails outside of Pydantic model validation."""



class UnsupportedOperationError(ABConnectError):
    """The server removed this contract and no lossless adapter exists."""
