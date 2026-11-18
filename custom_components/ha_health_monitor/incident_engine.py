"""Deterministic incident lifecycle, deduplication and correlation."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

MAX_INCIDENT_HISTORY = 500
VALID_STATUSES = {"active", "resolved"}
VALID_CATEGORIES = {"availability", "freshness", "integrations", "automations"}


def make_issue_id(rule_id: str, entity_id: str) -> str:
    """Return a stable, language-independent issue identifier."""
    digest = sha256(f"{rule_id}:{entity_id}".encode()).hexdigest()[:20]
    return f"issue_{digest}"


def _make(
    rule: str,
    category: str,
    target: str,
    severity: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    """Build a normalized monitor observation."""
    return {
        "issue_id": make_issue_id(rule, target),
        "rule_id": rule,
        "category": category,
        "entity_id": target if "." in target else None,
        "target": target,
        "severity": severity,
        "details": details,
        "correlation_key": details.get(
            "correlation_key", f"{category}:{target}"
        ),
    }


def build_observations(
    unavailable: list[dict[str, Any]],
    stale: list[dict[str, Any]],
    failed_integrations: list[dict[str, Any]] | None = None,
    unavailable_automations: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Convert monitor findings into stable incident observations."""
    observations = []
    for item in unavailable:
        observations.append(
            _make(
                "availability.unavailable",
                "availability",
                item["entity_id"],
                "error",
                item,
            )
        )
    for item in stale:
        observations.append(
            _make(
                "freshness.stale",
                "freshness",
                item["entity_id"],
                "warning",
                item,
            )
        )
    for item in failed_integrations or []:
        observations.append(
            _make(
                item.get("rule_id", "integration.setup_failed"),
                "integrations",
                item["entry_id"],
                "error",
                item,
            )
        )
    for item in unavailable_automations or []:
        observations.append(
            _make(
                "automation.unavailable",
                "automations",
                item["entity_id"],
                "error",
                item,
            )
        )
    return observations


def correlate_incidents(
    active_incidents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group incidents by explicit root-cause key without merging lifecycle."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in active_incidents:
        key = item.get("correlation_key") or (
            f"{item.get('category')}:{item.get('target')}"
        )
        groups.setdefault(key, []).append(item)

    result = []
    for key, members in groups.items():
        primary = sorted(
            members,
            key=lambda item: (
                item.get("severity") != "error",
                item["issue_id"],
            ),
        )[0]
        severity = (
            "error"
            if any(item.get("severity") == "error" for item in members)
            else "warning"
        )
        result.append(
            {
                "correlation_id": (
                    f"corr_{sha256(key.encode()).hexdigest()[:16]}"
                ),
                "correlation_key": key,
                "issue_ids": sorted(item["issue_id"] for item in members),
                "categories": sorted(
                    {item["category"] for item in members}
                ),
                "severity": severity,
                "member_count": len(members),
                "primary_issue_id": primary["issue_id"],
            }
        )
    return sorted(
        result,
        key=lambda item: (
            -item["member_count"],
            item["correlation_id"],
        ),
    )


def _count(value: Any) -> int:
    """Clamp persisted occurrence counts to a safe positive range."""
    try:
        return max(1, min(int(value), 1_000_000))
    except (TypeError, ValueError, OverflowError):
        return 1


def reconcile_incidents(
    observations: list[dict[str, Any]],
    previous: list[dict[str, Any]],
    now: str,
) -> list[dict[str, Any]]:
    """Reconcile current observations with bounded persisted incident history."""
    previous_by_id = {
        item["issue_id"]: item
        for item in previous
        if isinstance(item, dict)
        and isinstance(item.get("issue_id"), str)
        and item.get("status") in VALID_STATUSES
        and item.get("category") in VALID_CATEGORIES
        and isinstance(item.get("rule_id"), str)
    }
    current = {
        item["issue_id"]: item
        for item in observations
        if isinstance(item, dict)
        and isinstance(item.get("issue_id"), str)
        and item.get("category") in VALID_CATEGORIES
    }
    history = []

    for issue_id, item in current.items():
        old = previous_by_id.get(issue_id, {})
        old_status = old.get("status")
        occurrence_count = _count(old.get("occurrence_count", 1))
        if old_status == "active":
            first_seen = old.get("first_seen", now)
            next_count = occurrence_count
        else:
            first_seen = now
            next_count = occurrence_count + 1 if old_status == "resolved" else 1
        history.append(
            {
                **item,
                "status": "active",
                "first_seen": first_seen,
                "last_seen": now,
                "resolved_at": None,
                "occurrence_count": next_count,
            }
        )

    for issue_id, old in previous_by_id.items():
        if issue_id in current:
            continue
        if old.get("status") == "active":
            history.append(
                {
                    **old,
                    "status": "resolved",
                    "resolved_at": now,
                    "last_seen": old.get("last_seen") or now,
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
