"""Availability observations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from homeassistant.core import State


def collect_device_metadata(
    entity_registry_entries: Iterable,
    device_registry_entries: Iterable,
) -> dict[str, dict]:
    """Map entities to their registered device and integration metadata."""
    devices = {device.id: device for device in device_registry_entries}
    metadata = {}
    for entity in entity_registry_entries:
        platform = getattr(entity, "platform", None)
        device_id = getattr(entity, "device_id", None)
        metadata[entity.entity_id] = {"platform": platform}
        if device_id is None:
            continue
        device = devices.get(device_id)
        if device is None:
            continue
        metadata[entity.entity_id].update(
            {
                "device_id": device.id,
                "device_name": getattr(device, "name_by_user", None)
                or getattr(device, "name", None),
                "manufacturer": getattr(device, "manufacturer", None),
                "model": getattr(device, "model", None),
            }
        )
    return metadata


def collect_unavailable(
    states: Iterable[State],
    excluded_entities: set[str],
    now: datetime,
    grace_period: timedelta,
    device_metadata: dict[str, dict] | None = None,
) -> list[dict]:
    """Return entities that have remained unavailable beyond the grace period."""
    unavailable = []
    for state in states:
        if state.entity_id in excluded_entities or state.state != "unavailable":
            continue
        duration = now - state.last_changed
        if duration < grace_period:
            continue
        unavailable.append(
            {
                "entity_id": state.entity_id,
                "name": state.name,
                "last_changed": state.last_changed.isoformat(),
                "duration_seconds": int(duration.total_seconds()),
                **(device_metadata or {}).get(state.entity_id, {}),
            }
        )
    return unavailable


def evaluate_availability_profiles(
    states: Iterable[State],
    profiles: dict[str, dict],
    device_metadata: dict[str, dict],
) -> dict:
    """Suppress conditional entities only for explicitly configured standby states."""
    state_by_id = {state.entity_id: state for state in states}
    conditional_ids: set[str] = set()
    suppressed_ids: set[str] = set()
    statuses = []
    for device_id, profile in (profiles or {}).items():
        if not isinstance(profile, dict):
            continue
        reference = profile.get("reference_entity")
        entities = profile.get("conditional_entities", [])
        inactive = profile.get("inactive_states", [])
        if (
            not isinstance(reference, str)
            or not isinstance(entities, list)
            or not isinstance(inactive, list)
        ):
            continue
        if device_metadata.get(reference, {}).get("device_id") != device_id:
            continue
        valid = {
            entity_id
            for entity_id in entities
            if isinstance(entity_id, str)
            and device_metadata.get(entity_id, {}).get("device_id") == device_id
        }
        conditional_ids.update(valid)
        state = state_by_id.get(reference)
        reference_state = state.state if state is not None else None
        standby = isinstance(reference_state, str) and reference_state in inactive
        if standby:
            suppressed_ids.update(valid)
        statuses.append(
            {
                "device_id": device_id,
                "reference_entity": reference,
                "reference_state": reference_state,
                "conditional_entities": sorted(valid),
                "suppressed_entities": sorted(valid) if standby else [],
                "status": "standby" if standby else "monitoring",
            }
        )
    return {
        "conditional_entity_ids": conditional_ids,
        "suppressed_entity_ids": suppressed_ids,
        "profiles": statuses,
    }


def collect_disabled_entities(registry_entries: Iterable) -> list[dict]:
    """Return registry entities explicitly disabled in Home Assistant."""
    disabled = []
    for entry in registry_entries:
        disabled_by = getattr(entry, "disabled_by", None)
        if disabled_by is None:
            continue
        disabled.append(
            {
                "entity_id": entry.entity_id,
                "name": getattr(entry, "name", None)
                or getattr(entry, "original_name", None)
                or entry.entity_id,
                "platform": getattr(entry, "platform", None),
                "disabled_by": getattr(disabled_by, "value", str(disabled_by)),
                "entity_category": getattr(
                    getattr(entry, "entity_category", None), "value",
                    getattr(entry, "entity_category", None),
                ),
            }
        )
    return sorted(disabled, key=lambda item: item["entity_id"])


def evaluate_integration_activity_profiles(
    states: Iterable[State],
    profiles: dict[str, dict],
    entity_registry_entries: Iterable,
) -> dict:
    """Suppress only explicitly selected conditional entities while inactive.

    Unknown, unavailable or missing reference states fail open.
    """
    state_by_id = {state.entity_id: state for state in states}
    entries = {entry.entity_id: entry for entry in entity_registry_entries}
    conditional_ids: set[str] = set()
    suppressed_ids: set[str] = set()
    statuses = []
    for config_entry_id, profile in (profiles or {}).items():
        if not isinstance(profile, dict):
            continue
        reference = profile.get("reference_entity")
        inactive = profile.get("inactive_states", [])
        configured_entities = profile.get("conditional_entities", [])
        reference_entry = entries.get(reference) if isinstance(reference, str) else None
        if (
            reference_entry is None
            or reference_entry.config_entry_id != config_entry_id
            or not isinstance(inactive, list)
            or not inactive
            or not isinstance(configured_entities, list)
        ):
            continue
        valid = {
            entity_id
            for entity_id in configured_entities
            if isinstance(entity_id, str)
            and entity_id != reference
            and entity_id in entries
            and entries[entity_id].config_entry_id == config_entry_id
            and getattr(entries[entity_id], "disabled_by", None) is None
        }
        conditional_ids.update(valid)
        reference_state_obj = state_by_id.get(reference)
        reference_state = reference_state_obj.state if reference_state_obj is not None else None
        standby = (
            isinstance(reference_state, str)
            and reference_state not in ("unknown", "unavailable")
            and reference_state in inactive
        )
        if standby:
            suppressed_ids.update(valid)
        statuses.append({
            "config_entry_id": config_entry_id,
            "integration": reference_entry.platform,
            "reference_entity": reference,
            "reference_state": reference_state,
            "conditional_entity_count": len(valid),
            "suppressed_entities": sorted(valid) if standby else [],
            "status": "standby" if standby else "monitoring",
        })
    return {
        "conditional_entity_ids": conditional_ids,
        "suppressed_entity_ids": suppressed_ids,
        "profiles": statuses,
    }
