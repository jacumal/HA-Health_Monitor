# HA Health Monitor

**Know your Home Assistant. Before something breaks.**

Advanced observability and diagnostics for Home Assistant. Detect availability problems, stale entities, integration failures and automation issues; correlate symptoms; and explain incidents without silently changing the user's setup.

> Status: design and prototyping. Any metrics in mockups are illustrative, not live measurements.

## Product principles
1. Evidence-based diagnostics and useful alerts, not noise.
2. A polished, accessible and visually coherent interface.
3. Graphical setup by default; YAML is optional.
4. Safe by default: monitor, explain and recommend. Never modify devices or configuration without explicit user action.
5. Separate backend and frontend packages with a documented data contract.

## Confirmed product decisions
- **Visual direction: Hybrid.** Apple-inspired hierarchy, typography, spacing, restrained surfaces and accessibility, combined with modular interactive patterns inspired by Bubble Card. Original design; no copied implementation or runtime dependency.
- **Organization: Both.** One overview card plus independent module cards, all sharing the same data model and design system.
- **Configuration: UI-first.** Config Flow / Options Flow and a visual Lovelace card editor.
- **Incident detail:** facts, inferences and hypotheses must be clearly distinguished.
- **Safety:** no automatic repair or configuration mutation without explicit approval.

## Monitoring domains
- Availability: unavailable entities/devices, duration and recurrence.
- Freshness: entities not updating according to observed or configured cadence.
- Integrations: setup/load failures and supported diagnostic signals.
- Automations: execution problems using supported interfaces, with optional interoperability.
- Incident intelligence: grouping, correlation, severity and lifecycle.
- Health score: score, status, trend and confidence/coverage.

## Repository layout
This repository contains the Home Assistant backend and product documentation. The Lovelace frontend will be a separate companion package/repository: `ha-health-monitor-card`.

## Documentation
- [Technical architecture](docs/ARCHITECTURE.md)
- [UI prototype specification](docs/UI_PROTOTYPE.md)
- [Roadmap](docs/ROADMAP.md)

No runtime implementation is included yet. The first milestone is architecture and interaction validation before implementing monitoring engines.
