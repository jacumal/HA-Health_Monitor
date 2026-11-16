# UI prototype specification

## Purpose
Define the user experience before frontend implementation. All example metrics are fictitious and must never be represented as live data.

## Confirmed direction

### Hybrid visual identity
- Apple-inspired information hierarchy, readable typography, generous spacing, restrained status colors, subtle surfaces and considered light/dark themes.
- Bubble-inspired interaction patterns: rounded modules, compact submodules, progressive disclosure, popups and contextual navigation.
- Original visual language: do not copy Bubble Card assets/code and do not depend on Bubble Card.

### Both card organizations
- Main overview card for overall system health.
- Independent cards for each monitoring domain.
- Shared data contract and visual tokens; never duplicate monitor calculations.

## 1. Overview
Header:
- Product mark and “HA Health Monitor”.
- Subtitle “System observability · Home Assistant”.
- Monitoring state: Monitoring / Paused / Setup required.

Health summary:
- Score (0–100) and status label.
- Last successful scan.
- Coverage/confidence beside score.
- Never show score without status and data-coverage context.

Domain tiles:
- Unavailable entities.
- Stale sensors.
- Integration errors.
- Automation issues.

Recent incidents:
- Highest-priority active incidents.
- Severity, concise title, affected area/entity and elapsed time.
- Selecting an item opens its detail.

Footer/actions:
- Monitoring state and last scan.
- Manual scan action.
- Optional link to incident centre.

## 2. Independent module cards
Each module can be added separately using the visual editor:
- Availability.
- Freshness.
- Integrations.
- Automations.
- Incidents.
- Health score/trend.

Support compact and expanded density where relevant. Provide meaningful empty, loading, unsupported-data and integration-missing states.

## 3. Incident detail
Default proposed interaction: popup/overlay from selected incident.
1. Title and severity.
2. What was observed (facts, timestamps, source).
3. What is inferred (clearly marked correlation).
4. Possible causes (explicit hypotheses).
5. Recommended checks/actions.
6. First detected, last seen, duration and lifecycle.
7. Acknowledge/dismiss action, with clear semantics.

Never call a diagnosis confirmed unless evidence supports it. Recommendations are non-destructive; no automatic repair.

## 4. Navigation prototype
Three conceptual views:
- Overview: global score, domain tiles, latest incidents and coverage.
- Modules: detail summaries for each monitoring engine.
- Incidents: issue list and selected explanation.

Production Lovelace implementation should use native card configuration and accessible overlay/navigation patterns, not assume a standalone app route.

## 5. Sample data only
The initial concept uses:
- Score 94/100.
- 0 unavailable entities.
- 3 stale sensors.
- 0 integration errors.
- 0 automation issues.
- One fictitious delayed temperature sensor.

Every preview must be labelled sample data. The production card must never fall back to sample values when integration data is absent.

## 6. Visual system
- Prefer Home Assistant theme variables.
- Light/dark theme support.
- Pair semantic status colors with text/icons.
- Maintain contrast and touch target sizes.
- Restrained borders/surfaces; avoid excessive shadows/gradients.
- Readable typography and layouts suitable for narrow screens.
- Compact/expanded options and user-configurable sections.

## 7. Visual editor
Allow:
- selecting overview or module card;
- choosing displayed sections;
- compact/expanded density;
- toggling recent incidents and coverage;
- choosing incident count;
- selecting module and optional entity/domain filters.

Defaults should be useful immediately. Advanced settings can be collapsible. YAML is an optional escape hatch, never the primary setup path.

## 8. Prototype acceptance criteria
- Overall health is understandable at a glance.
- User can identify which subsystem needs attention.
- Incident details distinguish observation, inference and hypothesis.
- Handle no incidents, missing data, partial coverage and setup-required states.
- Overview and independent modules feel like one product.
- Works on mobile/desktop and light/dark themes.
- Mockup values are always clearly marked as sample data.
