"""Tests for consolidated weighted score and monitor coverage."""
from custom_components.ha_health_monitor.scoring import calculate_health_score


def complete(**overrides):
    values = dict(
        availability_eligible_count=10, availability_assessed_count=10,
        freshness_enabled=False, selected_freshness_count=0,
        freshness_monitoring_count=0, integration_eligible_count=2,
        integration_assessed_count=2, automation_eligible_count=4,
        automation_assessed_count=4,
    )
    values.update(overrides)
    return calculate_health_score([], **values)


def test_all_monitor_domains_assessed_have_full_coverage():
    result = complete()
    assert result["score"] == 100
    assert result["coverage_percent"] == 100
    assert result["status"] == "healthy"


def test_partial_integration_coverage_is_visible():
    result = complete(integration_assessed_count=1)
    assert result["coverage_percent"] == 87.5
    assert result["status"] == "partial"
    assert result["categories"]["integrations"]["assessment"] == "partial"


def test_freshness_learning_reduces_coverage():
    result = complete(
        freshness_enabled=True, selected_freshness_count=10,
        freshness_monitoring_count=5,
    )
    assert result["coverage_percent"] == 90
    assert result["categories"]["freshness"]["assessment"] == "partial"


def test_incident_deductions_are_traceable_and_capped():
    incidents = [
        {"issue_id": f"int_{i}", "category": "integrations",
         "rule_id": "integration.setup_failed", "severity": "error",
         "target": f"entry_{i}"}
        for i in range(5)
    ]
    result = calculate_health_score(
        incidents, availability_eligible_count=10, availability_assessed_count=10,
        freshness_enabled=False, selected_freshness_count=0,
        freshness_monitoring_count=0, integration_eligible_count=5,
        integration_assessed_count=5, automation_eligible_count=3,
        automation_assessed_count=3,
    )
    category = result["categories"]["integrations"]
    assert category["deducted_points"] == 25
    assert sum(x["points"] for x in category["deductions"]) == 25
    assert len({x["issue_id"] for x in result["deductions"]}) == 5


def test_partial_coverage_keeps_score_separate_from_confidence():
    result = complete(availability_assessed_count=5)
    assert result["score"] == 100
    assert result["status"] == "partial"
    assert result["coverage_percent"] == 85
    assert result["assessed_points"] == 85


def test_score_is_not_assessed_when_no_domain_has_coverage():
    result = complete(
        availability_assessed_count=0,
        integration_assessed_count=0,
        automation_assessed_count=0,
    )
    assert result["score"] is None
    assert result["status"] == "not_assessed"
    assert result["coverage_percent"] == 0


def test_warning_deductions_are_half_of_error_deductions():
    incidents = [
        {"issue_id": "warning", "category": "freshness",
         "rule_id": "freshness.stale", "severity": "warning"},
        {"issue_id": "error", "category": "freshness",
         "rule_id": "freshness.sensor_missing", "severity": "error"},
    ]
    result = calculate_health_score(
        incidents,
        availability_eligible_count=1, availability_assessed_count=1,
        freshness_enabled=True, selected_freshness_count=1,
        freshness_monitoring_count=1,
        integration_eligible_count=1, integration_assessed_count=1,
        automation_eligible_count=1, automation_assessed_count=1,
    )
    deductions = {
        item["issue_id"]: item["points"]
        for item in result["categories"]["freshness"]["deductions"]
    }
    assert deductions == {"error": 4.0, "warning": 2.0}
    assert result["categories"]["freshness"]["earned_points"] == 14
