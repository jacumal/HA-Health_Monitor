# HA Health Monitor

**Know your Home Assistant. Before something breaks.**

HA Health Monitor is an open-source Home Assistant integration for local observability and diagnostics. It detects meaningful problems, explains evidence and helps users troubleshoot without silently changing their installation.

> **Requires Home Assistant 2024.11 or newer.**
>
> **Current status: early development (0.1.0).** This is not a stable release and does not yet implement every planned monitoring engine or the Lovelace card.

## Current functionality

- Graphical installation and options through Home Assistant.
- Availability scan for entities in the `unavailable` state.
- Adaptive freshness learning for explicitly selected entities, using filtered state-change and state-report events plus local statistics.
- Per-entry persistence of cadence profiles using Home Assistant Store.
- Per-entity learning/monitoring state, sample count, expected cadence and adaptive stale threshold in sensor attributes.
- Manual service to reset one selected profile or all selected profiles.
- English and Spanish integration translations.

## Freshness learning

- Only explicitly selected entities are eligible for learning.
- Each entity needs at least five valid update intervals. There is no fixed time window.
- Startup seeds a timestamp but does not count as a sample.
- Filtered Home Assistant state-change and state-report events feed the learner, including reports where the value has not changed; periodic scans do not fabricate samples.
- The expected cadence adapts gradually with bounded intervals.
- Initial stale threshold: three times the learned expected interval. This default requires validation on real installations.
- Profiles survive restarts and are discarded when entities are removed from the selected list.
- Learning is local and deterministic; no external AI service is required.
- Reset with `ha_health_monitor.reset_freshness_learning`; provide `entity_id` for one selected entity or omit it for all selected profiles.

## Known limitations

- Freshness monitoring is disabled by default.
- `unknown` is not treated as `unavailable`.
- Entity unavailability does not prove that a physical device is offline.
- Automated tests have been added, but CI execution and real HA OS validation are still pending.
- Integration setup failures, automation traces, incident correlation, durable incident history, explainable 0–100 score and the companion Lovelace card are not implemented yet.

## Installation (development)

1. Copy `custom_components/ha_health_monitor` into `config/custom_components/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **HA Health Monitor**.

HACS distribution is not yet a validated stable release.

## Configuration

Open the integration's **Configure** options:
- Scan interval (1–60 minutes; default 5).
- Entities to exclude.
- Enable adaptive freshness monitoring.
- Select entities to learn and monitor.

Only select entities expected to report regularly. Static, event-driven and battery-powered entities may not be suitable.

## Entities

- `sensor.ha_health_monitor_unavailable_entities`
- `sensor.ha_health_monitor_stale_entities`
- `sensor.ha_health_monitor_last_scan`
- `binary_sensor.ha_health_monitor_system_has_issues`

The stale entities sensor exposes selected profiles, learning state, sample count and expected cadence.

## Services

- `ha_health_monitor.scan_now`: run an immediate scan.
- `ha_health_monitor.reset_freshness_learning`: reset one selected entity (optional `entity_id`) or all selected profiles.

## Privacy

All monitoring runs locally inside Home Assistant. No entity states or diagnostics are sent to external services.

## Product principles

Real diagnostic usefulness, a polished interface, graphical configuration, an original Hybrid Lovelace card, and internationalization from the beginning (English and Spanish initially).

See [Product pillars](docs/PRODUCT_PILLARS.md), [Architecture](docs/ARCHITECTURE.md), [UI prototype](docs/UI_PROTOTYPE.md) and [Roadmap](docs/ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).
