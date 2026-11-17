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
