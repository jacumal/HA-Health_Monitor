# Roadmap

## Product acceptance gate

Every phase must preserve the five non-negotiable pillars: real diagnostic usefulness, polished and accessible UI, graphical configuration, a first-class Hybrid Lovelace card bundled with the integration, and internationalization. See [PRODUCT_PILLARS.md](PRODUCT_PILLARS.md).

## Phase 0 — Product definition

- [x] Confirm Hybrid visual direction and overview + independent module cards.
- [x] Define UI-first setup, product pillars and English/Spanish internationalization.
- [ ] Review and freeze the interaction prototype before frontend implementation.

## Phase 1 — Backend foundations

- [x] Integration skeleton, Config Flow / Options Flow and translations.
- [x] Availability monitor with grace period and exclusions.
- [x] Adaptive Freshness with selected-entity event subscriptions.
- [x] Persistent profiles, outlier-resistant learning and manual reset.
- [x] Stable incident IDs and active/resolved lifecycle.
- [x] Initial coverage-aware score with traceable deductions.
- [x] Integration monitor using supported ConfigEntry state signals.
- [x] Automation monitor with conservative state checks and documented limitations.
- [x] Deterministic incident grouping using explicit correlation keys.
- [x] Sanitize and bound restored incident history and Freshness profiles.
- [x] Automated CI: Ruff, JSON/manifest validation and regression tests.
- [x] Coordinator tests for restore, profile pruning, listener teardown and shutdown persistence.
- [ ] Real HA OS validation of startup, reload, unload and persistence.

## Phase 2 — Diagnostics and score hardening

- [ ] Validate score weights, caps, thresholds and recovery against real installations.
- [ ] Add incident acknowledgement and user-controlled lifecycle actions.
- [ ] Add evidence-grounded remediation guidance and post-fix verification.
- [ ] Extend automation diagnostics only where Home Assistant exposes reliable supported signals (traces, references and execution health).
- [ ] Validate false-positive behavior across common integrations and device classes.

## Phase 3 — Bundled Hybrid Lovelace frontend

The card is part of this repository and integration. It will not be a separate companion package.

- [ ] Review and freeze the interaction prototype.
- [ ] Add the integration-bundled `www/` assets and frontend resource registration.
- [ ] Build the Hybrid overview card and independent monitor modules.
- [ ] Explain Health Score, coverage, category breakdown and deductions.
- [ ] Add incident list, detail view, correlation groups and resolution guidance.
- [ ] Add a graphical card editor with compact/detailed display modes and sensible defaults.
- [ ] Add period controls, charts, module filters and recent-issue views where useful.
- [ ] English/Spanish parity, responsive light/dark themes, keyboard support and accessibility.
- [ ] Frontend tests and validation on mobile, tablet and desktop dashboards.

## Phase 4 — Release readiness

- [ ] Validate installation, options, reload, unload and storage migration on real HA OS.
- [ ] Validate Zigbee, Shelly, Netatmo, ESPHome and other common integrations.
- [ ] Tune false positives, thresholds, privacy and performance.
- [ ] HACS packaging, versioning, migration strategy and release documentation.
- [ ] Publish a stable release only after backend and frontend acceptance gates pass.

## Release principle

No monitor or frontend module is complete until it has reliable signal sources, automated tests, real-installation validation, translated user-facing strings and meets all five product pillars. A green CI run is necessary, but it is not a substitute for real HA OS validation.
