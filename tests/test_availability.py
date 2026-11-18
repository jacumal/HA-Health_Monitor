"""Tests for the availability monitor."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from custom_components.ha_health_monitor.monitors.availability import (
    collect_device_metadata,
    collect_disabled_entities,
    collect_unavailable,
)


def test_unavailable_entities_are_reported_after_grace_period():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    state = SimpleNamespace(
        entity_id="sensor.room_temperature",
        state="unavailable",
        name="Room temperature",
        last_changed=now - timedelta(minutes=5),
    )
    result = collect_unavailable([state], set(), now, timedelta(minutes=2))
    assert len(result) == 1
    assert result[0]["entity_id"] == "sensor.room_temperature"
    assert result[0]["duration_seconds"] == 300


def test_recent_unavailable_state_is_suppressed_during_grace_period():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    state = SimpleNamespace(
        entity_id="sensor.room_temperature",
        state="unavailable",
        name="Room temperature",
        last_changed=now - timedelta(seconds=30),
    )
    assert collect_unavailable([state], set(), now, timedelta(minutes=2)) == []


def test_unknown_and_excluded_entities_are_not_unavailable_issues():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    states = [
        SimpleNamespace(
            entity_id="sensor.unknown",
            state="unknown",
            name="Unknown",
            last_changed=now - timedelta(hours=1),
        ),
        SimpleNamespace(
            entity_id="sensor.excluded",
            state="unavailable",
            name="Excluded",
            last_changed=now - timedelta(hours=1),
        ),
    ]
    assert collect_unavailable(
        states, {"sensor.excluded"}, now, timedelta(minutes=2)
    ) == []


def test_disabled_entities_are_listed_with_registry_metadata():
    entries = [
        SimpleNamespace(
            entity_id="sensor.iphone_current_pace",
            name=None,
            original_name="Current Pace",
            platform="mobile_app",
            disabled_by=SimpleNamespace(value="user"),
            entity_category=None,
        ),
        SimpleNamespace(
            entity_id="sensor.active",
            name="Active",
            original_name=None,
            platform="mqtt",
            disabled_by=None,
            entity_category=None,
        ),
    ]
    result = collect_disabled_entities(entries)
    assert len(result) == 1
    assert result[0] == {
        "entity_id": "sensor.iphone_current_pace",
        "name": "Current Pace",
        "platform": "mobile_app",
        "disabled_by": "user",
        "entity_category": None,
    }



def test_device_metadata_links_entities_to_registered_devices():
    device = SimpleNamespace(
        id="device-1",
        name="Washer",
        name_by_user=None,
        manufacturer="Example",
        model="W100",
    )
    entities = [
        SimpleNamespace(
            entity_id="sensor.washer_power",
            device_id="device-1",
            platform="washdata",
        ),
        SimpleNamespace(
            entity_id="sensor.unrelated",
            device_id=None,
            platform="mqtt",
        ),
        SimpleNamespace(
            entity_id="sensor.orphan",
            device_id="missing-device",
            platform="test",
        ),
    ]

    metadata = collect_device_metadata(entities, [device])

    assert metadata == {
        "sensor.washer_power": {
            "device_id": "device-1",
            "device_name": "Washer",
            "manufacturer": "Example",
            "model": "W100",
            "platform": "washdata",
        }
    }


def test_unavailable_finding_includes_device_context_when_known():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    state = SimpleNamespace(
        entity_id="sensor.washer_power",
        state="unavailable",
        name="Washer power",
        last_changed=now - timedelta(minutes=5),
    )
    metadata = {
        "sensor.washer_power": {
            "device_id": "device-1",
            "device_name": "Washer",
            "manufacturer": "Example",
            "model": "W100",
            "platform": "washdata",
        }
    }

    result = collect_unavailable(
        [state], set(), now, timedelta(minutes=2), metadata
    )

    assert result[0]["device_name"] == "Washer"
    assert result[0]["manufacturer"] == "Example"
    assert result[0]["platform"] == "washdata"
