"""Coordinator tests for selected freshness event handling."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from custom_components.ha_health_monitor.const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_MONITOR_FRESHNESS,
    DOMAIN,
)
from custom_components.ha_health_monitor.coordinator import HealthMonitorCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry


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


async def test_freshness_event_observer_ignores_unselected_entities(hass):
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
    state = SimpleNamespace(state="20")
    coordinator._async_observe_report(
        "sensor.selected", state, baseline + timedelta(minutes=5)
    )
    coordinator._async_observe_report(
        "sensor.other", state, baseline + timedelta(minutes=10)
    )
    assert coordinator.learner.sample_count("sensor.selected") == 1
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
