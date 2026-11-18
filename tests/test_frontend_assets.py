from pathlib import Path

CARD = Path(__file__).parents[1] / "custom_components" / "ha_health_monitor" / "www" / "ha-health-monitor-card.js"


def test_bundled_card_registers_card_and_editor():
    source = CARD.read_text()
    assert 'customElements.define("ha-health-monitor-card"' in source
    assert 'customElements.define("ha-health-monitor-editor"' in source
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
