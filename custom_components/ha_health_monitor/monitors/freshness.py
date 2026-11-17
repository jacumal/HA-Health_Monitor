"""Opt-in freshness observations and adaptive per-entity cadence learning."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from math import isfinite
from statistics import median

from homeassistant.core import State

MAX_INTERVAL_SECONDS = 30 * 24 * 60 * 60
MIN_INTERVAL_SAMPLES = 5
MAX_INTERVAL_SAMPLES = 21
OUTLIER_FACTOR = 6.0
ADAPTATION_ALPHA = 0.2
STALE_MULTIPLIER = 3.0


class FreshnessLearner:
    """Learn expected reporting cadence for explicitly selected entities."""

    def __init__(self, data: dict | None = None) -> None:
        raw = data.get("entities", {}) if isinstance(data, dict) else {}
        self._entities: dict[str, dict] = {}
        if isinstance(raw, dict):
            for entity_id, profile in raw.items():
                if not isinstance(entity_id, str) or not isinstance(profile, dict):
                    continue
                self._entities[entity_id] = self._normalize_profile(profile)

    @staticmethod
    def _normalize_profile(profile: dict) -> dict:
        """Validate and normalize persisted profile data."""
        last_reported = profile.get("last_reported")
        if not isinstance(last_reported, str):
            last_reported = None
        try:
            if last_reported is not None:
                parsed = datetime.fromisoformat(last_reported)
                if parsed.tzinfo is None:
                    last_reported = None
        except ValueError:
            last_reported = None

        if last_reported is None:
            return {
                "last_reported": None,
                "intervals": [],
                "expected_interval": None,
                "sample_count": 0,
            }

        intervals = profile.get("intervals", [])
        if not isinstance(intervals, list):
            intervals = []
        valid_intervals = [
            float(value)
            for value in intervals
            if isinstance(value, (int, float))
            and 0 < value <= MAX_INTERVAL_SECONDS
        ][-MAX_INTERVAL_SAMPLES:]
        expected = profile.get("expected_interval")
        if (
            not isinstance(expected, (int, float))
            or not 0 < expected <= MAX_INTERVAL_SECONDS
        ):
            expected = None
        count = profile.get("sample_count", len(valid_intervals))
        if not isinstance(count, int) or count < 0:
            count = len(valid_intervals)
        if expected is None and len(valid_intervals) >= MIN_INTERVAL_SAMPLES:
            expected = float(median(valid_intervals))
        return {
            "last_reported": last_reported,
            "intervals": valid_intervals,
            "expected_interval": float(expected) if expected is not None else None,
            "sample_count": count,
        }

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
        """Record a real report and update the learned cadence."""
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
        if previous is None:
            record["last_reported"] = reported_at.isoformat()
            return True
        try:
            previous_at = datetime.fromisoformat(previous)
        except (TypeError, ValueError):
            record["last_reported"] = reported_at.isoformat()
            return True
        if previous_at.tzinfo is None:
            record["last_reported"] = reported_at.isoformat()
            return True

        interval = (reported_at - previous_at).total_seconds()
        if interval <= 0:
            return False
        if interval > MAX_INTERVAL_SECONDS:
            record["last_reported"] = reported_at.isoformat()
            return True

        expected = record.get("expected_interval")
        samples = record.setdefault("intervals", [])
        if expected is None:
            # Reject extreme gaps during initial learning so a temporary outage
            # cannot poison the first cadence estimate.
            if len(samples) >= 3:
                center = median(samples)
                if (
                    interval > center * OUTLIER_FACTOR
                    or interval < center / OUTLIER_FACTOR
                ):
                    record["last_reported"] = reported_at.isoformat()
                    return True
            samples.append(interval)
            del samples[:-MAX_INTERVAL_SAMPLES]
            record["sample_count"] = len(samples)
            if len(samples) >= MIN_INTERVAL_SAMPLES:
                record["expected_interval"] = float(median(samples))
        else:
            if (
                interval > expected * OUTLIER_FACTOR
                or interval < expected / OUTLIER_FACTOR
            ):
                record["last_reported"] = reported_at.isoformat()
                return True
            bounded = min(max(interval, expected * 0.5), expected * 2.0)
            record["expected_interval"] = (
                expected * (1 - ADAPTATION_ALPHA) + bounded * ADAPTATION_ALPHA
            )
            samples.append(interval)
            del samples[:-MAX_INTERVAL_SAMPLES]
            record["sample_count"] = min(
                int(record.get("sample_count", MIN_INTERVAL_SAMPLES)) + 1, 10000
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
        """Return JSON-serializable data suitable for HA Store."""
        return {"entities": self._entities}

    @classmethod
    def from_storage(cls, data: dict | None) -> FreshnessLearner:
        """Restore a learner from stored representation."""
        return cls(data)

    def status(self, entity_id: str) -> str:
        """Return the user-facing lifecycle state identifier."""
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
        profile_status = (
            "missing"
            if state is None
            else "paused"
            if state.state in ("unknown", "unavailable")
            else learner.status(entity_id)
        )
        profiles[entity_id] = {
            "status": profile_status,
            "sample_count": learner.sample_count(entity_id),
            "expected_interval_seconds": (
                round(expected) if expected is not None else None
            ),
            "threshold_seconds": int(threshold.total_seconds()) if threshold else None,
        }
        if (
            state is None
            or state.state in ("unknown", "unavailable")
            or threshold is None
        ):
            continue
        age = now - state.last_reported
        if age > threshold:
            stale.append(
                {
                    "entity_id": entity_id,
                    "name": state.name,
                    "last_reported": state.last_reported.isoformat(),
                    "age_seconds": int(age.total_seconds()),
                    "threshold_seconds": int(threshold.total_seconds()),
                }
            )
    return stale, profiles
