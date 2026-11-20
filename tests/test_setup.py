"""End-to-end setup and unload tests for the integration."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_health_monitor.const import (
    DOMAIN,
    SERVICE_RESET_FRESHNESS_LEARNING,
    SERVICE_SCAN_NOW,
    SERVICE_SET_INTEGRATION_AVAILABILITY_PROFILE,
)


async def test_setup_registers_entities_and_services_then_cleans_up(
    hass: HomeAssistant,
):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_SCAN_NOW)
    assert hass.services.has_service(DOMAIN, SERVICE_RESET_FRESHNESS_LEARNING)
    assert hass.services.has_service(
        DOMAIN, SERVICE_SET_INTEGRATION_AVAILABILITY_PROFILE
    )
    assert hass.states.get("sensor.ha_health_monitor_health_score") is not None
    assert hass.states.get("sensor.ha_health_monitor_active_incidents") is not None
    assert (
        hass.states.get("binary_sensor.ha_health_monitor_system_has_issues")
        is not None
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not hass.services.has_service(DOMAIN, SERVICE_SCAN_NOW)
    assert not hass.services.has_service(DOMAIN, SERVICE_RESET_FRESHNESS_LEARNING)
    assert not hass.services.has_service(
        DOMAIN, SERVICE_SET_INTEGRATION_AVAILABILITY_PROFILE
    )


async def test_integration_activity_profile_service_configures_and_removes_profile(
    hass: HomeAssistant,
):
    """The service validates registry ownership and supports removal."""
    from homeassistant.helpers import entity_registry as er

    integration_entry = MockConfigEntry(domain="washdata", title="Washer")
    integration_entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "sensor",
        "washdata",
        "activity",
        suggested_object_id="washer_activity",
        config_entry=integration_entry,
    )

    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_INTEGRATION_AVAILABILITY_PROFILE,
        {
            "config_entry_id": integration_entry.entry_id,
            "reference_entity": "sensor.washer_activity",
            "inactive_states": "off, idle",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    profile = entry.options["integration_availability_profiles"][
        integration_entry.entry_id
    ]
    assert profile["reference_entity"] == "sensor.washer_activity"
    assert profile["inactive_states"] == ["idle", "off"]

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_INTEGRATION_AVAILABILITY_PROFILE,
        {
            "config_entry_id": integration_entry.entry_id,
            "remove": True,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (
        integration_entry.entry_id
        not in entry.options["integration_availability_profiles"]
    )
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
