"""HA Health Monitor integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_SCAN_NOW,
)
from .coordinator import HealthMonitorCoordinator

_LOGGER = logging.getLogger(__name__)

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
        await coordinator.async_config_entry_first_refresh()
    except (UpdateFailed, OSError) as err:
        raise ConfigEntryNotReady from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.SENSOR, Platform.BINARY_SENSOR]
    )

    async def handle_scan_now(call: ServiceCall) -> None:
        """Run a scan immediately."""
        await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_SCAN_NOW):
        hass.services.async_register(DOMAIN, SERVICE_SCAN_NOW, handle_scan_now)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HealthMonitorConfigEntry
) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR, Platform.BINARY_SENSOR]
    )
    if unloaded and not hass.config_entries.async_entries(DOMAIN):
        if hass.services.has_service(DOMAIN, SERVICE_SCAN_NOW):
            hass.services.async_remove(DOMAIN, SERVICE_SCAN_NOW)
    return unloaded
