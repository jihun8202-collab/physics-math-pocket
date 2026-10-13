# 빌드 및 업데이트 배포

Windows x64 Python 3.12, PyInstaller 6.21.0, Inno Setup 6 또는 7을 사용합니다.

```powershell
python build_release.py
```

전용 `.buildenv`를 준비하고 기존 기능·업데이트·새 콘텐츠·시뮬레이션 테스트를 실행한 뒤 앱 EXE, 업데이트 에이전트, 업데이트 ZIP, 설치 프로그램을 생성합니다. ZIP에는 파일별 SHA-256을 넣습니다. 생성한 ZIP을 실제 업데이트 에이전트로 임시 설치 폴더에 적용하고 모든 파일의 크기와 해시를 다시 확인합니다. 결과와 전체 로그는 `release/`, `build_release.log`에 남습니다.

이미 빌드 도구를 설치한 x64 Python을 사용할 때는 `python build_release.py --use-current-python --skip-tool-install`을 사용할 수 있습니다. 실제 Python 및 PyInstaller 버전이 로그에 기록됩니다. 설치 프로그램만 다시 만들려면 `python build_release.py --installer-only`를 사용합니다.

설치 프로그램은 기존 실제 설치와 동일한 AppId `68D9A3E3-1F4A-4772-90A7-77D4BC2B2A56`를 사용합니다. 이전 설치 위치를 재사용하며 `%LOCALAPPDATA%\PhysicsMathPocket`의 즐겨찾기·메모·사용자 SQLite 데이터·설정을 업데이트 파일에 넣거나 삭제하지 않습니다.

등록된 공개 저장소는 [jihun8202-collab/physics-math-pocket](https://github.com/jihun8202-collab/physics-math-pocket)입니다. main 및 pull request 검사는 전체 테스트, EXE 빌드, 업데이트 ZIP 적용 검증을 수행합니다. `v3.1.7_Build31700`처럼 버전과 빌드가 일치하는 태그를 푸시하면 설치 프로그램과 ZIP, `SHA256SUMS.txt`를 Releases에 올립니다. 태그와 앱 버전이 다르거나 업데이트 설정의 저장소가 실제 GitHub 저장소와 다르면 릴리스가 실패합니다. Actions의 일회성 `GITHUB_TOKEN`을 사용하며 앱이나 소스에 개인 토큰을 넣지 않습니다.

3.1.7에서는 운동 상태와 표시 위치를 분리하며, 재생·일시정지·재시작과 실제 시간 진행을 검증합니다. 앱 버전은 `core.py`, 실행 파일 버전 리소스는 `version_info.txt`에 기록합니다. 설치 프로그램의 숫자 버전과 결과 파일명은 빌드 명령이 전달하는 버전·빌드에서 생성합니다. 기존 설치 ID는 유지합니다.

GitHub에서 실행한 결과와 로컬 검사는 별개입니다. 워크플로 파일을 만들거나 로컬 빌드가 통과한 것만으로 원격 워크플로의 성공을 주장하지 않습니다.

참고: [GitHub workflow token](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token), [GitHub Release CLI](https://cli.github.com/manual/gh_release_create).
