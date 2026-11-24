import os
from pathlib import Path
from typing import Any

import yaml

from tracelens.config.settings import Settings, get_settings


def overlay_path() -> Path:
    raw = os.environ.get(
        "TRACELENS_CONFIG_OVERLAY_PATH",
        os.environ.get("TRACELENS_OVERLAY_PATH", "config/overlay.yaml"),
    )
    return Path(raw)


def load_overlay_dict(path: Path | None = None) -> dict[str, Any]:
    target = path or overlay_path()
    if not target.is_file():
        return {}
    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def apply_overlay(settings: Settings, overlay: dict[str, Any]) -> Settings:
    if not overlay:
        return settings
    if routing := overlay.get("routing"):
        settings.routing = settings.routing.model_copy(update=routing)
    if circuit := overlay.get("circuit_breaker"):
        settings.circuit_breaker = settings.circuit_breaker.model_copy(update=circuit)
    if retry := overlay.get("retry"):
        settings.retry = settings.retry.model_copy(update=retry)
    if shadow := overlay.get("shadow"):
        settings.shadow = settings.shadow.model_copy(update=shadow)
    if mock_latency := overlay.get("mock_default_latency_ms"):
        settings.mock_default_latency_ms = float(mock_latency)
    if mock_error := overlay.get("mock_default_error_rate"):
        settings.mock_default_error_rate = float(mock_error)
    return settings


def build_settings() -> Settings:
    base = Settings()
    return apply_overlay(base, load_overlay_dict())


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


def save_overlay_dict(overlay: dict[str, Any], path: Path | None = None) -> Path:
    target = path or overlay_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(overlay, sort_keys=True, default_flow_style=False),
        encoding="utf-8",
    )
    return target
