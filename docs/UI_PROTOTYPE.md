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

## 1. Overview card

### Header
- Product mark and “HA Health Monitor”.
- Subtitle “System observability · Home Assistant”.
- Monitoring state: Monitoring / Paused / Setup required.

### Health score: 0–100, with an explanation of every lost point
The score is a first-class element of the overview, not a decorative badge. The user must be able to answer: “Why is my installation not at 100?”

The score area must include:
- Current score (0–100) and a human-readable status.
- A visible “Why not 100?” / “Score breakdown” affordance.
- Category-level contribution and deduction, showing earned points against possible points.
- A list of the active issues responsible for deductions, with each issue's contribution clearly attributed.
- Coverage/confidence and last successful scan.
- A clear explanation when a category is not yet measurable because baseline or telemetry is insufficient.

The score engine must make deductions traceable and deterministic:
- Define category weights and scoring rules centrally in the backend.
- Every deduction must reference one or more concrete observations/incidents and a documented rule.
- Avoid double-penalizing the same underlying incident across correlated monitors.
- Show the maximum possible points, earned points and deduction for each category.
- If a category cannot be assessed, do not silently award full points. Surface reduced coverage/confidence and define how unavailable scoring weight is handled.
- Keep provisional weights configurable/subject to real-world validation; the UI must display the actual configured scoring model rather than hard-coded explanatory numbers.

Illustrative example only: 94/100 because freshness issues account for six lost points. In the real UI, the exact deduction must come from the scoring engine and be drillable to the contributing issues.

### Domain summary
- Unavailable entities.
- Stale sensors.
- Integration errors.
- Automation issues.
- Active incidents and monitoring coverage.

### Issue summary
Show a concise, prioritized list of issues on the overview. Each row/card should include:
- Severity and concise title.
- Affected entity/device/integration or automation.
- Short explanation of the symptom.
- Duration / first detected or last observed.
- Visible indication if the cause is confirmed, inferred or only a hypothesis.
- Tap/click affordance to open the issue detail.

Sort by severity and impact, with stable ordering to avoid items jumping around unnecessarily.

## 2. Issue detail and remediation guidance

Selecting an issue opens a detailed view. Preferred interaction is configurable in the card editor:
- Expand inline.
- Open an accessible popup/dialog.

The detail view should explain:
1. What happened: observed facts, entity IDs/names, timestamps and source monitor.
2. Why it matters: impact and affected functionality, where known.
3. Evidence: state history or supported diagnostic evidence available to the integration.
4. Cause assessment: confirmed cause, evidence-backed inference, and possible causes/hypotheses kept distinct.
5. Recommended troubleshooting steps, ordered from safest/easiest to more involved.
6. Suggested resolution and how to verify that the issue is fixed.
7. First detected, last seen, duration, recurrence and lifecycle.
8. User actions such as acknowledge/dismiss, with clear semantics.

Advice must be actionable and specific to the issue type. Do not present generic guesses as a confirmed diagnosis. Never execute repair steps or modify device/configuration state automatically. If a step requires a change, explain it and leave execution to the user.

## 3. Independent module cards
Each module can be added separately using the visual editor:
- Availability.
- Freshness.
- Integrations.
- Automations.
- Incidents.
- Health score/trend.

Support compact and detailed presentation. Provide meaningful empty, loading, unsupported-data and integration-missing states.

## 4. Visual card editor: user-selectable presentation

The editor must expose clear, graphical controls rather than requiring YAML. It should allow the user to configure:

### Layout density
- **Compact:** score/status and concise issue summaries; minimal height for dense dashboards.
- **Detailed:** richer explanations, category breakdowns and selected issue metadata.
- The editor should preview the chosen layout where Home Assistant's card editor supports it.

### Charts
- Show charts: on/off.
- Select relevant chart types per card (e.g. score trend, issue count over time, availability/freshness trend).
- Choose a time range where applicable (e.g. 24 hours, 7 days, 30 days).
- Hiding charts must not hide essential status or issue explanations.
- Charts only appear when sufficient historical data exists; show a helpful empty state otherwise.

### Issue interaction
- Expand inline.
- Open popup/dialog.
- Choose how many issues to show.
- Show/hide recommendations in the summary; full recommendations remain available in issue detail.

### Content and modules
- Show/hide score breakdown, coverage, recent issues and last scan.
- Select which module cards/sections appear.
- Optional entity/domain filters where applicable.
- Select compact or detailed module presentation.

### Defaults
Provide sensible defaults so adding the card immediately produces a useful dashboard. Put advanced controls in collapsible sections. YAML is an optional escape hatch, never the primary setup path.

## 5. Navigation prototype
Three conceptual views:
- Overview: global score, score explanation, domain tiles, prioritized issues and coverage.
- Modules: detail summaries for each monitoring engine.
- Incidents: issue list and selected explanation.

Production Lovelace implementation should use native card configuration and accessible overlay/navigation patterns, not assume a standalone app route.

## 6. Sample data only
The initial concept may use:
- Score 94/100.
- 0 unavailable entities.
- 3 stale sensors.
- 0 integration errors.
- 0 automation issues.
- One fictitious delayed temperature sensor.

Every preview must be labelled sample data. The production card must never fall back to sample values when integration data is absent. Example deductions must be internally consistent and clearly labelled illustrative.

## 7. Visual system
- Prefer Home Assistant theme variables.
- Light/dark theme support.
- Pair semantic status colors with text/icons.
- Maintain contrast and touch target sizes.
- Restrained borders/surfaces; avoid excessive shadows/gradients.
- Readable typography and layouts suitable for narrow screens.
- Compact/detailed options and user-configurable sections.

## 8. Prototype acceptance criteria
- Overall health and score are understandable at a glance.
- User can see exactly why the score is below 100 and trace each deduction to issues/rules.
- Score communicates coverage/confidence and never hides missing telemetry.
- User sees a useful issue summary without opening every issue.
- Selecting an issue opens a complete, actionable diagnosis with safe recommendations.
- Facts, inferences and hypotheses are clearly distinguished.
- The editor lets users choose compact/detailed, charts on/off, issue detail interaction and visible sections without YAML.
- Handle no incidents, missing data, partial coverage and setup-required states.
- Overview and independent modules feel like one coherent product.
- Works on mobile/desktop and light/dark themes.
- Mockup values are always clearly marked as sample data.
