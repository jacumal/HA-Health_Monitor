"""Unit tests for integration and automation health monitors."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from homeassistant.config_entries import ConfigEntryState

from custom_components.ha_health_monitor.monitors.automations import collect_automation_health
from custom_components.ha_health_monitor.monitors.integrations import collect_integration_health


def test_integration_setup_errors_are_reported_and_retries_are_informational():
    entries = [
        SimpleNamespace(entry_id="e1", domain="mqtt", title="MQTT", state=ConfigEntryState.SETUP_ERROR),
        SimpleNamespace(entry_id="e2", domain="zha", title="ZHA", state=ConfigEntryState.SETUP_RETRY),
        SimpleNamespace(entry_id="e3", domain="hue", title="Hue", state=ConfigEntryState.LOADED),
    ]
    result = collect_integration_health(entries)
    assert result["eligible_count"] == 3
    assert result["failed_count"] == 1
    assert result["retrying_count"] == 1
    assert result["assessed_count"] == 2


def test_disabled_automation_is_not_an_incident():
    now = datetime.now(UTC)
    states = [
        SimpleNamespace(entity_id="automation.enabled", state="on"),
        SimpleNamespace(entity_id="automation.disabled", state="off"),
    ]
    result = collect_automation_health(states, set(), now, timedelta(minutes=2))
    assert result["enabled_count"] == 1
    assert result["disabled_count"] == 1
    assert result["unavailable_count"] == 0


def test_persistently_unavailable_automation_is_reported():
    now = datetime.now(UTC)
    state = SimpleNamespace(
        entity_id="automation.broken", state="unavailable", name="Broken",
        last_changed=now - timedelta(minutes=10),
    )
    result = collect_automation_health([state], set(), now, timedelta(minutes=2))
    assert result["unavailable_count"] == 1
    assert result["unavailable_automations"][0]["entity_id"] == "automation.broken"
