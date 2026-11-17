"""Deterministic incident lifecycle, deduplication and correlation."""
from __future__ import annotations
from hashlib import sha256
from typing import Any

MAX_INCIDENT_HISTORY = 500
VALID_STATUSES = {"active", "resolved"}
VALID_CATEGORIES = {"availability", "freshness", "integrations", "automations"}

def make_issue_id(rule_id: str, entity_id: str) -> str:
    digest = sha256(f"{rule_id}:{entity_id}".encode()).hexdigest()[:20]
    return f"issue_{digest}"

def _make(rule: str, category: str, target: str, severity: str, details: dict) -> dict:
    return {
        "issue_id": make_issue_id(rule, target), "rule_id": rule,
        "category": category, "entity_id": target if "." in target else None,
        "target": target, "severity": severity, "details": details,
        "correlation_key": details.get("correlation_key", f"{category}:{target}"),
    }

def build_observations(unavailable: list[dict], stale: list[dict],
                       failed_integrations: list[dict] | None = None,
                       unavailable_automations: list[dict] | None = None) -> list[dict[str, Any]]:
    observations = []
    for item in unavailable:
        observations.append(_make("availability.unavailable", "availability",
                                  item["entity_id"], "error", item))
    for item in stale:
        observations.append(_make("freshness.stale", "freshness",
                                  item["entity_id"], "warning", item))
    for item in failed_integrations or []:
        observations.append(_make("integration.setup_failed", "integrations",
                                  item["entry_id"], "error", item))
    for item in unavailable_automations or []:
        observations.append(_make("automation.unavailable", "automations",
                                  item["entity_id"], "error", item))
    return observations

def correlate_incidents(active_incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group incidents by explicit root-cause key without merging their lifecycle."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in active_incidents:
        key = item.get("correlation_key") or f'{item.get("category")}:{item.get("target")}'
        groups.setdefault(key, []).append(item)
    result = []
    for key, members in groups.items():
        result.append({
            "correlation_id": f"corr_{sha256(key.encode()).hexdigest()[:16]}",
            "correlation_key": key,
            "issue_ids": sorted(x["issue_id"] for x in members),
            "categories": sorted({x["category"] for x in members}),
            "severity": "error" if any(x.get("severity") == "error" for x in members) else "warning",
            "member_count": len(members),
            "primary_issue_id": sorted(members, key=lambda x: (x.get("severity") != "error", x["issue_id"]))[0]["issue_id"],
        })
    return sorted(result, key=lambda x: (-x["member_count"], x["correlation_id"]))

def _count(value: Any) -> int:
    try:
        return max(1, min(int(value), 1_000_000))
    except (TypeError, ValueError, OverflowError):
        return 1

def reconcile_incidents(observations: list[dict[str, Any]],
                        previous: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    previous_by_id = {
        x["issue_id"]: x for x in previous
        if isinstance(x, dict) and isinstance(x.get("issue_id"), str)
        and x.get("status") in VALID_STATUSES and x.get("category") in VALID_CATEGORIES
        and isinstance(x.get("rule_id"), str)
    }
    current = {x["issue_id"]: x for x in observations
               if isinstance(x, dict) and isinstance(x.get("issue_id"), str)
               and x.get("category") in VALID_CATEGORIES}
    history = []
    for issue_id, item in current.items():
        old = previous_by_id.get(issue_id, {})
        status = old.get("status")
        count = _count(old.get("occurrence_count", 1))
        history.append({
            **item, "status": "active",
            "first_seen": old.get("first_seen", now) if status == "active" else now,
            "last_seen": now, "resolved_at": None,
            "occurrence_count": count if status == "active" else count + 1 if status == "resolved" else 1,
        })
    for issue_id, old in previous_by_id.items():
        if issue_id not in current:
            history.append({**old, "status": "resolved", "resolved_at": now,
                            "last_seen": old.get("last_seen") or now}
                           if old.get("status") == "active" else old)
    history.sort(key=lambda x: (x.get("status") == "active", str(x.get("last_seen") or "")), reverse=True)
    return history[:MAX_INCIDENT_HISTORY]
