from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from core import resource_path, user_data_dir

USER_AGENT = "PhysicsMathPocket-Updater/3.1.7"


@dataclass
class ReleaseInfo:
    version: str
    build: int
    channel: str
    name: str
    notes: str = ""
    published_at: str = ""
    page_url: str = ""
    download_url: str = ""
    sha256: str = ""
    asset_name: str = ""
    local_path: str = ""
    asset_kind: str = "installer"

    @property
    def is_beta(self) -> bool:
        return self.channel.lower() in {"beta", "prerelease", "preview", "rc", "alpha"}

    @property
    def display_version(self) -> str:
        suffix = " Beta" if self.is_beta else ""
        return f"{self.version}{suffix} (Build {self.build})"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "build": self.build,
            "channel": self.channel,
            "name": self.name,
            "notes": self.notes,
            "published_at": self.published_at,
            "page_url": self.page_url,
            "download_url": self.download_url,
            "sha256": self.sha256,
            "asset_name": self.asset_name,
            "local_path": self.local_path,
            "asset_kind": self.asset_kind,
        }


@dataclass
class UpdateCheckResult:
    status: str
    message: str
    release: Optional[ReleaseInfo] = None
    source: str = ""


_VERSION_RE = re.compile(
    r"(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?"
    r"(?:[-_.]?(?P<pre>alpha|beta|rc|preview)[-_.]?(?P<pre_num>\d+)?)?",
    re.I,
)
_BUILD_RE = re.compile(r"(?:build|b)[-_. ]?(\d+)", re.I)
_LOCAL_SETUP_RE = re.compile(
    r"PhysicsMathPocket_Setup_(?P<version>\d+\.\d+\.\d+)"
    r"(?:[-_. ]?(?P<channel>beta|preview|rc|alpha|stable))?"
    r"(?:[-_. ]?(?:build|b)[-_. ]?(?P<build>\d+))?\.exe$",
    re.I,
)


def parse_version(value: str) -> Tuple[int, int, int, int, int]:
    text = str(value or "").strip().lstrip("vV")
    match = _VERSION_RE.search(text)
    if not match:
        return (0, 0, 0, -10, 0)
    major = int(match.group("major") or 0)
    minor = int(match.group("minor") or 0)
    patch = int(match.group("patch") or 0)
    pre = (match.group("pre") or "").lower()
    pre_num = int(match.group("pre_num") or 0)
    rank = {"alpha": -4, "beta": -3, "preview": -2, "rc": -1}.get(pre, 0)
    return (major, minor, patch, rank, pre_num)


def release_is_newer(release: ReleaseInfo, current_version: str, current_build: int) -> bool:
    candidate = parse_version(release.version)
    current = parse_version(current_version)
    if candidate != current:
        return candidate > current
    return int(release.build) > int(current_build)


def default_build_for_version(version: str, beta: bool = False) -> int:
    major, minor, patch, _rank, _pre_num = parse_version(version)
    base = major * 10000 + minor * 1000 + patch * 100
    return base + (1 if beta else 0)


def default_local_update_dir() -> Path:
    path = user_data_dir() / "UpdateInbox"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_config() -> Dict[str, Any]:
    try:
        return json.loads(resource_path("data/update_config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _request_json(url: str, timeout: float = 8.0) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json, application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _build_from_tag(tag: str, default: int = 0) -> int:
    match = _BUILD_RE.search(tag or "")
    return int(match.group(1)) if match else int(default)


def _normalize_digest(value: str) -> str:
    value = (value or "").strip().lower()
    if value.startswith("sha256:"):
        value = value.split(":", 1)[1]
    return value if re.fullmatch(r"[0-9a-f]{64}", value) else ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_from_github(item: Dict[str, Any], asset_contains: str, fallback_build: int = 0) -> ReleaseInfo:
    tag = str(item.get("tag_name") or item.get("name") or "")
    version_match = _VERSION_RE.search(tag.lstrip("vV"))
    version = version_match.group(0) if version_match else tag.lstrip("vV")
    version = re.sub(r"[-_.]?(alpha|beta|rc|preview)[-_.]?\d*$", "", version, flags=re.I)
    release_name = str(item.get("name") or "")
    release_body = str(item.get("body") or "")
    build = _build_from_tag(tag, 0) or _build_from_tag(release_name, 0) or _build_from_tag(release_body, fallback_build)
    prerelease = bool(item.get("prerelease"))
    channel = "beta" if prerelease else "stable"
    assets = item.get("assets") or []
    chosen: Dict[str, Any] = {}
    # 3.1.5+: prefer the in-place update package. Setup.exe remains a repair/first-install fallback.
    for asset in assets:
        name = str(asset.get("name") or "")
        lowered = name.casefold()
        if lowered.endswith(".zip") and "physicsmathpocket_update_" in lowered:
            chosen = asset
            break
    if not chosen:
        preferred = str(asset_contains or "").casefold()
        for asset in assets:
            name = str(asset.get("name") or "")
            if preferred and preferred in name.casefold() and name.lower().endswith(".exe"):
                chosen = asset
                break
    if not chosen:
        for asset in assets:
            if str(asset.get("name") or "").lower().endswith((".zip", ".exe")):
                chosen = asset
                break
    digest = _normalize_digest(str(chosen.get("digest") or ""))
    if not build:
        build = default_build_for_version(version, prerelease)
    return ReleaseInfo(
        version=version or "0.0.0",
        build=build,
        channel=channel,
        name=release_name or tag or "새 버전",
        notes=release_body.strip(),
        published_at=str(item.get("published_at") or item.get("created_at") or ""),
        page_url=str(item.get("html_url") or ""),
        download_url=str(chosen.get("browser_download_url") or ""),
        sha256=digest,
        asset_name=str(chosen.get("name") or ""),
        asset_kind="package" if str(chosen.get("name") or "").lower().endswith(".zip") else "installer",
    )


def _check_github(repository: str, channel: str, asset_contains: str, timeout: float) -> UpdateCheckResult:
    repo = repository.strip().strip("/")
    if not repo or "/" not in repo:
        return UpdateCheckResult("unconfigured", "GitHub 업데이트 저장소가 설정되지 않았습니다.")
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    payload = _request_json(url, timeout=timeout)
    if not isinstance(payload, list):
        return UpdateCheckResult("error", "GitHub 릴리스 응답 형식이 올바르지 않습니다.", source="github")
    candidates: List[ReleaseInfo] = []
    for item in payload:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        if channel != "beta" and item.get("prerelease"):
            continue
        candidates.append(_release_from_github(item, asset_contains))
    if not candidates:
        return UpdateCheckResult("no_release", "공개된 업데이트 릴리스를 찾지 못했습니다.", source="github")
    candidates.sort(key=lambda r: (parse_version(r.version), r.build), reverse=True)
    return UpdateCheckResult("found", "GitHub 업데이트 정보를 확인했습니다.", candidates[0], source="github")


def list_github_releases(repository: str, channel: str = "beta", asset_contains: str = "PhysicsMathPocket_Setup_", timeout: float = 8.0) -> List[ReleaseInfo]:
    """Return selectable public releases for the update history/rollback UI."""
    repo = repository.strip().strip("/")
    if not repo or "/" not in repo:
        return []
    payload = _request_json(f"https://api.github.com/repos/{repo}/releases?per_page=100", timeout=timeout)
    if not isinstance(payload, list):
        return []
    releases: List[ReleaseInfo] = []
    for item in payload:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        if channel != "beta" and item.get("prerelease"):
            continue
        release = _release_from_github(item, asset_contains)
        if release.download_url:
            releases.append(release)
    releases.sort(key=lambda r: (parse_version(r.version), r.build), reverse=True)
    return releases


def _manifest_releases(payload: Any, channel: str, *, base_dir: Optional[Path] = None) -> List[ReleaseInfo]:
    items: Iterable[Dict[str, Any]]
    if isinstance(payload, dict) and isinstance(payload.get("releases"), list):
        items = payload["releases"]
    elif isinstance(payload, dict):
        items = [payload]
    else:
        return []
    releases: List[ReleaseInfo] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_channel = str(item.get("channel") or "stable").lower()
        if channel != "beta" and item_channel != "stable":
            continue
        version = str(item.get("version") or "0.0.0")
        build = int(item.get("build") or default_build_for_version(version, item_channel != "stable"))
        file_value = str(item.get("file") or item.get("local_path") or "").strip()
        local_path = ""
        if file_value and base_dir is not None:
            candidate = Path(file_value)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            local_path = str(candidate.resolve())
        releases.append(ReleaseInfo(
            version=version,
            build=build,
            channel=item_channel,
            name=str(item.get("name") or f"Physics + Math Pocket {version}"),
            notes=str(item.get("notes") or ""),
            published_at=str(item.get("published_at") or ""),
            page_url=str(item.get("page_url") or ""),
            download_url=str(item.get("download_url") or ""),
            sha256=_normalize_digest(str(item.get("sha256") or "")),
            asset_name=str(item.get("asset_name") or (Path(file_value).name if file_value else "")),
            local_path=local_path,
            asset_kind=str(item.get("asset_kind") or ("package" if str(file_value).lower().endswith(".zip") else "installer")),
        ))
    return releases


def _check_manifest(url: str, channel: str, timeout: float) -> UpdateCheckResult:
    payload = _request_json(url, timeout=timeout)
    releases = _manifest_releases(payload, channel)
    if not releases:
        return UpdateCheckResult("no_release", "선택한 채널에 릴리스가 없습니다.", source="manifest")
    releases.sort(key=lambda r: (parse_version(r.version), r.build), reverse=True)
    return UpdateCheckResult("found", "업데이트 매니페스트를 확인했습니다.", releases[0], source="manifest")


def _release_from_setup_filename(path: Path) -> Optional[ReleaseInfo]:
    match = _LOCAL_SETUP_RE.search(path.name)
    if not match:
        return None
    version = match.group("version")
    raw_channel = (match.group("channel") or "stable").lower()
    channel = "beta" if raw_channel in {"beta", "preview", "rc", "alpha"} else "stable"
    build = int(match.group("build") or default_build_for_version(version, channel == "beta"))
    return ReleaseInfo(
        version=version,
        build=build,
        channel=channel,
        name=f"로컬 설치 파일 {path.name}",
        notes="파일 이름에서 버전 정보를 읽은 로컬 테스트 업데이트입니다.",
        asset_name=path.name,
        local_path=str(path.resolve()),
        sha256=sha256_file(path),
    )


def _check_local_folder(folder: Path, channel: str) -> UpdateCheckResult:
    folder.mkdir(parents=True, exist_ok=True)
    releases: List[ReleaseInfo] = []
    manifest_names = ["update-manifest.json", "PhysicsMathPocket_Update.json", "latest.json"]
    seen_manifests: set[Path] = set()
    for name in manifest_names:
        path = folder / name
        if path.exists():
            seen_manifests.add(path)
    for path in folder.glob("*.update.json"):
        seen_manifests.add(path)
    for path in sorted(seen_manifests):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            releases.extend(_manifest_releases(payload, channel, base_dir=path.parent))
        except Exception:
            continue
    # Zero-config test path: a correctly named Setup.exe is enough.
    for path in folder.glob("PhysicsMathPocket_Setup_*.exe"):
        release = _release_from_setup_filename(path)
        if release and (channel == "beta" or not release.is_beta):
            releases.append(release)
    # Drop manifest entries whose local file is missing.
    filtered: List[ReleaseInfo] = []
    for release in releases:
        if release.local_path:
            p = Path(release.local_path)
            if not p.exists() or p.suffix.lower() != ".exe":
                continue
            if not release.sha256:
                release.sha256 = sha256_file(p)
            if not release.asset_name:
                release.asset_name = p.name
        filtered.append(release)
    if not filtered:
        return UpdateCheckResult(
            "no_release",
            f"로컬 업데이트 폴더에 설치 파일이 없습니다.\n{folder}",
            source="local",
        )
    filtered.sort(key=lambda r: (parse_version(r.version), r.build), reverse=True)
    return UpdateCheckResult("found", "로컬 업데이트 폴더를 확인했습니다.", filtered[0], source="local")


def check_for_updates(
    current_version: str,
    current_build: int,
    *,
    channel: str = "stable",
    repository: str = "",
    manifest_url: str = "",
    local_dir: str = "",
    source_mode: str = "auto",
    timeout: float = 8.0,
) -> UpdateCheckResult:
    config = _load_config()
    repository = (repository or str(config.get("github_repository") or "")).strip()
    manifest_url = (manifest_url or str(config.get("manifest_url") or "")).strip()
    asset_contains = str(config.get("asset_name_contains") or "PhysicsMathPocket_Setup")
    channel = "beta" if str(channel).lower() == "beta" else "stable"
    source_mode = str(source_mode or "auto").lower()
    if source_mode not in {"auto", "local", "github", "manifest"}:
        source_mode = "auto"
    folder = Path(local_dir).expanduser() if str(local_dir or "").strip() else default_local_update_dir()

    def finalize(result: UpdateCheckResult) -> UpdateCheckResult:
        if result.release:
            if release_is_newer(result.release, current_version, current_build):
                result.status = "update_available"
                result.message = f"새 버전 {result.release.display_version}을 사용할 수 있습니다."
            else:
                result.status = "current"
                result.message = "현재 최신 버전을 사용 중입니다."
        return result

    try:
        if source_mode in {"auto", "local"}:
            local_result = _check_local_folder(folder, channel)
            if local_result.release:
                return finalize(local_result)
            if source_mode == "local":
                return local_result

        if source_mode in {"auto", "manifest"} and manifest_url:
            return finalize(_check_manifest(manifest_url, channel, timeout))
        if source_mode == "manifest":
            return UpdateCheckResult("unconfigured", "HTTPS manifest URL이 설정되지 않았습니다.", source="manifest")

        if source_mode in {"auto", "github"} and repository:
            return finalize(_check_github(repository, channel, asset_contains, timeout))
        if source_mode == "github":
            return UpdateCheckResult("unconfigured", "GitHub 저장소 owner/repo가 설정되지 않았습니다.", source="github")

        return UpdateCheckResult(
            "unconfigured",
            "로컬 UpdateInbox에는 새 설치 파일이 없고 온라인 업데이트 소스도 아직 설정되지 않았습니다.",
            source="auto",
        )
    except urllib.error.HTTPError as exc:
        return UpdateCheckResult("error", f"업데이트 서버 응답 오류: HTTP {exc.code}")
    except urllib.error.URLError as exc:
        return UpdateCheckResult("error", f"네트워크 연결을 확인하세요: {exc.reason}")
    except Exception as exc:
        return UpdateCheckResult("error", f"업데이트 확인 실패: {exc}")


def download_installer(release: ReleaseInfo, destination_dir: Optional[Path] = None, timeout: float = 30.0) -> Path:
    # Local dev/test updates do not need a second copy; hash them before launch.
    if release.local_path:
        source = Path(release.local_path)
        if not source.exists():
            raise FileNotFoundError(f"로컬 업데이트 파일을 찾을 수 없습니다: {source}")
        if not release.sha256:
            raise ValueError("로컬 업데이트 파일에 SHA-256 정보가 없습니다.")
        actual = sha256_file(source)
        if actual.lower() != release.sha256.lower():
            raise ValueError("로컬 업데이트 파일 SHA-256 검증에 실패했습니다. 설치하지 않습니다.")
        return source

    if not release.download_url:
        raise ValueError("이 릴리스에는 Windows 업데이트 파일 URL이 없습니다.")
    if not release.sha256:
        raise ValueError("안전한 자동 설치를 위해 SHA-256 값이 필요합니다. 릴리스 페이지에서 수동으로 받으세요.")
    folder = destination_dir or Path(tempfile.gettempdir()) / "PhysicsMathPocketUpdates"
    folder.mkdir(parents=True, exist_ok=True)
    filename = release.asset_name or (f"PhysicsMathPocket_Update_{release.version}.zip" if release.asset_kind == "package" else f"PhysicsMathPocket_Setup_{release.version}.exe")
    filename = re.sub(r"[^0-9A-Za-z가-힣._+-]+", "_", filename)
    target = folder / filename
    partial = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(release.download_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response, partial.open("wb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    actual = sha256_file(partial)
    if actual.lower() != release.sha256.lower():
        try:
            partial.unlink()
        except OSError:
            pass
        raise ValueError("업데이트 파일 SHA-256 검증에 실패했습니다. 설치하지 않습니다.")
    partial.replace(target)
    return target


def _find_update_agent() -> Path:
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "PhysicsMathPocketUpdater.exe")
    candidates.append(resource_path("PhysicsMathPocketUpdater.exe"))
    candidates.append(Path(__file__).resolve().parent / "dist" / "PhysicsMathPocket" / "PhysicsMathPocketUpdater.exe")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("PhysicsMathPocketUpdater.exe를 찾지 못했습니다. 3.1.5 빌드에서 업데이트 에이전트를 함께 빌드하세요.")


def launch_seamless_update(package_path: Path, *, restart: bool = True, rollback: bool = False) -> subprocess.Popen[Any]:
    """Start the external updater helper, then the main app may exit.

    The helper runs from TEMP so it can overwrite the installed application in place.
    User data lives outside the installation directory and is never part of the package.
    """
    if os.name != "nt":
        raise OSError("무중단 Windows 업데이트 실행은 Windows에서만 지원됩니다.")
    if package_path.suffix.lower() != ".zip":
        raise ValueError("무중단 업데이트 패키지는 .zip 형식이어야 합니다.")
    agent = _find_update_agent()
    temp_agent_dir = Path(tempfile.gettempdir()) / "PhysicsMathPocketUpdateAgent"
    temp_agent_dir.mkdir(parents=True, exist_ok=True)
    temp_agent = temp_agent_dir / "PhysicsMathPocketUpdater.exe"
    shutil.copy2(agent, temp_agent)
    install_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    restart_exe = install_dir / "PhysicsMathPocket.exe"
    args = [
        str(temp_agent),
        "--package", str(package_path),
        "--install-dir", str(install_dir),
        "--wait-pid", str(os.getpid()),
    ]
    if restart:
        args.extend(["--restart", str(restart_exe)])
    if rollback:
        args.extend(["--clear-user-data", "--user-data-dir", str(user_data_dir())])
    return subprocess.Popen(args, close_fds=True)


def launch_installer(path: Path, silent: bool = True) -> subprocess.Popen[Any]:
    if os.name != "nt":
        raise OSError("Windows 설치 파일 실행은 Windows에서만 지원됩니다.")
    args = [str(path)]
    if silent:
        args.extend(["/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART"])
    return subprocess.Popen(args, close_fds=True)
