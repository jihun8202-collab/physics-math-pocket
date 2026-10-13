# Physics + Math Pocket

물리·수학·과학 개념 사전과 국어 학습을 제공하는 Windows 앱입니다. 현재 버전은 **3.1.6 · Build 31600**입니다.

이 프로젝트는 실제 사용하던 3.1.5 Beta 2 소스를 이어서 개발합니다. 즐겨찾기, 개념별 메모, 최근 검색, 사용자 개념, SQLite 저장소, 단위 변환, 상수, 공식과 계산기를 유지합니다.

## 설치

[최신 릴리스](https://github.com/jihun8202-collab/physics-math-pocket/releases/latest)에서 `PhysicsMathPocket_Setup_*.exe`를 내려받아 실행하세요. 사용자 데이터는 앱 설치 위치와 별도로 `%LOCALAPPDATA%\PhysicsMathPocket`에 저장됩니다. 설치 파일은 코드 서명되지 않았습니다.

앱의 업데이트 센터에서 새 버전을 확인할 수 있습니다. 시작할 때 자동 확인이 기본으로 켜져 있으며, 사용자가 설치를 선택하면 검증한 ZIP을 적용한 뒤 다시 시작합니다. 네트워크 실패 시 기존 오프라인 학습 기능을 계속 사용할 수 있습니다.

## 학습 내용

기존 50,000개 항목은 자세한 설명이 있는 기초 개념 2,363개와 확장 색인 47,637개로 구성되어 있습니다. 새 버전은 이를 모두 보존하고, 물리 심화 설명과 국어 개념 및 확인 문제를 더합니다. 색인을 완성된 설명과 구분해 표시합니다.

새 물리 실험은 공기저항을 받는 포물선, 비선형 진자, 감쇠 용수철 운동입니다. 시간 재생·일시정지·초기화, 단위와 실시간 계산값을 통해 매개변수가 결과에 미치는 영향을 확인합니다. 교육용 모델의 가정은 실험 화면에 표시됩니다.

## 소스로 실행

Python 3.9 이상에서 `python main.py`를 실행하세요. 표준 라이브러리와 Tkinter를 사용합니다. 빌드에 필요한 패키지는 `requirements-build.txt`에 있습니다.

```powershell
python build_release.py --tests-only --use-current-python --skip-tool-install
python build_release.py
```

Windows 설치 파일 빌드에는 Inno Setup이 필요합니다. [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md)와 [GITHUB_UPDATE_SETUP.md](GITHUB_UPDATE_SETUP.md)를 확인하세요.

## 자동 빌드 및 릴리스

`main` 변경 및 Pull Request는 회귀 테스트와 Windows 앱 빌드를 실행합니다. `v3.1.6_Build31600`처럼 버전과 빌드가 일치하는 태그를 push하면 설치 파일, 업데이트 ZIP, 파일별 검사 정보와 SHA256SUMS를 릴리스에 게시합니다. 저장소 설정이나 코드에 개인 토큰을 넣지 않습니다.

[변경 내역](RELEASE_NOTES.md) · [기존 프로젝트 라이선스](LICENSE.md) · [내용 출처](SOURCES.md)
