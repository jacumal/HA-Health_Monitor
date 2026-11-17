"""Tests for selected-entity freshness monitoring and adaptive learning."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.ha_health_monitor.monitors.freshness import (
    FreshnessLearner,
    collect_stale,
)


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


def test_learning_waits_for_five_valid_intervals():
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc)

    for minute in range(5):
        learner.observe("sensor.temperature", start + timedelta(minutes=minute * 5))
    assert learner.status("sensor.temperature") == "learning"
    assert learner.expected_interval("sensor.temperature") is None

    learner.observe("sensor.temperature", start + timedelta(minutes=25))
    assert learner.status("sensor.temperature") == "monitoring"
    assert learner.expected_interval("sensor.temperature") == 300
    assert learner.stale_after("sensor.temperature") == timedelta(seconds=900)


def test_adaptation_is_gradual_and_limits_single_outlier():
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc)
    for minute in range(6):
        learner.observe("sensor.temperature", start + timedelta(minutes=minute * 5))

    before = learner.expected_interval("sensor.temperature")
    learner.observe("sensor.temperature", start + timedelta(minutes=25 + 10))
    after = learner.expected_interval("sensor.temperature")

    assert before == 300
    assert 300 < after < 600


def test_reset_can_target_one_entity_or_all_and_storage_round_trips():
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc)
    for entity_id in ("sensor.one", "sensor.two"):
        for minute in range(6):
            learner.observe(entity_id, start + timedelta(minutes=minute * 5))

    restored = FreshnessLearner.from_storage(learner.export())
    assert restored.is_ready("sensor.one")
    restored.reset("sensor.one")
    assert not restored.is_ready("sensor.one")
    assert restored.is_ready("sensor.two")
    restored.reset()
    assert restored.status("sensor.two") == "learning"


def test_naive_and_non_increasing_timestamps_do_not_train():
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc)
    assert learner.observe("sensor.temperature", start)
    assert not learner.observe("sensor.temperature", start.replace(tzinfo=None))
    assert not learner.observe("sensor.temperature", start - timedelta(minutes=1))
    assert learner.expected_interval("sensor.temperature") is None
