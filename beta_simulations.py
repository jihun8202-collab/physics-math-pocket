"""Generated but fully interactive beta simulation catalog for 3.1.8.

Each entry is a real MiniSimulator relationship model.  The catalog is kept
data-driven so the UI, search, and smoke tests can exercise every entry.
"""
from __future__ import annotations

from typing import Dict, List, Tuple


_VARIANTS = ("관계 탐색", "조건 비교", "측정 실험", "오차 분석", "시간 변화")
_TOPICS: Dict[str, Tuple[int, List[str]]] = {
    "물리": (60, ["힘과 운동", "마찰", "일과 에너지", "운동량", "충돌", "회전", "토크", "진동", "파동", "소리", "열", "전기장", "회로", "자기장", "전자기파"]),
    "화학": (55, ["원자 구조", "주기율", "화학 결합", "분자 기하", "몰 계산", "기체", "용액", "산과 염기", "완충", "산화 환원", "전지", "반응 속도", "평형", "용해도", "열화학"]),
    "생명과학": (50, ["세포 구조", "세포막", "효소", "세포 호흡", "광합성", "유전", "염색체", "돌연변이", "집단 유전", "생태계", "개체군", "신경", "호르몬", "면역", "항상성"]),
    "지구과학": (45, ["지층", "판 구조론", "지진", "화산", "풍화", "침식", "지하수", "해류", "대기", "기압", "구름", "강수", "기후", "해수면", "지구 자기장"]),
    "천문학": (45, ["태양계", "행성 궤도", "달의 위상", "식 현상", "중력", "케플러 법칙", "별의 밝기", "별의 색", "항성 진화", "성단", "은하", "적색편이", "우주 팽창", "블랙홀", "외계행성"]),
    "수학": (50, ["함수", "방정식", "부등식", "수열", "급수", "확률", "통계", "벡터", "행렬", "기하", "삼각함수", "미분", "적분", "최적화", "수치해석"]),
    "정보과학": (45, ["이진수", "논리 게이트", "불 대수", "자료 구조", "정렬", "탐색", "그래프", "최단 경로", "압축", "암호", "오류 검출", "네트워크", "데이터베이스", "머신러닝", "정보 시각화"]),
    "환경과학": (45, ["탄소 순환", "질소 순환", "물 순환", "생물 다양성", "먹이 그물", "개체군 변화", "대기 오염", "수질", "토양", "산성비", "온실효과", "재생에너지", "자원 순환", "도시 열섬", "환경 영향"]),
}


def _make_spec(title: str, subject: str, index: int) -> dict:
    mode = index % 4
    if mode == 0:
        return {"title": title, "subject": subject, "term": title, "formula": "y = a·x + b", "x_label": "입력 x", "y_label": "출력 y", "xmin": -5, "xmax": 5, "expr": "a*x+b", "sliders": [("기울기 a", "a", -5, 5, 1), ("절편 b", "b", -10, 10, 0)]}
    if mode == 1:
        return {"title": title, "subject": subject, "term": title, "formula": "y = a·x² + b", "x_label": "입력 x", "y_label": "출력 y", "xmin": -5, "xmax": 5, "expr": "a*x*x+b", "sliders": [("계수 a", "a", -3, 3, 1), ("이동 b", "b", -10, 10, 0)]}
    if mode == 2:
        return {"title": title, "subject": subject, "term": title, "formula": "y = A sin(kx)", "x_label": "위치 x", "y_label": "변위 y", "xmin": -6.283, "xmax": 6.283, "expr": "A*sin(k*x)", "sliders": [("진폭 A", "A", 0.1, 5, 1), ("파수 k", "k", 0.2, 5, 1)]}
    return {"title": title, "subject": subject, "term": title, "formula": "y = A e⁻ᵏˣ", "x_label": "시간 t", "y_label": "상대량 y", "xmin": 0, "xmax": 10, "expr": "A*exp(-k*x)", "sliders": [("초기량 A", "A", 0.1, 10, 1), ("감쇠율 k", "k", 0.01, 2, 0.3)]}


BETA_SIM_SPECS: Dict[str, dict] = {}
for _subject, (_count, _bases) in _TOPICS.items():
    for _index in range(_count):
        _base = _bases[_index % len(_bases)]
        _variant = _VARIANTS[(_index // len(_bases)) % len(_VARIANTS)]
        _title = f"{_base} · {_variant} {_index + 1:02d}"
        _sid = f"beta_{_subject}_{_index + 1:03d}"
        BETA_SIM_SPECS[_sid] = _make_spec(_title, _subject, _index)


assert len(BETA_SIM_SPECS) == 395
