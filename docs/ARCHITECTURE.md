# Technical architecture

## Current implementation status

HA Health Monitor is in early development, not a stable release. The backend currently connects four monitor domains (availability, freshness, integrations and automations) to a deterministic incident lifecycle, explicit-key incident grouping, bounded persistence and a coverage-aware Health Score.

The integration is local-first. It does not send entity states or diagnostics to external services, and it never changes the user's Home Assistant configuration automatically.

## Monitor domains

### Availability

- Scans Home Assistant states and reports entities that remain `unavailable` beyond a two-minute grace period.
- `unknown` is not treated as unavailable.
- Globally excluded entities are not eligible.
- An unavailable entity is a symptom, not proof of physical device failure.

### Freshness

- Only explicitly selected `sensor` and `binary_sensor` entities are eligible; global exclusions apply.
- The coordinator subscribes only to selected entity IDs using Home Assistant state-change and state-report events.
- Changed states use `last_updated`; unchanged reports use `last_reported`.
- Startup seeds a baseline but is never counted as a sample.
- Five valid intervals are required. Initial cadence is the median of those intervals.
- During initial learning and after training, extreme gaps/outliers are rejected as cadence samples; the last-report baseline still advances so learning can recover.
- After training, a bounded exponential moving average (alpha 0.2) adapts gradually. Individual intervals are clamped to 0.5x–2x the current estimate.
- Intervals over 30 days are not cadence samples. Non-increasing and timezone-naive timestamps are ignored.
- Initial stale threshold is three times learned cadence. The graphical global multiplier (1.5x–10x, default 3x) provides manual sensitivity adjustment.
- Profiles are persisted with Home Assistant Store, restored on startup, coalesced after event bursts and flushed on unload.
- Learning profiles are not flagged stale. Missing and paused entities do not contribute Freshness coverage.
- Manual reset supports one configured entity or all configured profiles. Removing an entity from selection prunes its profile. Disabling Freshness suspends event collection while preserving profiles.
- Learning is local and deterministic; no external AI/LLM is required.

### Integration monitor

- Uses public ConfigEntry state information.
- Persistent failure rules: `setup_error` → `integration.setup_failed`; `migration_error` → `integration.migration_failed`; `failed_unload` → `integration.unload_failed`.
- Transitional states (`setup_retry`, `setup_in_progress`, `unload_in_progress`) are counted separately and do not become failures.
- `loaded` and `not_loaded` are assessed neutrally; an intentionally unloaded entry is not automatically unhealthy.
- The monitor does not inspect private integration internals or claim to identify the physical root cause.

### Automation monitor

- Scans `automation.*` states and respects global exclusions.
- `on` and `off` are assessed states; an automation turned off by the user is not a failure.
- `unavailable` is reported only after the two-minute grace period.
- `unknown` is not treated as a fault and remains outside assessed coverage.
- It does not inspect traces, invalid triggers, broken references, never-run automations or execution quality. Those are explicit future capabilities, not current guarantees.

## Incident lifecycle and grouping

- Each monitor finding becomes a stable, language-independent issue ID based on rule and target.
- Repeated scans update one active incident rather than creating duplicates.
- When a finding disappears, the incident moves to resolved history. A later recurrence starts a new occurrence.
- Freshness skips unknown/unavailable entities to avoid duplicate symptom penalties.
- Restored history is normalized before use: IDs, categories, statuses, severities, timestamps and chronology are checked; malformed records are discarded.
- Duplicate persisted IDs are reconciled deterministically using the latest lifecycle timestamp.
- History is bounded to 500 records.
- Incidents can be grouped by explicit correlation keys. Grouping does not merge lifecycle records and does not infer root causes. Root-cause analysis and acknowledgement are future work.

## Health Score and coverage

The backend calculates one score snapshot for all domains. Current category weights:

| Category | Weight |
|---|---:|
| Availability | 30 |
| Freshness | 20 |
| Integrations | 25 |
| Automations | 25 |

- Freshness is disabled by default. When disabled, it is excluded from the enabled-weight denominator.
- An enabled category with zero eligible items has zero coverage and is marked not assessed; an empty domain must not create artificial full coverage.
- Coverage is the assessed share of enabled category weight.
- The score is normalized over assessed possible points, independently of coverage. A score of 100 with partial coverage therefore means the assessed scope has no deductions, not that the whole installation has been certified healthy.
- Each category reports weight, coverage, possible/earned points, deductions, contributing issue IDs and rule IDs.
- Errors deduct more points than warnings. Category deductions are capped; current per-finding bases are 6 availability, 4 freshness, 10 integrations and 8 automations, with warnings at half the error value.
- Incident intelligence is cross-cutting and does not apply a second score penalty.
- Weights, caps, status thresholds and recovery semantics remain subject to real-installation validation before release.

## Persistence and lifecycle

- Freshness profiles and incident history use separate versioned Home Assistant Store instances scoped to the config entry.
- Startup restores and sanitizes both datasets. Freshness profiles for entities no longer selected are pruned; disabling Freshness preserves configured profiles.
- Event-driven Freshness writes and scan-driven incident writes are coalesced with delayed saves.
- Coordinator shutdown removes both state listeners and explicitly saves current Freshness and incident state.
- The integration calls coordinator shutdown after successful platform unload and when initial setup/first refresh fails.
- Options changes reload the config entry so subscriptions reflect the new selection.
- No direct access to Home Assistant's internal storage files is used.

## Lovelace frontend distribution

The planned Hybrid Lovelace card will be bundled inside this repository under the integration's `www/` directory, following the distribution pattern used by the AEMET Alertas integration:

- Static files are served from the integration package.
- The integration registers the module resource with Home Assistant Lovelace when available.
- The card is installed and updated together with the integration; no companion repository is required.
- The card consumes integration entities/coordinator attributes and does not duplicate monitor logic.
- The UI direction is an overview plus independent modules, with explanatory score/coverage, issue details and a visual editor.
- It will be original code, with no Bubble Card dependency or copied third-party assets.

Frontend implementation is deliberately gated on backend tests and documentation being aligned.

## Internationalization and privacy

- English is canonical; English and Spanish ship from the beginning.
- User-facing config flow, options, entity names and services are translated.
- IDs, rule IDs, service IDs and enums are language-neutral.
- Diagnostics redact secret-bearing keys; no telemetry is sent externally.

## Remaining work

- Add incident acknowledgement and evidence-grounded remediation guidance.
- Extend automation diagnostics to supported trace and reference signals, with honest coverage.
- Validate score thresholds and false-positive rates against real HA OS installations.
- Build the bundled Hybrid Lovelace overview/modules, visual editor, locale parity, accessibility and responsive light/dark themes.
- Validate install, reload, unload and persistence on real HA OS.
- Complete HACS packaging, migration strategy and release documentation.

See [PRODUCT_PILLARS.md](PRODUCT_PILLARS.md), [ROADMAP.md](ROADMAP.md) and [UI_PROTOTYPE.md](UI_PROTOTYPE.md).
