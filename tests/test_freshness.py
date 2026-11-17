"""Tests for selected-entity freshness monitoring and adaptive learning."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from custom_components.ha_health_monitor.monitors.freshness import (
    FreshnessLearner,
    collect_adaptive_stale,
)


def make_state(entity_id, state, last_reported, name="Test entity"):
    return SimpleNamespace(
        entity_id=entity_id,
        state=state,
        last_reported=last_reported,
        name=name,
    )


def trained_learner(entity_id="sensor.temperature"):
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    learner.seed(entity_id, start)
    for minute in range(5, 31, 5):
        learner.observe(entity_id, start + timedelta(minutes=minute))
    return learner, start


def test_five_valid_intervals_are_required():
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    learner.seed("sensor.temperature", start)
    for minute in range(5, 26, 5):
        learner.observe("sensor.temperature", start + timedelta(minutes=minute))
    assert learner.status("sensor.temperature") == "learning"
    assert learner.expected_interval("sensor.temperature") is None

    learner.observe("sensor.temperature", start + timedelta(minutes=30))
    assert learner.status("sensor.temperature") == "monitoring"
    assert learner.expected_interval("sensor.temperature") == 300
    assert learner.stale_after("sensor.temperature") == timedelta(seconds=900)


def test_adaptation_is_gradual_and_limits_single_outlier():
    learner, start = trained_learner()
    before = learner.expected_interval("sensor.temperature")
    learner.observe("sensor.temperature", start + timedelta(minutes=40))
    after = learner.expected_interval("sensor.temperature")
    assert before == 300
    assert 300 < after < 600


def test_reset_can_target_one_entity_or_all_and_storage_round_trips():
    learner, start = trained_learner("sensor.one")
    learner.seed("sensor.two", start)
    for minute in range(5, 31, 5):
        learner.observe("sensor.two", start + timedelta(minutes=minute))
    restored = FreshnessLearner.from_storage(learner.export())
    assert restored.is_ready("sensor.one")
    restored.reset("sensor.one")
    assert not restored.is_ready("sensor.one")
    assert restored.is_ready("sensor.two")
    restored.reset()
    assert restored.status("sensor.two") == "learning"


def test_invalid_timestamps_do_not_train():
    learner = FreshnessLearner()
    start = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    learner.seed("sensor.temperature", start)
    assert not learner.observe("sensor.temperature", start.replace(tzinfo=None))
    assert not learner.observe("sensor.temperature", start - timedelta(minutes=1))
    assert learner.expected_interval("sensor.temperature") is None


def test_long_outage_resets_baseline_without_polluting_cadence():
    learner, start = trained_learner()
    learner.observe("sensor.temperature", start + timedelta(days=40))
    assert learner.expected_interval("sensor.temperature") == 300
    assert learner.export()["entities"]["sensor.temperature"]["last_reported"] == (
        start + timedelta(days=40)
    ).isoformat()


def test_learning_entities_are_not_flagged_stale():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    state = make_state("sensor.temperature", "21", now - timedelta(hours=3))
    learner = FreshnessLearner()
    learner.seed("sensor.temperature", now - timedelta(hours=4))
    stale, profiles = collect_adaptive_stale(
        [state], {"sensor.temperature"}, set(), learner, now
    )
    assert stale == []
    assert profiles["sensor.temperature"]["status"] == "learning"


def test_only_selected_and_trained_entities_can_be_stale():
    now = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    learner, _ = trained_learner()
    states = [
        make_state("sensor.temperature", "21", now - timedelta(minutes=20)),
        make_state("sensor.not_selected", "21", now - timedelta(hours=5)),
    ]
    stale, profiles = collect_adaptive_stale(
        states, {"sensor.temperature"}, set(), learner, now
    )
    assert [item["entity_id"] for item in stale] == ["sensor.temperature"]
    assert profiles["sensor.temperature"]["status"] == "monitoring"


def test_removed_entities_are_pruned_but_retained_entities_survive():
    learner, _ = trained_learner("sensor.keep")
    learner.seed(
        "sensor.remove", datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    )
    assert learner.retain_entities({"sensor.keep"})
    assert learner.has_profile("sensor.keep")
    assert not learner.has_profile("sensor.remove")
