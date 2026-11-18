"""Coordinator tests for selected freshness event handling."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from homeassistant.core import Event
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_health_monitor.const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_MONITOR_FRESHNESS,
    DOMAIN,
)
from custom_components.ha_health_monitor.coordinator import HealthMonitorCoordinator


async def test_freshness_selection_respects_exclusions(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_MONITOR_FRESHNESS: True,
            CONF_FRESHNESS_ENTITIES: ["sensor.one", "sensor.two"],
            CONF_EXCLUDED_ENTITIES: ["sensor.two"],
        },
    )
    coordinator = HealthMonitorCoordinator(hass, entry)
    assert coordinator.configured_freshness_entities == {"sensor.one"}
    assert coordinator.selected_freshness_entities == {"sensor.one"}


async def test_changed_and_unchanged_reports_train_selected_entities(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_MONITOR_FRESHNESS: True,
            CONF_FRESHNESS_ENTITIES: ["sensor.selected"],
        },
    )
    hass.states.async_set("sensor.selected", "20")
    coordinator = HealthMonitorCoordinator(hass, entry)
    await coordinator.async_initialize()
    baseline = hass.states.get("sensor.selected").last_reported

    unchanged_state = SimpleNamespace(
        state="20", last_reported=baseline + timedelta(minutes=5)
    )
    coordinator._async_handle_state_report(
        Event(
            "state_reported",
            {
                "entity_id": "sensor.selected",
                "new_state": unchanged_state,
                "old_last_reported": baseline,
            },
        )
    )
    changed_state = SimpleNamespace(
        state="21", last_updated=baseline + timedelta(minutes=10)
    )
    coordinator._async_handle_state_change(
        Event(
            "state_changed",
            {"entity_id": "sensor.selected", "new_state": changed_state},
        )
    )
    coordinator._async_observe_report(
        "sensor.other", changed_state, baseline + timedelta(minutes=15)
    )
    assert coordinator.learner.sample_count("sensor.selected") == 2
    assert not coordinator.learner.has_profile("sensor.other")
    await coordinator.async_shutdown()


async def test_disabling_freshness_preserves_configured_profile_for_reenable(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_MONITOR_FRESHNESS: False,
            CONF_FRESHNESS_ENTITIES: ["sensor.selected"],
        },
    )
    coordinator = HealthMonitorCoordinator(hass, entry)
    coordinator.learner.seed("sensor.selected", datetime.now(UTC))
    await coordinator._freshness_store.async_save(coordinator.learner.export())
    await coordinator.async_initialize()
    assert coordinator.selected_freshness_entities == set()
    assert coordinator.learner.has_profile("sensor.selected")
    await coordinator.async_shutdown()



async def test_initialize_sanitizes_incidents_and_prunes_unselected_profiles(hass):
    from custom_components.ha_health_monitor.incident_engine import (
        build_observations,
        reconcile_incidents,
    )
    from custom_components.ha_health_monitor.monitors.freshness import FreshnessLearner

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_MONITOR_FRESHNESS: True,
            CONF_FRESHNESS_ENTITIES: ["sensor.selected"],
        },
    )
    hass.states.async_set("sensor.selected", "20")
    coordinator = HealthMonitorCoordinator(hass, entry)

    learner = FreshnessLearner()
    baseline = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    learner.seed("sensor.selected", baseline)
    learner.seed("sensor.removed", baseline)
    await coordinator._freshness_store.async_save(learner.export())

    observations = build_observations(
        [], [{"entity_id": "sensor.stale", "age_seconds": 600}]
    )
    valid_history = reconcile_incidents(
        observations, [], "2026-11-17T10:00:00+00:00"
    )
    await coordinator._incident_store.async_save(
        {"incidents": [*valid_history, {"issue_id": "corrupt"}]}
    )

    await coordinator.async_initialize()

    assert coordinator.learner.has_profile("sensor.selected")
    assert not coordinator.learner.has_profile("sensor.removed")
    assert len(coordinator._incident_history) == 1
    assert coordinator._unsub_state_listener is not None
    assert coordinator._unsub_state_report_listener is not None

    stored_incidents = await coordinator._incident_store.async_load()
    assert stored_incidents["incidents"] == coordinator._incident_history

    await coordinator.async_shutdown()

    assert coordinator._unsub_state_listener is None
    assert coordinator._unsub_state_report_listener is None
    stored_freshness = await coordinator._freshness_store.async_load()
    assert set(stored_freshness["entities"]) == {"sensor.selected"}
    stored_incidents = await coordinator._incident_store.async_load()
    assert stored_incidents["incidents"] == coordinator._incident_history


async def test_shutdown_flushes_freshness_observations_to_storage(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_MONITOR_FRESHNESS: True,
            CONF_FRESHNESS_ENTITIES: ["sensor.selected"],
        },
    )
    hass.states.async_set("sensor.selected", "20")
    coordinator = HealthMonitorCoordinator(hass, entry)
    await coordinator.async_initialize()
    baseline = hass.states.get("sensor.selected").last_reported
    next_report = baseline + timedelta(minutes=5)
    reported_state = SimpleNamespace(state="20", last_reported=next_report)

    coordinator._async_observe_report(
        "sensor.selected", reported_state, next_report
    )
    assert coordinator.learner.sample_count("sensor.selected") == 1

    await coordinator.async_shutdown()

    stored = await coordinator._freshness_store.async_load()
    from custom_components.ha_health_monitor.monitors.freshness import FreshnessLearner

    restored = FreshnessLearner.from_storage(stored)
    assert restored.sample_count("sensor.selected") == 1
    assert restored.export()["entities"]["sensor.selected"]["last_reported"] == (
        next_report.isoformat()
    )


async def test_disabled_entities_are_excluded_from_freshness_selection(hass):
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor",
        "mobile_app",
        "disabled_unique",
        suggested_object_id="disabled_sensor",
        disabled_by=RegistryEntryDisabler.USER,
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_MONITOR_FRESHNESS: True,
            CONF_FRESHNESS_ENTITIES: ["sensor.disabled_sensor", "sensor.enabled_sensor"],
        },
    )
    coordinator = HealthMonitorCoordinator(hass, entry)
    assert coordinator.disabled_entity_ids == {"sensor.disabled_sensor"}
    assert coordinator.configured_freshness_entities == {"sensor.enabled_sensor"}
