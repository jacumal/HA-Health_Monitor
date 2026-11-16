# HA Health Monitor

**Know your Home Assistant. Before something breaks.**

Advanced observability and diagnostics for Home Assistant. Detect availability problems, stale entities, integration failures and automation issues; correlate symptoms; and explain incidents without silently changing the user's setup.

> Status: design and prototyping. Any metrics in mockups are illustrative, not live measurements.

## Five non-negotiable product pillars

1. **Real usefulness:** detect real issues, avoid noise, explain why they matter, show why health points were lost and provide practical troubleshooting advice.
2. **Easy and pleasant interface:** polished, intuitive, responsive and accessible; concise summaries with deeper details on demand.
3. **Easy configuration:** graphical setup and sensible defaults. YAML is optional, never required for normal use.
4. **First-class Lovelace card:** an original Hybrid design combining Apple-inspired visual clarity with Bubble Card-inspired modular interactions.
5. **Internationalization:** multilingual from the start, with locale-aware presentation and an architecture ready for additional languages.

These are acceptance criteria for every feature and release. See [Product pillars](docs/PRODUCT_PILLARS.md).

## Confirmed product decisions
- **Visual direction: Hybrid.** Apple-inspired hierarchy, typography, spacing, restrained surfaces and accessibility, combined with modular interactive patterns inspired by Bubble Card. Original design; no copied implementation or runtime dependency.
- **Organization: Both.** One overview card plus independent module cards, all sharing the same data model and design system.
- **Configuration: UI-first.** Config Flow / Options Flow and a visual Lovelace card editor.
- **Languages:** English (default/fallback) and Spanish for the initial release; further languages can be added through translation catalogs.
- **Health score:** prominent 0–100 score with a transparent explanation of why it is below 100, including category deductions and links to contributing issues.
- **Issues:** concise prioritized summary on the overview; selecting an issue opens detailed evidence, cause assessment and actionable, non-destructive troubleshooting advice.
- **Card editor:** graphical choices for compact/detailed layout, charts on/off and chart range, issue detail as inline expansion or popup, visible sections and issue count.
- **Incident detail:** facts, inferences and hypotheses must be clearly distinguished.
- **Safety:** no automatic repair or configuration mutation without explicit approval.

## Monitoring domains
- Availability: unavailable entities/devices, duration and recurrence.
- Freshness: entities not updating according to observed or configured cadence.
- Integrations: setup/load failures and supported diagnostic signals.
- Automations: execution problems using supported interfaces, with optional interoperability.
- Incident intelligence: grouping, correlation, severity and lifecycle.
- Health score: score, status, transparent deductions, trend and confidence/coverage.

## Repository layout
This repository contains the Home Assistant backend and product documentation. The Lovelace frontend will be a separate companion package/repository: `ha-health-monitor-card`.

## Documentation
- [Product pillars](docs/PRODUCT_PILLARS.md)
- [Technical architecture](docs/ARCHITECTURE.md)
- [UI prototype specification](docs/UI_PROTOTYPE.md)
- [Internationalization](docs/I18N.md)
- [Roadmap](docs/ROADMAP.md)

No runtime implementation is included yet. The first milestone is architecture and interaction validation before implementing monitoring engines.
