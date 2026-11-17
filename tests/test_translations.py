"""Basic translation catalog consistency tests."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
TRANSLATIONS = ROOT / "custom_components" / "ha_health_monitor" / "translations"


def _flatten(value, prefix=""):
    result = set()
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(child, dict):
            result.update(_flatten(child, path))
        else:
            result.add(path)
    return result


def test_english_and_spanish_have_same_translation_keys():
    english = json.loads((TRANSLATIONS / "en.json").read_text())
    spanish = json.loads((TRANSLATIONS / "es.json").read_text())
    assert _flatten(english) == _flatten(spanish)


def test_translation_catalogs_are_valid_json():
    for catalog in TRANSLATIONS.glob("*.json"):
        json.loads(catalog.read_text())
