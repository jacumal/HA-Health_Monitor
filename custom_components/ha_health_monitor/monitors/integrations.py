"""Integration setup health using public ConfigEntry state information."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def collect_integration_health(config_entries: Iterable[Any]) -> dict[str, Any]:
    """Report persistent setup failures; transitional retries stay informational."""
    entries = list(config_entries)
    failed = []
    loaded = assessed = retrying = 0
    for entry in entries:
        state = getattr(entry, "state", None)
        value = getattr(state, "value", state)
        if value == "loaded":
            loaded += 1
            assessed += 1
        elif value == "setup_error":
            assessed += 1
            failed.append(
                {
                    "entry_id": entry.entry_id,
                    "domain": entry.domain,
                    "title": entry.title,
                    "state": value,
                    "correlation_key": f"integration:{entry.domain}",
                }
            )
        elif value == "setup_retry":
            retrying += 1
        elif value in ("not_loaded", "failed_unload"):
            assessed += 1
    return {
        "eligible_count": len(entries),
        "assessed_count": assessed,
        "loaded_count": loaded,
        "failed_count": len(failed),
        "retrying_count": retrying,
        "failed_entries": failed,
    }
