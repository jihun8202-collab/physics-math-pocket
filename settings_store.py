from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core import user_data_dir

DEFAULT_SETTINGS: Dict[str, Any] = {
    # Public release feed for the shipped 3.1.7 app.  Users can override this
    # in Settings for a fork or an internal test feed.
    "update_repository": "jihun8202-collab/physics-math-pocket",
    "theme": "system",
    "font_scale": 1.0,
    "density": "comfortable",
    "animations": True,
    "simulation_fps": 30,
    "storage_limit_gb": 5,
    "show_simulations": True,
    "search_result_limit": 100,
    "confirm_external_links": False,
    "check_updates_on_startup": True,
    "update_channel": "stable",
    "update_manifest_url": "",
    "update_source_mode": "github",
    "update_defaults_revision": 2,
    "update_local_dir": "",
    "prefer_seamless_update": True,
}


class SettingsStore:
    def __init__(self) -> None:
        self.path = user_data_dir() / "settings_v3.json"

    def load(self) -> Dict[str, Any]:
        data = dict(DEFAULT_SETTINGS)
        incoming: Dict[str, Any] = {}
        try:
            incoming = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(incoming, dict):
                data.update(incoming)
            else:
                incoming = {}
        except Exception:
            pass
        data["font_scale"] = min(1.4, max(0.8, float(data.get("font_scale", 1.0))))
        data["storage_limit_gb"] = min(5, max(1, int(data.get("storage_limit_gb", 5))))
        data["simulation_fps"] = 60 if int(data.get("simulation_fps", 30)) >= 60 else 30
        data["search_result_limit"] = min(300, max(30, int(data.get("search_result_limit", 100))))
        if data.get("theme") not in ("system", "light", "dark"):
            data["theme"] = "system"
        if data.get("density") not in ("comfortable", "compact"):
            data["density"] = "comfortable"
        if data.get("update_channel") not in ("stable", "beta"):
            data["update_channel"] = "stable"
        data["check_updates_on_startup"] = bool(data.get("check_updates_on_startup", True))
        data["update_repository"] = str(data.get("update_repository", "") or "").strip()
        data["update_manifest_url"] = str(data.get("update_manifest_url", "") or "").strip()
        if data.get("update_source_mode") not in ("auto", "local", "github", "manifest"):
            data["update_source_mode"] = "auto"
        data["update_local_dir"] = str(data.get("update_local_dir", "") or "").strip()
        data["prefer_seamless_update"] = bool(data.get("prefer_seamless_update", True))
        # Migrate the pre-GitHub default (local inbox with no repository). A
        # deliberate custom repository or manifest remains untouched.
        try:
            old_revision = int(incoming.get("update_defaults_revision", 0) or 0)
        except (TypeError, ValueError):
            old_revision = 0
        if old_revision < 2 and not data["update_repository"]:
            data["update_repository"] = DEFAULT_SETTINGS["update_repository"]
            if data.get("update_source_mode") in ("auto", "local"):
                data["update_source_mode"] = DEFAULT_SETTINGS["update_source_mode"]
        data["update_defaults_revision"] = DEFAULT_SETTINGS["update_defaults_revision"]
        return data

    def save(self, data: Dict[str, Any]) -> None:
        payload = dict(DEFAULT_SETTINGS)
        payload.update(data)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
