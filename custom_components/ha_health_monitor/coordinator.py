"""Coordinator joining monitors, incident lifecycle and explainable score."""

from __future__ import annotations

import logging
from datetime import timedelta
from math import isfinite

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_state_report_event,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AVAILABILITY_PROFILES,\n    CONF_INTEGRATION_AVAILABILITY_PROFILES,
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_FRESHNESS_MULTIPLIER,
    CONF_MONITOR_FRESHNESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_FRESHNESS_MULTIPLIER,
    DEFAULT_MONITOR_FRESHNESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .incident_engine import (
    build_observations,
    correlate_incidents,
    normalize_incident_history,
    reconcile_incidents,
)
from .monitors.automations import collect_automation_health
from .monitors.availability import (
    collect_device_metadata,
    collect_disabled_entities,
    collect_unavailable,
    evaluate_availability_profiles,\n    evaluate_integration_activity_profiles,
)
from .monitors.freshness import FreshnessLearner, collect_adaptive_stale
from .monitors.integrations import collect_integration_health
from .scoring import calculate_health_score

_LOGGER = logging.getLogger(__name__)
AVAILABILITY_GRACE_PERIOD = timedelta(minutes=2)
FRESHNESS_STORAGE_VERSION = 1
INCIDENT_STORAGE_VERSION = 1
FRESHNESS_SAVE_DELAY = 5
INCIDENT_SAVE_DELAY = 5


class HealthMonitorCoordinator(DataUpdateCoordinator[dict]):
    """Collect observations and publish one consistent health snapshot."""

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
        self._freshness_store = Store(
            hass,
            FRESHNESS_STORAGE_VERSION,
            f"{DOMAIN}_{entry.entry_id}_freshness",
        )
        self._incident_store = Store(
            hass,
            INCIDENT_STORAGE_VERSION,
            f"{DOMAIN}_{entry.entry_id}_incidents",
        )
        self.learner = FreshnessLearner()
        self._incident_history: list[dict] = []
        self._unsub_state_listener = None
        self._unsub_state_report_listener = None

    @property
    def configured_freshness_entities(self) -> set[str]:
        """Return selected entities after applying global exclusions."""
        selected = set(self.options.get(CONF_FRESHNESS_ENTITIES, []))
        excluded = set(self.options.get(CONF_EXCLUDED_ENTITIES, []))
        return selected - excluded - self.disabled_entity_ids

    @property
    def disabled_entities(self) -> list[dict]:
        """Return entities disabled in Home Assistant's entity registry."""
        return collect_disabled_entities(er.async_get(self.hass).entities.values())

    @property
    def disabled_entity_ids(self) -> set[str]:
        """Return entity IDs disabled in Home Assistant's entity registry."""
        return {item["entity_id"] for item in self.disabled_entities}

    @property
    def selected_freshness_entities(self) -> set[str]:
        """Return selected entities only while freshness monitoring is enabled."""
        if not self.options.get(CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS):
            return set()
        return self.configured_freshness_entities

    async def async_initialize(self) -> None:
        """Restore persistent state, reconcile selection and subscribe to events."""
        freshness_data = await self._freshness_store.async_load()
        incident_data = await self._incident_store.async_load()
        self.learner = FreshnessLearner.from_storage(freshness_data)
        raw_incidents = (
            incident_data.get("incidents")
            if isinstance(incident_data, dict)
            else None
        )
        self._incident_history = normalize_incident_history(raw_incidents)
        if self._incident_history != raw_incidents:
            await self._incident_store.async_save(
                {"incidents": self._incident_history}
            )

        configured = self.configured_freshness_entities
        selected = self.selected_freshness_entities
        changed = self.learner.retain_entities(configured)
        changed = self.learner.export() != freshness_data or changed
        for entity_id in selected:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in ("unknown", "unavailable"):
                changed = self.learner.seed(entity_id, state.last_reported) or changed
        if changed:
            await self._freshness_store.async_save(self.learner.export())

        if selected:
            self._unsub_state_listener = async_track_state_change_event(
                self.hass, selected, self._async_handle_state_change
            )
            self._unsub_state_report_listener = async_track_state_report_event(
                self.hass, selected, self._async_handle_state_report
            )

    @callback
    def _async_handle_state_change(self, event: Event) -> None:
        """Learn from changed states using last_updated."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self._async_observe_report(
            event.data.get("entity_id"), new_state, new_state.last_updated
        )

    @callback
    def _async_handle_state_report(self, event: Event) -> None:
        """Learn from unchanged state reports using the updated State timestamp."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self._async_observe_report(
            event.data.get("entity_id"), new_state, new_state.last_reported
        )

    @callback
    def _async_observe_report(self, entity_id: str, new_state, reported_at) -> None:
        """Record reports only for selected, available entities."""
        if entity_id not in self.selected_freshness_entities:
            return
        if new_state.state in ("unknown", "unavailable") or reported_at is None:
            return
        if self.learner.observe(entity_id, reported_at):
            self._freshness_store.async_delay_save(
                self.learner.export, FRESHNESS_SAVE_DELAY
            )

    async def async_reset_freshness_learning(
        self, entity_id: str | None = None
    ) -> None:
        """Reset one configured profile or all configured profiles."""
        configured = self.configured_freshness_entities
        if entity_id is not None and entity_id not in configured:
            raise ValueError("Entity is not selected for freshness monitoring")
        targets = {entity_id} if entity_id else configured
        for target in targets:
            self.learner.reset(target)
            state = self.hass.states.get(target)
            if state is not None and state.state not in ("unknown", "unavailable"):
                self.learner.seed(target, state.last_reported)
        await self._freshness_store.async_save(self.learner.export())
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Release listeners and flush persistent state."""
        if self._unsub_state_listener is not None:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        if self._unsub_state_report_listener is not None:
            self._unsub_state_report_listener()
            self._unsub_state_report_listener = None
        await self._freshness_store.async_save(self.learner.export())
        await self._incident_store.async_save({"incidents": self._incident_history})

    async def _async_update_data(self) -> dict:
        """Build one consistent monitoring, incident and scoring snapshot."""
        now = dt_util.utcnow()
        excluded = set(self.options.get(CONF_EXCLUDED_ENTITIES, []))
        disabled_entities = self.disabled_entities
        disabled_ids = {item["entity_id"] for item in disabled_entities}
        excluded |= disabled_ids
        selected = self.selected_freshness_entities
        states = self.hass.states.async_all()
        raw_multiplier = self.options.get(
            CONF_FRESHNESS_MULTIPLIER, DEFAULT_FRESHNESS_MULTIPLIER
        )
        try:
            threshold_multiplier = float(raw_multiplier)
        except (TypeError, ValueError, OverflowError):
            threshold_multiplier = DEFAULT_FRESHNESS_MULTIPLIER
        if not isfinite(threshold_multiplier):
            threshold_multiplier = DEFAULT_FRESHNESS_MULTIPLIER
        threshold_multiplier = min(max(threshold_multiplier, 1.5), 10.0)

        try:
            entity_registry = er.async_get(self.hass)
            device_registry = dr.async_get(self.hass)
            device_metadata = collect_device_metadata(
                entity_registry.entities.values(), device_registry.devices.values()
            )
            availability_profiles = evaluate_availability_profiles(
                states,
                self.options.get(CONF_AVAILABILITY_PROFILES, {}),
                device_metadata,
            )
            integration_activity_profiles = evaluate_integration_activity_profiles(\n                states,\n                self.options.get(CONF_INTEGRATION_AVAILABILITY_PROFILES, {}),\n                entity_registry.entities.values(),\n            )\n            availability_excluded = (\n                excluded\n                | availability_profiles["suppressed_entity_ids"]\n                | integration_activity_profiles["suppressed_entity_ids"]\n            )
            unavailable = collect_unavailable(
                states,
                availability_excluded,
                now,
                AVAILABILITY_GRACE_PERIOD,
                device_metadata,
            )
            stale, profiles = collect_adaptive_stale(
                states,
                selected,
                excluded,
                self.learner,
                now,
                threshold_multiplier,
            )
        except (AttributeError, TypeError, ValueError) as err:
            raise UpdateFailed(
                f"Unable to inspect Home Assistant states: {err}"
            ) from err

        integration_health = collect_integration_health(
            self.hass.config_entries.async_entries()
        )
        automation_health = collect_automation_health(
            states, excluded, now, AVAILABILITY_GRACE_PERIOD
        )
        observations = build_observations(
            unavailable,
            stale,
            integration_health["failed_entries"],
            automation_health["unavailable_automations"],
        )
        self._incident_history = reconcile_incidents(
            observations, self._incident_history, now.isoformat()
        )
        self._incident_store.async_delay_save(
            lambda: {"incidents": self._incident_history}, INCIDENT_SAVE_DELAY
        )
        active_incidents = [
            incident for incident in self._incident_history
            if incident.get("status") == "active"
        ]
        correlation_groups = correlate_incidents(active_incidents)
        eligible_count = sum(
            state.entity_id not in availability_excluded for state in states
        )
        availability_assessed_count = sum(
            state.entity_id not in availability_excluded
            and state.state != "unknown"
            for state in states
        )
        freshness_monitoring_count = sum(
            profile["status"] == "monitoring" for profile in profiles.values()
        )
        freshness_enabled = bool(
            self.options.get(CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS)
        )
        score = calculate_health_score(
            active_incidents,
            availability_eligible_count=eligible_count,
            availability_assessed_count=availability_assessed_count,
            freshness_enabled=freshness_enabled,
            selected_freshness_count=len(selected),
            freshness_monitoring_count=freshness_monitoring_count,
            integration_eligible_count=integration_health["eligible_count"],
            integration_assessed_count=integration_health["assessed_count"],
            automation_eligible_count=automation_health["eligible_count"],
            automation_assessed_count=automation_health["assessed_count"],
        )
        return {
            "last_scan": now,
            "unavailable_entities": unavailable,
            "availability_profiles": availability_profiles["profiles"],\n            "integration_activity_profiles": integration_activity_profiles["profiles"],
            "standby_suppressed_entities": sorted(
                availability_profiles["suppressed_entity_ids"]
            ),
            "disabled_entities": disabled_entities,
            "excluded_entities": sorted(
                self.options.get(CONF_EXCLUDED_ENTITIES, [])
            ),
            "stale_entities": stale,
            "monitored_entity_count": eligible_count,
            "availability_assessed_count": availability_assessed_count,
            "unknown_entity_count": eligible_count - availability_assessed_count,
            "freshness_enabled": freshness_enabled,
            "freshness_threshold_multiplier": threshold_multiplier,
            "freshness_entity_count": len(selected),
            "freshness_learning_count": sum(
                profile["status"] == "learning" for profile in profiles.values()
            ),
            "freshness_monitoring_count": freshness_monitoring_count,
            "freshness_missing_count": sum(
                profile["status"] == "missing" for profile in profiles.values()
            ),
            "freshness_paused_count": sum(
                profile["status"] == "paused" for profile in profiles.values()
            ),
            "freshness_profiles": profiles,
            "availability_grace_seconds": int(
                AVAILABILITY_GRACE_PERIOD.total_seconds()
            ),
            "integration_health": integration_health,
            "automation_health": automation_health,
            "correlation_groups": correlation_groups,
            "active_incidents": active_incidents,
            "incident_history": self._incident_history,
            "health_score": score["score"],
            "health_status": score["status"],
            "health_coverage_percent": score["coverage_percent"],
            "health_score_breakdown": score,
        }

    @callback
    def get_issue_count(self) -> int:
        """Return the number of active incidents."""
        if not self.data:
            return 0
        return len(self.data["active_incidents"])
