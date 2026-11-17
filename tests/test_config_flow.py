"""Tests for the HA Health Monitor config flow."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_health_monitor.const import DOMAIN


async def test_user_config_flow_creates_entry(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HA Health Monitor"


async def test_options_flow_is_bound_to_config_entry(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    entry = result["result"]
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["type"] is FlowResultType.FORM
