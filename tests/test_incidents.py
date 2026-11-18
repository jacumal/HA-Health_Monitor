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



def test_persisted_incident_history_discards_corrupt_records_and_normalizes_fields():
    from custom_components.ha_health_monitor.incident_engine import (
        make_issue_id,
        normalize_incident_history,
    )

    valid_id = make_issue_id("freshness.stale", "sensor.temp")
    records = [
        {
            "issue_id": valid_id,
            "rule_id": "freshness.stale",
            "category": "freshness",
            "target": "sensor.temp",
            "severity": "warning",
            "status": "resolved",
            "first_seen": "2026-11-17T10:00:00+00:00",
            "last_seen": "2026-11-17T10:05:00+00:00",
            "resolved_at": "2026-11-17T10:10:00+00:00",
            "occurrence_count": "3",
            "details": "corrupt details",
        },
        {"issue_id": "forged", "rule_id": "freshness.stale"},
        None,
    ]

    result = normalize_incident_history(records)
    assert len(result) == 1
    assert result[0]["occurrence_count"] == 3
    assert result[0]["details"] == {}
    assert result[0]["correlation_key"] == "freshness:sensor.temp"
    assert normalize_incident_history({"not": "a list"}) == []


def test_persisted_incident_history_rejects_invalid_timestamps_and_status():
    from custom_components.ha_health_monitor.incident_engine import (
        make_issue_id,
        normalize_incident_history,
    )

    record = {
        "issue_id": make_issue_id("freshness.stale", "sensor.temp"),
        "rule_id": "freshness.stale",
        "category": "freshness",
        "target": "sensor.temp",
        "severity": "warning",
        "status": "resolved",
        "first_seen": "not-a-date",
        "last_seen": "2026-11-17T10:05:00+00:00",
        "resolved_at": "2026-11-17T10:10:00+00:00",
    }
    assert normalize_incident_history([record]) == []
    record["first_seen"] = "2026-11-17T10:00:00+00:00"
    record["status"] = "unknown"
    assert normalize_incident_history([record]) == []
