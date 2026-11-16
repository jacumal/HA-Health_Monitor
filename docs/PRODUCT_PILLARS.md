# Product pillars and non-negotiable acceptance criteria

These four pillars define whether HA Health Monitor is successful. They are product requirements, not optional polish or future enhancements. Every architecture, feature and release decision must support them.

## 1. Real usefulness

The product must help Home Assistant users detect, understand and resolve real problems.

Acceptance criteria:
- Detect meaningful issues with reliable evidence and entity-specific expectations.
- Minimize false positives and explain uncertainty.
- Explain the impact and why an issue matters.
- Provide practical, ordered troubleshooting advice and verification steps.
- Explain every point lost from the 0–100 health score and link deductions to their causes.
- Avoid duplicate incidents and double penalties for symptoms caused by one underlying fault.
- Never claim a diagnosis is confirmed when it is only a hypothesis.
- Monitor and advise by default; never change configuration or devices without explicit user action.

A feature that adds counts or graphs without helping users make a decision is not sufficient.

## 2. Easy, pleasant interface

The product must be easy to understand and enjoyable to use.

Acceptance criteria:
- Important status and issues are understandable at a glance.
- Consistent hierarchy, readable typography, spacing and clear status language.
- Responsive layouts for mobile, tablet and desktop.
- Light and dark theme support.
- Accessible contrast, touch targets and keyboard/focus behavior.
- Progressive disclosure: concise summaries first, deeper diagnostic information on demand.
- Clear empty, loading, partial-data, unsupported and setup-required states.

## 3. Easy configuration

The main product capabilities must not require users to edit YAML.

Acceptance criteria:
- Graphical installation and setup through Home Assistant Config Flow.
- Sensible defaults that deliver value immediately.
- Graphical options for exclusions, sensitivity and entity-specific behavior.
- Visual Lovelace card editor with clear controls and preview where supported.
- Advanced options may exist, but must not burden the normal setup path.
- YAML remains optional for advanced users, never a prerequisite.

## 4. First-class Lovelace card: Hybrid design

The product must include its own polished Lovelace card, combining:
- **Apple-inspired design language:** restrained visual style, typography, hierarchy, whitespace, clarity and polished light/dark appearance.
- **Bubble Card-inspired interaction patterns:** modular rounded surfaces, compact summaries, contextual expansion, popups and configurable composition.

This is an original design. Do not copy Bubble Card implementation/assets and do not require Bubble Card as a dependency.

The card package must provide:
- A main overview card.
- Independent cards for monitoring modules.
- A transparent 0–100 score and “Why not 100?” explanation.
- Prioritized issue summaries with selectable detailed diagnosis and remediation guidance.
- A visual editor for compact/detailed layout, charts on/off and chart period, inline expansion or popup, visible sections and issue count.
- Shared design tokens and data contract across all card types.

## Product decision gate

Before accepting a feature or release, ask:
1. Does it provide real diagnostic or operational value?
2. Is it clear and pleasant to use?
3. Can a normal user configure it graphically?
4. Does it fit the coherent Hybrid Lovelace experience?

If a change weakens any pillar, redesign it before release.
