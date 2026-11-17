"""Opt-in freshness observations."""

from __future__ import annotations

from datetime import datetime, timedelta
from collections.abc import Iterable

from homeassistant.core import State


def collect_stale(
    states: Iterable[State],
    selected_entities: set[str],
    excluded_entities: set[str],
    now: datetime,
    stale_after: timedelta,
) -> list[dict]:
    """Return selected entities whose state has not changed within the threshold."""
    stale = []
    for state in states:
        if (
            state.entity_id not in selected_entities
            or state.entity_id in excluded_entities
            or state.state in ("unknown", "unavailable")
        ):
            continue
        age = now - state.last_updated
        if age <= stale_after:
            continue
        stale.append(
            {
                "entity_id": state.entity_id,
                "name": state.name,
                "last_updated": state.last_updated.isoformat(),
                "age_seconds": int(age.total_seconds()),
                "threshold_seconds": int(stale_after.total_seconds()),
            }
        )
    return stale
