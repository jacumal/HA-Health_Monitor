from pathlib import Path

CARD = (
    Path(__file__).parents[1]
    / "custom_components"
    / "ha_health_monitor"
    / "www"
    / "ha-health-monitor-card.js"
)


def test_bundled_card_registers_card_and_editor():
    source = CARD.read_text()
    assert 'customElements.define("ha-health-monitor-card"' in source
    assert 'customElements.define("ha-health-monitor-editor"' in source
    assert 'customElements.define("ha-health-monitor",HaHealthMonitorCard)' in source
    assert "class HaHealthMonitorLegacyCard extends HaHealthMonitorCard" in source
    assert "static getConfigElement()" in source
    assert 'type:"ha-health-monitor"' in source


def test_card_reads_real_backend_entities_and_score_explanation():
    source = CARD.read_text()
    assert "sensor.ha_health_monitor_health_score" in source
    assert "sensor.ha_health_monitor_active_incidents" in source
    assert "coverage_percent" in source
    assert "94/100" not in source


def test_card_has_english_and_spanish_locales_and_issue_details():
    source = CARD.read_text()
    assert "en:{" in source and "es:{" in source
    assert "issuePanel" in source
    assert "aria-label" in source
    assert "shell.detailed" in source
    assert "scoremodule" in source


def test_card_exposes_disabled_entities_as_non_scoring_module():
    source = CARD.read_text()
    assert "sensor.ha_health_monitor_disabled_entities" in source
    assert 'disabled:["disabled","mdi:eye-off-outline"' in source
    assert "filter_disabled" in source
    assert "not_scored" in source



def test_card_supports_reversible_manual_entity_exclusions():
    source = CARD.read_text()
    assert '"set_entity_excluded"' in source
    assert 'data-a=\'exclude\'' in source
    assert "manual_exclusions" in source
    assert "entityPanel" in source
    assert "data-a='more-info'" in source
    assert 'new CustomEvent("hass-more-info"' in source


def test_card_labels_issues_with_translated_integration_names():
    source = CARD.read_text()
    assert 'integrationName(domain)' in source
    assert 'hass.localize(key)' in source
    assert 'entityLabel(entityId,domain)' in source
    assert (
        'this.entityLabel(i.entity_id||i.target||"—",i.details&&i.details.platform)'
        in source
    )
    assert 'this.entityLabel(id,typeof x==="object"?x.platform:null)' in source

def test_card_footer_version_matches_manifest_release_candidate():
    source = CARD.read_text()
    manifest = (
        Path(__file__).parents[1]
        / "custom_components"
        / "ha_health_monitor"
        / "manifest.json"
    )
    import json

    version = json.loads(manifest.read_text())["version"]
    assert f"<small>v{version}</small>" in source
