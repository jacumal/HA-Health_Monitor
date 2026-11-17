"""Sensor entities for HA Health Monitor."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HealthMonitorConfigEntry
from .coordinator import HealthMonitorCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="health_score",
        translation_key="health_score",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="health_status",
        translation_key="health_status",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="active_incidents",
        translation_key="active_incidents",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="incident_history",
        translation_key="incident_history",
        icon="mdi:history",
    ),
    SensorEntityDescription(
        key="unavailable_entities",
        translation_key="unavailable_entities",
        icon="mdi:lan-disconnect",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="stale_entities",
        translation_key="stale_entities",
        icon="mdi:clock-alert-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="last_scan",
        translation_key="last_scan",
        device_class=SensorDeviceClass.TIMESTAMP,
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
        data = self.coordinator.data
        key = self.entity_description.key
        if key == "health_score":
            return data["health_score"]
        if key == "health_status":
            return data["health_status"]
        if key == "active_incidents":
            return len(data["active_incidents"])
        if key == "incident_history":
            return len(data["incident_history"])
        if key == "last_scan":
            return data["last_scan"]
        return len(data[key])

    @property
    def extra_state_attributes(self):
        """Expose issue details and score explainability."""
        if self.coordinator.data is None:
            return {}
        data = self.coordinator.data
        key = self.entity_description.key
        if key == "health_score":
            return {
                "coverage_percent": data["health_coverage_percent"],
                "breakdown": data["health_score_breakdown"],
            }
        if key == "active_incidents":
            return {"incidents": data["active_incidents"]}
        if key == "incident_history":
            return {"incidents": data["incident_history"][-50:]}
        if key == "unavailable_entities":
            return {
                "entities": data["unavailable_entities"],
                "eligible_entity_count": data["monitored_entity_count"],
                "assessed_entity_count": data["availability_assessed_count"],
                "unknown_entity_count": data["unknown_entity_count"],
                "grace_period_seconds": data["availability_grace_seconds"],
            }
        if key == "stale_entities":
            return {
                "entities": data["stale_entities"],
                "freshness_enabled": data["freshness_enabled"],
                "selected_entity_count": data["freshness_entity_count"],
                "learning_entity_count": data["freshness_learning_count"],
                "monitoring_entity_count": data["freshness_monitoring_count"],
                "missing_entity_count": data["freshness_missing_count"],
                "paused_entity_count": data["freshness_paused_count"],
                "profiles": data["freshness_profiles"],
            }
        return {}
