# 종합 지식 사전 · v3.5.5 문제은행 개발 명세 (WIP)

> 이 문서는 **요구사항과 구현 현황을 구분**합니다. 현재 코드가 350,000문제를 제공한다고 주장하지 않습니다.

## 확정 목표

- 대상 과목 7개: 수학, 물리, 화학, 생명과학, 지구과학, 천문학, 국어
- 과목별 **서로 다른 고유 문항 50,000개**, 합계 **350,000개**
- 모든 개념 상세 화면의 설명 아래 **확인문제 5칸**
- 난이도: 기초, 중급, 심화, 최상위
- 유형: 개념 확인, 계산, 적용, 자료 해석, 추론
- 객관식 정답과 설명, 출처, 편집 검수 상태, 연결 개념, 유일한 ID가 있어야 함
- 기존 인체 실험실·물리 시뮬레이션·국어 학습·즐겨찾기·메모·업데이트 데이터 삭제 금지
- 종합 지식 사전 브랜드와 Pocket Glass UI는 별도 진행 항목

## 정확한 목표 수학

목표 개념 122,500개 × 화면당 5문제 = **612,500개 개념별 노출 자리**.
고유 문제 350,000개를 기반으로 관련 개념 간 검증된 문항을 재사용할 수 있지만,
서로 다른 문제를 하나의 숫자에 부풀려 계산할 수 없으며 연관성 없는 내용으로 자리를 채우면 안 됨.
부족한 자리에는 **검증된 문제 준비 중**을 명확히 보여 준다.

## 이번 브랜치에 구현된 것

- 기존 국어 자체 작성 문제 **42개** 읽기
- 각 과목에서 예시 개념 1개씩 출처 연결 문제 5개씩 확보. 국어 품사는 신규 4개 + 기존 1개
- 신규 자체 작성 문제 **34개**, 총 **76개**, 7과목 분류 가능
- 문제 검증 `quiz_engine.py`, 개념별 5칸 `quiz_panel.py`, 필터 탐색 `quiz_browser.py`
- 사용자 PC에 정답·오답 기록을 원자적으로 저장, 최근 오답/정답률/난이도/문제 유형으로 추천
- 대용량 인덱스를 위한 편집 완료 JSONL → SQLite 구축 도구 `tools/build_quiz_db_355.py`
- 테스트 `tests/test_quiz_engine_355.py`

## 자료 검증·도입 정책

검증되지 않은 원문이나 자동 생성 문장으로 목표 숫자를 채우지 않는다. 학술·교육·국어 출처에
기반하여 **문제를 직접 작성하고 정답과 해설을 독립 검산**한다. 원문 문제의 무단 복사 및
출처 확인 없는 사실 단정은 금지한다. 또한 참고 링크가 붙었다는 이유만으로
모든 문항의 사실 검토 또는 저작권 검토가 완료되었다고 주장하지 않는다.

개별 JSONL 레코드는 `id`, `subject`, `concept_id` 또는 `concept_name`,
`difficulty`, `kind`, `question`, `choices`, `answer_index`,
`explanation`, `source`, `review_status`를 요구한다.

### 실제로 검수한 데이터 가져오기

```powershell
python tools/build_quiz_db_355.py reviewed_questions.jsonl --acknowledge-reviewed
python -m unittest discover -s tests -p "test_quiz_engine_355.py" -v
```

실제 에디터 검수 증빙 없이 `--acknowledge-reviewed`를 사용해서는 안 된다.
완성된 SQLite는 `data/quiz_bank_355.sqlite3`로 배치되고 기존 앱 빌드 과정에서 데이터와 함께 패키징된다.
스마트 추천은 **오프라인 규칙 기반**이며 LLM 모델 학습/서버 API 호출이 없다.

## 학술 내용 검토를 위한 기준 출처

- 수학: [OpenStax 일차함수](https://openstax.org/books/algebra-and-trigonometry-2e/pages/4-1-linear-functions)
- 물리: [OpenStax 뉴턴 제2법칙](https://openstax.org/books/college-physics-2e/pages/4-3-newtons-second-law-of-motion-concept-of-a-system)
- 화학: [OpenStax 원자 구조](https://openstax.org/books/chemistry-atoms-first-2e/pages/2-3-atomic-structure-and-symbolism)
- 생명과학: [OpenStax 진핵세포](https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells)
- 지구과학: [USGS 지진파](https://www.usgs.gov/programs/earthquake-hazards/science-earthquakes)
- 천문학: [NASA 태양](https://science.nasa.gov/sun/)
- 국어: [국립국어원 품사 설명](https://www.korean.go.kr/front/onlineQna/onlineQnaView.do?mn_id=&pageIndex=1&qna_seq=336203)

## 버전과 배포

이 브랜치의 3.5.5는 **개발 목표**이며 `core.APP_VERSION`은 3.5.0 Beta 상태이다.
완성도와 기존 회귀 테스트를 검증한 후 변경하고 태그/설치 파일/자동 업데이트를 배포한다.
지금은 앱 사용자에게 미완성 내용을 자동 업데이트로 내보내지 않는다.
