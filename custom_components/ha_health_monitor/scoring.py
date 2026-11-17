"""Explainable, coverage-aware score across all operational monitor domains."""
from __future__ import annotations
from typing import Any

# Incident intelligence is cross-cutting; it must not apply a second penalty.
CATEGORY_WEIGHTS = {"availability": 30, "freshness": 20, "integrations": 25, "automations": 25}

def _coverage(eligible: int, assessed: int) -> float:
    return min(max(assessed, 0) / eligible, 1.0) if eligible > 0 else 0.0

def calculate_health_score(active_incidents: list[dict[str, Any]], *,
    availability_eligible_count: int, availability_assessed_count: int,
    freshness_enabled: bool, selected_freshness_count: int,
    freshness_monitoring_count: int, integration_eligible_count: int = 0,
    integration_assessed_count: int = 0, automation_eligible_count: int = 0,
    automation_assessed_count: int = 0) -> dict[str, Any]:
    coverage = {
        "availability": _coverage(availability_eligible_count, availability_assessed_count),
        "freshness": _coverage(selected_freshness_count, freshness_monitoring_count) if freshness_enabled else 1.0,
        "integrations": _coverage(integration_eligible_count, integration_assessed_count),
        "automations": _coverage(automation_eligible_count, automation_assessed_count),
    }
    breakdown, deductions_all = {}, []
    assessed_points = earned_points = 0.0
    base_points = {"availability": 6.0, "freshness": 4.0, "integrations": 10.0, "automations": 8.0}
    for category, weight in CATEGORY_WEIGHTS.items():
        possible = weight * coverage[category]
        items = [x for x in active_incidents if x.get("category") == category]
        remaining, deductions = possible, []
        for issue in sorted(items, key=lambda x: (x.get("severity") != "error", x.get("issue_id", ""))):
            points = min(base_points[category] if issue.get("severity") == "error" else base_points[category] / 2, remaining)
            if points <= 0:
                continue
            remaining -= points
            deduction = {
                "issue_id": issue["issue_id"],
                "rule_id": f"score.{category}.{issue.get('rule_id', 'finding').split('.')[-1]}",
                "category": category, "entity_id": issue.get("entity_id"),
                "target": issue.get("target"), "points": round(points, 2),
                "reason": "active_monitor_finding",
                "correlation_key": issue.get("correlation_key"),
            }
            deductions.append(deduction)
            deductions_all.append(deduction)
        assessed_points += possible
        earned_points += remaining
        state = "assessed" if coverage[category] >= 1 else "partial" if coverage[category] > 0 else "not_assessed"
        breakdown[category] = {
            "weight": weight, "coverage_percent": round(coverage[category] * 100, 1),
            "possible_points": round(possible, 2), "earned_points": round(remaining, 2),
            "deducted_points": round(possible - remaining, 2), "assessment": state,
            "issue_ids": [x["issue_id"] for x in items], "deductions": deductions,
        }
    percent = round(assessed_points, 1)
    score = round(earned_points / assessed_points * 100) if assessed_points else None
    status = ("not_assessed" if score is None else "partial" if percent < 100
              else "healthy" if score >= 90 else "attention" if score >= 70 else "unhealthy")
    return {
        "score": score, "status": status, "coverage_percent": percent,
        "assessed_points": round(assessed_points, 2), "possible_points": 100,
        "unassessed_categories": [k for k,v in breakdown.items() if v["assessment"] == "not_assessed"],
        "partial_categories": [k for k,v in breakdown.items() if v["assessment"] == "partial"],
        "categories": breakdown, "deductions": deductions_all,
    }
