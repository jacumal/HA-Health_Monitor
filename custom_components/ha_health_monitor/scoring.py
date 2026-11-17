"""Explainable, coverage-aware health score."""

from __future__ import annotations

from typing import Any

# Provisional product weights; validate before a stable release.
CATEGORY_WEIGHTS = {
    "availability": 30,
    "freshness": 25,
    "integrations": 25,
    "automations": 10,
    "incident_intelligence": 10,
}


def calculate_health_score(
    active_incidents: list[dict[str, Any]],
    *,
    availability_eligible_count: int,
    availability_assessed_count: int,
    freshness_enabled: bool,
    selected_freshness_count: int,
    freshness_monitoring_count: int,
) -> dict[str, Any]:
    """Calculate score, coverage and deductions without hiding unassessed areas."""
    category_coverage = {
        "availability": (
            min(availability_assessed_count / availability_eligible_count, 1.0)
            if availability_eligible_count > 0
            else 0.0
        ),
        "freshness": (
            min(freshness_monitoring_count / selected_freshness_count, 1.0)
            if freshness_enabled and selected_freshness_count > 0
            else 0.0
        ),
        "integrations": 0.0,
        "automations": 0.0,
        "incident_intelligence": 0.0,
    }

    breakdown: dict[str, dict[str, Any]] = {}
    all_deductions: list[dict[str, Any]] = []
    assessed_points = 0.0
    earned_points = 0.0

    for category, weight in CATEGORY_WEIGHTS.items():
        coverage = category_coverage[category]
        possible = weight * coverage
        category_incidents = [
            item for item in active_incidents if item.get("category") == category
        ]
        deductions = []
        for incident in category_incidents:
            if category == "availability":
                points = 6.0 if incident.get("severity") == "error" else 3.0
                rule_id = "score.availability.unavailable"
            elif category == "freshness":
                points = 4.0
                rule_id = "score.freshness.stale"
            else:
                continue
            deduction = {
                "issue_id": incident["issue_id"],
                "rule_id": rule_id,
                "category": category,
                "entity_id": incident["entity_id"],
                "points": points,
                "reason": "active_monitor_finding",
            }
            deductions.append(deduction)
            all_deductions.append(deduction)

        lost = min(possible, sum(item["points"] for item in deductions))
        earned = max(0.0, possible - lost)
        assessed_points += possible
        earned_points += earned
        breakdown[category] = {
            "weight": weight,
            "coverage_percent": round(coverage * 100, 1),
            "possible_points": round(possible, 2),
            "earned_points": round(earned, 2),
            "deducted_points": round(lost, 2),
            "assessment": (
                "assessed"
                if coverage >= 1
                else "partial"
                if coverage > 0
                else "not_assessed"
            ),
            "issue_ids": [item["issue_id"] for item in category_incidents],
            "deductions": deductions,
        }

    coverage_percent = round(assessed_points, 1)
    score = (
        round(earned_points / assessed_points * 100)
        if assessed_points > 0
        else None
    )
    if score is None:
        status = "not_assessed"
    elif coverage_percent < 80:
        status = "partial"
    elif score >= 90:
        status = "healthy"
    elif score >= 70:
        status = "attention"
    else:
        status = "unhealthy"

    return {
        "score": score,
        "status": status,
        "coverage_percent": coverage_percent,
        "assessed_points": round(assessed_points, 2),
        "possible_points": 100,
        "unassessed_categories": [
            category
            for category, result in breakdown.items()
            if result["assessment"] != "assessed"
        ],
        "categories": breakdown,
        "deductions": all_deductions,
    }
