"""HA Health Monitor integration."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, SERVICE_RESET_FRESHNESS_LEARNING, SERVICE_SCAN_NOW
from .coordinator import HealthMonitorCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]
CARD_DIR = Path(__file__).parent / "www"
CARD_URL = "/ha_health_monitor/ha-health-monitor-card.js?v=0.1.2"

type HealthMonitorConfigEntry = ConfigEntry[HealthMonitorCoordinator]


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve and register the bundled Lovelace card."""
    card_path = CARD_DIR / "ha-health-monitor-card.js"
    if not card_path.is_file():
        return
    if hass.http is not None:
        try:
            await hass.http.async_register_static_paths(
                [StaticPathConfig("/ha_health_monitor", str(CARD_DIR), False)]
            )
        except RuntimeError:
            # Static path can already exist after an integration reload.
            pass
    else:
        return
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return
    resources = getattr(lovelace, "resources", None)
    if resources is None or not hasattr(resources, "async_create_item"):
        return
    await resources.async_get_info()
    if any(item.get("url") == CARD_URL for item in resources.async_items()):
        return
    await resources.async_create_item({"res_type": "module", "url": CARD_URL})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration domain and bundled Lovelace resource."""
    await _async_register_card(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: HealthMonitorConfigEntry
) -> bool:
    """Set up HA Health Monitor from a config entry."""
    await _async_register_card(hass)
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
        for service in (SERVICE_SCAN_NOW, SERVICE_RESET_FRESHNESS_LEARNING):
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)
    return unloaded
