"""Conservative automation health checks; does not inspect trace internals."""
from __future__ import annotations
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

def collect_automation_health(
    states: Iterable[Any], excluded_entities: set[str], now: datetime,
    grace_period: timedelta,
) -> dict[str, Any]:
    """Count enabled/disabled automations and report persistent unavailable states."""
    items = [s for s in states if s.entity_id.startswith("automation.")
             and s.entity_id not in excluded_entities]
    unavailable, enabled, disabled, assessed = [], 0, 0, 0
    for state in items:
        if state.state == "on":
            enabled += 1
            assessed += 1
        elif state.state == "off":
            disabled += 1  # Disabled by the user is not a fault.
            assessed += 1
        elif state.state == "unavailable":
            assessed += 1
            age = now - state.last_changed
            if age >= grace_period:
                unavailable.append({
                    "entity_id": state.entity_id, "name": state.name,
                    "duration_seconds": int(age.total_seconds()),
                    "correlation_key": f"automation:{state.entity_id}",
                })
    return {
        "eligible_count": len(items), "assessed_count": assessed,
        "enabled_count": enabled, "disabled_count": disabled,
        "unavailable_count": len(unavailable),
        "unavailable_automations": unavailable,
    }
