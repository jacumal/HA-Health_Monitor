# Roadmap

## Product acceptance gate — applies to every phase

All work must preserve the five non-negotiable pillars: real usefulness, easy and pleasant interface, easy graphical configuration, a first-class Hybrid Lovelace card, and multilingual support. See [Product pillars](PRODUCT_PILLARS.md).

## Phase 0 — Product definition and prototype
- [x] Confirm Hybrid visual direction and overview + independent module cards.
- [x] Define UI-first setup, architecture, product pillars and internationalization.
- [ ] Review interaction prototype before frontend implementation.

## Phase 1 — Backend foundation
- [x] Integration skeleton, Config Flow / Options Flow and translation catalogs.
- [x] Freshness adaptive learning core.
- [x] Selected-entity state event collection.
- [x] Per-entry profile persistence using Home Assistant Store.
- [x] Manual per-entity and global reset service.
- [x] Learning and monitoring status exposed in sensor attributes.
- [ ] Execute CI successfully and validate on a real HA OS installation.

## Phase 2 — Core monitoring
- [ ] Availability monitor hardening.
- [x] Freshness adaptive learning flow (real-installation validation pending).
- [ ] Integration monitor using supported HA signals.
- [ ] Automation monitor with documented capabilities/limits.
- [ ] Incident lifecycle, grouping and correlation.
- [ ] Explainable score and confidence/coverage calculation.
- [ ] Actionable, evidence-grounded remediation guidance.

## Phase 3 — Lovelace frontend
- [ ] Companion repository/package.
- [ ] Hybrid overview and independent module cards.
- [ ] Score explanation, issue details and visual editor.
- [ ] English and Spanish parity, responsive light/dark themes and accessibility.

## Phase 4 — Real-world validation
- [ ] Test on a real HA OS installation.
- [ ] Validate Zigbee, Shelly, Netatmo, ESPHome and other common integrations.
- [ ] Tune false-positive handling, cadence learning and threshold.
- [ ] Validate privacy, performance and HACS packaging.

## Release principle
Do not advertise a monitoring domain as complete until it has reliable signal sources, automated tests, real-installation validation, translation coverage and meets all five product pillars.
