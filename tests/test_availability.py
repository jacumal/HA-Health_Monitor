"""Tests for the availability monitor."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from custom_components.ha_health_monitor.monitors.availability import (
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
