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
