"""Caller-visible compatibility notices for retained legacy API requests."""

import warnings


class LegacyRequestWarning(UserWarning):
    """A supported legacy request has a more explicit 8_01 replacement.

    This is not a removal notice. Filter this category to control migration
    notices independently of other SDK or Python warnings.
    """


def warn_legacy_request(old: str, replacement: str) -> None:
    """Attribute the notice to the SDK caller, including older forwarding shims."""
    import inspect

    frame = inspect.currentframe()
    stacklevel = 1
    try:
        while frame is not None and str(frame.f_globals.get("__name__", "")).startswith("ab."):
            stacklevel += 1
            frame = frame.f_back
    finally:
        del frame
    warnings.warn(
        f"{old} uses a legacy request shape. Use {replacement} for explicit 8_01 selection. "
        "The legacy request remains supported; no removal is scheduled.",
        LegacyRequestWarning,
        stacklevel=stacklevel,
    )
