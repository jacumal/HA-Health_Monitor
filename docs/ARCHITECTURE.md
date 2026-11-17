# Technical architecture

## Status
Design baseline, not a claim that the whole product is complete.

## Freshness monitor — implemented flow and confirmed decisions

- Only explicitly selected entities are eligible for observation, learning and stale detection. Globally excluded entities are also excluded from freshness.
- The coordinator subscribes to both state_changed and state_reported for selected entity IDs only. Changed states use last_updated; unchanged reports use the state_reported event's last_reported timestamp. This captures same-value reports without listening globally or relying on periodic polling.
- At startup, a new profile is seeded with the current last_reported timestamp. Startup itself is never counted as an interval.
- Five valid intervals are required before the entity becomes monitorable. There is no fixed learning window.
- Initial cadence is the median of the first five valid intervals. Thereafter, a bounded exponential moving average (alpha 0.2) adapts gradually; an individual interval is clamped to 0.5x–2x the current estimate.
- Gaps over 30 days reset the timestamp baseline but do not contaminate cadence estimation. Non-increasing and timezone-naive timestamps are ignored.
- The initial stale threshold is three times the learned interval. This is an engineering default to validate against real installations, not a universal guarantee.
- Profiles are persisted locally with Home Assistant's Store helper, restored on startup, coalesced after event bursts and flushed on unload. The integration never accesses the internal .storage files directly.
- The stale-entities sensor exposes per-entity learning/monitoring status, valid sample count, expected interval and threshold. Learning entities are neither stale nor considered healthy.
- Service ha_health_monitor.reset_freshness_learning: supply one selected entity_id to reset one profile; omit it to reset all selected profiles. Reset seeds a fresh baseline from the current state and returns the profile to learning.
- Removing an entity from the selected list prunes its profile. Disabling freshness stops event collection but preserves learned profiles for a later re-enable.
- Learning is deterministic and local; no external AI/LLM is needed.

## Other architectural requirements

- Availability must distinguish unknown from unavailable and must not infer that an unavailable entity proves a physical device is offline.
- Integration and automation monitoring must use supported Home Assistant interfaces, not private storage files or undocumented APIs.
- Incidents must separate observations, inferences and hypotheses and avoid duplicate penalties.
- The health score must be calculated in the backend and explain every deduction with a rule and issue reference. Insufficient coverage must not be presented as healthy.
- Persistence must use Home Assistant storage helpers; event listeners and coordinator updates should avoid excessive polling.
- English is the canonical translation source and Spanish ships from the beginning. All visible strings must be translated.
- The Lovelace frontend remains a separate Hybrid overview + module-card package, with visual configuration and no mandatory YAML.

See Product pillars, Roadmap and UI prototype.
