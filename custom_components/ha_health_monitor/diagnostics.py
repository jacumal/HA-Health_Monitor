"""Diagnostics for HA Health Monitor."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import HealthMonitorConfigEntry

TO_REDACT = {"api_key", "token", "password", "secret"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HealthMonitorConfigEntry
) -> dict:
    """Return redacted, local diagnostic information."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "monitoring": {
            "last_scan": (
                coordinator.data["last_scan"].isoformat()
                if coordinator.data
                else None
            ),
            "unavailable_count": (
                len(coordinator.data["unavailable_entities"])
                if coordinator.data
                else None
            ),
            "stale_count": (
                len(coordinator.data["stale_entities"])
                if coordinator.data
                else None
            ),
        },
    }
