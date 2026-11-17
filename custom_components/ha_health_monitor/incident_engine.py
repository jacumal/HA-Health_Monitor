"""Deterministic incident lifecycle and deduplication."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

MAX_INCIDENT_HISTORY = 500
VALID_STATUSES = {"active", "resolved"}


def make_issue_id(rule_id: str, entity_id: str) -> str:
    """Build a stable, language-independent identifier for a monitor finding."""
    digest = sha256(f"{rule_id}:{entity_id}".encode()).hexdigest()[:20]
    return f"issue_{digest}"


def build_observations(
    unavailable: list[dict], stale: list[dict]
) -> list[dict[str, Any]]:
    """Convert raw monitor findings into normalized incident observations."""
    observations = []
    for item in unavailable:
        entity_id = item["entity_id"]
        observations.append(
            {
                "issue_id": make_issue_id("availability.unavailable", entity_id),
                "rule_id": "availability.unavailable",
                "category": "availability",
                "entity_id": entity_id,
                "severity": "error",
                "details": item,
            }
        )
    for item in stale:
        entity_id = item["entity_id"]
        observations.append(
            {
                "issue_id": make_issue_id("freshness.stale", entity_id),
                "rule_id": "freshness.stale",
                "category": "freshness",
                "entity_id": entity_id,
                "severity": "warning",
                "details": item,
            }
        )
    return observations


def _occurrence_count(value: Any) -> int:
    """Safely normalize persisted occurrence counts."""
    try:
        return max(1, min(int(value), 1_000_000))
    except (TypeError, ValueError, OverflowError):
        return 1


def reconcile_incidents(
    observations: list[dict[str, Any]],
    previous: list[dict[str, Any]],
    now: str,
) -> list[dict[str, Any]]:
    """Update active incidents and mark findings that disappeared as resolved."""
    previous_by_id = {
        item["issue_id"]: item
        for item in previous
        if isinstance(item, dict)
        and isinstance(item.get("issue_id"), str)
        and item.get("status") in VALID_STATUSES
    }
    current_by_id = {
        item["issue_id"]: item
        for item in observations
        if isinstance(item, dict) and isinstance(item.get("issue_id"), str)
    }
    history: list[dict[str, Any]] = []

    for issue_id, observation in current_by_id.items():
        old = previous_by_id.get(issue_id, {})
        old_status = old.get("status")
        old_count = _occurrence_count(old.get("occurrence_count", 1))
        if old_status == "active":
            occurrence_count = old_count
            first_seen = old.get("first_seen", now)
        elif old_status == "resolved":
            occurrence_count = old_count + 1
            first_seen = now
        else:
            occurrence_count = 1
            first_seen = now
        history.append(
            {
                **observation,
                "status": "active",
                "first_seen": first_seen,
                "last_seen": now,
                "resolved_at": None,
                "occurrence_count": occurrence_count,
            }
        )

    for issue_id, old in previous_by_id.items():
        if issue_id in current_by_id:
            continue
        if old.get("status") == "active":
            history.append(
                {
                    **old,
                    "status": "resolved",
                    "resolved_at": now,
                    "last_seen": (
                        old.get("last_seen")
                        if isinstance(old.get("last_seen"), str)
                        else now
                    ),
                }
            )
        else:
            history.append(old)

    history.sort(
        key=lambda item: (
            item.get("status") == "active",
            str(item.get("last_seen") or ""),
        ),
        reverse=True,
    )
    return history[:MAX_INCIDENT_HISTORY]
