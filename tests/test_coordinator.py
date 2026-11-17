"""Coordinator tests for selected freshness event handling."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from homeassistant.core import Event

from custom_components.ha_health_monitor.const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_MONITOR_FRESHNESS,
    DOMAIN,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
