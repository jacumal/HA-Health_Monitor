"""Coordinator and first monitoring pass."""

from __future__ import annotations

from datetime import timedelta
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
from .monitors.availability import collect_unavailable
from .monitors.freshness import collect_stale

_LOGGER = logging.getLogger(__name__)
AVAILABILITY_GRACE_PERIOD = timedelta(minutes=2)


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
        monitor_freshness = self.options.get(
            CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS
        )
        freshness_entities = set(self.options.get(CONF_FRESHNESS_ENTITIES, []))
        threshold = int(
            self.options.get(
                CONF_FRESHNESS_THRESHOLD, DEFAULT_FRESHNESS_THRESHOLD
            )
        )
        states = self.hass.states.async_all()

        try:
            unavailable = collect_unavailable(
                states, excluded, now, AVAILABILITY_GRACE_PERIOD
            )
            stale = (
                collect_stale(
                    states,
                    freshness_entities,
                    excluded,
                    now,
                    timedelta(minutes=threshold),
                )
                if monitor_freshness
                else []
            )
        except (AttributeError, TypeError, ValueError) as err:
            raise UpdateFailed(f"Unable to inspect Home Assistant states: {err}") from err

        return {
            "last_scan": now,
            "unavailable_entities": unavailable,
            "stale_entities": stale,
            "monitored_entity_count": sum(
                state.entity_id not in excluded for state in states
            ),
            "freshness_enabled": bool(monitor_freshness),
            "freshness_entity_count": len(freshness_entities),
            "freshness_threshold_minutes": threshold,
            "availability_grace_seconds": int(
                AVAILABILITY_GRACE_PERIOD.total_seconds()
            ),
        }

    @callback
    def get_issue_count(self) -> int:
        """Return current count of monitored observations."""
        if not self.data:
            return 0
        return len(self.data["unavailable_entities"]) + len(self.data["stale_entities"])
