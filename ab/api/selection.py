"""Validate explicit shipment selectors before constructing an HTTP path."""

from uuid import UUID


def quote_id(value: str | UUID) -> str:
    """Return a nonempty quote UUID, rejecting shipping and carrier IDs."""
    try:
        parsed = value if isinstance(value, UUID) else UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("quote_id must be a quote UUID, not a shipping or carrier shipment ID") from exc
    if not parsed.int:
        raise ValueError("quote_id must not be the empty UUID")
    return str(parsed)


def shipping_id(value: int) -> int:
    """Return a positive integer shipping ID without coercing UUIDs or booleans."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("shipping_id must be a positive integer from jobs.shippings.get_all()")
    return value


def select_shipping(records, *, shipping_id: int | None = None, quote_id: str | UUID | None = None):
    """Select an active shipping record without ever choosing the first match.

    Explicit IDs must belong to this job's supplied collection. Supplying both
    IDs requires them to identify the same record. Archived records cannot be
    targets of booking/export/cancellation mutations.
    """
    if shipping_id is not None:
        if isinstance(shipping_id, bool) or not isinstance(shipping_id, int) or shipping_id <= 0:
            raise ValueError("shipping_id must be a positive integer")
    selected_quote = None
    if quote_id is not None:
        try:
            selected_quote = quote_id if isinstance(quote_id, UUID) else UUID(quote_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("quote_id must be a quote UUID") from exc
        if not selected_quote.int:
            raise ValueError("quote_id must not be the empty UUID")
    matches = [
        record
        for record in records
        if record.is_archived is False
        and (shipping_id is None or record.id == shipping_id)
        and (selected_quote is None or selected_quote in (record.freight_quote_options or []))
    ]
    if len(matches) != 1:
        raise ValueError(
            "Exactly one active shipping record must match; provide a shipping_id or quote_id from "
            "jobs.shippings.get_all(). Archived, missing, ambiguous, and conflicting selectors are rejected."
        )
    return matches[0]
