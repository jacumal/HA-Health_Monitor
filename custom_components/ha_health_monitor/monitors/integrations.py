"""Integration setup health using public ConfigEntry state information."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# ConfigEntry states that represent a persistent failure, rather than a
# transitional state or an entry intentionally left unloaded by the user.
FAILURE_RULES = {
    "setup_error": "integration.setup_failed",
    "migration_error": "integration.migration_failed",
    "failed_unload": "integration.unload_failed",
}
TRANSITIONAL_STATES = {"setup_retry", "setup_in_progress", "unload_in_progress"}


def collect_integration_health(config_entries: Iterable[Any]) -> dict[str, Any]:
    """Report persistent setup, migration and unload failures."""
    entries = list(config_entries)
    failed = []
    loaded = assessed = retrying = 0
    for entry in entries:
        state = getattr(entry, "state", None)
        value = getattr(state, "value", state)
        if value == "loaded":
            loaded += 1
            assessed += 1
        elif value in FAILURE_RULES:
            assessed += 1
            failed.append(
                {
                    "entry_id": entry.entry_id,
                    "domain": entry.domain,
                    "title": entry.title,
                    "state": value,
                    "rule_id": FAILURE_RULES[value],
                    "correlation_key": f"integration:{entry.domain}",
                }
            )
        elif value in TRANSITIONAL_STATES:
            retrying += 1
        elif value == "not_loaded":
            # An unloaded entry is not inherently unhealthy: users can
            # intentionally disable or unload integrations.
            assessed += 1
    return {
        "eligible_count": len(entries),
        "assessed_count": assessed,
        "loaded_count": loaded,
        "failed_count": len(failed),
        "retrying_count": retrying,
        "failed_entries": failed,
    }
