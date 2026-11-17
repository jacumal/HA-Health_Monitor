"""Integration packaging checks."""

import json
from pathlib import Path


def test_manifest_has_required_installation_metadata():
    manifest_path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "ha_health_monitor"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text())

    assert manifest["domain"] == "ha_health_monitor"
    assert manifest["config_flow"] is True
    assert manifest["version"]
