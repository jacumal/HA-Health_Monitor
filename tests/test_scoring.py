"""Tests for explainable score and coverage."""

from custom_components.ha_health_monitor.scoring import calculate_health_score


def test_unimplemented_categories_reduce_coverage_not_score_silently():
    result = calculate_health_score(
        [],
        availability_eligible_count=20,
        availability_assessed_count=20,
        freshness_enabled=True,
        selected_freshness_count=10,
        freshness_monitoring_count=10,
    )
    assert result["score"] == 100
    assert result["coverage_percent"] == 55
    assert result["status"] == "partial"
    assert "integrations" in result["unassessed_categories"]
    assert "automations" in result["unassessed_categories"]


def test_unknown_entities_reduce_availability_coverage():
    result = calculate_health_score(
        [],
        availability_eligible_count=10,
        availability_assessed_count=8,
        freshness_enabled=False,
        selected_freshness_count=0,
        freshness_monitoring_count=0,
    )
    assert result["coverage_percent"] == 24
    assert result["categories"]["availability"]["assessment"] == "partial"


def test_learning_entities_reduce_freshness_coverage_until_baseline_ready():
    result = calculate_health_score(
        [],
        availability_eligible_count=10,
        availability_assessed_count=10,
        freshness_enabled=True,
        selected_freshness_count=10,
        freshness_monitoring_count=4,
    )
    assert result["coverage_percent"] == 40
    assert result["categories"]["freshness"]["assessment"] == "partial"


def test_active_issues_produce_traceable_deductions_once():
    incidents = [
        {
            "issue_id": "issue_avail_1",
            "category": "availability",
            "entity_id": "sensor.a",
            "severity": "error",
        },
        {
            "issue_id": "issue_stale_1",
            "category": "freshness",
            "entity_id": "sensor.b",
            "severity": "warning",
        },
    ]
    result = calculate_health_score(
        incidents,
        availability_eligible_count=10,
        availability_assessed_count=10,
        freshness_enabled=True,
        selected_freshness_count=5,
        freshness_monitoring_count=5,
    )
    assert result["score"] < 100
    assert {item["issue_id"] for item in result["deductions"]} == {
        "issue_avail_1",
        "issue_stale_1",
    }
