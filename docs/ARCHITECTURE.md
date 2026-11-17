# Technical architecture

## Current implementation status

Early development backend foundation, not a stable release. The implemented path is availability + adaptive freshness → incident lifecycle → coverage-aware score. Integration and automation monitors, advanced correlation, remediation and frontend remain incomplete.

## Freshness monitor

- Only explicitly selected sensor and binary sensor entities are eligible for observation, learning and stale detection. Globally excluded entities are excluded too. Missing entities receive a missing profile state; unknown and unavailable entities are paused and do not contribute freshness coverage.
- The coordinator subscribes only to selected entity IDs using Home Assistant state-change and state-report events. Changed states use last_updated; unchanged reports use the state_reported event timestamp.
- Startup seeds a baseline but is never counted as a sample.
- Five valid intervals are required. Initial cadence is the median of those intervals.
- During initial learning and after training, extreme gaps/outliers are rejected as cadence samples; the last-report baseline still advances so learning can recover.
- After training, a bounded exponential moving average (alpha 0.2) adapts gradually. Individual intervals are clamped to 0.5x–2x the current estimate.
- Intervals over 30 days are not cadence samples. Non-increasing and timezone-naive timestamps are ignored.
- Initial stale threshold is three times learned cadence. A graphical global multiplier (1.5–10x, default 3x) provides the manual adjustment side of the hybrid model. Very large cadence changes are treated as outliers; users can reset the selected profile after intentional sensor reconfiguration.
- Profiles are persisted with Home Assistant Store, restored on startup, coalesced after event bursts and flushed on unload.
- The stale sensor exposes learning/monitoring state, sample count, expected interval and threshold. Learning entities are not flagged stale and do not contribute full freshness coverage.
- Manual service resets one selected profile or all selected profiles. Removing an entity from selection prunes its profile. Disabling freshness suspends event collection while preserving existing profiles.
- Learning is local and deterministic; no external AI/LLM is required.

## Availability monitor

- Reports entities that remain unavailable beyond a two-minute grace period.
- Unknown is not treated as unavailable.
- Entity unavailability is not proof that a physical device is offline.
- Excluded entities are not assessed.

## Incident lifecycle

- Each monitor finding becomes a stable, language-independent issue ID based on rule and entity.
- Repeated scans update one active incident rather than creating duplicates.
- Resolved findings remain in bounded history; a reappearing finding starts a new occurrence.
- Freshness skips unavailable/unknown entities to avoid duplicate symptom penalties.
- The current engine is deterministic and does not claim root-cause correlation. Correlation and acknowledgement remain future work.

## Health score and coverage

- Score is calculated once in the backend.
- Each category reports weight, assessed coverage, possible points, earned points, deductions, contributing issue IDs and rule IDs.
- Candidate weights are availability 30, freshness 25, integrations 25, automations 10 and incident intelligence 10. They remain provisional.
- Currently only availability and trained freshness profiles are assessed. Other categories remain explicitly unassessed and reduce overall coverage.
- A score can be 100 while coverage is partial; status must say partial and the frontend must show coverage and unassessed categories.
- Deductions are linked to incidents; multiple symptoms must not be penalized twice.
- Validate weights, caps, thresholds and recovery behavior against real installations before release.

## Persistence and lifecycle

- Freshness profiles and incident history use versioned Home Assistant Store instances; direct internal storage access is prohibited.
- Event listeners are filtered to selected entities and removed on unload.
- Event writes are coalesced. Incident history is bounded.
- Options changes reload the config entry so listeners match the new selection.

## Internationalization and privacy

- English is canonical; English and Spanish ship from the beginning.
- User-facing config flow, options, entity names and services are translated.
- IDs, rule IDs, service IDs and enums are language-neutral.
- Diagnostics redact secret-bearing keys and no telemetry is sent externally.

## Remaining product work

- Integration monitor using supported config-entry state.
- Automation monitor based only on reliable supported signals; no false claim of trace coverage.
- Root-cause correlation, acknowledgement and incident lifecycle UX.
- Evidence-grounded remediation.
- Complete score validation and expanded tests.
- Separate Hybrid Lovelace overview/module cards, visual editor, locale catalogs, accessibility and responsive light/dark themes.

See PRODUCT_PILLARS.md, ROADMAP.md and UI_PROTOTYPE.md.
