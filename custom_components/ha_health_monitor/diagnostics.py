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
    data = coordinator.data or {}
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "monitoring": {
            "last_scan": (
                data["last_scan"].isoformat() if data.get("last_scan") else None
            ),
            "unavailable_count": len(data.get("unavailable_entities", [])),
            "stale_count": len(data.get("stale_entities", [])),
            "active_incident_count": len(data.get("active_incidents", [])),
            "health_score": data.get("health_score"),
            "health_status": data.get("health_status"),
            "coverage_percent": data.get("health_coverage_percent"),
            "freshness_enabled": data.get("freshness_enabled", False),
            "freshness_profile_count": len(data.get("freshness_profiles", {})),
        },
    }
