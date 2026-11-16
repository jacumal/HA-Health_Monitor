# Technical architecture

## Status
Design baseline, not a claim that implementation is complete.

## 1. Boundaries
1. **Home Assistant integration** (`custom_components/ha_health_monitor`): observes supported HA state/diagnostics, maintains incident history, calculates health, exposes entities/services.
2. **Lovelace frontend** (companion package): renders overview and independent module cards and consumes the documented entity/attribute contract.
3. **Home Assistant platform**: config entries, state machine, event bus, supported diagnostics/repairs interfaces and storage APIs.

Frontend and backend are independently packaged. The card must gracefully report missing or incompatible integration versions.

## 2. Monitoring engines

### Availability
- Track entity availability, duration and recurrence.
- Distinguish entity status from device-level status; do not infer every unavailable entity means a physical device is offline.
- Treat `unknown` separately from `unavailable`; suppress expected startup/transient states.
- Support domain/entity exclusions and per-entity overrides.

### Freshness
- Learn or configure expected update cadence.
- Detect deviations from an entity's normal/configured behavior; no single global timeout.
- Avoid false positives for event-driven, static, battery-powered and intentionally quiet entities.
- Initial baseline target: 24 hours, provisional and configurable.
- Expose confidence/coverage; insufficient history must not be presented as healthy.

### Integrations
- Use supported config-entry, setup and diagnostic surfaces.
- Detect failed setup/reload only where reliable signals are available.
- Never read internal `.storage` files or rely on undocumented private APIs.

### Automations
- Use supported signals and documented interfaces.
- Do not classify unmet conditions or skipped runs as execution failures.
- Evaluate interoperability with Automation Monitor (olli-dot-dev) rather than duplicating trace parsing or depending on private APIs.
- Be transparent where reliable traces are unavailable.

### Incident intelligence
- Group repeated symptoms and correlate only when evidence supports a common cause.
- Keep observations, inferred correlations and hypotheses separate.
- Lifecycle: detected, active, acknowledged/dismissed and resolved.
- Store timestamps, duration, severity, source monitor and safe diagnostic context.

### Health score and explainability
The score is user-facing and must be explainable down to the issues and scoring rules that produced it.
- Initial candidate category weights (subject to validation): availability 30%, freshness 25%, integrations 25%, automations 10%, active incidents 10%.
- Keep weights and scoring rules in one backend scoring model; do not duplicate score calculations in frontend code.
- Return category-level possible points, earned points, deductions and contributing issue IDs/rule identifiers.
- Each deduction must have a traceable reason and must be attributable to an observation/incident.
- Avoid double penalties when multiple monitors report symptoms from the same root incident.
- Include coverage/confidence and category assessment state. Insufficient telemetry/baseline must not be silently counted as healthy or grant full points.
- The frontend must show a “Why not 100?” breakdown and let the user navigate from a deduction to the contributing issue(s).
- Validate weights, caps, severity multipliers and recovery behavior with real installations before release. Candidate weights are not yet a final product promise.

## 3. Initial entities
- `sensor.ha_health_score`
- `sensor.ha_health_status`
- `sensor.ha_active_incidents`
- `sensor.ha_unavailable_entities`
- `sensor.ha_stale_entities`
- `sensor.ha_failed_integrations`
- `sensor.ha_automation_issues`
- `sensor.ha_last_scan`
- `binary_sensor.ha_system_healthy`

Count sensors expose structured summaries in attributes; do not create an entity per incident. The score entity should expose a structured breakdown (category weights, possible/earned points, deductions, coverage and contributing incident references) using a stable, documented schema.

Proposed services:
- `health_monitor.scan_now`
- `health_monitor.dismiss_incident`
- `health_monitor.reset_history`

Service schemas and destructive-action protections are implementation tasks. History reset requires explicit user action.

## 4. Persistence and update model
- Use supported Home Assistant storage APIs for durable history.
- Use coordinator patterns for shared calculated data and efficient entity updates.
- Use state/event listeners where appropriate; avoid excessive whole-state polling.
- Separate scheduled scans, event-driven checks and manual scans.
- Bound history and version the storage schema.
- Never access `.storage` directly.

## 5. Configuration experience
Config Flow defaults should make first install useful without a long questionnaire. Options Flow exposes:
- monitored domains and entity exclusions;
- sensitivity and baseline controls;
- per-entity freshness overrides;
- incident retention and notification preferences;
- optional supported automation-monitor interoperability.

Use Home Assistant selectors where available. YAML is never mandatory.

## 6. Diagnostics and privacy
- Provide exportable diagnostics with relevant entity metadata.
- Redact tokens, credentials, secret-bearing URLs and sensitive values.
- Explain included diagnostic data before export.
- No external data transmission.

## 7. Frontend architecture
Companion package: `ha-health-monitor-card`.
- One overview card and independent module cards.
- Shared components, tokens, icons, localization and data adapter.
- Visual editor with explicit compact/detailed layout, charts on/off, chart time range, issue detail mode (inline expansion or popup), visible sections, issue count and module/entity filters.
- Score breakdown UI with “Why not 100?” and clickable deductions linking to the contributing issue details.
- Issue summaries are visible on the overview; full diagnosis and safe remediation guidance are available on selection.
- Keep facts, inferences and hypotheses visually distinct.
- Light/dark theme using HA theme variables and standard `ha-card` integration.
- Responsive mobile/tablet/desktop behavior and accessible dialog/focus behavior.
- Avoid undocumented frontend internals where possible.
- No runtime dependency on Bubble Card, Mushroom or a CDN framework.

## 8. Proposed backend structure
```text
custom_components/ha_health_monitor/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  coordinator.py
  models.py
  scoring.py
  incident_engine.py
  diagnostics.py
  sensor.py
  binary_sensor.py
  services.yaml
  strings.json
  translations/{en,es}.json
  monitors/{__init__,availability,freshness,integrations,automations}.py
tests/
  test_config_flow.py
  test_availability.py
  test_freshness.py
  test_integrations.py
  test_incidents.py
  test_scoring.py
.github/workflows/validate.yaml
hacs.json
pyproject.toml
README.md
LICENSE
CONTRIBUTING.md
CHANGELOG.md
```
This layout may evolve with implementation.

## 9. Quality gates
- Unit tests for each monitor and incident transitions.
- Startup/shutdown, unknown/unavailable transitions and history restoration.
- Entities with no stable update cadence.
- Partial coverage and score confidence.
- Score deductions trace to rule IDs and issue IDs; correlated symptoms are not double-counted.
- Tests for unassessed categories, score explanation and recovery after issue resolution.
- Static checks, formatting and HA integration validation in CI.
- Manual validation on real HA OS before release.
