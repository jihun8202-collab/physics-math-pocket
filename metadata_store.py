from __future__ import annotations

import configparser
import datetime as dt
import json
from typing import Any, Dict, Optional

from core import user_data_dir


def _now_iso() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


class InstallMetadataStore:
    """Persist install/update metadata outside the app install directory.

    The first launch after installation is used as the install timestamp. Because the
    file lives under LOCALAPPDATA/PhysicsMathPocket, replacing application binaries
    during an upgrade does not erase it.
    """

    def __init__(self, current_version: str, current_build: int, channel: str) -> None:
        self.path = user_data_dir() / "install_metadata.json"
        self.current_version = str(current_version)
        self.current_build = int(current_build)
        self.channel = str(channel)
        self.data: Dict[str, Any] = self._load_and_migrate()

    def _read(self) -> Dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _write(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)


    def _installer_stamp(self) -> Dict[str, Any]:
        path = user_data_dir() / "install_state.ini"
        if not path.exists():
            return {}
        parser = configparser.ConfigParser()
        try:
            parser.read(str(path), encoding="utf-8")
            section = parser["Install"] if parser.has_section("Install") else {}
            return {
                "first_installed_at": section.get("FirstInstalledAt"),
                "last_updated_at": section.get("LastUpdatedAt"),
                "installer_version": section.get("Version"),
                "installer_build": section.get("Build"),
            }
        except Exception:
            return {}

    def _load_and_migrate(self) -> Dict[str, Any]:
        now = _now_iso()
        data = self._read()
        if not data:
            data = {
                "first_installed_at": now,
                "last_updated_at": now,
                "first_version": self.current_version,
                "first_build": self.current_build,
                "current_version": self.current_version,
                "current_build": self.current_build,
                "channel": self.channel,
                "previous_version": None,
                "previous_build": None,
                "update_count": 0,
                "last_update_check_at": None,
                "latest_known": None,
                "update_history": [],
                "pending_update": None,
            }
        else:
            old_version = str(data.get("current_version") or self.current_version)
            try:
                old_build = int(data.get("current_build", self.current_build))
            except Exception:
                old_build = self.current_build
            if old_version != self.current_version or old_build != self.current_build:
                data["previous_version"] = old_version
                data["previous_build"] = old_build
                data["current_version"] = self.current_version
                data["current_build"] = self.current_build
                data["channel"] = self.channel
                data["last_updated_at"] = now
                data["update_count"] = int(data.get("update_count", 0)) + 1
                pending = data.get("pending_update") if isinstance(data.get("pending_update"), dict) else {}
                if str(pending.get("kind") or "").lower() == "rollback":
                    data["update_history"] = []
                    data["update_count"] = 0
                else:
                    history = data.setdefault("update_history", [])
                    history.append({
                        "timestamp": now,
                        "from_version": old_version,
                        "from_build": old_build,
                        "to_version": self.current_version,
                        "to_build": self.current_build,
                        "channel": self.channel,
                        "kind": str(pending.get("kind") or "update"),
                        "notes": str(pending.get("notes") or "버전 파일이 교체되었습니다."),
                    })
                    data["update_history"] = history[-30:]
                data["pending_update"] = None
            data.setdefault("first_installed_at", now)
            data.setdefault("last_updated_at", data.get("first_installed_at", now))
            data.setdefault("first_version", old_version)
            data.setdefault("first_build", old_build)
            data.setdefault("last_update_check_at", None)
            data.setdefault("latest_known", None)
            data.setdefault("update_history", [])
            data.setdefault("pending_update", None)
        stamp = self._installer_stamp()
        if stamp.get("first_installed_at"):
            data["first_installed_at"] = stamp["first_installed_at"]
        if stamp.get("last_updated_at"):
            data["last_updated_at"] = stamp["last_updated_at"]
        if stamp.get("installer_version"):
            data["installer_version"] = stamp["installer_version"]
        if stamp.get("installer_build"):
            data["installer_build"] = stamp["installer_build"]
        self.data = data
        self._write()
        return data

    def mark_check(self, latest: Optional[Dict[str, Any]] = None) -> None:
        self.data["last_update_check_at"] = _now_iso()
        if latest is not None:
            self.data["latest_known"] = latest
        self._write()

    def latest_known(self) -> Optional[Dict[str, Any]]:
        value = self.data.get("latest_known")
        return value if isinstance(value, dict) else None

    def record_update_started(self, release: Dict[str, Any], kind: str = "update") -> None:
        payload = dict(release)
        payload["kind"] = kind
        self.data["pending_update"] = payload
        self._write()

    def history(self) -> list:
        value = self.data.get("update_history")
        return value if isinstance(value, list) else []

    def reset_for_rollback(self, target: Dict[str, Any]) -> None:
        """Forget version-specific update history before applying an older package."""
        self.data["update_history"] = []
        self.data["latest_known"] = None
        self.data["pending_update"] = dict(target)
        self.data["pending_update"]["kind"] = "rollback"
        self.data["previous_version"] = None
        self.data["previous_build"] = None
        self.data["update_count"] = 0
        self._write()

    @staticmethod
    def format_timestamp(value: Any) -> str:
        if not value:
            return "기록 없음"
        try:
            parsed = dt.datetime.fromisoformat(str(value))
            return parsed.astimezone().strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(value)

