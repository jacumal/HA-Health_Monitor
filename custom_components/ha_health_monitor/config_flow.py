"""Config flow for HA Health Monitor."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_FRESHNESS_ENTITIES,
    CONF_MONITOR_FRESHNESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_MONITOR_FRESHNESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
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
            return self.async_create_entry(title="", data=user_input)

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
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
