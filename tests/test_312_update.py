from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from core import APP_BUILD, APP_CHANNEL, APP_COPYRIGHT, APP_VERSION
from updater import ReleaseInfo, check_for_updates, parse_version, release_is_newer
from metadata_store import InstallMetadataStore


class UpdateInfrastructure312Tests(unittest.TestCase):
    def test_version_and_build(self):
        self.assertEqual(APP_VERSION, "3.1.7")
        self.assertEqual(APP_BUILD, 31700)
        self.assertEqual(APP_CHANNEL, "stable")
        self.assertIn("Copyright", APP_COPYRIGHT)

    def test_beta_version_comparison(self):
        self.assertLess(parse_version("3.2.0-beta.1"), parse_version("3.2.0"))
        release = ReleaseInfo("3.2.0", 32001, "beta", "3.2 Beta 1")
        self.assertTrue(release_is_newer(release, APP_VERSION, APP_BUILD))

    def test_local_manifest_beta_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "latest.json"
            path.write_text(json.dumps({"releases": [
                {"version": "3.2.0", "build": 32001, "channel": "beta", "name": "3.2 Beta 1"},
                {"version": "3.1.2", "build": 31200, "channel": "stable", "name": "3.1.2"},
            ]}), encoding="utf-8")
            result = check_for_updates(APP_VERSION, APP_BUILD, channel="beta", manifest_url=path.as_uri())
            self.assertEqual(result.status, "update_available")
            self.assertIsNotNone(result.release)
            self.assertEqual(result.release.channel, "beta")

    def test_stable_channel_ignores_beta(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "latest.json"
            path.write_text(json.dumps({"releases": [
                {"version": "3.2.0", "build": 32001, "channel": "beta", "name": "3.2 Beta 1"},
                {"version": "3.1.2", "build": 31200, "channel": "stable", "name": "3.1.2"},
            ]}), encoding="utf-8")
            result = check_for_updates(APP_VERSION, APP_BUILD, channel="stable", manifest_url=path.as_uri())
            self.assertEqual(result.status, "current")

    def test_installer_stamp_is_used_for_dates(self):
        old = os.environ.get("PHYSICSMATHPOCKET_DATA_DIR")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = tmp
                data_dir = Path(tmp)
                data_dir.mkdir(parents=True, exist_ok=True)
                (data_dir / "install_state.ini").write_text(
                    "[Install]\nFirstInstalledAt=2026-08-01T10:00:00\nLastUpdatedAt=2026-08-08T01:30:00\nVersion=3.1.2\nBuild=31200\n",
                    encoding="utf-8",
                )
                store = InstallMetadataStore(APP_VERSION, APP_BUILD, APP_CHANNEL)
                self.assertEqual(store.data["first_installed_at"], "2026-08-01T10:00:00")
                self.assertEqual(store.data["last_updated_at"], "2026-08-08T01:30:00")
        finally:
            if old is None:
                os.environ.pop("PHYSICSMATHPOCKET_DATA_DIR", None)
            else:
                os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = old

    def test_installer_keeps_upgrade_identity(self):
        text = (ROOT / "installer.iss").read_text(encoding="utf-8")
        self.assertIn("AppId={{68D9A3E3-1F4A-4772-90A7-77D4BC2B2A56}", text)
        self.assertIn("UsePreviousAppDir=yes", text)
        self.assertIn("PhysicsMathPocket_Setup_{#MyAppVersion}_Stable_Build{#MyAppBuild}", text)
        self.assertIn('#define MyAppVersion "3.1.7"', text)
        self.assertIn('#define MyAppBuild "31700"', text)
        self.assertIn("VersionInfoCopyright=", text)

    def test_app_has_update_ui(self):
        text = (ROOT / "app.py").read_text(encoding="utf-8")
        for needle in ["def show_updates", "업데이트 확인", "최초 설치일", "최신 업데이트 설치일", "최신 빌드 정보", "Setup.exe 직접 선택"]:
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
