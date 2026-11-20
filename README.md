# HA Health Monitor

**Know your Home Assistant. Before something breaks.**

HA Health Monitor is an open-source Home Assistant integration for local observability and diagnostics. It detects meaningful problems, explains the evidence and helps users troubleshoot without silently changing their installation.

> Requires Home Assistant 2024.11 or newer.
>
> **Development status:** early development (0.1.0). The four backend monitor domains, incident lifecycle, bounded persistence and coverage-aware Health Score are implemented and covered by automated CI. The first bundled Hybrid Lovelace card is implemented; CI and real-installation validation are in progress. This is not yet a stable release.

## Implemented backend

- Graphical installation and options through Home Assistant.
- Availability monitoring with a two-minute grace period and entity exclusions.
- Adaptive freshness monitoring for explicitly selected sensors and binary sensors.
- Learning from changed states and unchanged state reports.
- Five valid reporting intervals before stale detection.
- Median-based initial cadence, outlier rejection and gradual adaptation.
- Per-entity learning/monitoring state, sample count, expected cadence and stale threshold.
- Manual reset of one profile or all configured profiles.
- Integration setup monitoring using public ConfigEntry states.
- Automation state monitoring for enabled, disabled and persistently unavailable automations.
- Stable incident IDs, active/resolved lifecycle and bounded history.
- Deterministic grouping by explicit correlation keys.
- Explainable Health Score with category coverage, point breakdown and incident-linked deductions.
- English and Spanish integration translations.

## Monitoring behavior

### Availability

- Reports entities that remain `unavailable` for at least two minutes.
- `unknown` is not treated as unavailable.
- Excluded entities are not assessed.
- An unavailable entity is not, by itself, proof that a physical device is offline.

### Freshness

- Only explicitly selected sensor and binary sensor entities are observed.
- Changed values and same-value reports are captured using filtered Home Assistant state events.
- Startup seeds a baseline but never counts as a reporting interval.
- Five valid intervals are required before an entity is monitored for staleness.
- Initial cadence is the median of the first five valid intervals.
- Extreme intervals are rejected so temporary outages do not poison cadence learning.
- Once trained, cadence adapts gradually using a bounded exponential moving average.
- Initial stale threshold is three times learned cadence. The graphical tolerance multiplier can be tuned from 1.5x to 10x.
- Profiles survive restarts. Entities removed from the selected list are pruned.
- Disabling Freshness suspends event collection while preserving profiles.
- Learning is local and deterministic; no external AI service is required.

### Integrations

- Detects persistent `setup_error`, `migration_error` and `failed_unload` ConfigEntry states.
- Treats setup retry/in-progress and unload-in-progress as transitional rather than failures.
- A deliberately unloaded integration (`not_loaded`) is neutral.
- This monitor uses supported Home Assistant ConfigEntry state information; it does not inspect integration internals.

### Automations

- Evaluates `automation.*` entities, excluding configured exclusions.
- Both `on` and `off` are valid assessed states; an automation disabled by the user is not a fault.
- Reports `unavailable` automations only after the two-minute grace period.
- It does **not** inspect traces, invalid triggers, broken entity references, never-run automations or execution quality. These remain future work.

## Incidents and Health Score

Monitor findings become stable, language-independent issue IDs. Repeated scans update the same active incident; resolved incidents remain in bounded history, and a later recurrence starts a new occurrence.

Incidents can be grouped by explicit correlation keys. This is deterministic grouping, **not inferred root-cause analysis**. The monitor does not automatically modify Home Assistant or apply remediation.

The current score weights are:

| Category | Weight |
|---|---:|
| Availability | 30 |
| Freshness | 20 |
| Integrations | 25 |
| Automations | 25 |

Freshness is disabled by default and is excluded from the score denominator while disabled. Enabled categories with no eligible items have zero coverage, not artificial full coverage. The score is normalized over assessed points, while the separate coverage percentage communicates how much of the enabled monitoring scope has actually been assessed.

Errors deduct more points than warnings. Deductions are capped within each category and linked to their originating issue IDs. The score and weights remain subject to validation on real Home Assistant installations before release.

## Persistence and privacy

- Freshness profiles and incident history use versioned Home Assistant Store instances.
- Restored data is validated before entering the live coordinator.
- Incident history is bounded to 500 records.
- Event-driven writes are coalesced; current state is flushed on unload.
- No entity states or diagnostics are sent to external services.

## Current limitations

- Freshness monitoring is disabled by default and requires explicit entity selection.
- Static, event-driven and irregularly reporting entities may not be suitable for cadence learning.
- Automation trace analysis and deeper automation diagnostics are not implemented.
- Correlation is explicit-key grouping, not root-cause inference.
- Acknowledgements, guided remediation and automatic verification of fixes are not implemented.
- The first Hybrid Lovelace card is bundled **inside this same repository and integration**. Its initial version provides overview and module views, score breakdown, issue details, a visual editor, responsive styling and English/Spanish UI strings.
- Historical charts, richer evidence-backed recommendations and deeper diagnosis views are not exposed yet because the backend does not currently provide the required history/diagnostic data.
- Real HA OS validation, interaction/accessibility review and release/HACS readiness are still pending.

## Installation (development)

1. Copy `custom_components/ha_health_monitor` into `config/custom_components/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **HA Health Monitor**.

HACS packaging may be used for development testing, but a stable release has not yet been validated.

## Configuration

Open the integration's **Configure** options:

- Scan interval (1–60 minutes; default 5).
- Entities to exclude.
- Enable or disable adaptive Freshness monitoring.
- Select entities to learn and monitor.
- Set the Freshness tolerance multiplier (1.5x–10x).

Only select entities expected to report regularly. Static, event-driven and battery-powered entities may not be suitable.

## Entities

- `sensor.ha_health_monitor_health_score`
- `sensor.ha_health_monitor_health_status`
- `sensor.ha_health_monitor_active_incidents`
- `sensor.ha_health_monitor_incident_history`
- `sensor.ha_health_monitor_unavailable_entities`
- `sensor.ha_health_monitor_stale_entities`
- `sensor.ha_health_monitor_failed_integrations`
- `sensor.ha_health_monitor_unavailable_automations`
- `sensor.ha_health_monitor_last_scan`
- `binary_sensor.ha_health_monitor_system_has_issues`

The score sensor exposes coverage, status, category breakdown and traceable deductions. The incidents sensor exposes active incidents and correlation groups; the history sensor exposes the latest 50 historical records. The stale sensor exposes per-entity learning status and cadence. The integration and automation sensors expose their respective assessment counts and findings.

## Statistics

The integration exposes numeric measurement entities (health score, active incidents, unavailable entities, stale entities, failed integrations and unavailable automations) with Home Assistant measurement state classes where applicable. Home Assistant Recorder/statistics settings determine the retention and availability of historical graphs. The incident history entity is a bounded current snapshot (up to 50 records in its attributes), not a time-series event warehouse; historical incident analysis beyond that snapshot remains future work.

## Services

- `ha_health_monitor.scan_now`: run an immediate scan.
- `ha_health_monitor.reset_freshness_learning`: reset one selected entity (optional `entity_id`) or all selected profiles.
- `ha_health_monitor.set_integration_availability_profile`: pause availability and freshness findings for all enabled entities belonging to one integration config entry while a reference entity reports one of the explicitly configured inactive states. Set `config_entry_id`, `reference_entity` and comma-separated `inactive_states`; set `remove: true` with only the config entry ID to remove the profile. Missing, unknown and unavailable reference states fail open (normal monitoring).

## Product direction

The product is being built around five pillars: reliable diagnostics, a polished responsive interface, UI-first configuration, an original Hybrid Lovelace card and internationalization from the beginning (English and Spanish initially).

The first card version ships with the integration in this repository. It provides an overview plus independent module views, score explanation, issue details and a visual editor. The design combines Apple-inspired visual hierarchy with Bubble Card-inspired modular interactions, without depending on Bubble Card or copying third-party code/assets.

See [PRODUCT_PILLARS.md](docs/PRODUCT_PILLARS.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), [UI_PROTOTYPE.md](docs/UI_PROTOTYPE.md) and [ROADMAP.md](docs/ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).
