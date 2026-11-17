"""HA Health Monitor integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, SERVICE_RESET_FRESHNESS_LEARNING, SERVICE_SCAN_NOW
from .coordinator import HealthMonitorCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type HealthMonitorConfigEntry = ConfigEntry[HealthMonitorCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration domain."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: HealthMonitorConfigEntry
) -> bool:
    """Set up HA Health Monitor from a config entry."""
    coordinator = HealthMonitorCoordinator(hass, entry)
    try:
        await coordinator.async_initialize()
        await coordinator.async_config_entry_first_refresh()
    except (UpdateFailed, OSError) as err:
        await coordinator.async_shutdown()
        raise ConfigEntryNotReady from err

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_scan_now(call: ServiceCall) -> None:
        """Run an immediate scan."""
        await coordinator.async_request_refresh()

    async def handle_reset_freshness(call: ServiceCall) -> None:
        """Reset cadence profiles explicitly requested by the user."""
        entity_id = call.data.get("entity_id")
        try:
            await coordinator.async_reset_freshness_learning(entity_id)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    if not hass.services.has_service(DOMAIN, SERVICE_SCAN_NOW):
        hass.services.async_register(DOMAIN, SERVICE_SCAN_NOW, handle_scan_now)
    if not hass.services.has_service(DOMAIN, SERVICE_RESET_FRESHNESS_LEARNING):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET_FRESHNESS_LEARNING,
            handle_reset_freshness,
            schema=vol.Schema({vol.Optional("entity_id"): cv.entity_id}),
        )
    return True


async def async_reload_entry(
    hass: HomeAssistant, entry: HealthMonitorConfigEntry
) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: HealthMonitorConfigEntry
) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
        if not hass.config_entries.async_entries(DOMAIN):
            for service in (SERVICE_SCAN_NOW, SERVICE_RESET_FRESHNESS_LEARNING):
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)
    return unloaded
