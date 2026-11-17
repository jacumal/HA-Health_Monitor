"""Tests for deterministic incident reconciliation."""

from custom_components.ha_health_monitor.incident_engine import (
    build_observations,
    reconcile_incidents,
)


def test_same_entity_finding_has_stable_issue_id():
    first = build_observations([], [{"entity_id": "sensor.temp"}])[0]
    second = build_observations([], [{"entity_id": "sensor.temp"}])[0]
    assert first["issue_id"] == second["issue_id"]
    assert first["rule_id"] == "freshness.stale"


def test_repeated_scan_does_not_duplicate_or_increment_occurrence():
    observation = build_observations(
        [], [{"entity_id": "sensor.temp", "age_seconds": 600}]
    )
    first = reconcile_incidents(observation, [], "2026-11-17T10:00:00+00:00")
    second = reconcile_incidents(
        observation, first, "2026-11-17T10:05:00+00:00"
    )
    assert len(second) == 1
    assert second[0]["occurrence_count"] == 1
    assert second[0]["first_seen"] == "2026-11-17T10:00:00+00:00"
    assert second[0]["last_seen"] == "2026-11-17T10:05:00+00:00"


def test_disappeared_finding_moves_to_resolved_history():
    observation = build_observations(
        [], [{"entity_id": "sensor.temp", "age_seconds": 600}]
    )
    active = reconcile_incidents(observation, [], "2026-11-17T10:00:00+00:00")
    resolved = reconcile_incidents([], active, "2026-11-17T10:10:00+00:00")
    assert resolved[0]["status"] == "resolved"
    assert resolved[0]["resolved_at"] == "2026-11-17T10:10:00+00:00"


def test_resolved_finding_reappearing_increments_occurrence():
    observation = build_observations(
        [], [{"entity_id": "sensor.temp", "age_seconds": 600}]
    )
    active = reconcile_incidents(observation, [], "2026-11-17T10:00:00+00:00")
    resolved = reconcile_incidents([], active, "2026-11-17T10:10:00+00:00")
    active_again = reconcile_incidents(
        observation, resolved, "2026-11-17T10:20:00+00:00"
    )
    assert active_again[0]["occurrence_count"] == 2
    assert active_again[0]["first_seen"] == "2026-11-17T10:20:00+00:00"
