from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from core import APP_BUILD, APP_CHANNEL, APP_VERSION
from settings_store import DEFAULT_SETTINGS
from settings_store import SettingsStore
from updater import (
    ReleaseInfo,
    check_for_updates,
    default_build_for_version,
    release_is_newer,
    sha256_file,
)


class UpdateLab313Tests(unittest.TestCase):
    def test_github_updater_is_a_release_default(self):
        self.assertEqual(DEFAULT_SETTINGS["update_repository"], "jihun8202-collab/physics-math-pocket")
        self.assertEqual(DEFAULT_SETTINGS["update_source_mode"], "github")
        installer = (ROOT / "installer.iss").read_text(encoding="utf-8")
        builder = (ROOT / "build_release.py").read_text(encoding="utf-8")
        self.assertIn('Source: "dist\\PhysicsMathPocket\\*"', installer)
        self.assertIn("build_update_agent", builder)

    def test_old_local_default_migrates_to_github(self):
        with tempfile.TemporaryDirectory() as td:
            store = SettingsStore()
            old_path = store.path
            store.path = Path(td) / "settings_v3.json"
            store.path.write_text(json.dumps({"update_source_mode": "local", "update_repository": ""}), encoding="utf-8")
            loaded = store.load()
            store.path = old_path
            self.assertEqual(loaded["update_source_mode"], "github")
            self.assertEqual(loaded["update_repository"], "jihun8202-collab/physics-math-pocket")

    def test_beta_identity(self):
        self.assertEqual(APP_VERSION, "4.0.0")
        self.assertEqual(APP_BUILD, 40001)
        self.assertEqual(APP_CHANNEL, "beta")

    def test_default_build_mapping(self):
        self.assertEqual(default_build_for_version("3.1.5"), 31500)
        self.assertEqual(default_build_for_version("3.1.5", True), 31501)

    def test_local_setup_filename_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            setup = folder / "PhysicsMathPocket_Setup_4.0.1_Beta_Build40001.exe"
            setup.write_bytes(b"test-installer")
            result = check_for_updates(
                APP_VERSION,
                APP_BUILD,
                channel="beta",
                local_dir=str(folder),
                source_mode="local",
            )
            self.assertEqual(result.status, "update_available")
            self.assertEqual(result.source, "local")
            self.assertIsNotNone(result.release)
            self.assertEqual(result.release.version, "4.0.1")
            self.assertEqual(result.release.build, 40001)
            self.assertTrue(result.release.is_beta)
            self.assertEqual(result.release.sha256, sha256_file(setup))

    def test_stable_channel_ignores_beta_local_file(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "PhysicsMathPocket_Setup_3.1.5_Beta_Build31502.exe").write_bytes(b"beta")
            result = check_for_updates(
                APP_VERSION,
                APP_BUILD,
                channel="stable",
                local_dir=str(folder),
                source_mode="local",
            )
            self.assertEqual(result.status, "no_release")

    def test_local_manifest_can_drive_update(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            setup = folder / "next.exe"
            setup.write_bytes(b"next-version")
            manifest = {
                "version": "4.0.1",
                "build": 40001,
                "channel": "stable",
                "name": "4.0.1 Stable",
                "file": "next.exe",
                "sha256": sha256_file(setup),
            }
            (folder / "update-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = check_for_updates(
                APP_VERSION,
                APP_BUILD,
                channel="stable",
                local_dir=str(folder),
                source_mode="local",
            )
            self.assertEqual(result.status, "update_available")
            # Windows may spell the same temporary path using an 8.3 alias.
            self.assertTrue(Path(result.release.local_path).samefile(setup))

    @patch("updater._load_config", return_value={})
    def test_auto_mode_falls_back_to_unconfigured_without_remote(self, _config):
        with tempfile.TemporaryDirectory() as td:
            result = check_for_updates(
                APP_VERSION,
                APP_BUILD,
                channel="beta",
                local_dir=td,
                source_mode="auto",
            )
            self.assertEqual(result.status, "unconfigured")

    def test_app_exposes_update_test_controls(self):
        text = (ROOT / "app.py").read_text(encoding="utf-8")
        for needle in [
            "업데이트 기능 테스트",
            "로컬 업데이트 폴더",
            "def test_update_prompt",
            "def run_update_diagnostics",
            "update_source_mode",
            "update_local_dir",
        ]:
            self.assertIn(needle, text)

    def test_installer_keeps_same_app_id(self):
        text = (ROOT / "installer.iss").read_text(encoding="utf-8")
        self.assertIn("AppId={{68D9A3E3-1F4A-4772-90A7-77D4BC2B2A56}", text)
        self.assertIn("UsePreviousAppDir=yes", text)
        self.assertIn("PhysicsMathPocket_Setup_{#MyAppVersion}_{#MyAppChannel}_Build{#MyAppBuild}", text)


if __name__ == "__main__":
    unittest.main()




