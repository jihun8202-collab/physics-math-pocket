# Physics + Math Pocket

물리·수학·과학 개념 사전과 국어 학습을 제공하는 Windows 앱입니다. 현재 버전은 **3.1.7 · Build 31700**입니다.

이 프로젝트는 실제 사용하던 3.1.5 Beta 2 소스를 이어서 개발합니다. 즐겨찾기, 개념별 메모, 최근 검색, 사용자 개념, SQLite 저장소, 단위 변환, 상수, 공식과 계산기를 유지합니다.

## 설치

[최신 릴리스](https://github.com/jihun8202-collab/physics-math-pocket/releases/latest)에서 `PhysicsMathPocket_Setup_*.exe`를 내려받아 실행하세요. 사용자 데이터는 앱 설치 위치와 별도로 `%LOCALAPPDATA%\PhysicsMathPocket`에 저장됩니다. 설치 파일은 코드 서명되지 않았습니다.

앱의 업데이트 센터에서 새 버전을 확인할 수 있습니다. 시작할 때 자동 확인이 기본으로 켜져 있으며, 사용자가 설치를 선택하면 검증한 ZIP을 적용한 뒤 다시 시작합니다. 네트워크 실패 시 기존 오프라인 학습 기능을 계속 사용할 수 있습니다.

## 학습 내용

기존 50,000개 항목은 자세한 설명이 있는 기초 개념 2,363개와 확장 색인 47,637개로 구성되어 있습니다. 새 버전은 이를 모두 보존하고, 물리 심화 설명과 국어 개념 및 확인 문제를 더합니다. 색인을 완성된 설명과 구분해 표시합니다.

새 물리 실험은 2~6개 물체의 2차원 충돌, 일정한 힘과 가속 운동, 공기저항을 받는 포물선, 비선형 진자, 감쇠 용수철 운동입니다. 시간 재생·일시정지·초기화, 단위와 실시간 계산값을 통해 조건이 결과에 미치는 영향을 확인합니다. 기존 힘·포물선·용수철·탄성 충돌 항목도 새 실험으로 연결됩니다.

충돌 실험은 마찰·회전이 없는 원판의 연속 충돌 시점을 계산합니다. 질량·반지름·위치·속도, 반발계수, 반사 벽·열린 경계·주기 경계를 선택할 수 있습니다. 주기 경계는 반대편 공간으로 연결되는 모델이며, 반사 벽의 외부 충격량을 물체끼리의 운동량 변화와 구분합니다. 전체 운동량·운동에너지·손실과 계산 잔차를 함께 표시합니다. 동시에 여러 원판이 닿으면 명시된 강체 충돌 모델을 사용하며 실제 변형·접촉 시간은 다루지 않습니다.

가속 운동은 해석식으로 위치와 속도를 계산합니다. 나머지 시간 실험은 1/240초의 계산 간격을 사용하며 화면 갱신 속도와 물리 시간을 분리합니다. 관계식 그래프의 표시점은 순방향으로 이동하고, 극점이나 정의되지 않은 구간은 선으로 잇지 않습니다. 모델의 가정은 각 화면에 표시됩니다. [OpenStax 충돌 설명](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions)과 [PhET Collision Lab](https://phet.colorado.edu/en/simulations/collision-lab)을 참고했습니다. 이 앱은 PhET 제품이 아니며 동일한 완성도나 학습 효과를 검증한 것은 아닙니다.

## 소스로 실행

Python 3.9 이상에서 `python main.py`를 실행하세요. 표준 라이브러리와 Tkinter를 사용합니다. 빌드에 필요한 패키지는 `requirements-build.txt`에 있습니다.

```powershell
python build_release.py --tests-only --use-current-python --skip-tool-install
python build_release.py
```

Windows 설치 파일 빌드에는 Inno Setup이 필요합니다. [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md)와 [GITHUB_UPDATE_SETUP.md](GITHUB_UPDATE_SETUP.md)를 확인하세요.

## 자동 빌드 및 릴리스

`main` 변경 및 Pull Request는 회귀 테스트와 Windows 앱 빌드를 실행합니다. `v3.1.7_Build31700`처럼 버전과 빌드가 일치하는 태그를 push하면 설치 파일, 업데이트 ZIP, 파일별 검사 정보와 SHA256SUMS를 릴리스에 게시합니다. 저장소 설정이나 코드에 개인 토큰을 넣지 않습니다.

[변경 내역](RELEASE_NOTES.md) · [기존 프로젝트 라이선스](LICENSE.md) · [내용 출처](SOURCES.md)
