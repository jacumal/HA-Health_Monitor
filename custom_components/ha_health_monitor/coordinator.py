"""Coordinator and event-driven monitoring."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_MONITOR_FRESHNESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_MONITOR_FRESHNESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .monitors.availability import collect_unavailable
from .monitors.freshness import FreshnessLearner, collect_adaptive_stale

_LOGGER = logging.getLogger(__name__)
AVAILABILITY_GRACE_PERIOD = timedelta(minutes=2)
FRESHNESS_STORAGE_VERSION = 1
FRESHNESS_SAVE_DELAY = 5


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
        self._store = Store(
            hass, FRESHNESS_STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}_freshness"
        )
        self.learner = FreshnessLearner()
        self._unsub_state_listener = None

    @property
    def selected_freshness_entities(self) -> set[str]:
        """Return selected, non-excluded entities while freshness is enabled."""
        if not self.options.get(CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS):
            return set()
        selected = set(self.options.get(CONF_FRESHNESS_ENTITIES, []))
        excluded = set(self.options.get(CONF_EXCLUDED_ENTITIES, []))
        return selected - excluded

    async def async_initialize(self) -> None:
        """Restore profiles, reconcile selection and subscribe to selected entities."""
        stored = await self._store.async_load()
        self.learner = FreshnessLearner.from_storage(stored)
        selected = self.selected_freshness_entities
        enabled = self.options.get(CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS)
        changed = self.learner.retain_entities(selected) if enabled else False

        # Seed new profiles without counting startup as an update interval.
        for entity_id in selected:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in ("unknown", "unavailable"):
                changed = self.learner.seed(entity_id, state.last_reported) or changed
        if changed:
            await self._store.async_save(self.learner.export())

        if selected:
            self._unsub_state_listener = async_track_state_change_event(
                self.hass, selected, self._async_handle_state_change
            )

    @callback
    def _async_handle_state_change(self, event: Event) -> None:
        """Learn only from real reports for explicitly selected entities."""
        entity_id = event.data.get("entity_id")
        if entity_id not in self.selected_freshness_entities:
            return
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return
        if self.learner.observe(entity_id, new_state.last_reported):
            self._store.async_delay_save(self.learner.export, FRESHNESS_SAVE_DELAY)

    async def async_reset_freshness_learning(
        self, entity_id: str | None = None
    ) -> None:
        """Reset one selected profile or all selected profiles."""
        selected = self.selected_freshness_entities
        if entity_id is not None and entity_id not in selected:
            raise ValueError("Entity is not selected for freshness monitoring")
        targets = {entity_id} if entity_id else selected
        for target in targets:
            self.learner.reset(target)
            state = self.hass.states.get(target)
            if state is not None and state.state not in ("unknown", "unavailable"):
                self.learner.seed(target, state.last_reported)
        await self._store.async_save(self.learner.export())
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Release listeners and flush the latest learned profiles."""
        if self._unsub_state_listener is not None:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        await self._store.async_save(self.learner.export())

    async def _async_update_data(self) -> dict:
        """Build a point-in-time snapshot from Home Assistant state."""
        now = dt_util.utcnow()
        excluded = set(self.options.get(CONF_EXCLUDED_ENTITIES, []))
        selected = self.selected_freshness_entities
        states = self.hass.states.async_all()
        try:
            unavailable = collect_unavailable(
                states, excluded, now, AVAILABILITY_GRACE_PERIOD
            )
            stale, profiles = collect_adaptive_stale(
                states, selected, excluded, self.learner, now
            )
        except (AttributeError, TypeError, ValueError) as err:
            raise UpdateFailed(
                f"Unable to inspect Home Assistant states: {err}"
            ) from err
        return {
            "last_scan": now,
            "unavailable_entities": unavailable,
            "stale_entities": stale,
            "monitored_entity_count": sum(
                state.entity_id not in excluded for state in states
            ),
            "freshness_enabled": bool(
                self.options.get(CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS)
            ),
            "freshness_entity_count": len(selected),
            "freshness_learning_count": sum(
                profile["status"] == "learning" for profile in profiles.values()
            ),
            "freshness_monitoring_count": sum(
                profile["status"] == "monitoring" for profile in profiles.values()
            ),
            "freshness_profiles": profiles,
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
