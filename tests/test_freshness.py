"""Tests for opt-in freshness monitoring."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.ha_health_monitor.monitors.freshness import collect_stale


def make_state(entity_id, state, last_reported, name="Test entity"):
    return SimpleNamespace(
        entity_id=entity_id,
        state=state,
        last_reported=last_reported,
        name=name,
    )


def test_selected_entity_is_stale_after_threshold():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    state = make_state(
        "sensor.office_temperature",
        "21.5",
        now - timedelta(minutes=90),
        "Office temperature",
    )

    result = collect_stale(
        [state],
        {"sensor.office_temperature"},
        set(),
        now,
        timedelta(minutes=60),
    )

    assert len(result) == 1
    assert result[0]["age_seconds"] == 5400


def test_fresh_unselected_unknown_and_excluded_entities_are_ignored():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    states = [
        make_state("sensor.fresh", "21", now - timedelta(minutes=5)),
        make_state("sensor.unknown", "unknown", now - timedelta(hours=4)),
        make_state("sensor.excluded", "21", now - timedelta(hours=4)),
    ]

    result = collect_stale(
        states,
        {"sensor.fresh", "sensor.unknown", "sensor.excluded"},
        {"sensor.excluded"},
        now,
        timedelta(minutes=60),
    )

    assert result == []
