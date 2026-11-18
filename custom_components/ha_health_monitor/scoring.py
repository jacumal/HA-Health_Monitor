"""Explainable, coverage-aware score across all operational monitor domains."""

from __future__ import annotations

from typing import Any

# Incident intelligence is cross-cutting; it must not apply a second penalty.
CATEGORY_WEIGHTS = {
    "availability": 30,
    "freshness": 20,
    "integrations": 25,
    "automations": 25,
}


def _coverage(eligible: int, assessed: int) -> float:
    return min(max(assessed, 0) / eligible, 1.0) if eligible > 0 else 1.0


def calculate_health_score(
    active_incidents: list[dict[str, Any]],
    *,
    availability_eligible_count: int,
    availability_assessed_count: int,
    freshness_enabled: bool,
    selected_freshness_count: int,
    freshness_monitoring_count: int,
    integration_eligible_count: int = 0,
    integration_assessed_count: int = 0,
    automation_eligible_count: int = 0,
    automation_assessed_count: int = 0,
) -> dict[str, Any]:
    """Calculate a normalized score and expose coverage and deductions."""
    enabled = {
        "availability": True,
        "freshness": freshness_enabled,
        "integrations": True,
        "automations": True,
    }
    coverage = {
        "availability": _coverage(
            availability_eligible_count, availability_assessed_count
        ),
        "freshness": (
            _coverage(selected_freshness_count, freshness_monitoring_count)
            if freshness_enabled
            else 0.0
        ),
        "integrations": _coverage(
            integration_eligible_count, integration_assessed_count
        ),
        "automations": _coverage(
            automation_eligible_count, automation_assessed_count
        ),
    }
    breakdown: dict[str, Any] = {}
    deductions_all: list[dict[str, Any]] = []
    assessed_points = earned_points = 0.0
    enabled_points = sum(
        weight for category, weight in CATEGORY_WEIGHTS.items()
        if enabled[category]
    )
    base_points = {
        "availability": 6.0,
        "freshness": 4.0,
        "integrations": 10.0,
        "automations": 8.0,
    }

    for category, weight in CATEGORY_WEIGHTS.items():
        category_enabled = enabled[category]
        possible = weight * coverage[category] if category_enabled else 0.0
        items = [
            issue
            for issue in active_incidents
            if issue.get("category") == category
        ]
        remaining = possible
        deductions = []
        ordered_items = sorted(
            items,
            key=lambda issue: (
                issue.get("severity") != "error",
                issue.get("issue_id", ""),
            ),
        )
        for issue in ordered_items:
            severity_points = (
                base_points[category]
                if issue.get("severity") == "error"
                else base_points[category] / 2
            )
            points = min(severity_points, remaining)
            remaining -= points
            rule_suffix = issue.get("rule_id", "finding").split(".")[-1]
            deduction = {
                "issue_id": issue["issue_id"],
                "rule_id": f"score.{category}.{rule_suffix}",
                "category": category,
                "entity_id": issue.get("entity_id"),
                "target": issue.get("target"),
                "points": round(points, 2),
                "reason": (
                    "active_monitor_finding"
                    if points > 0
                    else "category_deduction_cap_reached"
                ),
                "correlation_key": issue.get("correlation_key"),
            }
            deductions.append(deduction)
            deductions_all.append(deduction)

        assessed_points += possible
        earned_points += remaining
        category_coverage = coverage[category]
        if not category_enabled:
            assessment = "disabled"
        elif category_coverage >= 1:
            assessment = "assessed"
        elif category_coverage > 0:
            assessment = "partial"
        else:
            assessment = "not_assessed"
        breakdown[category] = {
            "weight": weight,
            "coverage_percent": round(category_coverage * 100, 1),
            "possible_points": round(possible, 2),
            "earned_points": round(remaining, 2),
            "deducted_points": round(possible - remaining, 2),
            "assessment": assessment,
            "issue_ids": [issue["issue_id"] for issue in items],
            "deductions": deductions,
        }

    percent = round(assessed_points / enabled_points * 100, 1) if enabled_points else 0
    score = round(earned_points / assessed_points * 100) if assessed_points else None
    if score is None:
        status = "not_assessed"
    elif percent < 100:
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
        "coverage_percent": percent,
        "assessed_points": round(assessed_points, 2),
        "possible_points": enabled_points,
        "unassessed_categories": [
            key
            for key, value in breakdown.items()
            if value["assessment"] == "not_assessed"
        ],
        "partial_categories": [
            key
            for key, value in breakdown.items()
            if value["assessment"] == "partial"
        ],
        "categories": breakdown,
        "deductions": deductions_all,
    }
