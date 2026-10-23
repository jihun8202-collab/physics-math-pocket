"""Exercise real payload replacement and rollback state transactions."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import build_release
import update_agent
from metadata_store import InstallMetadataStore
from updater import check_for_updates, list_github_releases


def package_at(root, payload, build=32002, corrupt=False):
    package = root / "rollback.zip"
    manifest = {
        "version": "3.2.0", "build": build, "files": [
            {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in payload.items()
        ],
    }
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("update-manifest.json", json.dumps(manifest))
        for name, data in payload.items():
            archive.writestr("payload/" + name, data + (b"corrupt" if corrupt else b""))
    return package


class Rollback355Tests(unittest.TestCase):
    def seed_user(self, root):
        user = root / "user"
        user.mkdir()
        (user / "database").mkdir()
        (user / "database/knowledge_user.db").write_bytes(b"database")
        for name in ("recent_searches.json", "favorites.json", "term_notes.json",
                     "install_metadata.json", "install_state.ini"):
            (user / name).write_bytes(b"previous-state")
        (user / "settings_v3.json").write_text(json.dumps({
            "theme": "dark", "font_scale": 1.4, "future_ui": True,
            "update_repository": "owner/repo", "update_channel": "beta",
            "update_source_mode": "github", "check_updates_on_startup": False,
        }), encoding="utf-8")
        return user

    def snapshots(self, root):
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in root.rglob("*") if p.is_file()}

    def test_rollback_resets_version_state_and_keeps_only_updater_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = self.seed_user(root)
            (user / "exported-notes.txt").write_text("user export", encoding="utf-8")
            update_agent.apply_update(package_at(root, {"PhysicsMathPocket.exe": b"old-version"}),
                                      root / "install", rollback_data_dir=user)
            settings = json.loads((user / "settings_v3.json").read_text(encoding="utf-8"))
            self.assertEqual(settings, {
                "update_repository": "owner/repo", "update_channel": "beta",
                "update_source_mode": "github", "check_updates_on_startup": False,
            })
            self.assertEqual(set(self.snapshots(user)), {"settings_v3.json", "exported-notes.txt"})

    def test_cleanup_failure_restores_payload_and_every_user_state_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = self.seed_user(root)
            install = root / "install"
            install.mkdir()
            (install / "PhysicsMathPocket.exe").write_bytes(b"current-version")
            before_user, before_install = self.snapshots(user), self.snapshots(install)
            original_replace = update_agent.os.replace
            def fail_one_move(source, target):
                if Path(source) == user / "install_metadata.json":
                    raise PermissionError("simulated locked metadata")
                return original_replace(source, target)
            with patch("update_agent.os.replace", side_effect=fail_one_move):
                with self.assertRaises(PermissionError):
                    update_agent.apply_update(package_at(root, {"PhysicsMathPocket.exe": b"old-version"}),
                                              install, rollback_data_dir=user)
            self.assertEqual(self.snapshots(user), before_user)
            self.assertEqual(self.snapshots(install), before_install)

    def test_failed_payload_or_invalid_build_cannot_clear_user_data(self):
        for build in ("invalid-build", 32002):
            with self.subTest(build=build), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                user = self.seed_user(root)
                before = self.snapshots(user)
                package = package_at(root, {"PhysicsMathPocket.exe": b"old-version"},
                                     build=build, corrupt=build == 32002)
                with self.assertRaises(ValueError):
                    update_agent.apply_update(package, root / "install", rollback_data_dir=user)
                self.assertEqual(self.snapshots(user), before)

    def test_regular_update_keeps_user_state_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = self.seed_user(root)
            before = self.snapshots(user)
            update_agent.apply_update(package_at(root, {"PhysicsMathPocket.exe": b"update"}), root / "install")
            self.assertEqual(self.snapshots(user), before)

    def test_pending_rollback_does_not_erase_history_before_apply(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"PHYSICSMATHPOCKET_DATA_DIR": temp}):
            store = InstallMetadataStore("3.5.5", 35500, "beta")
            store.data.update(update_history=[{"notes": "earlier update"}], update_count=4,
                              latest_known={"version": "3.5.5"})
            store._write()
            before = dict(store.data)
            store.reset_for_rollback({"version": "3.2.0", "build": 32002})
            for key in ("update_history", "update_count", "latest_known"):
                self.assertEqual(store.data[key], before[key])
            self.assertEqual(store.data["pending_update"]["kind"], "rollback")

    def test_seamless_update_date_is_not_replaced_by_old_setup_date(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"PHYSICSMATHPOCKET_DATA_DIR": temp}):
            (Path(temp) / "install_state.ini").write_text(
                "[Install]\nFirstInstalledAt=2026-08-01T10:00:00\n"
                "LastUpdatedAt=2026-08-08T01:30:00\nVersion=3.5.0\nBuild=35001\n",
                encoding="utf-8",
            )
            original = InstallMetadataStore("3.5.0", 35001, "beta")
            self.assertEqual(original.data["last_updated_at"], "2026-08-08T01:30:00")
            updated_at = "2026-10-20T12:00:00+09:00"
            with patch("metadata_store._now_iso", return_value=updated_at):
                updated = InstallMetadataStore("3.5.5", 35500, "beta")
                again = InstallMetadataStore("3.5.5", 35500, "beta")
            for store in (updated, again):
                self.assertEqual(store.data["last_updated_at"], updated_at)
                self.assertEqual(store.data["first_installed_at"], "2026-08-01T10:00:00")

    @unittest.skipUnless(os.name == "nt", "Windows updater process wait")
    def test_running_app_timeout_does_not_allow_update_to_continue(self):
        process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            with self.assertRaises(TimeoutError):
                update_agent.wait_for_pid(process.pid, timeout=0.05)
            self.assertIsNone(process.poll())
        finally:
            process.terminate()
            process.wait(timeout=5)
        update_agent.wait_for_pid(process.pid, timeout=0.05)

    def test_setup_inventory_removes_newer_assets_on_first_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            install = root / "dist/PhysicsMathPocket"
            install.mkdir(parents=True)
            for name in ("PhysicsMathPocket.exe", "PhysicsMathPocketUpdater.exe",
                         "new-layout.dat", "README_KO.md"):
                (install / name).write_bytes(b"new-version")
            with patch.object(build_release, "ROOT", root), patch.object(build_release, "LOG", root / "build.log"):
                current_package = build_release.build_update_package()
                # Rebuilding must not put the updater's protected inventory in its payload.
                build_release.build_update_package()
            inventory = json.loads((install / ".pmp-files.json").read_text(encoding="utf-8"))
            self.assertIn("new-layout.dat", inventory["files"])
            self.assertIn("README_KO.md", inventory["files"])
            with zipfile.ZipFile(current_package) as archive:
                self.assertNotIn(".pmp-files.json",
                                 [f["path"] for f in json.loads(archive.read("update-manifest.json"))["files"]])
            update_agent.apply_update(package_at(root, {"PhysicsMathPocket.exe": b"old-version"}), install)
            self.assertFalse((install / "new-layout.dat").exists())
            self.assertFalse((install / "README_KO.md").exists())
            self.assertEqual((install / "PhysicsMathPocket.exe").read_bytes(), b"old-version")

    @patch("updater._request_json")
    def test_source_archive_is_not_offered_as_app_update(self, request):
        request.return_value = [{
            "tag_name": "v3.5.5_Beta_Build35500", "prerelease": True,
            "assets": [{"name": "Source.zip", "browser_download_url": "https://example.invalid/source.zip"}],
        }]
        result = check_for_updates("3.5.0", 35001, channel="beta",
                                   repository="owner/repo", source_mode="github")
        self.assertEqual(result.status, "no_release")

    @patch("updater._request_json")
    def test_rollback_list_requires_full_update_package(self, request):
        request.return_value = [{
            "tag_name": "v3.2.0_Stable_Build32002", "prerelease": False,
            "assets": [{"name": "PhysicsMathPocket_Setup_3.2.0.exe",
                        "browser_download_url": "https://example.invalid/setup.exe"}],
        }]
        self.assertEqual(list_github_releases("owner/repo", asset_contains="PhysicsMathPocket_Update_"), [])


if __name__ == "__main__":
    unittest.main()
