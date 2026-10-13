from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
import sys
import struct
from pathlib import Path
from typing import Iterable, Optional
from core import APP_VERSION, APP_BUILD, APP_CHANNEL

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "build_release.log"
VENV = ROOT / ".buildenv"
VENV_PYTHON = VENV / "Scripts" / "python.exe"
RELEASE_LABEL = "{}_{}_Build{}".format(APP_VERSION, APP_CHANNEL.capitalize(), APP_BUILD)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class BuildError(RuntimeError):
    pass


def write(message: str = "") -> None:
    print(message, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


def run(command: Iterable[str], title: str, cwd: Path = ROOT) -> None:
    command = [str(x) for x in command]
    write("\n[{}]".format(title))
    write("$ " + " ".join(command))
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    for line in process.stdout:
        write(line.rstrip("\n"))
    code = process.wait()
    if code != 0:
        raise BuildError("{} 단계가 종료 코드 {}로 실패했습니다.".format(title, code))


def find_iscc() -> Optional[Path]:
    direct = shutil.which("ISCC.exe") or shutil.which("ISCC")
    if direct:
        return Path(direct)
    candidates = []
    for env_name in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env_name)
        if not base:
            continue
        candidates.extend(
            [
                Path(base) / "Inno Setup 7" / "ISCC.exe",
                Path(base) / "Inno Setup 6" / "ISCC.exe",
                Path(base) / "Programs" / "Inno Setup 7" / "ISCC.exe",
                Path(base) / "Programs" / "Inno Setup 6" / "ISCC.exe",
            ]
        )
    return next((path for path in candidates if path.exists()), None)


def ensure_windows() -> None:
    if os.name != "nt":
        raise BuildError("Windows용 EXE는 Windows에서 빌드해야 합니다. 이 프로젝트를 Windows PC에서 실행하세요.")


def ensure_python() -> None:
    if struct.calcsize("P") != 8:
        raise BuildError("Windows x64 Python is required.")
    if sys.version_info < (3, 9):
        raise BuildError("Python 3.9 이상이 필요합니다. 현재: {}".format(sys.version.split()[0]))
    write("Python: {}".format(sys.executable))
    write("Version: {}".format(sys.version.split()[0]))


def create_venv() -> None:
    if VENV_PYTHON.exists():
        write("빌드 가상환경 확인: {}".format(VENV))
        return
    run([sys.executable, "-m", "venv", str(VENV)], "1/6 빌드 가상환경 생성")


def install_build_tools() -> None:
    # Avoid upgrading to a future pip release that may drop the user's Python version.
    run([VENV_PYTHON, "-m", "ensurepip", "--upgrade"], "2/6 pip 준비")
    run([VENV_PYTHON, "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements-build.txt"], "3/6 PyInstaller 설치")


def run_tests() -> None:
    # Never let build-time tests touch the user's real settings or SQLite DB.
    # user_data_dir() honors this override on every OS, including Windows.
    old = os.environ.get("PHYSICSMATHPOCKET_DATA_DIR")
    try:
        with tempfile.TemporaryDirectory(prefix="pmp-build-tests-") as tmp:
            os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = tmp
            run([VENV_PYTHON, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], "4/6 자동 검사")
    finally:
        if old is None:
            os.environ.pop("PHYSICSMATHPOCKET_DATA_DIR", None)
        else:
            os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = old


def build_app() -> None:
    for path in (ROOT / "build", ROOT / "dist" / "PhysicsMathPocket"):
        if path.exists():
            if ROOT.resolve() not in path.resolve().parents:
                raise BuildError("Build cleanup path escapes project root.")
            shutil.rmtree(path)
    run([VENV_PYTHON, "-m", "PyInstaller", "--noconfirm", "--clean", "PhysicsMathPocket.spec"], "5/6 Windows 앱 빌드")
    exe = ROOT / "dist" / "PhysicsMathPocket" / "PhysicsMathPocket.exe"
    if not exe.exists():
        raise BuildError("PyInstaller가 끝났지만 {}가 없습니다.".format(exe))
    write("앱 완성: {}".format(exe))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_update_agent() -> None:
    out = ROOT / "update_agent_dist"
    work = ROOT / "update_agent_build"
    for path in (out, work):
        if path.exists():
            if ROOT.resolve() not in path.resolve().parents:
                raise BuildError("Build cleanup path escapes project root.")
            shutil.rmtree(path)
    run([VENV_PYTHON, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--noconsole", "--name", "PhysicsMathPocketUpdater", "--distpath", str(out), "--workpath", str(work), "--specpath", str(work), str(ROOT / "update_agent.py")], "5.5/7 업데이트 에이전트 빌드")
    src = out / "PhysicsMathPocketUpdater.exe"
    if not src.exists():
        raise BuildError("업데이트 에이전트가 생성되지 않았습니다.")
    dst = ROOT / "dist" / "PhysicsMathPocket" / "PhysicsMathPocketUpdater.exe"
    shutil.copy2(src, dst)
    write("업데이트 에이전트 포함: {}".format(dst))


def build_update_package() -> Path:
    app_dir = ROOT / "dist" / "PhysicsMathPocket"
    if not (app_dir / "PhysicsMathPocket.exe").exists():
        raise BuildError("업데이트 패키지를 만들 앱 빌드가 없습니다.")
    release_dir = ROOT / "release"
    release_dir.mkdir(exist_ok=True)
    target = release_dir / ("PhysicsMathPocket_Update_" + RELEASE_LABEL + ".zip")
    files = []
    for path in sorted(app_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(app_dir).as_posix()
            files.append({"path": rel, "sha256": _sha256(path), "size": path.stat().st_size})
    manifest = {"product":"Physics + Math Pocket","version":APP_VERSION,"build":APP_BUILD,"channel":APP_CHANNEL,"format":1,"files":files}
    if target.exists(): target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("update-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for entry in files:
            zf.write(app_dir / entry["path"], "payload/" + entry["path"])
    write("무설치 업데이트 패키지 완성: {}".format(target))
    write("Update package SHA-256: {}".format(_sha256(target)))
    return target


def build_installer() -> None:
    exe = ROOT / "dist" / "PhysicsMathPocket" / "PhysicsMathPocket.exe"
    if not exe.exists():
        raise BuildError("먼저 앱을 빌드해야 합니다: {}".format(exe))
    iscc = find_iscc()
    if not iscc:
        raise BuildError(
            "Inno Setup Compiler(ISCC.exe)를 찾지 못했습니다. Inno Setup을 설치한 뒤 다시 실행하세요.\n"
            "공식 페이지: https://jrsoftware.org/isdl.php"
        )
    (ROOT / "release").mkdir(exist_ok=True)
    run([iscc, "/DMyAppVersion=" + APP_VERSION, "/DMyAppBuild=" + str(APP_BUILD), "installer.iss"], "6/6 설치 프로그램 빌드")
    setup = ROOT / "release" / ("PhysicsMathPocket_Setup_" + RELEASE_LABEL + ".exe")
    if not setup.exists():
        raise BuildError("설치 프로그램이 생성되지 않았습니다: {}".format(setup))
    write("설치 프로그램 완성: {}".format(setup))
    try:
        run(["certutil", "-hashfile", str(setup), "SHA256"], "SHA-256 확인")
    except BuildError:
        write("certutil 해시 확인은 건너뛰었습니다.")


def main() -> int:
    global VENV_PYTHON
    parser = argparse.ArgumentParser(description="Physics + Math Pocket Windows release builder")
    parser.add_argument("--app-only", action="store_true", help="PyInstaller 앱까지만 빌드")
    parser.add_argument("--installer-only", action="store_true", help="기존 앱으로 설치 프로그램만 빌드")
    parser.add_argument("--use-current-python", action="store_true")
    parser.add_argument("--skip-tool-install", action="store_true")
    parser.add_argument("--tests-only", action="store_true")
    parser.add_argument("--expected-tag", default="")
    args = parser.parse_args()

    LOG.write_text("Physics + Math Pocket {} build {}\n".format(APP_VERSION, APP_BUILD), encoding="utf-8")
    write("=" * 64)
    write(" Physics + Math Pocket {} · Windows 설치 프로그램 만들기".format(APP_VERSION))
    write("=" * 64)
    try:
        expected_tag = "v{}_Build{}".format(APP_VERSION, APP_BUILD)
        if args.expected_tag and args.expected_tag != expected_tag:
            raise BuildError("Release tag must be " + expected_tag)
        ensure_windows()
        ensure_python()
        if args.use_current_python or args.tests_only:
            VENV_PYTHON = Path(sys.executable)
        if args.tests_only:
            run_tests()
            return 0
        if args.installer_only:
            build_installer()
        else:
            if not args.use_current_python:
                create_venv()
            if not args.skip_tool_install:
                install_build_tools()
            run([VENV_PYTHON, "-c", "import sys,PyInstaller; print(sys.version); print('PyInstaller '+PyInstaller.__version__)"], "Build environment")
            run_tests()
            build_app()
            build_update_agent()
            build_update_package()
            run([VENV_PYTHON, "tools/verify_release.py"], "Verify generated update ZIP")
            if not args.app_only:
                build_installer()
        release_dir = ROOT / "release"
        targets = [release_dir / ("PhysicsMathPocket_Update_" + RELEASE_LABEL + ".zip"), release_dir / ("PhysicsMathPocket_Setup_" + RELEASE_LABEL + ".exe")]
        (release_dir / "SHA256SUMS.txt").write_text("".join("{}  {}\n".format(_sha256(p), p.name) for p in targets if p.is_file()), encoding="ascii")
        write("\n완료되었습니다. release 폴더를 확인하세요.")
        return 0
    except (BuildError, OSError, subprocess.SubprocessError) as exc:
        write("\n[빌드 실패] {}".format(exc))
        write("로그 파일: {}".format(LOG))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
