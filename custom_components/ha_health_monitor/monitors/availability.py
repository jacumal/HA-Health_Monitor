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
