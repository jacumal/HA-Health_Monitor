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
    """Learn expected reporting cadence from explicitly selected entities.

    The learner is deliberately deterministic and local. It needs five valid
    intervals before a profile becomes monitorable. Once ready, its expected
    interval moves gradually using an exponential moving average.
    """

    def __init__(self, data: dict | None = None) -> None:
        self._entities: dict[str, dict] = (data or {}).get("entities", {})

    def observe(self, entity_id: str, reported_at: datetime) -> bool:
        """Record a report timestamp. Return whether the profile changed."""
        if reported_at.tzinfo is None:
            return False

        record = self._entities.setdefault(
            entity_id,
            {"last_reported": None, "intervals": [], "expected_interval": None},
        )
        previous = record.get("last_reported")
        record["last_reported"] = reported_at.isoformat()
        if previous is None:
            return True

        previous_at = datetime.fromisoformat(previous)
        interval = (reported_at - previous_at).total_seconds()
        if interval <= 0 or interval > MAX_INTERVAL_SECONDS:
            return False

        expected = record.get("expected_interval")
        samples = record.setdefault("intervals", [])
        if expected is None:
            samples.append(interval)
            if len(samples) > MIN_INTERVAL_SAMPLES:
                del samples[:-MIN_INTERVAL_SAMPLES]
            if len(samples) >= MIN_INTERVAL_SAMPLES:
                record["expected_interval"] = float(median(samples))
        else:
            # Limit the influence of one unusual gap, then adapt gradually.
            bounded = min(max(interval, expected * 0.5), expected * 2.0)
            record["expected_interval"] = (
                expected * (1 - ADAPTATION_ALPHA) + bounded * ADAPTATION_ALPHA
            )
            record["sample_count"] = min(
                int(record.get("sample_count", MIN_INTERVAL_SAMPLES)) + 1, 10000
            )
        return True

    def is_ready(self, entity_id: str) -> bool:
        """Return whether enough intervals exist to monitor this entity."""
        record = self._entities.get(entity_id, {})
        return record.get("expected_interval") is not None

    def expected_interval(self, entity_id: str) -> float | None:
        """Return the learned expected interval in seconds."""
        return self._entities.get(entity_id, {}).get("expected_interval")

    def stale_after(self, entity_id: str) -> timedelta | None:
        """Return the adaptive stale threshold, if learning is complete."""
        expected = self.expected_interval(entity_id)
        if expected is None:
            return None
        return timedelta(seconds=expected * STALE_MULTIPLIER)

    def reset(self, entity_id: str | None = None) -> None:
        """Reset one entity or all learned profiles."""
        if entity_id is None:
            self._entities.clear()
        else:
            self._entities.pop(entity_id, None)

    def export(self) -> dict:
        """Return JSON-serializable data suitable for HA Store persistence."""
        return {"entities": self._entities}

    @classmethod
    def from_storage(cls, data: dict | None) -> FreshnessLearner:
        """Restore a learner from its stored representation."""
        return cls(data if isinstance(data, dict) else None)

    def status(self, entity_id: str) -> str:
        """Return the user-facing lifecycle state identifier."""
        return "monitoring" if self.is_ready(entity_id) else "learning"


def collect_stale(
    states: Iterable[State],
    selected_entities: set[str],
    excluded_entities: set[str],
    now: datetime,
    stale_after: timedelta,
) -> list[dict]:
    """Return selected entities that have not reported within a fixed threshold."""
    stale = []
    for state in states:
        if (
            state.entity_id not in selected_entities
            or state.entity_id in excluded_entities
            or state.state in ("unknown", "unavailable")
        ):
            continue
        last_reported = state.last_reported
        age = now - last_reported
        if age <= stale_after:
            continue
        stale.append(
            {
                "entity_id": state.entity_id,
                "name": state.name,
                "last_reported": last_reported.isoformat(),
                "age_seconds": int(age.total_seconds()),
                "threshold_seconds": int(stale_after.total_seconds()),
            }
        )
    return stale
