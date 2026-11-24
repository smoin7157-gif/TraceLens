from pathlib import Path

import pytest

from tracelens.config import get_settings, reload_settings
from tracelens.config.overlay import apply_overlay, save_overlay_dict
from tracelens.config.settings import Settings


def test_overlay_updates_routing_chains(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    overlay_file = tmp_path / "overlay.yaml"
    save_overlay_dict(
        {
            "routing": {
                "fallback_chains": {
                    "mock-gpt": ["mock-gpt-4"],
                }
            }
        },
        overlay_file,
    )
    monkeypatch.setenv("TRACELENS_CONFIG_OVERLAY_PATH", str(overlay_file))
    get_settings.cache_clear()
    settings = reload_settings()
    assert settings.routing.fallback_chains["mock-gpt"] == ["mock-gpt-4"]


def test_apply_overlay_merge() -> None:
    base = Settings()
    merged = apply_overlay(base, {})
    assert merged.routing.fallback_chains["mock-gpt"]
