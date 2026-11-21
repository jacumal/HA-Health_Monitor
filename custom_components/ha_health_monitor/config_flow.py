"""Config flow for HA Health Monitor."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_FRESHNESS_MULTIPLIER,
    CONF_INTEGRATION_AVAILABILITY_PROFILES,
    CONF_MONITOR_FRESHNESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_FRESHNESS_MULTIPLIER,
    DEFAULT_MONITOR_FRESHNESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_FRESHNESS_MULTIPLIER,
    MAX_SCAN_INTERVAL,
    MIN_FRESHNESS_MULTIPLIER,
    MIN_SCAN_INTERVAL,
)


class HAHealthMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Health Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(title="HA Health Monitor", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create an options flow bound to its config entry."""
        return HAHealthMonitorOptionsFlow(config_entry)


class HAHealthMonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, config_entry) -> None:
        """Keep the config entry reference for HA 2024.11 compatibility."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage monitoring options."""
        if user_input is not None:
            options = dict(self._config_entry.options)
            values = dict(user_input)
            config_entry_id = values.pop("activity_profile_config_entry", None)
            reference = values.pop("activity_profile_reference_entity", None)
            conditional = values.pop("activity_profile_conditional_entities", [])
            inactive_raw = values.pop("activity_profile_inactive_states", "off")
            remove = values.pop("activity_profile_remove", False)
            options.update(values)
            if config_entry_id:
                profiles = dict(options.get(CONF_INTEGRATION_AVAILABILITY_PROFILES, {}))
                if remove:
                    profiles.pop(config_entry_id, None)
                else:
                    integration_entry = self.hass.config_entries.async_get_entry(
                        config_entry_id
                    )
                    registry = er.async_get(self.hass)
                    reference_entry = (
                        registry.async_get(reference) if reference else None
                    )
                    inactive = [
                        value.strip()
                        for value in str(inactive_raw or "").split(",")
                        if value.strip()
                    ]
                    if (
                        integration_entry is None
                        or reference_entry is None
                        or reference_entry.config_entry_id != config_entry_id
                        or reference_entry.platform != integration_entry.domain
                        or not conditional
                        or not inactive
                    ):
                        return self.async_abort(reason="invalid_activity_profile")
                    for entity_id in conditional:
                        entity = registry.async_get(entity_id)
                        if (
                            entity is None
                            or entity.config_entry_id != config_entry_id
                            or entity_id == reference
                        ):
                            return self.async_abort(reason="invalid_activity_profile")
                    profiles[config_entry_id] = {
                        "domain": integration_entry.domain,
                        "title": integration_entry.title,
                        "reference_entity": reference,
                        "conditional_entities": sorted(set(conditional)),
                        "inactive_states": sorted(set(inactive)),
                    }
                options[CONF_INTEGRATION_AVAILABILITY_PROFILES] = profiles
            return self.async_create_entry(title="", data=options)

        options = self._config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
                vol.Optional(
                    CONF_EXCLUDED_ENTITIES,
                    default=options.get(CONF_EXCLUDED_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(
                    CONF_MONITOR_FRESHNESS,
                    default=options.get(
                        CONF_MONITOR_FRESHNESS, DEFAULT_MONITOR_FRESHNESS
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_FRESHNESS_ENTITIES,
                    default=options.get(CONF_FRESHNESS_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["sensor", "binary_sensor"], multiple=True
                    )
                ),
                vol.Optional(
                    CONF_FRESHNESS_MULTIPLIER,
                    default=options.get(
                        CONF_FRESHNESS_MULTIPLIER, DEFAULT_FRESHNESS_MULTIPLIER
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_FRESHNESS_MULTIPLIER,
                        max=MAX_FRESHNESS_MULTIPLIER,
                        step=0.5,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("activity_profile_config_entry"): (
                    selector.ConfigEntrySelector()
                ),
                vol.Optional("activity_profile_reference_entity"): (
                    selector.EntitySelector()
                ),
                vol.Optional("activity_profile_conditional_entities"): (
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(multiple=True)
                    )
                ),
                vol.Optional("activity_profile_inactive_states", default="off"): (
                    selector.TextSelector()
                ),
                vol.Optional("activity_profile_remove", default=False): (
                    selector.BooleanSelector()
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
