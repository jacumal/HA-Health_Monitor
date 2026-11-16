# Product pillars and non-negotiable acceptance criteria

These five pillars define whether HA Health Monitor is successful. They are product requirements, not optional polish or future enhancements. Every architecture, feature and release decision must support them.

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

## 5. Internationalization and localization

HA Health Monitor is intended for an international audience. Multilingual support is a product requirement from the beginning, not a later translation task.

Acceptance criteria:
- All user-facing integration and Lovelace strings must be externalized into translation catalogs; no user-visible text hard-coded in components or Python modules.
- Initial supported languages: English (default/fallback) and Spanish. The architecture must make adding further languages straightforward.
- Respect the Home Assistant user's selected language/locale where available.
- Use locale-aware date/time, number, decimal, percentage and unit formatting; use Home Assistant conventions and unit systems where possible.
- Translate setup flows, options, selectors, card editor labels, statuses, severities, issue summaries, explanations, recommendations, empty/error states, notifications and accessibility labels.
- Keep entity IDs, service IDs, domain names, protocol terms and user-provided entity/device names stable; translate display labels, not identifiers.
- Avoid building sentences by concatenating translated fragments. Use complete translatable messages with placeholders and pluralization support.
- Keep translation keys stable and documented; include a process for detecting missing and obsolete translations.
- A missing translation must fall back cleanly to English rather than displaying a blank label or raw key.
- Technical diagnostic details may preserve original error text where translation would obscure the source, but should provide a localized explanation around it.

## Product decision gate

Before accepting a feature or release, ask:
1. Does it provide real diagnostic or operational value?
2. Is it clear and pleasant to use?
3. Can a normal user configure it graphically?
4. Does it fit the coherent Hybrid Lovelace experience?
5. Is every user-facing part internationalization-ready?

If a change weakens any pillar, redesign it before release.
