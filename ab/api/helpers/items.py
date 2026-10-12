"""Job item helpers — lenient create/replace/update/delete for parcel & freight.

Exposed as ``api.jobs.items``. A thin, ergonomic layer over the routed
parcel-item and freight-item endpoints that:

* accepts loose keyword input and silently drops keys the request model does
  not declare, so callers never fight ``extra="forbid"`` validation — i.e. the
  pydantic model never "squawks";
* implements freight's *replace-all* semantics with get-merge-write, so
  updating or deleting one freight item preserves the others (the freight
  endpoint takes a full ``SaveAllFreightItemsRequest`` and has no per-item
  routes); and
* round-trips GET responses (now drift-free, see :class:`JobFreightItem`) back
  into requests losslessly.

Like :class:`~ab.api.helpers.timeline.TimelineHelpers` and
:class:`~ab.api.helpers.agent.AgentHelpers`, this is a plain helper (not a
routed :class:`~ab.api.base.BaseEndpoint` subgroup): it composes existing
endpoints and introduces no new routes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterable

from ab.api.models.jobs import (
    FreightShipment,
)

if TYPE_CHECKING:
    from ab.api.endpoints.jobs import JobsEndpoint
    from ab.api.models.jobs import JobFreightItem, ParcelItem
    from ab.api.models.shared import ServiceBaseResponse

logger = logging.getLogger(__name__)

#: Friendly shorthand → ``FreightShipment`` python field names, so callers can
#: write ``replace_freight(job, fid, weight=120, length=10)`` without knowing
#: the item/total field split.
_FREIGHT_SHORTHAND = {
    "weight": "item_weight",
    "length": "item_length",
    "width": "item_width",
    "height": "item_height",
    "value": "item_value",
    "description": "freight_description",
    "freight_class": "freight_item_class",
    "nmfc": "nmfc_item",
}


def _known_keys(model_cls: type) -> set[str]:
    """Every field name and alias a model accepts."""
    keys: set[str] = set()
    for name, field in model_cls.model_fields.items():
        keys.add(name)
        if field.alias:
            keys.add(field.alias)
    return keys


def _filtered(model_cls: type, data: dict) -> dict:
    """Drop keys *model_cls* does not declare so ``extra="forbid"`` never trips."""
    allowed = _known_keys(model_cls)
    kept = {k: v for k, v in data.items() if k in allowed}
    dropped = sorted(set(data) - set(kept))
    if dropped:
        logger.debug("%s: dropped unrecognized keys %s", model_cls.__name__, dropped)
    return kept


def _normalize_freight_fields(fields: dict) -> dict:
    """Apply freight shorthand, then keep only ``FreightShipment`` keys."""
    translated: dict[str, Any] = {}
    allowed = _known_keys(FreightShipment)
    for key, value in fields.items():
        if key in allowed:
            translated[key] = value
        elif key in _FREIGHT_SHORTHAND:
            translated[_FREIGHT_SHORTHAND[key]] = value
        else:
            logger.debug("FreightShipment: dropped unrecognized key %r", key)
    return translated


class JobItemsHelpers:
    """Lenient parcel/freight item operations — ``api.jobs.items``."""

    def __init__(self, jobs: JobsEndpoint) -> None:
        self._jobs = jobs

    # ---- Parcel items -------------------------------------------------------

    def list_parcel(self, job_display_id: int) -> list[ParcelItem]:
        """Return the job's parcel items (``GET /job/{id}/parcelitems``)."""
        return self._jobs.parcel_items.list(job_display_id)

    def upsert_parcel(self, job_display_id: int, *, description: str, **fields: Any) -> ParcelItem:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    def update_parcel(self, job_display_id: int, item_id: str, **fields: Any) -> ServiceBaseResponse:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    def delete_parcel(self, job_display_id: int, parcel_item_id: str) -> ServiceBaseResponse:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    def replace_parcel(
        self, job_display_id: int, parcel_item_id: str, *, description: str, **fields: Any
    ) -> ParcelItem:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    # ---- Freight items (get-merge-write; replace-all) -----------------------

    def list_freight(self, job_display_id: int) -> list[JobFreightItem]:
        """Return the job's current freight items (from ``GET /job/{id}``)."""
        job = self._jobs.get(job_display_id)
        return list(getattr(job, "freight_items", None) or [])

    def _current_freight_dicts(self, job_display_id: int) -> list[dict]:
        """Current freight items as ``FreightShipment``-shaped camelCase dicts."""
        return [
            _filtered(FreightShipment, item.model_dump(by_alias=True, exclude_none=True))
            for item in self.list_freight(job_display_id)
        ]

    @staticmethod
    def _matches(item: dict, *, freight_item_id: str | None, item_id: str | None) -> bool:
        if freight_item_id is not None and item.get("freightItemId") == freight_item_id:
            return True
        return item_id is not None and item.get("itemID") == item_id

    def set_freight(
        self, job_display_id: int, items: Iterable[Any], *, force_update: bool = True
    ) -> list[JobFreightItem]:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    def upsert_freight(
        self,
        job_display_id: int,
        *,
        freight_item_id: str | None = None,
        item_id: str | None = None,
        **fields: Any,
    ) -> list[JobFreightItem]:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    def replace_freight(self, job_display_id: int, freight_item_id: str, **fields: Any) -> list[JobFreightItem]:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )

    def delete_freight(self, job_display_id: int, freight_item_id: str) -> list[JobFreightItem]:
        """Legacy mutation; use inventory/handling_units on 8_01."""
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            (
                "8_01 replaced parcel/freight item writes. Use jobs.inventory and jobs.handling_units with "
                "their integer IDs; legacy UUIDs cannot be translated losslessly."
            )
        )


def _normalize_freight_to_camel(fields: dict) -> dict:
    """Normalize loose kwargs to camelCase ``FreightShipment`` keys via the model."""
    snake = _normalize_freight_fields(fields)
    # Round-trip through the request model to get camelCase aliases + type
    # coercion, dropping nothing (already filtered) and never raising on extras.
    model = FreightShipment.model_validate(snake)
    return model.model_dump(by_alias=True, exclude_unset=True)
