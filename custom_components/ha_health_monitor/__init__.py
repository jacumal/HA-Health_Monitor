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
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    CONF_AVAILABILITY_PROFILES,
    CONF_EXCLUDED_ENTITIES,
    DOMAIN,
    SERVICE_RESET_FRESHNESS_LEARNING,
    SERVICE_SCAN_NOW,
    SERVICE_SET_ENTITY_EXCLUDED,
    SERVICE_SET_AVAILABILITY_PROFILE,
)
from .coordinator import HealthMonitorCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]
CARD_DIR = Path(__file__).parent / "www"
CARD_URL = "/ha_health_monitor/ha-health-monitor-card.js?v=0.1.8"

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

    async def handle_set_entity_excluded(call: ServiceCall) -> None:
        """Include or exclude one entity from health monitoring."""
        entity_id = call.data["entity_id"]
        excluded = call.data["excluded"]
        options = dict(entry.options)
        excluded_entities = set(options.get(CONF_EXCLUDED_ENTITIES, []))
        if excluded:
            excluded_entities.add(entity_id)
        else:
            excluded_entities.discard(entity_id)
        options[CONF_EXCLUDED_ENTITIES] = sorted(excluded_entities)
        hass.config_entries.async_update_entry(entry, options=options)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_ENTITY_EXCLUDED):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_ENTITY_EXCLUDED,
            handle_set_entity_excluded,
            schema=vol.Schema({
                vol.Required("entity_id"): cv.entity_id,
                vol.Required("excluded"): cv.boolean,
            }),
        )
    async def handle_set_availability_profile(call: ServiceCall) -> None:
        """Create, replace or remove a device availability profile."""
        device_id = call.data["device_id"]
        options = dict(entry.options)
        profiles = dict(options.get(CONF_AVAILABILITY_PROFILES, {}))
        if call.data.get("remove", False):
            profiles.pop(device_id, None)
        else:
            device = dr.async_get(hass).devices.get(device_id)
            registry = er.async_get(hass)
            if device is None:
                raise HomeAssistantError("Unknown Home Assistant device_id")
            reference = call.data["reference_entity"]
            entities = call.data["conditional_entities"]
            inactive = call.data["inactive_states"]
            for entity_id in [reference, *entities]:
                item = registry.async_get(entity_id)
                if item is None or item.device_id != device_id:
                    raise HomeAssistantError(f"{entity_id} is not registered to the selected device")
            if reference in entities:
                raise HomeAssistantError("The reference entity cannot also be conditional")
            if not entities or not inactive:
                raise HomeAssistantError("Select conditional entities and at least one inactive state")
            profiles[device_id] = {"device_name": device.name_by_user or device.name, "reference_entity": reference, "conditional_entities": sorted(set(entities)), "inactive_states": sorted(set(inactive))}
        options[CONF_AVAILABILITY_PROFILES] = profiles
        hass.config_entries.async_update_entry(entry, options=options)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_AVAILABILITY_PROFILE):
        hass.services.async_register(DOMAIN, SERVICE_SET_AVAILABILITY_PROFILE, handle_set_availability_profile, schema=vol.Schema({
            vol.Required("device_id"): cv.string,
            vol.Optional("remove", default=False): cv.boolean,
            vol.Optional("reference_entity"): cv.entity_id,
            vol.Optional("conditional_entities", default=[]): vol.All(cv.ensure_list, [cv.entity_id]),
            vol.Optional("inactive_states", default=[]): vol.All(cv.ensure_list, [cv.string]),
        }))
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
        for service in (
            SERVICE_SCAN_NOW,
            SERVICE_RESET_FRESHNESS_LEARNING,
            SERVICE_SET_ENTITY_EXCLUDED,
            SERVICE_SET_AVAILABILITY_PROFILE,
        ):
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)
    return unloaded
