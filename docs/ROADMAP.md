# Roadmap

## Product acceptance gate

Every phase must preserve the five non-negotiable pillars: real diagnostic usefulness, easy and polished UI, graphical configuration, first-class Hybrid Lovelace cards, and internationalization. See PRODUCT_PILLARS.md.

## Phase 0 — Product definition
- [x] Confirm Hybrid visual direction and overview + independent module cards.
- [x] Define UI-first setup, product pillars and English/Spanish internationalization.
- [ ] Review interaction prototype before frontend implementation.

## Phase 1 — Backend foundations
- [x] Integration skeleton, Config Flow / Options Flow and translations.
- [x] Availability monitor with grace period and exclusions.
- [x] Adaptive freshness with selected-entity event subscriptions.
- [x] Persistent profiles, outlier-resistant learning and manual reset.
- [x] Stable incident IDs and active/resolved lifecycle.
- [x] Initial coverage-aware score with traceable deductions.
- [ ] CI green, full regression coverage and real HA OS validation.

## Phase 2 — Complete monitoring and diagnostics
- [ ] Integration monitor using supported config-entry signals.
- [ ] Automation monitor with honest coverage and documented limitations.
- [ ] Incident correlation, acknowledgement and lifecycle controls.
- [ ] Evidence-grounded remediation guidance.
- [ ] Validate score weights, thresholds, recovery and coverage semantics.
- [ ] Add comprehensive coordinator, storage, lifecycle and event tests.

## Phase 3 — Lovelace frontend
- [ ] Companion repository/package.
- [ ] Hybrid overview and independent module cards.
- [ ] Score explanation, issue detail and visual editor.
- [ ] English/Spanish parity, responsive light/dark themes and accessibility.

## Phase 4 — Release readiness
- [ ] Real HA OS validation after backend and CI gates are complete.
- [ ] Validate Zigbee, Shelly, Netatmo, ESPHome and other common integrations.
- [ ] Tune false positives, thresholds, privacy and performance.
- [ ] HACS packaging, migration strategy and release documentation.

## Release principle
No monitor is complete until it has reliable signal sources, automated tests, real-installation validation, translated user-facing strings and meets all five product pillars.
