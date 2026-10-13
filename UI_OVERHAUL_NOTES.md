# Physics + Math Pocket 3.1.5 Beta 2 — UI Overhaul Notes

## 목표
3.1.4/3.1.5의 50,000개 지식 데이터와 업데이트 엔진을 유지하면서, 오래된 3열 데스크톱 레이아웃을 버리고 탐색 중심의 새 셸로 재구성했습니다.

## 디자인 참고 원칙
이 프로젝트는 특정 회사 UI를 픽셀 단위로 복제하지 않습니다. 다음 공식 디자인 원칙을 참고해 Physics + Math Pocket 고유 UI로 재구성했습니다.

- Samsung One UI: task focus, natural interaction, visual comfort, responsive layouts
  - https://developer.samsung.com/one-ui/index.html
- Microsoft Fluent 2: natural on every platform, adaptive layout, familiar controls
  - https://fluent2.microsoft.design/design-principles
- Microsoft Windows materials: Mica as a long-lived window base layer, Acrylic for transient surfaces
  - https://learn.microsoft.com/en-us/windows/apps/develop/ui/system-backdrops
- Apple Human Interface Guidelines: hierarchy, simplicity, consistency, layered materials
  - https://developer.apple.com/design/human-interface-guidelines/design-principles
  - https://developer.apple.com/design/human-interface-guidelines/materials
  - https://developer.apple.com/design/human-interface-guidelines/layout

Samsung 공식 개발자 페이지에는 별도 "One UI 8.5 PC 앱 스펙"이 공개되어 있지 않으므로, 버전 번호 자체를 복제하지 않고 공개된 One UI 디자인 원칙을 기준으로 했습니다.

## 실제 변경점
- 상단 가로 메뉴 제거 → 왼쪽 Navigation Rail
- 좌/중앙/우 3열 고정 레이아웃 제거 → 넓은 단일 콘텐츠 영역
- 홈 화면 완전 재구성
  - 대형 검색 Hero
  - 6개 과목 카드
  - 최근 검색 / 즐겨찾기 2열 카드
  - 학습 도구 바로가기
- 검색 결과
  - 상단 과목 필터 + 수준/기능 필터
  - 영구 사이드바 제거
- 업데이트 센터
  - 업데이트 상태 Hero
  - 현재 설치 / 업데이트 설정 2열 정보 카드
  - 릴리스 노트 영역
  - 고급/테스트 영역 분리
- 설정
  - 더 큰 모달과 명확한 상단 정보 영역
- 로딩 화면
  - 독립 Splash
  - 진행 바 / 새 아이콘 / 레이어드 배경
- 아이콘
  - 새 원본 atom + sigma 계열 아이콘
  - PNG 1024/512 + multi-size ICO
  - Inno Setup wizard 이미지 갱신
- Windows 11
  - 지원되는 경우 DWM dark title bar / rounded corner / main-window system backdrop를 best-effort로 요청
  - 미지원 OS에서는 자동으로 일반 Tkinter 표면으로 fallback

## 기술적 한계
Tkinter는 WinUI 3, SwiftUI, Samsung Android UI 프레임워크가 아닙니다. 따라서 Microsoft Mica/Apple Liquid Glass/Samsung One UI 컴포넌트를 네이티브 그대로 사용하는 것이 아니라, 레이아웃·계층·간격·표면 설계 원칙을 적용한 독자 구현입니다.
