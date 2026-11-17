"""Constants for HA Health Monitor."""

from datetime import timedelta

DOMAIN = "ha_health_monitor"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_SCAN_INTERVAL = "scan_interval_minutes"
CONF_EXCLUDED_ENTITIES = "excluded_entities"
CONF_MONITOR_FRESHNESS = "monitor_freshness"
CONF_FRESHNESS_ENTITIES = "freshness_entities"
CONF_FRESHNESS_THRESHOLD = "freshness_threshold_minutes"

DEFAULT_SCAN_INTERVAL = 5
DEFAULT_MONITOR_FRESHNESS = False
DEFAULT_FRESHNESS_THRESHOLD = 60
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60

SERVICE_SCAN_NOW = "scan_now"

STORAGE_VERSION = 1
UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)
