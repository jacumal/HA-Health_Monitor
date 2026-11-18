"""Availability observations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from homeassistant.core import State


def collect_unavailable(
    states: Iterable[State],
    excluded_entities: set[str],
    now: datetime,
    grace_period: timedelta,
) -> list[dict]:
    """Return entities that have remained unavailable beyond the grace period."""
    unavailable = []
    for state in states:
        if state.entity_id in excluded_entities or state.state != "unavailable":
            continue
        duration = now - state.last_changed
        if duration < grace_period:
            continue
        unavailable.append(
            {
                "entity_id": state.entity_id,
                "name": state.name,
                "last_changed": state.last_changed.isoformat(),
                "duration_seconds": int(duration.total_seconds()),
            }
        )
    return unavailable


def collect_disabled_entities(registry_entries: Iterable) -> list[dict]:
    """Return registry entities explicitly disabled in Home Assistant."""
    disabled = []
    for entry in registry_entries:
        disabled_by = getattr(entry, "disabled_by", None)
        if disabled_by is None:
            continue
        disabled.append(
            {
                "entity_id": entry.entity_id,
                "name": getattr(entry, "name", None)
                or getattr(entry, "original_name", None)
                or entry.entity_id,
                "platform": getattr(entry, "platform", None),
                "disabled_by": getattr(disabled_by, "value", str(disabled_by)),
                "entity_category": getattr(
                    getattr(entry, "entity_category", None), "value",
                    getattr(entry, "entity_category", None),
                ),
            }
        )
    return sorted(disabled, key=lambda item: item["entity_id"])
