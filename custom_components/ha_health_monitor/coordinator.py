"""Coordinator and first monitoring pass."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_FRESHNESS_THRESHOLD,
    CONF_MONITOR_FRESHNESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_FRESHNESS_THRESHOLD,
    DEFAULT_MONITOR_FRESHNESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class HealthMonitorCoordinator(DataUpdateCoordinator[dict]):
    """Collect supported state-based health observations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.options = entry.options
        interval = int(self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
        )

    async def _async_update_data(self) -> dict:
        """Build a point-in-time snapshot from Home Assistant's state machine."""
        now = dt_util.utcnow()
        excluded = set(self.options.get(CONF_EXCLUDED_ENTITIES, []))
        unavailable: list[dict] = []
        stale: list[dict] = []

        monitor_freshness = self.options.get(
            CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS
        )
        freshness_entities = set(self.options.get(CONF_FRESHNESS_ENTITIES, []))
        threshold = int(
            self.options.get(
                CONF_FRESHNESS_THRESHOLD, DEFAULT_FRESHNESS_THRESHOLD
            )
        )
        stale_after = timedelta(minutes=threshold)

        try:
            for state in self.hass.states.async_all():
                entity_id = state.entity_id
                if entity_id in excluded:
                    continue

                if state.state == "unavailable":
                    unavailable.append(
                        {
                            "entity_id": entity_id,
                            "name": state.name,
                            "last_changed": state.last_changed.isoformat(),
                        }
                    )
                    continue

                # Freshness is opt-in and only applies to entities explicitly selected
                # by the user. A global timeout would create false positives for
                # event-driven and battery-powered entities.
                if (
                    monitor_freshness
                    and entity_id in freshness_entities
                    and state.state not in ("unknown", "unavailable")
                ):
                    age = now - state.last_updated
                    if age > stale_after:
                        stale.append(
                            {
                                "entity_id": entity_id,
                                "name": state.name,
                                "last_updated": state.last_updated.isoformat(),
                                "age_seconds": int(age.total_seconds()),
                                "threshold_seconds": int(stale_after.total_seconds()),
                            }
                        )
        except Exception as err:  # Defensive boundary around HA state snapshot.
            raise UpdateFailed(f"Unable to inspect Home Assistant states: {err}") from err

        return {
            "last_scan": now,
            "unavailable_entities": unavailable,
            "stale_entities": stale,
            "monitored_entity_count": len(self.hass.states.async_all()) - len(excluded),
            "freshness_enabled": bool(monitor_freshness),
            "freshness_entity_count": len(freshness_entities),
            "freshness_threshold_minutes": threshold,
        }

    @callback
    def get_issue_count(self) -> int:
        """Return current count of monitored observations."""
        if not self.data:
            return 0
        return len(self.data["unavailable_entities"]) + len(self.data["stale_entities"])
