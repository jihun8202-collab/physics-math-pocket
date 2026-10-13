# GitHub Releases 업데이트 서버 설정

1. GitHub에 공개 저장소를 만듭니다. 예: `owner/PhysicsMathPocket`.
2. 이 프로젝트 전체를 저장소에 올립니다. 비밀번호나 Personal Access Token을 앱 코드에 넣지 마세요.
3. 앱 `설정 → 업데이트 → GitHub 저장소`에 `owner/repository`를 입력하고 소스를 `github` 또는 `auto`로 선택합니다.
4. 태그를 push하면 `.github/workflows/release.yml`이 Windows에서 테스트/빌드하고 Release에 ZIP + Setup.exe를 게시하도록 준비되어 있습니다.
5. 앱은 `PhysicsMathPocket_Update_*.zip`을 우선 받고 GitHub asset SHA-256을 검증합니다. 패키지 내부 파일도 다시 SHA-256 검증한 뒤 TEMP의 업데이트 에이전트가 설치 폴더 파일만 교체하고 앱을 재시작합니다.

공개 GitHub Release 조회에는 앱 사용자 토큰이 필요하지 않습니다.
