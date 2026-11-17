"""Opt-in freshness observations and adaptive per-entity cadence learning."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from statistics import median

from homeassistant.core import State

MAX_INTERVAL_SECONDS = 30 * 24 * 60 * 60
MIN_INTERVAL_SAMPLES = 5
ADAPTATION_ALPHA = 0.2
STALE_MULTIPLIER = 3.0


class FreshnessLearner:
    """Learn expected reporting cadence for explicitly selected entities."""

    def __init__(self, data: dict | None = None) -> None:
        self._entities: dict[str, dict] = (data or {}).get("entities", {})

    def has_profile(self, entity_id: str) -> bool:
        """Return whether any learning state exists for an entity."""
        return entity_id in self._entities

    def seed(self, entity_id: str, reported_at: datetime) -> bool:
        """Set initial timestamp without counting startup as a sample."""
        if reported_at.tzinfo is None or self.has_profile(entity_id):
            return False
        self._entities[entity_id] = {
            "last_reported": reported_at.isoformat(),
            "intervals": [],
            "expected_interval": None,
            "sample_count": 0,
        }
        return True

    def observe(self, entity_id: str, reported_at: datetime) -> bool:
        """Record a real report timestamp and update the learned cadence."""
        if reported_at.tzinfo is None:
            return False
        record = self._entities.setdefault(
            entity_id,
            {
                "last_reported": None,
                "intervals": [],
                "expected_interval": None,
                "sample_count": 0,
            },
        )
        previous = record.get("last_reported")
        if previous is not None:
            previous_at = datetime.fromisoformat(previous)
            interval = (reported_at - previous_at).total_seconds()
            if interval <= 0:
                return False
            if interval > MAX_INTERVAL_SECONDS:
                record["last_reported"] = reported_at.isoformat()
                return True

            expected = record.get("expected_interval")
            samples = record.setdefault("intervals", [])
            if expected is None:
                samples.append(interval)
                if len(samples) > MIN_INTERVAL_SAMPLES:
                    del samples[:-MIN_INTERVAL_SAMPLES]
                record["sample_count"] = len(samples)
                if len(samples) >= MIN_INTERVAL_SAMPLES:
                    record["expected_interval"] = float(median(samples))
            else:
                bounded = min(max(interval, expected * 0.5), expected * 2.0)
                record["expected_interval"] = (
                    expected * (1 - ADAPTATION_ALPHA)
                    + bounded * ADAPTATION_ALPHA
                )
                record["sample_count"] = min(
                    int(record.get("sample_count", MIN_INTERVAL_SAMPLES)) + 1,
                    10000,
                )
        record["last_reported"] = reported_at.isoformat()
        return True

    def is_ready(self, entity_id: str) -> bool:
        """Return whether enough intervals exist to monitor this entity."""
        return self.expected_interval(entity_id) is not None

    def expected_interval(self, entity_id: str) -> float | None:
        """Return learned expected interval in seconds."""
        return self._entities.get(entity_id, {}).get("expected_interval")

    def sample_count(self, entity_id: str) -> int:
        """Return valid intervals contributing to the profile."""
        return int(self._entities.get(entity_id, {}).get("sample_count", 0))

    def stale_after(self, entity_id: str) -> timedelta | None:
        """Return adaptive stale threshold, if learning is complete."""
        expected = self.expected_interval(entity_id)
        return timedelta(seconds=expected * STALE_MULTIPLIER) if expected else None

    def reset(self, entity_id: str | None = None) -> None:
        """Reset one entity or all learned profiles."""
        if entity_id is None:
            self._entities.clear()
        else:
            self._entities.pop(entity_id, None)

    def retain_entities(self, selected_entities: set[str]) -> bool:
        """Drop profiles for entities no longer explicitly selected."""
        retained = {
            entity_id: profile
            for entity_id, profile in self._entities.items()
            if entity_id in selected_entities
        }
        changed = len(retained) != len(self._entities)
        self._entities = retained
        return changed

    def export(self) -> dict:
        """Return JSON-serializable data for HA Store."""
        return {"entities": self._entities}

    @classmethod
    def from_storage(cls, data: dict | None) -> FreshnessLearner:
        """Restore learner from stored representation."""
        return cls(data if isinstance(data, dict) else None)

    def status(self, entity_id: str) -> str:
        """Return lifecycle state identifier."""
        return "monitoring" if self.is_ready(entity_id) else "learning"


def collect_adaptive_stale(
    states: Iterable[State],
    selected_entities: set[str],
    excluded_entities: set[str],
    learner: FreshnessLearner,
    now: datetime,
) -> tuple[list[dict], dict[str, dict]]:
    """Return stale observations and per-entity learning status."""
    stale: list[dict] = []
    profiles: dict[str, dict] = {}
    state_by_id = {state.entity_id: state for state in states}
    for entity_id in sorted(selected_entities - excluded_entities):
        state = state_by_id.get(entity_id)
        expected = learner.expected_interval(entity_id)
        threshold = learner.stale_after(entity_id)
        profiles[entity_id] = {
            "status": learner.status(entity_id),
            "sample_count": learner.sample_count(entity_id),
            "expected_interval_seconds": round(expected) if expected is not None else None,
            "threshold_seconds": int(threshold.total_seconds()) if threshold else None,
        }
        if state is None or state.state in ("unknown", "unavailable") or threshold is None:
            continue
        age = now - state.last_reported
        if age > threshold:
            stale.append({
                "entity_id": entity_id,
                "name": state.name,
                "last_reported": state.last_reported.isoformat(),
                "age_seconds": int(age.total_seconds()),
                "threshold_seconds": int(threshold.total_seconds()),
            })
    return stale, profiles
