"""Binary sensor entities for HA Health Monitor."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HealthMonitorConfigEntry
from .coordinator import HealthMonitorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HealthMonitorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor."""
    async_add_entities([HealthSystemHealthySensor(entry.runtime_data, entry)])


class HealthSystemHealthySensor(
    CoordinatorEntity[HealthMonitorCoordinator], BinarySensorEntity
):
    """Report whether any currently monitored issue observations exist."""

    _attr_has_entity_name = True
    _attr_translation_key = "system_healthy"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self, coordinator: HealthMonitorCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_system_healthy"

    @property
    def suggested_object_id(self) -> str:
        """Return a stable, language-independent entity ID suffix."""
        return "ha_health_monitor_system_has_issues"

    @property
    def is_on(self) -> bool:
        """Return true when an issue observation exists."""
        return bool(self.coordinator.get_issue_count())
