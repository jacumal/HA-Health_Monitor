# HA Health Monitor

**Know your Home Assistant. Before something breaks.**

HA Health Monitor is an open-source Home Assistant integration for local observability and diagnostics. It detects meaningful problems, explains evidence and helps users troubleshoot without silently changing their installation.

> Requires Home Assistant 2024.11 or newer.
>
> Current status: early development (0.1.0). Availability and adaptive freshness are connected to a persistent incident lifecycle and a coverage-aware score. Other monitoring engines and the Lovelace card remain in development.

## Implemented backend foundation

- Graphical installation and options through Home Assistant.
- Availability scan for entities in the unavailable state, with a two-minute grace period.
- Adaptive freshness learning for explicitly selected entities, using filtered state-change and state-report events.
- Per-entity profiles persisted locally with Home Assistant Store.
- Five valid intervals before an entity becomes eligible for stale detection.
- Robust initial learning with median intervals and rejection of extreme outliers.
- Gradual cadence adaptation using a bounded exponential moving average.
- Per-entity learning/monitoring state, sample count, expected cadence and stale threshold.
- Manual reset of one profile or all selected profiles.
- Deterministic incident IDs, active/resolved lifecycle and bounded history.
- Preliminary explainable health score with per-category breakdown, rule-linked deductions and explicit coverage.
- English and Spanish integration translations.

## Freshness behavior

- Only explicitly selected sensor and binary sensor entities are observed.
- Changed values and same-value reports are both captured using Home Assistant's filtered state events.
- Startup seeds a baseline but never counts as a reporting interval.
- Each entity needs five valid intervals. There is no fixed learning window. Missing, unknown and unavailable entities are not counted as fully monitored.
- Initial cadence is the median of the first five intervals.
- Extreme intervals are ignored as cadence samples so temporary outages do not poison learning.
- Once ready, cadence adapts gradually; individual intervals are bounded to reduce outlier influence.
- Initial stale threshold: three times the learned cadence. This is an engineering default that still requires validation against real installations.
- Profiles survive restarts and are pruned when entities are removed from the selected list.
- Learning is local and deterministic; no external AI service is required.

## Score and incidents

The coordinator converts monitor findings into stable issue IDs and maintains active/resolved incident history. The score includes category-level possible/earned points, deductions linked to issue IDs and a coverage percentage.

The score is deliberately marked partial while integration monitoring, automation monitoring and incident intelligence are not fully implemented. A score of 100 with partial coverage does not certify the whole installation as healthy. Candidate weights and deduction sizes are provisional until validated on real installations.

## Current limitations

- Freshness monitoring is disabled by default and must be explicitly configured.
- Static or irregularly reporting entities are not suitable for cadence learning.
- Integration and automation monitors are not implemented yet.
- Incident correlation, acknowledgements and guided remediation are not complete.
- The companion Hybrid Lovelace card is a separate planned package.
- CI and real HA OS validation must pass before a stable release.

## Installation (development)

1. Copy custom_components/ha_health_monitor into config/custom_components/.
2. Restart Home Assistant.
3. Go to Settings → Devices & services → Add integration.
4. Search for HA Health Monitor.

HACS distribution is not yet a validated stable release.

## Configuration

Open the integration's Configure options:
- Scan interval (1–60 minutes; default 5).
- Entities to exclude.
- Enable adaptive freshness monitoring.
- Select entities to learn and monitor.

Only select entities expected to report regularly. Static, event-driven and battery-powered entities may not be suitable.

## Entities

- sensor.ha_health_monitor_health_score
- sensor.ha_health_monitor_active_incidents
- sensor.ha_health_monitor_unavailable_entities
- sensor.ha_health_monitor_stale_entities
- sensor.ha_health_monitor_last_scan
- binary_sensor.ha_health_monitor_system_has_issues

The score sensor exposes coverage, status, category breakdown and traceable deductions. The incidents sensor exposes active incidents. The stale sensor exposes per-entity learning status and cadence.

## Services

- ha_health_monitor.scan_now: run an immediate scan.
- ha_health_monitor.reset_freshness_learning: reset one selected entity (optional entity_id) or all selected profiles.

## Privacy

All monitoring runs locally inside Home Assistant. No entity states or diagnostics are sent to external services.

## Product principles

Real diagnostic usefulness, a polished interface, graphical configuration, an original Hybrid Lovelace card, and internationalization from the beginning (English and Spanish initially).

See docs/PRODUCT_PILLARS.md, docs/ARCHITECTURE.md, docs/UI_PROTOTYPE.md and docs/ROADMAP.md.

## License

MIT. See LICENSE.
