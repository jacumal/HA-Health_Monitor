"""Tests for the HA Health Monitor config flow."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_health_monitor.const import (
    CONF_INTEGRATION_AVAILABILITY_PROFILES,
    DOMAIN,
)


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


async def test_selecting_one_of_multiple_activity_profiles_prefills_edit_form(hass):
    washer = MockConfigEntry(domain="washdata", title="Washer")
    washer.add_to_hass(hass)
    roomba = MockConfigEntry(domain="roomba_plus", title="Roomba")
    roomba.add_to_hass(hass)

    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", "washdata", "activity",
        suggested_object_id="washer_activity", config_entry=washer,
    )
    registry.async_get_or_create(
        "button", "washdata", "resume",
        suggested_object_id="washer_resume", config_entry=washer,
    )
    registry.async_get_or_create(
        "sensor", "roomba_plus", "phase",
        suggested_object_id="roomba_phase", config_entry=roomba,
    )
    registry.async_get_or_create(
        "button", "roomba_plus", "start",
        suggested_object_id="roomba_start", config_entry=roomba,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_INTEGRATION_AVAILABILITY_PROFILES: {
                washer.entry_id: {
                    "domain": "washdata",
                    "title": "Washer",
                    "reference_entity": "sensor.washer_activity",
                    "conditional_entities": ["button.washer_resume"],
                    "inactive_states": ["off"],
                },
                roomba.entry_id: {
                    "domain": "roomba_plus",
                    "title": "Roomba",
                    "reference_entity": "sensor.roomba_phase",
                    "conditional_entities": ["button.roomba_start"],
                    "inactive_states": ["idle"],
                },
            }
        },
    )
    entry.add_to_hass(hass)

    flow = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={"activity_profile_config_entry": washer.entry_id},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            "activity_profile_config_entry": washer.entry_id,
            "activity_profile_reference_entity": "sensor.washer_activity",
            "activity_profile_conditional_entities": ["button.washer_resume"],
            "activity_profile_inactive_states": "off",
            "activity_profile_remove": False,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_INTEGRATION_AVAILABILITY_PROFILES][washer.entry_id][
        "conditional_entities"
    ] == ["button.washer_resume"]
