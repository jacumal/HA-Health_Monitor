# Roadmap

## Phase 0 — Product definition and prototype
- [x] Confirm Hybrid visual direction.
- [x] Confirm Both card organization (overview + independent modules).
- [x] Record UI-first setup and no mandatory YAML.
- [x] Define architecture and UI prototype specification.
- [ ] Review and validate prototype interactions.

## Phase 1 — Backend foundation
- [ ] Integration skeleton and manifest.
- [ ] Config Flow / Options Flow with useful defaults.
- [ ] Typed models for observations, incidents and coverage.
- [ ] Persistence and coordinator lifecycle.
- [ ] CI and unit-test foundation.

## Phase 2 — Core monitoring
- [ ] Availability monitor.
- [ ] Freshness monitor and baseline handling.
- [ ] Integration monitor using supported HA signals.
- [ ] Automation monitor with documented capabilities/limits.
- [ ] Incident lifecycle, grouping and correlation.
- [ ] Score and confidence/coverage calculation.

## Phase 3 — Lovelace frontend
- [ ] Companion repository/package.
- [ ] Shared design tokens and components.
- [ ] Overview card.
- [ ] Independent module cards.
- [ ] Incident popup/detail.
- [ ] Visual card editor.
- [ ] Responsive light/dark themes and accessibility review.

## Phase 4 — Real-world validation
- [ ] Test on a real HA OS installation.
- [ ] Validate Zigbee, Shelly, Netatmo, ESPHome and other common integrations.
- [ ] Tune false-positive handling and baseline learning.
- [ ] Validate diagnostics privacy and performance.
- [ ] Prepare HACS packaging and release docs.

## Release principle
Do not advertise a monitoring domain as complete until it has reliable signal sources, documented limitations, automated tests and real-installation validation.
