"""Apply the generated ZIP to a temporary install and verify its actual payload."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import APP_BUILD, APP_CHANNEL, APP_VERSION
from update_agent import apply_update, sha256_file


def verify() -> None:
    label = "{}_{}_Build{}".format(APP_VERSION, APP_CHANNEL.capitalize(), APP_BUILD)
    package = ROOT / "release" / ("PhysicsMathPocket_Update_" + label + ".zip")
    with zipfile.ZipFile(package) as archive:
        manifest = json.loads(archive.read("update-manifest.json"))
        assert manifest["version"] == APP_VERSION and manifest["build"] == APP_BUILD
        assert len(manifest["files"]) == len(set(item["path"] for item in manifest["files"]))
        assert "PhysicsMathPocketUpdater.exe" in {item["path"] for item in manifest["files"]}
        inventory = json.loads((ROOT / "dist/PhysicsMathPocket/.pmp-files.json").read_text(encoding="utf-8"))
        assert (inventory["version"], inventory["build"]) == (APP_VERSION, APP_BUILD)
        assert set(inventory["files"]) == {item["path"] for item in manifest["files"]}
    with tempfile.TemporaryDirectory(prefix="pmp-release-verification-") as temp:
        install = Path(temp) / "install"
        install.mkdir()
        retained = install / "private-study-notes.txt"
        retained.write_text("preserve user file", encoding="utf-8")
        version, build = apply_update(package, install)
        assert (version, build) == (APP_VERSION, APP_BUILD)
        assert retained.read_text(encoding="utf-8") == "preserve user file"
        for item in manifest["files"]:
            path = install / item["path"]
            assert path.stat().st_size == item["size"], item["path"]
            assert sha256_file(path) == item["sha256"], item["path"]
        print("Verified generated ZIP: {} files; real updater applied it; unrelated user file preserved.".format(len(manifest["files"])))
        # Exercise the frozen helper as well as its Python implementation. No app restart.
        frozen_agent = ROOT / "dist/PhysicsMathPocket/PhysicsMathPocketUpdater.exe"
        process = subprocess.run([str(frozen_agent), "--package", str(package), "--install-dir", str(install)],
                                 timeout=600, check=False)
        assert process.returncode == 0, "Frozen updater failed: exit {}".format(process.returncode)
        assert retained.read_text(encoding="utf-8") == "preserve user file"
        for item in manifest["files"]:
            path = install / item["path"]
            assert path.stat().st_size == item["size"] and sha256_file(path) == item["sha256"], item["path"]
        print("Verified frozen updater EXE: same {} files and user file preserved.".format(len(manifest["files"])))


if __name__ == "__main__":
    verify()
