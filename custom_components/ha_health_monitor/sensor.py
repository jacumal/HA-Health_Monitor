"""Sensor entities for HA Health Monitor."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HealthMonitorConfigEntry
from .coordinator import HealthMonitorCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="unavailable_entities",
        translation_key="unavailable_entities",
        icon="mdi:lan-disconnect",
    ),
    SensorEntityDescription(
        key="stale_entities",
        translation_key="stale_entities",
        icon="mdi:clock-alert-outline",
    ),
    SensorEntityDescription(
        key="last_scan",
        translation_key="last_scan",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HealthMonitorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    async_add_entities(
        HealthMonitorSensor(entry.runtime_data, description)
        for description in ENTITY_DESCRIPTIONS
    )


class HealthMonitorSensor(CoordinatorEntity[HealthMonitorCoordinator], SensorEntity):
    """Represent a monitoring statistic."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HealthMonitorCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def suggested_object_id(self) -> str:
        """Return a stable, language-independent entity ID suffix."""
        return f"ha_health_monitor_{self.entity_description.key}"

    @property
    def native_value(self):
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None
        if self.entity_description.key == "last_scan":
            return self.coordinator.data["last_scan"]
        return len(self.coordinator.data[self.entity_description.key])

    @property
    def extra_state_attributes(self):
        """Expose concise, structured observations for dashboards."""
        if self.coordinator.data is None:
            return {}
        key = self.entity_description.key
        if key == "unavailable_entities":
            return {
                "entities": self.coordinator.data["unavailable_entities"],
                "monitored_entity_count": self.coordinator.data[
                    "monitored_entity_count"
                ],
                "grace_period_seconds": self.coordinator.data[
                    "availability_grace_seconds"
                ],
            }
        if key == "stale_entities":
            return {
                "entities": self.coordinator.data["stale_entities"],
                "freshness_enabled": self.coordinator.data["freshness_enabled"],
                "selected_entity_count": self.coordinator.data[
                    "freshness_entity_count"
                ],
                "threshold_minutes": self.coordinator.data[
                    "freshness_threshold_minutes"
                ],
            }
        return {}
