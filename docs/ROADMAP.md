# Roadmap

## Product acceptance gate — applies to every phase

All work must preserve the five non-negotiable pillars: real usefulness, easy and pleasant interface, easy graphical configuration, a first-class Hybrid Lovelace card, and multilingual support. See [Product pillars](PRODUCT_PILLARS.md). A feature is not complete merely because its backend works.

## Phase 0 — Product definition and prototype
- [x] Confirm Hybrid visual direction.
- [x] Confirm Both card organization (overview + independent modules).
- [x] Record UI-first setup and no mandatory YAML.
- [x] Define architecture and UI prototype specification.
- [x] Define product pillars and acceptance gate.
- [x] Add internationalization as a foundational requirement (English + Spanish initial locales).
- [ ] Review and validate prototype interactions and visual editor options.

## Phase 1 — Backend foundation
- [ ] Integration skeleton and manifest.
- [ ] Config Flow / Options Flow with useful defaults.
- [ ] Typed models for observations, incidents and coverage.
- [ ] Translation catalogs for English and Spanish from the first config-flow implementation.
- [ ] Persistence and coordinator lifecycle.
- [ ] CI and unit-test foundation, including translation validation.

## Phase 2 — Core monitoring
- [ ] Availability monitor.
- [ ] Freshness monitor and baseline handling.
- [ ] Integration monitor using supported HA signals.
- [ ] Automation monitor with documented capabilities/limits.
- [ ] Incident lifecycle, grouping and correlation.
- [ ] Explainable score and confidence/coverage calculation.
- [ ] Actionable, evidence-grounded remediation guidance.
- [ ] Localized issue explanations and recommendations in all shipped locales.

## Phase 3 — Lovelace frontend
- [ ] Companion repository/package.
- [ ] Shared Hybrid design tokens and components.
- [ ] Locale catalogs and locale-aware formatting in frontend foundation.
- [ ] Overview card with “Why not 100?” score explanation.
- [ ] Independent module cards.
- [ ] Prioritized issue summaries and detailed issue view.
- [ ] Visual card editor: compact/detailed, charts, time range, inline/popup, visible sections.
- [ ] Responsive light/dark themes and accessibility review.
- [ ] English and Spanish parity across every user-facing frontend string.

## Phase 4 — Real-world validation
- [ ] Test on a real HA OS installation.
- [ ] Validate Zigbee, Shelly, Netatmo, ESPHome and other common integrations.
- [ ] Tune false-positive handling and baseline learning.
- [ ] Validate diagnostics privacy and performance.
- [ ] Usability review: a normal user can install, configure and understand the dashboard without editing YAML.
- [ ] Review language fallback, date/number formatting and translation quality.
- [ ] Prepare HACS packaging and release docs.

## Release principle
Do not advertise a monitoring domain as complete until it has reliable signal sources, documented limitations, automated tests, real-installation validation, translation coverage for all shipped locales and meets all five product pillars.
