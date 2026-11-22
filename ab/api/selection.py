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


#: A new quote's created and modified stamps are written a few milliseconds apart.
_UNTOUCHED_TOLERANCE_SECONDS = 5.0


def is_untouched_estimate(quote, quotes_in_shipping) -> bool:
    """Whether *quote* is still the estimate its shipping started with.

    8_01 has no "initial" or "final" marker on a quote (the 7_11 option index is
    gone). What the data does record is whether a quote has been superseded,
    modified or acted on since it was created. *quote* is an untouched estimate
    only when all of these hold; any doubt reads as a selection (``False``):

    - it is active, and the only quote in its shipping;
    - it is not a final override and has not been booked
      (``is_overridden`` and ``shipment_accepted`` are false);
    - its ``order_in_shipping`` is 1 (or absent);
    - it has not been modified since creation. For a quote created on 8_01 that
      means ``modified_date`` within a few seconds of ``created_date``. A quote
      migrated from 7_11 has no ``created_by`` and the server substitutes the
      current time for its ``created_date`` on every read, so for those the dates
      are never compared: untouched means ``modified_by`` and ``modified_date``
      are both absent.

    Blind spot, by construction: a rate selected into a **new** shipping looks
    exactly like an estimate. Pass ``shippingId`` when selecting a rate for a
    shipping that already has an estimate, and the selection is recognised here.

    Args:
        quote: A :class:`~ab.api.models.release_support.TransportationQuoteResult`.
        quotes_in_shipping: Every quote of the job, or at least every quote of
            this quote's shipping (``jobs.freight_providers.get_quotes(job)``).
            Quotes of other shippings are ignored.
    """
    if quote.shipping_id is None or not quote.active:
        return False
    if quote.is_overridden or quote.shipment_accepted:
        return False
    if quote.order_in_shipping not in (None, 1):
        return False
    siblings = [q for q in quotes_in_shipping if q.shipping_id == quote.shipping_id]
    if any(q.id != quote.id for q in siblings) or not any(q.id == quote.id for q in siblings):
        return False
    if quote.created_by is None:
        return quote.modified_by is None and quote.modified_date is None
    if quote.modified_date is None:
        return quote.modified_by is None
    if quote.created_date is None:
        return False
    try:
        elapsed = abs((quote.modified_date - quote.created_date).total_seconds())
    except TypeError:  # one stamp timezone-aware, the other naive
        return False
    return elapsed <= _UNTOUCHED_TOLERANCE_SECONDS
