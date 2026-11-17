# HA Health Monitor

**Know your Home Assistant. Before something breaks.**

HA Health Monitor is an open-source Home Assistant integration for local observability and diagnostics. It is designed to detect meaningful problems, explain evidence and help users troubleshoot without silently changing their installation.

> **Requires Home Assistant 2024.11 or newer.**
>
> **Current status: early development (0.1.0).** The first installable foundation is available, but this is not a stable release and does not yet implement every planned monitoring engine or the Lovelace card.

## Current functionality (0.1.0)

- Graphical installation through Home Assistant Config Flow.
- Graphical options for scan interval and excluded entities.
- Availability scan for entities in the `unavailable` state.
- Optional freshness checks for explicitly selected entities only.
- Initial adaptive freshness learning engine (statistical core and unit tests); coordinator event collection, persistence, reset service and end-to-end HA validation are still pending.
- Sensors for unavailable entities, stale entities and last scan.
- A problem binary sensor.
- Manual scan service: `ha_health_monitor.scan_now`.
- Local diagnostics with sensitive configuration keys redacted.
- English and Spanish integration translations.

### Freshness learning decisions

- Only entities explicitly selected by the user are eligible for freshness learning.
- Initial learning is data-driven, not tied to a fixed number of hours or days. An entity needs at least five valid reporting intervals before its profile is ready.
- Once ready, the expected cadence adapts gradually; a single unusual interval cannot abruptly redefine the profile.
- Users will be able to reset an individual profile or all profiles manually.
- Learning is local, deterministic and does not require an external AI service.
- The initial stale threshold is three times the learned expected interval; this needs validation with real installations.

### Deliberate limitations

- `unknown` is not treated as `unavailable`.
- Entity unavailability is not presented as proof that a physical device is offline.
- Freshness monitoring is disabled by default. The adaptive learner core is implemented, but is not yet connected to Home Assistant event collection or persistent storage; adaptive freshness alerts are therefore not yet available end-to-end.
- Integration setup failures, automation traces, incident correlation, durable incident history and the explainable 0–100 score are not implemented yet.
- The custom Lovelace card is a separate planned package and is not included in this first backend milestone.

## Installation

### Manual installation (development)

1. Copy the `custom_components/ha_health_monitor` directory into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **HA Health Monitor** and complete the setup.

### HACS

The repository is being prepared for HACS distribution. Until a tagged release is published and validated through HACS, use the manual installation method above. You can add this repository as a custom integration in HACS for development/testing, but updates and compatibility are not yet guaranteed.

## Configuration

The initial setup has no required fields. After adding the integration, open its **Configure** options to set:

- Scan interval (1–60 minutes; default 5).
- Entities to exclude.
- Optional freshness monitoring.
- Entities to check for stale updates.
- Maximum allowed time without a state update (5–1440 minutes; default 60; fixed-threshold path pending replacement by the adaptive coordinator).

Only select entities that are expected to update regularly. Static, event-driven and battery-powered entities can otherwise produce false positives.

## Entities

The integration creates:

- `sensor.ha_health_monitor_unavailable_entities`
- `sensor.ha_health_monitor_stale_entities`
- `sensor.ha_health_monitor_last_scan`
- `binary_sensor.ha_health_monitor_system_has_issues`

Entity IDs are stable and language-independent. Exact entity IDs may be adjusted before the first stable release.

## Service

Run an immediate scan:

- Domain: `ha_health_monitor`
- Service: `scan_now`

## Privacy

All monitoring runs locally inside Home Assistant. The integration does not send entity states or diagnostics to external services. Diagnostic exports should still be reviewed before sharing.

## Development

The project follows five non-negotiable product pillars:

1. Real diagnostic usefulness and low false-positive rates.
2. A clear, polished and accessible interface.
3. Graphical configuration; YAML is never mandatory.
4. An original Hybrid Lovelace card (Apple-inspired clarity and modular Bubble-inspired interactions).
5. Internationalization from the beginning (English and Spanish initially).

See [Product pillars](docs/PRODUCT_PILLARS.md), [Architecture](docs/ARCHITECTURE.md), [UI prototype](docs/UI_PROTOTYPE.md) and [Roadmap](docs/ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).
