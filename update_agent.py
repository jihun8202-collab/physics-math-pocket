from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


def safe_relative(value: str) -> str:
    rel = str(value).replace("\\", "/")
    parts = rel.split("/")
    if (not rel or rel.startswith("/") or ":" in rel or
            any(p in ("", ".", "..") for p in parts)):
        raise ValueError("안전하지 않은 업데이트 파일 경로: " + rel)
    if any(p.rstrip(" .") != p for p in parts):
        raise ValueError("모호한 Windows 파일 경로: " + rel)
    return rel


def contained_path(root: Path, rel: str) -> Path:
    path = root / safe_relative(rel)
    if root.resolve() not in path.resolve().parents:
        raise ValueError("업데이트 파일이 대상 폴더를 벗어납니다: " + rel)
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wait_for_pid(pid: int, timeout: float = 60.0) -> None:
    if pid <= 0:
        return
    deadline = time.time() + timeout
    if os.name == "nt":
        import ctypes
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            remaining = max(0, int((deadline - time.time()) * 1000))
            ctypes.windll.kernel32.WaitForSingleObject(handle, remaining)
            ctypes.windll.kernel32.CloseHandle(handle)
            return
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.25)


def safe_extract(zf: zipfile.ZipFile, target: Path) -> None:
    target_real = target.resolve()
    for member in zf.infolist():
        name = member.filename.replace("\\", "/")
        if ((member.external_attr >> 16) & 0o170000) == 0o120000:
            raise ValueError("업데이트 ZIP에 심볼릭 링크를 넣을 수 없습니다.")
        if name.startswith("/") or ":" in name or ".." in name.split("/"):
            raise ValueError(f"안전하지 않은 ZIP 경로: {member.filename}")
        out = (target / name).resolve()
        if target_real not in out.parents and out != target_real:
            raise ValueError(f"ZIP 경로가 대상 폴더를 벗어납니다: {member.filename}")
    zf.extractall(target)


def verify_payload(staging: Path, manifest: dict) -> list[str]:
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("업데이트 패키지 manifest에 files 목록이 없습니다.")
    rels: list[str] = []
    seen = set()
    for entry in files:
        rel = safe_relative(str(entry.get("path") or ""))
        expected = str(entry.get("sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected) or rel.casefold() in seen:
            raise ValueError("업데이트 manifest 파일 항목이 올바르지 않습니다.")
        seen.add(rel.casefold())
        path = contained_path(staging / "payload", rel)
        if not path.is_file() or sha256_file(path).lower() != expected:
            raise ValueError(f"업데이트 파일 검증 실패: {rel}")
        rels.append(rel)
    return rels


def apply_update(package: Path, install_dir: Path) -> tuple[str, int]:
    work = Path(tempfile.mkdtemp(prefix="pmp-update-"))
    backup = work / "backup"
    changed: list[str] = []
    temporary: list[Path] = []
    metadata_path = install_dir / ".pmp-files.json"
    original_metadata = metadata_path.read_bytes() if metadata_path.is_file() else None
    try:
        with zipfile.ZipFile(package, "r") as zf:
            safe_extract(zf, work / "unpacked")
        unpacked = work / "unpacked"
        manifest = json.loads((unpacked / "update-manifest.json").read_text(encoding="utf-8"))
        rels = verify_payload(unpacked, manifest)
        if "PhysicsMathPocket.exe" not in rels:
            raise ValueError("업데이트 패키지에 앱 실행 파일이 없습니다.")
        for rel in rels:
            if Path(rel).name.lower().startswith("unins") or rel == ".pmp-files.json":
                raise ValueError("업데이트할 수 없는 관리 파일입니다: " + rel)
            contained_path(install_dir, rel)
        payload = unpacked / "payload"
        install_dir.mkdir(parents=True, exist_ok=True)

        # Back up every file we overwrite. User data is not located here.
        for rel in rels:
            dst = contained_path(install_dir, rel)
            if dst.exists() and dst.is_file():
                b = backup / rel
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, b)

        old_manifest_path = install_dir / ".pmp-files.json"
        old_files: set[str] = set()
        try:
            old_payload = json.loads(old_manifest_path.read_text(encoding="utf-8"))
            old_files = {safe_relative(str(x)) for x in old_payload.get("files", [])}
        except Exception:
            pass
        new_files = set(rels)
        protected_prefixes = ("unins",)
        for rel in sorted(old_files - new_files, reverse=True):
            if Path(rel).name.lower().startswith(protected_prefixes):
                continue
            target = contained_path(install_dir, rel)
            if target.is_file():
                b = backup / rel
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, b)
                target.unlink()
                changed.append(rel)

        for rel in rels:
            src = payload / rel
            dst = contained_path(install_dir, rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_name(dst.name + ".pmp-new")
            temporary.append(tmp)
            shutil.copy2(src, tmp)
            changed.append(rel)
            os.replace(tmp, dst)

        metadata_tmp = metadata_path.with_suffix(".json.pmp-new")
        temporary.append(metadata_tmp)
        metadata_tmp.write_text(
            json.dumps({"version": manifest.get("version"), "build": manifest.get("build"), "files": rels}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(metadata_tmp, metadata_path)
        return str(manifest.get("version") or ""), int(manifest.get("build") or 0)
    except Exception:
        # Restore removed/overwritten files and remove new files from an incomplete update.
        for rel in reversed(changed):
            dst = contained_path(install_dir, rel)
            if not (backup / rel).is_file():
                try:
                    dst.unlink(missing_ok=True)
                except OSError:
                    pass
        if backup.exists():
            for src in backup.rglob("*"):
                if src.is_file():
                    rel = src.relative_to(backup)
                    dst = install_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(src, dst)
                    except OSError:
                        pass
        if original_metadata is not None:
            metadata_path.write_bytes(original_metadata)
        else:
            metadata_path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        if work.parent.resolve() == Path(tempfile.gettempdir()).resolve() and work.name.startswith("pmp-update-"):
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Physics + Math Pocket seamless update agent")
    parser.add_argument("--package", required=True)
    parser.add_argument("--install-dir", required=True)
    parser.add_argument("--wait-pid", type=int, default=0)
    parser.add_argument("--restart", default="")
    args = parser.parse_args()
    package = Path(args.package).resolve()
    install_dir = Path(args.install_dir).resolve()
    wait_for_pid(args.wait_pid)
    try:
        apply_update(package, install_dir)
    except Exception as exc:
        try:
            (Path(tempfile.gettempdir()) / "PhysicsMathPocket_update_error.txt").write_text(str(exc), encoding="utf-8")
        except Exception:
            pass
        return 2
    if args.restart:
        restart = Path(args.restart)
        if restart.exists():
            try:
                subprocess.Popen([str(restart)], cwd=str(restart.parent), close_fds=True)
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
