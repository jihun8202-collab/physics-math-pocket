from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

SOURCES = [
    {
        "id": "openstax",
        "name": "OpenStax College Physics 2e",
        "organization": "OpenStax, Rice University",
        "url": "https://openstax.org/details/books/college-physics-2e",
        "scope": "고전역학, 유체, 파동, 열, 전자기학, 광학, 현대물리의 기본 개념",
        "license": "CC BY 4.0",
        "note": "용어 선정과 교과 범위 점검에 활용. 앱의 한국어 설명은 그대로 복사하지 않고 새로 작성함."
    },
    {
        "id": "bipm",
        "name": "The International System of Units (SI Brochure, 9th ed.)",
        "organization": "BIPM",
        "url": "https://www.bipm.org/en/publications/si-brochure",
        "scope": "SI 기본단위, 유도단위, 단위 표기 원칙",
        "license": "CC BY 4.0",
        "note": "단위와 차원 설명의 기준 자료."
    },
    {
        "id": "nist",
        "name": "CODATA Fundamental Physical Constants",
        "organization": "NIST Physical Measurement Laboratory",
        "url": "https://physics.nist.gov/cuu/Constants/",
        "scope": "기본 물리상수와 권고값",
        "license": "미국 연방정부 자료 중심",
        "note": "상수 탭의 수치 기준. 2022 CODATA 권고값을 중심으로 수록."
    },
    {
        "id": "nasa",
        "name": "NASA Science Universe Glossary",
        "organization": "NASA",
        "url": "https://science.nasa.gov/universe/glossary/",
        "scope": "천체물리, 우주론, 관측 관련 용어",
        "license": "미국 연방정부 자료 중심",
        "note": "천체·우주 분야의 용어 범위와 설명 검토에 활용."
    },
    {
        "id": "cern",
        "name": "ATLAS Glossary / CERN Standard Model",
        "organization": "CERN",
        "url": "https://atlas.cern/glossary",
        "scope": "입자물리, 표준모형, 가속기 관련 용어",
        "license": "CERN 웹 이용 조건 적용",
        "note": "입자물리 용어의 의미와 범위 검토에 활용."
    },
    {
        "id": "korean_terms",
        "name": "국립국어원 온용어·사전 자료",
        "organization": "국립국어원",
        "url": "https://kli.korean.go.kr/term/",
        "scope": "한국어 전문용어 표기와 표제어 확인",
        "license": "자료별 이용 조건 적용",
        "note": "한국어 표제어 점검에 활용."
    }
]

CATEGORY_NOTES = {
    "측정·기초": "물리학에서 관측값을 수와 단위로 표현하고, 모델과 법칙을 정확히 읽기 위한 바탕 개념이다.",
    "운동학": "물체가 왜 움직이는지는 잠시 미뤄 두고, 위치와 시간의 변화를 수학적으로 나타내는 분야다.",
    "힘·에너지": "힘이 운동을 어떻게 바꾸고 에너지와 운동량이 어떻게 전달·보존되는지를 다룬다.",
    "회전·평형": "회전 운동, 토크, 각운동량과 물체가 넘어지거나 돌지 않는 조건을 다룬다.",
    "유체": "액체와 기체의 압력, 흐름, 부력과 점성 같은 거시적 성질을 다룬다.",
    "진동·파동·소리": "반복 운동과 공간을 따라 전달되는 교란, 그리고 소리의 성질을 다룬다.",
    "열·열역학": "온도, 열, 내부에너지와 에너지 변환의 방향 및 한계를 다룬다.",
    "전기·자기": "전하, 전기장, 회로, 자기장과 전자기 유도를 하나의 체계로 다룬다.",
    "빛·광학": "빛의 진행, 반사·굴절·간섭과 렌즈 및 광자의 성질을 다룬다.",
    "상대성이론": "빛의 속도와 시공간, 중력에 대한 고전역학 이후의 설명을 다룬다.",
    "양자·원자": "아주 작은 규모에서 에너지와 물질이 연속적 직관과 다르게 행동하는 법칙을 다룬다.",
    "핵·입자": "원자핵의 변화와 물질을 이루는 기본입자 및 기본 상호작용을 다룬다.",
    "천체·우주": "행성의 궤도부터 별, 블랙홀, 우주의 팽창까지 큰 규모의 물리 현상을 다룬다."
}

CATEGORY_SOURCES = {
    "측정·기초": ["bipm", "nist", "openstax", "korean_terms"],
    "운동학": ["openstax", "korean_terms"],
    "힘·에너지": ["openstax", "korean_terms"],
    "회전·평형": ["openstax", "korean_terms"],
    "유체": ["openstax", "korean_terms"],
    "진동·파동·소리": ["openstax", "korean_terms"],
    "열·열역학": ["openstax", "bipm", "korean_terms"],
    "전기·자기": ["openstax", "bipm", "korean_terms"],
    "빛·광학": ["openstax", "bipm", "korean_terms"],
    "상대성이론": ["openstax", "nasa", "korean_terms"],
    "양자·원자": ["openstax", "nist", "korean_terms"],
    "핵·입자": ["openstax", "cern", "nist", "korean_terms"],
    "천체·우주": ["nasa", "openstax", "korean_terms"]
}

terms: list[dict] = []


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-").lower()
    return text or f"term-{len(terms)+1}"


def add(category: str, ko: str, en: str, summary: str, *, formula: str = "", unit: str = "", example: str = "", aliases: str = "", related: str = "", level: str = "중등", caution: str = "") -> None:
    detail_parts = [summary, CATEGORY_NOTES[category]]
    if formula:
        detail_parts.append("대표식은 상황과 가정이 맞을 때 사용해야 하며, 각 기호의 뜻과 단위를 함께 확인한다.")
    if unit:
        detail_parts.append(f"대표적으로 쓰는 SI 단위 또는 표기는 {unit}이다.")
    terms.append({
        "id": slug(en),
        "name_ko": ko,
        "name_en": en,
        "aliases": [a.strip() for a in aliases.split(",") if a.strip()],
        "category": category,
        "level": level,
        "summary": summary,
        "detail": " ".join(detail_parts),
        "formula": formula,
        "unit": unit,
        "example": example,
        "caution": caution,
        "related": [r.strip() for r in related.split(",") if r.strip()],
        "sources": CATEGORY_SOURCES[category]
    })

# 측정·기초
add("측정·기초", "물리량", "physical quantity", "측정하거나 계산하여 수치와 단위로 나타낼 수 있는 물리적 성질.", example="길이 2.0 m, 시간 3.0 s처럼 수와 단위를 함께 쓴다.", related="SI 단위계,차원,측정")
add("측정·기초", "스칼라", "scalar", "크기만으로 완전히 표현되는 물리량.", example="질량 3 kg, 온도 20 °C, 에너지 5 J.", related="벡터,물리량")
add("측정·기초", "벡터", "vector", "크기와 방향을 함께 가져야 완전히 표현되는 물리량.", example="동쪽으로 5 m/s인 속도.", related="스칼라,변위,속도,힘")
add("측정·기초", "SI 단위계", "International System of Units", "전 세계 과학과 공학에서 공통으로 사용하는 국제단위계.", aliases="국제단위계,SI", example="길이 m, 질량 kg, 시간 s, 전류 A, 온도 K.", related="기본단위,유도단위,접두어")
add("측정·기초", "기본단위", "base unit", "SI에서 서로 독립적으로 정한 일곱 기본 물리량의 단위.", example="m, kg, s, A, K, mol, cd.", related="SI 단위계,유도단위")
add("측정·기초", "유도단위", "derived unit", "기본단위의 곱과 나눗셈으로 표현되는 단위.", example="힘의 단위 N = kg·m/s².", related="기본단위,차원")
add("측정·기초", "차원", "dimension", "물리량이 길이·질량·시간 등 기본 종류에 어떻게 의존하는지 나타낸 표현.", example="속도의 차원은 L T⁻¹.", related="차원 분석,단위")
add("측정·기초", "차원 분석", "dimensional analysis", "식의 양변 차원이 같은지 확인하거나 물리량 사이의 형태를 추정하는 방법.", example="거리 = 속력×시간은 L=(L/T)×T로 차원이 맞다.", related="차원,단위 환산")
add("측정·기초", "단위 환산", "unit conversion", "같은 물리량을 다른 단위로 바꾸되 실제 크기는 유지하는 계산.", example="72 km/h = 20 m/s.", related="환산계수,차원 분석")
add("측정·기초", "유효숫자", "significant figures", "측정값에서 신뢰할 수 있는 자릿수와 마지막 추정 자릿수를 함께 나타내는 규칙.", example="2.30 m는 유효숫자 3개다.", related="측정 불확도,반올림")
add("측정·기초", "측정", "measurement", "정해진 기준과 비교하여 물리량의 값을 얻는 과정.", example="자를 이용해 책상 길이를 재는 것.", related="정확도,정밀도,불확도")
add("측정·기초", "오차", "measurement error", "측정값과 참값 또는 기준값의 차이.", formula="오차 = 측정값 - 기준값", related="상대오차,불확도", caution="실험에서는 참값을 정확히 모르는 경우가 많아 오차와 불확도를 구분한다.")
add("측정·기초", "상대오차", "relative error", "오차의 크기를 기준값의 크기로 나눈 비율.", formula="상대오차 = |오차| / |기준값|", unit="무차원 또는 %", related="오차,백분율 오차")
add("측정·기초", "정확도", "accuracy", "측정 결과가 기준값이나 참값에 얼마나 가까운지를 나타내는 정도.", related="정밀도,오차")
add("측정·기초", "정밀도", "precision", "반복 측정값들이 서로 얼마나 가깝게 모이는지를 나타내는 정도.", related="정확도,재현성")
add("측정·기초", "측정 불확도", "measurement uncertainty", "측정 결과에 합리적으로 붙일 수 있는 값의 범위를 나타내는 정량적 정보.", example="(10.0 ± 0.1) cm.", related="유효숫자,오차")
add("측정·기초", "좌표계", "coordinate system", "위치를 수로 나타내기 위해 원점과 축, 방향을 정한 체계.", example="수평 x축과 수직 y축을 정한다.", related="기준계,위치")
add("측정·기초", "기준계", "reference frame", "위치와 속도를 측정하는 관찰자의 좌표계와 시간 기준.", example="달리는 열차 안과 지면에서 본 공의 속도는 다를 수 있다.", related="좌표계,상대속도,관성계")
add("측정·기초", "관성계", "inertial frame", "외력이 없는 물체가 등속 직선 운동을 하는 것으로 관측되는 기준계.", related="뉴턴 운동 제1법칙,기준계,상대성 원리", level="고등")
add("측정·기초", "계", "system", "분석하려고 경계를 정해 선택한 물체 또는 물체들의 집합.", example="충돌하는 두 수레를 하나의 계로 잡을 수 있다.", related="외부,내부에너지,고립계")
add("측정·기초", "고립계", "isolated system", "주변과 에너지와 물질을 교환하지 않는 이상적인 계.", related="닫힌계,보존법칙")
add("측정·기초", "상태량", "state function", "계가 어떤 상태에 있는지만으로 값이 정해지고, 그 상태에 이른 경로에는 의존하지 않는 양.", example="내부에너지, 압력, 온도.", related="경로함수,열역학")
add("측정·기초", "보존법칙", "conservation law", "정해진 조건에서 어떤 물리량의 전체값이 시간에 따라 변하지 않는다는 법칙.", example="고립계의 에너지 보존.", related="에너지 보존,운동량 보존,전하 보존")
add("측정·기초", "물리상수", "physical constant", "자연 법칙에 나타나는 보편적인 수치 또는 정해진 상수.", example="빛의 속도 c, 플랑크 상수 h.", related="CODATA,빛의 속도,플랑크 상수")
add("측정·기초", "모델", "physical model", "복잡한 자연 현상에서 중요한 요소를 남기고 단순화해 설명·예측하는 표현.", example="공기 저항을 무시한 점입자 모델.", related="가정,이론,법칙")
add("측정·기초", "가정", "assumption", "문제를 풀거나 모델을 세울 때 성립한다고 두는 조건.", example="마찰이 없고 줄의 질량이 없다고 가정한다.", related="모델,근사")
add("측정·기초", "근사", "approximation", "작은 효과를 무시하거나 간단한 식으로 바꾸어 충분히 정확한 결과를 얻는 방법.", example="작은 각도에서 sin θ ≈ θ.", related="모델,오차")

# 운동학
add("운동학", "위치", "position", "정한 좌표계에서 물체가 있는 곳을 나타내는 벡터 또는 좌표.", unit="m", related="좌표계,변위")
add("운동학", "거리", "distance", "물체가 실제로 이동한 경로의 전체 길이.", unit="m", example="한 바퀴 돌아 출발점에 오면 거리는 원둘레이지만 변위는 0이다.", related="변위,속력")
add("운동학", "변위", "displacement", "처음 위치에서 나중 위치로 향하는 위치 변화 벡터.", formula="Δx = x_f - x_i", unit="m", related="거리,속도")
add("운동학", "속력", "speed", "이동 거리가 시간에 따라 얼마나 빠르게 늘어나는지를 나타내는 스칼라.", formula="평균 속력 = 총거리 / 걸린 시간", unit="m/s", related="속도,거리")
add("운동학", "속도", "velocity", "변위가 시간에 따라 변하는 비율로, 크기와 방향을 가진다.", formula="v_avg = Δx / Δt", unit="m/s", related="속력,변위,가속도")
add("운동학", "평균 속도", "average velocity", "전체 시간 동안의 변위를 전체 시간으로 나눈 값.", formula="v_avg = Δx / Δt", unit="m/s", related="순간 속도,변위")
add("운동학", "순간 속도", "instantaneous velocity", "특정 순간에서 위치가 시간에 따라 변하는 비율.", formula="v = dx/dt", unit="m/s", related="평균 속도,미분", level="고등")
add("운동학", "가속도", "acceleration", "속도가 시간에 따라 변하는 비율.", formula="a_avg = Δv / Δt", unit="m/s²", related="속도,등가속도 운동")
add("운동학", "평균 가속도", "average acceleration", "일정 시간 동안의 속도 변화를 그 시간으로 나눈 값.", formula="a_avg = Δv / Δt", unit="m/s²", related="순간 가속도")
add("운동학", "순간 가속도", "instantaneous acceleration", "특정 순간에서 속도가 시간에 따라 변하는 비율.", formula="a = dv/dt", unit="m/s²", level="고등", related="평균 가속도,미분")
add("운동학", "등속 직선 운동", "uniform linear motion", "속도의 크기와 방향이 일정하여 직선 위를 같은 시간마다 같은 변위만큼 움직이는 운동.", formula="x = x₀ + vt", related="속도,관성")
add("운동학", "등가속도 운동", "constant acceleration motion", "가속도가 일정한 운동.", formula="v=v₀+at; x=x₀+v₀t+½at²; v²=v₀²+2aΔx", related="가속도,자유낙하")
add("운동학", "자유낙하", "free fall", "공기 저항을 무시할 때 중력만 받아 움직이는 운동.", formula="a = g", unit="m/s²", example="지표 근처에서 g≈9.8 m/s².", related="중력가속도,등가속도 운동", caution="무거운 물체가 본질적으로 더 빨리 떨어지는 것은 아니다.")
add("운동학", "중력가속도", "gravitational acceleration", "중력에 의해 생기는 가속도.", formula="g = GM/r²", unit="m/s²", related="자유낙하,만유인력")
add("운동학", "포물선 운동", "projectile motion", "공기 저항을 무시할 때 수평 방향 등속 운동과 수직 방향 등가속도 운동이 합쳐진 운동.", example="비스듬히 던진 공의 궤적.", related="성분 분해,자유낙하")
add("운동학", "상대속도", "relative velocity", "한 관찰자가 본 물체의 속도를 다른 기준계의 속도와 비교한 값.", formula="v_A/B = v_A - v_B", unit="m/s", related="기준계,속도")
add("운동학", "원운동", "circular motion", "물체가 원 궤도를 따라 움직이는 운동.", related="각속도,구심가속도")
add("운동학", "등속 원운동", "uniform circular motion", "속력은 일정하지만 방향이 계속 변하는 원운동.", formula="a_c = v²/r", related="구심가속도,구심력")
add("운동학", "각위치", "angular position", "회전한 정도를 기준 방향에 대한 각으로 나타낸 값.", unit="rad", related="각변위,각속도")
add("운동학", "각변위", "angular displacement", "각위치의 변화량.", formula="Δθ = θ_f - θ_i", unit="rad", related="각속도")
add("운동학", "각속도", "angular velocity", "각변위가 시간에 따라 변하는 비율.", formula="ω = Δθ/Δt", unit="rad/s", related="주기,접선속도")
add("운동학", "각가속도", "angular acceleration", "각속도가 시간에 따라 변하는 비율.", formula="α = Δω/Δt", unit="rad/s²", related="각속도,토크")
add("운동학", "주기", "period", "한 번의 반복 운동이 끝나는 데 걸리는 시간.", formula="T = 1/f", unit="s", related="진동수,원운동")
add("운동학", "진동수", "frequency", "1초 동안 반복되는 횟수.", formula="f = 1/T", unit="Hz", aliases="주파수", related="주기,각진동수")
add("운동학", "각진동수", "angular frequency", "주기 운동의 위상이 시간에 따라 변하는 빠르기를 라디안으로 나타낸 값.", formula="ω = 2πf = 2π/T", unit="rad/s", related="진동수,단순 조화 운동")
add("운동학", "접선속도", "tangential velocity", "원운동에서 궤도의 접선 방향을 향하는 순간 속도.", formula="v = rω", unit="m/s", related="각속도,원운동")
add("운동학", "구심가속도", "centripetal acceleration", "원운동 물체의 속도 방향을 바꾸며 원의 중심을 향하는 가속도.", formula="a_c = v²/r = rω²", unit="m/s²", related="구심력,등속 원운동")

# 힘·에너지
add("힘·에너지", "힘", "force", "물체의 운동 상태를 바꾸거나 변형을 일으킬 수 있는 벡터량.", formula="F = ma", unit="N", related="합력,가속도")
add("힘·에너지", "합력", "net force", "한 물체에 작용하는 모든 힘을 벡터로 더한 결과.", formula="ΣF = ma", unit="N", aliases="알짜힘", related="힘,뉴턴 운동 제2법칙")
add("힘·에너지", "관성", "inertia", "물체가 자신의 운동 상태 변화를 저항하는 성질.", related="질량,뉴턴 운동 제1법칙")
add("힘·에너지", "질량", "mass", "물체의 관성 크기와 물질의 양을 나타내는 물리량.", unit="kg", related="관성,무게", caution="질량과 무게는 같은 뜻이 아니다.")
add("힘·에너지", "무게", "weight", "중력이 물체에 작용하는 힘.", formula="W = mg", unit="N", related="질량,중력")
add("힘·에너지", "뉴턴 운동 제1법칙", "Newton's first law", "합력이 0이면 물체는 정지 상태 또는 등속 직선 운동 상태를 유지한다.", aliases="관성 법칙", related="관성,관성계")
add("힘·에너지", "뉴턴 운동 제2법칙", "Newton's second law", "물체의 가속도는 합력에 비례하고 질량에 반비례한다.", formula="ΣF = ma", related="합력,가속도,질량")
add("힘·에너지", "뉴턴 운동 제3법칙", "Newton's third law", "두 물체가 상호작용할 때 서로에게 크기가 같고 방향이 반대인 힘을 동시에 가한다.", aliases="작용 반작용 법칙", related="상호작용,힘", caution="작용과 반작용은 서로 다른 물체에 작용하므로 한 물체에서 상쇄되는 두 힘이 아니다.")
add("힘·에너지", "중력", "gravity", "질량을 가진 물체 사이에 작용하는 인력 또는 시공간의 곡률로 설명되는 상호작용.", related="만유인력,일반상대성이론")
add("힘·에너지", "만유인력 법칙", "law of universal gravitation", "두 점질량 사이의 중력 크기는 질량의 곱에 비례하고 거리의 제곱에 반비례한다.", formula="F = Gm₁m₂/r²", unit="N", related="중력,중력가속도")
add("힘·에너지", "수직항력", "normal force", "접촉면이 물체를 면에 수직인 방향으로 미는 힘.", unit="N", aliases="법선력", related="접촉력,마찰력", caution="항상 mg와 같은 것은 아니다.")
add("힘·에너지", "장력", "tension", "팽팽한 줄이나 케이블이 연결된 물체를 당기는 힘.", unit="N", related="힘,도르래")
add("힘·에너지", "마찰력", "friction", "접촉한 두 표면 사이의 상대 운동 또는 운동하려는 경향을 방해하는 힘.", unit="N", related="정지 마찰력,운동 마찰력")
add("힘·에너지", "정지 마찰력", "static friction", "두 표면이 미끄러지지 않을 때 상대 운동을 막도록 필요한 만큼 생기는 마찰력.", formula="f_s ≤ μ_s N", unit="N", related="최대 정지 마찰력,운동 마찰력")
add("힘·에너지", "운동 마찰력", "kinetic friction", "두 표면이 서로 미끄러질 때 작용하는 마찰력.", formula="f_k = μ_k N", unit="N", related="정지 마찰력,마찰계수")
add("힘·에너지", "마찰계수", "coefficient of friction", "접촉면의 성질을 나타내며 마찰력과 수직항력의 관계에 쓰는 무차원 계수.", formula="μ = f/N", unit="무차원", related="마찰력")
add("힘·에너지", "탄성력", "elastic force", "변형된 물체가 원래 모양으로 돌아가려 하며 가하는 힘.", unit="N", related="후크 법칙,탄성에너지")
add("힘·에너지", "후크 법칙", "Hooke's law", "탄성 한계 안에서 용수철의 복원력은 변형량에 비례하고 반대 방향이다.", formula="F = -kx", unit="N", related="용수철 상수,탄성력")
add("힘·에너지", "구심력", "centripetal force", "원운동에 필요한 중심 방향 합력을 가리키는 역할 이름.", formula="F_c = mv²/r = mrω²", unit="N", related="구심가속도,원운동", caution="별도의 새로운 힘이 아니라 중력·마찰력·장력 등이 구심력 역할을 할 수 있다.")
add("힘·에너지", "일", "work", "힘이 작용한 방향으로 물체가 변위할 때 전달되는 에너지.", formula="W = Fd cosθ", unit="J", related="에너지,일률")
add("힘·에너지", "일-에너지 정리", "work-energy theorem", "물체에 한 합력의 일은 운동에너지 변화량과 같다.", formula="W_net = ΔK", related="일,운동에너지")
add("힘·에너지", "에너지", "energy", "계가 일을 하거나 변화를 일으킬 수 있는 능력을 정량화한 보존량.", unit="J", related="일,에너지 보존")
add("힘·에너지", "운동에너지", "kinetic energy", "물체의 운동 때문에 가지는 에너지.", formula="K = ½mv²", unit="J", related="일-에너지 정리,위치에너지")
add("힘·에너지", "중력 위치에너지", "gravitational potential energy", "중력장 안에서 물체의 위치와 관련된 에너지.", formula="U = mgh (지표 근처); U=-GMm/r", unit="J", related="위치에너지,중력")
add("힘·에너지", "탄성 위치에너지", "elastic potential energy", "용수철 같은 탄성체가 변형되어 저장한 에너지.", formula="U_s = ½kx²", unit="J", related="후크 법칙,탄성력")
add("힘·에너지", "역학적 에너지", "mechanical energy", "운동에너지와 위치에너지의 합.", formula="E_mech = K + U", unit="J", related="에너지 보존,비보존력")
add("힘·에너지", "에너지 보존 법칙", "conservation of energy", "고립계의 전체 에너지는 형태가 바뀔 수는 있어도 생성되거나 사라지지 않는다.", related="보존법칙,열역학 제1법칙")
add("힘·에너지", "보존력", "conservative force", "한 일이 경로와 무관하고 시작점과 끝점에만 의존하며 위치에너지를 정의할 수 있는 힘.", example="중력, 이상적인 용수철 힘.", related="위치에너지,비보존력")
add("힘·에너지", "비보존력", "non-conservative force", "한 일이 이동 경로에 의존하며 역학적 에너지를 다른 형태로 바꿀 수 있는 힘.", example="운동 마찰력.", related="마찰력,역학적 에너지")
add("힘·에너지", "일률", "power", "일을 하거나 에너지를 전달하는 빠르기.", formula="P = W/t = dE/dt", unit="W", related="일,에너지")
add("힘·에너지", "효율", "efficiency", "투입한 에너지나 일률 중 유용하게 얻은 부분의 비율.", formula="η = 유용한 출력 / 전체 입력", unit="무차원 또는 %", related="일률,열기관")
add("힘·에너지", "운동량", "momentum", "질량과 속도의 곱으로 정의되는 벡터량.", formula="p = mv", unit="kg·m/s", related="충격량,운동량 보존")
add("힘·에너지", "충격량", "impulse", "힘이 일정 시간 작용하여 만든 운동량 변화.", formula="J = ∫Fdt = Δp", unit="N·s", related="운동량,힘")
add("힘·에너지", "운동량 보존 법칙", "conservation of momentum", "계에 작용하는 외부 충격량이 0이면 전체 운동량이 일정하다.", formula="Σp_before = Σp_after", related="충돌,보존법칙")
add("힘·에너지", "충돌", "collision", "짧은 시간 동안 물체들이 큰 힘을 주고받아 운동량과 에너지가 재분배되는 상호작용.", related="탄성 충돌,비탄성 충돌")
add("힘·에너지", "탄성 충돌", "elastic collision", "전체 운동량과 전체 운동에너지가 모두 보존되는 충돌.", related="충돌,운동량 보존")
add("힘·에너지", "비탄성 충돌", "inelastic collision", "운동량은 보존되지만 운동에너지 일부가 열·소리·변형 에너지 등으로 바뀌는 충돌.", related="완전 비탄성 충돌,충돌")
add("힘·에너지", "완전 비탄성 충돌", "perfectly inelastic collision", "충돌 뒤 두 물체가 붙어서 같은 속도로 움직이는 비탄성 충돌.", related="비탄성 충돌,운동량 보존")

# 회전·평형
add("회전·평형", "토크", "torque", "힘이 물체를 회전시키려는 효과를 나타내는 벡터량.", formula="τ = rF sinθ", unit="N·m", aliases="돌림힘", related="회전축,각가속도")
add("회전·평형", "회전관성", "moment of inertia", "회전 운동 상태 변화에 대한 물체의 저항 정도로, 질량의 분포와 회전축에 따라 달라진다.", formula="I = Σmr²", unit="kg·m²", aliases="관성 모멘트", related="토크,각운동량")
add("회전·평형", "회전 운동의 제2법칙", "rotational form of Newton's second law", "회전축에 대한 합토크가 회전관성과 각가속도의 곱과 같다.", formula="Στ = Iα", related="토크,회전관성")
add("회전·평형", "각운동량", "angular momentum", "회전 운동의 양을 나타내는 보존 가능한 벡터량.", formula="L = r×p; 고정축에서 L=Iω", unit="kg·m²/s", related="토크,각운동량 보존")
add("회전·평형", "각운동량 보존", "conservation of angular momentum", "외부 토크가 0이면 계의 전체 각운동량이 일정하다.", formula="L_i = L_f", related="각운동량,회전관성")
add("회전·평형", "회전 운동에너지", "rotational kinetic energy", "회전하는 물체가 가지는 운동에너지.", formula="K_rot = ½Iω²", unit="J", related="회전관성,각속도")
add("회전·평형", "질량중심", "center of mass", "계의 전체 질량이 운동을 대표하도록 가중평균한 위치.", formula="r_cm = Σmᵢrᵢ / Σmᵢ", unit="m", related="무게중심,병진운동")
add("회전·평형", "무게중심", "center of gravity", "중력에 의한 전체 토크를 하나의 무게가 작용하는 것처럼 나타낼 수 있는 점.", related="질량중심,평형", caution="중력장이 거의 균일하면 질량중심과 무게중심이 일치한다.")
add("회전·평형", "병진 평형", "translational equilibrium", "물체에 작용하는 합력이 0인 상태.", formula="ΣF = 0", related="정적 평형,회전 평형")
add("회전·평형", "회전 평형", "rotational equilibrium", "어떤 축에 대해서도 합토크가 0인 상태.", formula="Στ = 0", related="병진 평형,토크")
add("회전·평형", "정적 평형", "static equilibrium", "물체가 정지해 있고 합력과 합토크가 모두 0인 상태.", formula="ΣF=0, Στ=0", related="병진 평형,회전 평형")
add("회전·평형", "안정 평형", "stable equilibrium", "조금 벗어나도 원래 평형 위치로 돌아가려는 상태.", example="그릇 바닥의 구슬.", related="불안정 평형,위치에너지")
add("회전·평형", "불안정 평형", "unstable equilibrium", "조금 벗어나면 평형 위치에서 더 멀어지는 상태.", example="언덕 꼭대기의 구슬.", related="안정 평형")
add("회전·평형", "지레", "lever", "받침점을 중심으로 막대를 회전시켜 힘의 크기나 방향을 바꾸는 단순기계.", formula="F₁r₁ = F₂r₂ (평형)", related="토크,역학적 이득")
add("회전·평형", "역학적 이득", "mechanical advantage", "기계가 입력 힘을 얼마나 크게 바꾸는지를 나타내는 비.", formula="MA = 출력 힘 / 입력 힘", unit="무차원", related="지레,효율")
add("회전·평형", "구름 운동", "rolling motion", "물체가 회전하면서 질량중심도 이동하는 운동.", formula="미끄럼 없음: v_cm = Rω", related="병진 운동,회전 운동에너지")

# 유체
add("유체", "유체", "fluid", "흐를 수 있으며 용기의 모양에 따라 변형되는 물질로, 액체와 기체를 포함한다.", related="액체,기체,압력")
add("유체", "밀도", "density", "단위 부피당 질량.", formula="ρ = m/V", unit="kg/m³", related="비중,부력")
add("유체", "압력", "pressure", "단위 면적에 수직으로 작용하는 힘.", formula="P = F/A", unit="Pa", related="유체 정역학,파스칼 원리")
add("유체", "정수압", "hydrostatic pressure", "정지한 유체에서 깊이에 따라 생기는 압력.", formula="P = P₀ + ρgh", unit="Pa", related="압력,깊이")
add("유체", "파스칼 원리", "Pascal's principle", "밀폐된 유체에 가한 압력 변화가 유체 전체에 거의 그대로 전달된다는 원리.", example="유압 브레이크와 유압 리프트.", related="압력,유압장치")
add("유체", "부력", "buoyant force", "유체 속 물체가 압력 차이 때문에 위쪽으로 받는 힘.", formula="F_B = ρ_fluid g V_displaced", unit="N", related="아르키메데스 원리,밀도")
add("유체", "아르키메데스 원리", "Archimedes' principle", "물체가 받는 부력은 물체가 밀어낸 유체의 무게와 같다.", related="부력,부피")
add("유체", "유량", "volume flow rate", "단위 시간에 단면을 통과하는 유체의 부피.", formula="Q = ΔV/Δt = Av", unit="m³/s", related="연속 방정식,유속")
add("유체", "연속 방정식", "continuity equation", "정상 흐름에서 질량 보존을 나타내는 식.", formula="ρAv = 일정; 비압축성 유체에서 A₁v₁=A₂v₂", related="유량,질량 보존")
add("유체", "베르누이 방정식", "Bernoulli's equation", "정상·비점성·비압축성 흐름의 한 유선에서 압력, 운동에너지, 위치에너지의 관계.", formula="P + ½ρv² + ρgh = 일정", related="압력,유속", caution="난류가 심하거나 점성 손실이 큰 실제 흐름에는 그대로 적용할 수 없다.")
add("유체", "점성", "viscosity", "유체 층 사이의 상대 운동을 방해하는 내부 마찰 성질.", unit="Pa·s (동점성 제외)", related="층류,항력")
add("유체", "층류", "laminar flow", "유체가 서로 섞임이 적은 매끄러운 층을 이루며 흐르는 상태.", related="난류,레이놀즈 수")
add("유체", "난류", "turbulent flow", "소용돌이와 불규칙한 속도 변화가 나타나는 복잡한 흐름.", related="층류,레이놀즈 수")
add("유체", "레이놀즈 수", "Reynolds number", "관성 효과와 점성 효과의 상대적 크기를 나타내어 흐름 상태를 판단하는 무차원 수.", formula="Re = ρvL/μ", unit="무차원", related="층류,난류")
add("유체", "표면장력", "surface tension", "액체 표면이 면적을 줄이려는 막처럼 행동하게 만드는 단위 길이당 힘 또는 단위 면적당 에너지.", unit="N/m", example="물방울이 둥글어지는 현상.", related="모세관 현상,응집력")
add("유체", "모세관 현상", "capillary action", "가는 관이나 좁은 틈에서 표면장력과 젖음성 때문에 액체가 오르거나 내려가는 현상.", related="표면장력,접촉각")
add("유체", "항력", "drag force", "유체 속에서 움직이는 물체의 상대 운동을 방해하는 힘.", unit="N", related="공기 저항,종단 속도")
add("유체", "종단 속도", "terminal velocity", "낙하 물체에서 중력과 부력·항력이 균형을 이루어 가속도가 0이 된 뒤의 일정한 속도.", unit="m/s", related="항력,자유낙하")

# 진동·파동·소리
add("진동·파동·소리", "진동", "oscillation", "평형 위치 주변에서 반복되는 운동이나 물리량의 변화.", related="주기,진폭")
add("진동·파동·소리", "단순 조화 운동", "simple harmonic motion", "복원력이 변위에 비례하고 반대 방향일 때 나타나는 사인·코사인 형태의 진동.", formula="a = -ω²x; x=A cos(ωt+φ)", related="용수철 진자,단진자")
add("진동·파동·소리", "진폭", "amplitude", "평형값에서 최대한 벗어난 크기.", unit="상황에 따라 m, Pa 등", related="진동,파동")
add("진동·파동·소리", "위상", "phase", "주기 운동이 한 주기 중 어느 단계에 있는지를 나타내는 양.", unit="rad 또는 °", related="위상차,간섭")
add("진동·파동·소리", "위상차", "phase difference", "두 진동 또는 파동의 위상이 얼마나 어긋나 있는지 나타낸 값.", unit="rad 또는 °", related="간섭,위상")
add("진동·파동·소리", "감쇠", "damping", "저항이나 마찰 때문에 진동의 에너지와 진폭이 시간에 따라 줄어드는 현상.", related="감쇠 진동,공명")
add("진동·파동·소리", "강제 진동", "forced oscillation", "외부에서 주기적인 힘을 받아 지속되는 진동.", related="공명,고유진동수")
add("진동·파동·소리", "고유진동수", "natural frequency", "계가 외부의 주기적 구동 없이 자유롭게 진동할 때 나타나는 고유한 진동수.", unit="Hz", related="공명,강제 진동")
add("진동·파동·소리", "공명", "resonance", "외부 구동 진동수가 계의 고유진동수와 가까울 때 진폭이 크게 증가하는 현상.", example="그네를 알맞은 박자로 밀 때 크게 흔들린다.", related="고유진동수,강제 진동")
add("진동·파동·소리", "파동", "wave", "물질의 대규모 이동 없이 에너지와 정보를 공간으로 전달하는 교란.", related="파장,진동수,파동속력")
add("진동·파동·소리", "매질", "medium", "역학적 파동이 전달될 때 진동을 전달하는 물질.", example="소리의 매질은 공기·물·고체가 될 수 있다.", related="음파,역학적 파동")
add("진동·파동·소리", "횡파", "transverse wave", "매질의 진동 방향이 파동의 진행 방향과 수직인 파동.", example="팽팽한 줄의 파동.", related="종파,편광")
add("진동·파동·소리", "종파", "longitudinal wave", "매질의 진동 방향이 파동의 진행 방향과 나란한 파동.", example="공기 중 음파의 압축과 팽창.", related="횡파,음파")
add("진동·파동·소리", "파장", "wavelength", "같은 위상인 이웃한 두 점 사이의 거리.", formula="v = fλ", unit="m", related="진동수,파동속력")
add("진동·파동·소리", "파수", "wave number", "공간에서 위상이 변하는 빠르기를 나타내는 양.", formula="k = 2π/λ", unit="rad/m", related="파장,각진동수", level="고등")
add("진동·파동·소리", "파동속력", "wave speed", "파동의 같은 위상 지점이 매질을 따라 이동하는 속력.", formula="v = fλ", unit="m/s", related="파장,진동수")
add("진동·파동·소리", "중첩 원리", "principle of superposition", "선형 범위에서 여러 파동이 겹칠 때 전체 변위가 각 파동 변위의 합이 되는 원리.", related="간섭,정상파")
add("진동·파동·소리", "간섭", "interference", "두 개 이상의 파동이 중첩되어 진폭이 커지거나 작아지는 현상.", related="보강 간섭,상쇄 간섭")
add("진동·파동·소리", "보강 간섭", "constructive interference", "위상이 맞는 파동이 겹쳐 합성 진폭이 커지는 간섭.", related="상쇄 간섭,위상차")
add("진동·파동·소리", "상쇄 간섭", "destructive interference", "위상이 반대인 파동이 겹쳐 합성 진폭이 작아지는 간섭.", related="보강 간섭,위상차")
add("진동·파동·소리", "회절", "diffraction", "파동이 장애물 가장자리나 좁은 틈을 지나며 퍼지는 현상.", related="간섭,파장")
add("진동·파동·소리", "반사", "wave reflection", "파동이 경계에서 되돌아오는 현상.", related="굴절,정상파")
add("진동·파동·소리", "굴절", "wave refraction", "파동이 속력이 다른 영역으로 들어갈 때 진행 방향과 파장이 변하는 현상.", related="스넬 법칙,파동속력")
add("진동·파동·소리", "정상파", "standing wave", "서로 반대 방향으로 진행하는 같은 진동수의 파동이 겹쳐 공간에 고정된 마디와 배가 생기는 파동.", related="마디,배,공명")
add("진동·파동·소리", "마디", "node", "정상파에서 진폭이 항상 0인 지점.", related="배,정상파")
add("진동·파동·소리", "배", "antinode", "정상파에서 진폭이 최대인 지점.", related="마디,정상파")
add("진동·파동·소리", "도플러 효과", "Doppler effect", "파원과 관찰자의 상대 운동 때문에 관측 진동수가 달라지는 현상.", example="다가오는 구급차의 사이렌이 더 높게 들린다.", related="진동수,적색편이")
add("진동·파동·소리", "음파", "sound wave", "물질 매질의 압력과 밀도 변화로 전달되는 역학적 파동.", related="종파,소리의 속력")
add("진동·파동·소리", "음속", "speed of sound", "소리 파동이 매질 속을 전달되는 속력.", unit="m/s", example="20 °C 공기에서 약 343 m/s.", related="음파,매질")
add("진동·파동·소리", "음압", "sound pressure", "소리 때문에 생기는 매질 압력의 순간적인 변화.", unit="Pa", related="소리 세기,데시벨")
add("진동·파동·소리", "소리 세기", "sound intensity", "단위 면적을 통과하는 평균 음향 일률.", formula="I = P/A", unit="W/m²", related="데시벨,음압")
add("진동·파동·소리", "데시벨", "decibel", "두 세기나 전력의 비를 로그 척도로 나타내는 단위.", formula="β = 10 log₁₀(I/I₀)", unit="dB", related="소리 세기,로그", caution="dB는 단순한 선형 눈금이 아니다. 10 dB 증가는 세기가 10배라는 뜻이다.")
add("진동·파동·소리", "맥놀이", "beats", "진동수가 조금 다른 두 파동이 겹쳐 소리의 세기가 주기적으로 커졌다 작아지는 현상.", formula="f_beat = |f₁-f₂|", unit="Hz", related="간섭,진동수")
add("진동·파동·소리", "기본진동", "fundamental mode", "정상파에서 가장 낮은 고유진동수를 갖는 진동 형태.", related="배음,정상파")
add("진동·파동·소리", "배음", "harmonic", "기본진동수의 정수배 진동수에 해당하는 성분 또는 진동 모드.", related="기본진동,음색")
add("진동·파동·소리", "음색", "timbre", "같은 높이와 크기의 소리도 다르게 느껴지게 하는 파형과 배음 구성의 특징.", related="배음,파형")

# 열·열역학
add("열·열역학", "온도", "temperature", "물체의 뜨겁고 차가운 정도를 나타내며 열평형의 방향을 결정하는 상태량.", unit="K (SI), °C", related="열,열평형")
add("열·열역학", "절대온도", "absolute temperature", "절대영도를 0으로 하는 열역학적 온도 척도.", formula="T(K)=t(°C)+273.15", unit="K", related="켈빈,절대영도")
add("열·열역학", "절대영도", "absolute zero", "열역학적 온도의 최저 한계인 0 K.", unit="0 K = -273.15 °C", related="절대온도,열역학 제3법칙", caution="고전적으로 입자 운동이 완전히 멈춘다는 단순 표현은 양자역학적으로 정확하지 않다.")
add("열·열역학", "열", "heat", "온도 차이 때문에 계의 경계를 넘어 전달되는 에너지.", unit="J", related="온도,내부에너지", caution="물체가 '열을 가지고 있다'기보다 내부에너지를 가지며 열은 전달 과정이다.")
add("열·열역학", "열평형", "thermal equilibrium", "접촉한 계들 사이에 순열전달이 없고 온도가 같은 상태.", related="열역학 제0법칙,온도")
add("열·열역학", "열용량", "heat capacity", "물체 전체의 온도를 1 K 높이는 데 필요한 열량.", formula="C = Q/ΔT", unit="J/K", related="비열")
add("열·열역학", "비열", "specific heat capacity", "물질 1 kg의 온도를 1 K 높이는 데 필요한 열량.", formula="Q = mcΔT", unit="J/(kg·K)", related="열용량,열량")
add("열·열역학", "잠열", "latent heat", "온도 변화 없이 상이 변할 때 단위 질량당 흡수하거나 방출하는 에너지.", formula="Q = mL", unit="J/kg", related="상전이,융해열,기화열")
add("열·열역학", "열팽창", "thermal expansion", "온도 변화로 물체의 길이·면적·부피가 변하는 현상.", formula="ΔL = αL₀ΔT", related="선팽창계수,온도")
add("열·열역학", "열전도", "thermal conduction", "물질의 거시적 이동 없이 입자 충돌과 전자 운동 등으로 열에너지가 전달되는 방식.", related="대류,복사")
add("열·열역학", "대류", "convection", "유체의 실제 이동으로 열이 전달되는 방식.", related="전도,복사")
add("열·열역학", "열복사", "thermal radiation", "물체가 전자기파를 방출하여 에너지를 전달하는 방식.", related="흑체복사,적외선")
add("열·열역학", "이상기체", "ideal gas", "분자 자체 부피와 분자 사이 힘을 무시하는 단순화된 기체 모델.", formula="PV = nRT", related="상태방정식,기체 분자 운동론")
add("열·열역학", "이상기체 상태방정식", "ideal gas law", "이상기체의 압력, 부피, 몰수, 절대온도의 관계.", formula="PV = nRT", related="이상기체,기체상수")
add("열·열역학", "기체 분자 운동론", "kinetic theory of gases", "기체의 압력과 온도를 많은 분자의 무질서한 운동과 충돌로 설명하는 이론.", related="이상기체,온도")
add("열·열역학", "내부에너지", "internal energy", "계를 이루는 미시적 입자들의 운동에너지와 상호작용 에너지의 합.", unit="J", related="열역학 제1법칙,상태량")
add("열·열역학", "열역학 제0법칙", "zeroth law of thermodynamics", "A와 B가 열평형이고 B와 C도 열평형이면 A와 C도 열평형이라는 법칙.", related="온도,열평형")
add("열·열역학", "열역학 제1법칙", "first law of thermodynamics", "계의 내부에너지 변화는 계에 들어온 열에서 계가 바깥에 한 일을 뺀 것과 같다.", formula="ΔU = Q - W (계가 한 일을 +로 둘 때)", related="에너지 보존,내부에너지", caution="교재마다 일 W의 부호 약속이 다를 수 있어 반드시 확인한다.")
add("열·열역학", "열역학 제2법칙", "second law of thermodynamics", "자연 과정의 방향과 열기관의 한계를 규정하며, 고립계의 엔트로피는 감소하지 않는다.", formula="ΔS_total ≥ 0", related="엔트로피,열기관")
add("열·열역학", "열역학 제3법칙", "third law of thermodynamics", "완전한 결정의 엔트로피가 절대영도에 가까워질수록 일정한 기준값에 접근한다는 법칙.", related="절대영도,엔트로피", level="고등")
add("열·열역학", "엔트로피", "entropy", "에너지의 분산 정도와 가능한 미시상태 수를 연결하며 자연 과정의 방향을 나타내는 상태량.", formula="ΔS = Q_rev/T; S=k_B lnΩ", unit="J/K", related="열역학 제2법칙,미시상태", level="고등")
add("열·열역학", "엔탈피", "enthalpy", "내부에너지에 압력과 부피의 곱을 더한 상태량.", formula="H = U + PV", unit="J", related="내부에너지,등압 과정", level="고등")
add("열·열역학", "등온 과정", "isothermal process", "온도가 일정하게 유지되는 열역학 과정.", formula="이상기체에서 PV=일정", related="단열 과정,이상기체")
add("열·열역학", "단열 과정", "adiabatic process", "계와 주변 사이에 열 교환이 없는 과정.", formula="Q=0; 이상기체 가역과정에서 PV^γ=일정", related="등온 과정,열역학 제1법칙")
add("열·열역학", "등압 과정", "isobaric process", "압력이 일정한 열역학 과정.", related="등적 과정,엔탈피")
add("열·열역학", "등적 과정", "isochoric process", "부피가 일정한 열역학 과정.", formula="W=0 (경계일)", aliases="정적 과정", related="등압 과정,열역학 제1법칙")
add("열·열역학", "열기관", "heat engine", "고온부에서 받은 열의 일부를 일로 바꾸고 나머지를 저온부로 내보내는 장치.", formula="η = W_out/Q_hot", related="효율,카르노 기관")
add("열·열역학", "카르노 기관", "Carnot engine", "두 열원 사이에서 작동하는 이상적인 가역 열기관으로 가능한 최대 효율을 갖는다.", formula="η_C = 1 - T_c/T_h", related="열기관,열역학 제2법칙")
add("열·열역학", "냉동기", "refrigerator", "외부에서 일을 받아 저온부의 열을 고온부로 옮기는 장치.", related="열펌프,성능계수")
add("열·열역학", "상", "phase of matter", "물질이 균일한 물리적 성질을 보이는 상태 영역.", example="고체, 액체, 기체, 플라스마.", related="상전이,임계점")
add("열·열역학", "상전이", "phase transition", "온도나 압력 변화 등에 따라 물질의 상이 바뀌는 현상.", example="융해, 응고, 기화, 응축.", related="잠열,상")
add("열·열역학", "임계점", "critical point", "액체와 기체의 구분이 사라지는 임계온도와 임계압력의 상태점.", related="상전이,초임계유체", level="고등")
add("열·열역학", "흑체", "blackbody", "들어오는 모든 전자기복사를 이상적으로 흡수하고 온도에 따른 스펙트럼으로 복사하는 물체.", related="흑체복사,플랑크 법칙")
add("열·열역학", "흑체복사", "blackbody radiation", "흑체가 온도에 따라 방출하는 연속적인 전자기복사 스펙트럼.", related="플랑크 법칙,빈 변위 법칙")

# 전기·자기
add("전기·자기", "전하", "electric charge", "전자기 상호작용의 원인이 되는 물리량으로 양전하와 음전하가 있다.", unit="C", related="전하 보존,쿨롱 법칙")
add("전기·자기", "전하 보존 법칙", "conservation of electric charge", "고립계의 전체 전하는 일정하며 전하는 생성·소멸하기보다 이동하거나 쌍으로 변환된다.", related="전하,보존법칙")
add("전기·자기", "전하의 양자화", "quantization of charge", "고립된 물체의 전하가 기본전하 e의 정수배로 나타나는 성질.", formula="q = ne", related="기본전하,전자")
add("전기·자기", "쿨롱 법칙", "Coulomb's law", "두 점전하 사이 전기력의 크기가 전하량의 곱에 비례하고 거리의 제곱에 반비례한다.", formula="F = k|q₁q₂|/r²", unit="N", related="전기력,전기장")
add("전기·자기", "전기장", "electric field", "공간의 한 점에 놓인 단위 양전하가 받을 힘으로 정의되는 벡터장.", formula="E = F/q", unit="N/C 또는 V/m", related="전기력,전위")
add("전기·자기", "전기력선", "electric field line", "전기장의 방향과 상대적 세기를 시각화한 가상의 선.", related="전기장,등전위면")
add("전기·자기", "전위", "electric potential", "단위 전하당 전기 위치에너지.", formula="V = U/q", unit="V", related="전압,전기 위치에너지")
add("전기·자기", "전압", "voltage", "두 점 사이의 전위차.", formula="ΔV = ΔU/q", unit="V", aliases="전위차", related="전위,전류")
add("전기·자기", "전기 위치에너지", "electric potential energy", "전기장 안에서 전하의 배치와 위치에 관련된 에너지.", formula="U = qV", unit="J", related="전위,전기장")
add("전기·자기", "등전위면", "equipotential surface", "전위가 같은 점들로 이루어진 면.", related="전위,전기장", caution="전기장은 등전위면에 수직이다.")
add("전기·자기", "전기선속", "electric flux", "면을 통과하는 전기장의 정도를 나타내는 양.", formula="Φ_E = ∫E·dA", unit="N·m²/C", related="가우스 법칙,전기장", level="고등")
add("전기·자기", "가우스 법칙", "Gauss's law", "닫힌 면을 지나는 총 전기선속이 그 면 안의 순전하에 비례한다.", formula="∮E·dA = Q_enclosed/ε₀", related="전기선속,전기장", level="고등")
add("전기·자기", "도체", "electrical conductor", "전하 운반자가 비교적 자유롭게 이동할 수 있어 전류가 잘 흐르는 물질.", example="구리, 알루미늄.", related="부도체,반도체")
add("전기·자기", "부도체", "electrical insulator", "전하 운반자가 쉽게 이동하지 않아 전류가 잘 흐르지 않는 물질.", example="유리, 고무.", related="도체,유전체")
add("전기·자기", "유전체", "dielectric", "전기장에 놓이면 분극되어 전기 에너지를 저장하는 절연 물질.", related="분극,유전율,축전기")
add("전기·자기", "분극", "electric polarization", "유전체 내부의 양전하와 음전하 중심이 약간 분리되거나 쌍극자가 정렬되는 현상.", related="유전체,전기쌍극자")
add("전기·자기", "축전기", "capacitor", "서로 떨어진 두 도체에 전하와 전기 에너지를 저장하는 소자.", formula="C = Q/ΔV", related="전기용량,유전체")
add("전기·자기", "전기용량", "capacitance", "축전기가 주어진 전압에서 얼마나 많은 전하를 저장하는지 나타내는 양.", formula="C = Q/V", unit="F", related="축전기,유전율")
add("전기·자기", "전류", "electric current", "단면을 통과하는 전하량의 시간 변화율.", formula="I = ΔQ/Δt", unit="A", related="전압,저항")
add("전기·자기", "전류밀도", "current density", "단위 면적당 흐르는 전류를 방향과 함께 나타낸 벡터량.", formula="J = I/A (균일할 때)", unit="A/m²", related="전류,표류속도", level="고등")
add("전기·자기", "표류속도", "drift velocity", "전기장 때문에 도체 속 전하 운반자가 평균적으로 이동하는 속도.", formula="I = nqAv_d", unit="m/s", related="전류,전류밀도", level="고등")
add("전기·자기", "저항", "electrical resistance", "전류의 흐름을 방해하는 정도.", formula="R = V/I", unit="Ω", related="옴 법칙,비저항")
add("전기·자기", "비저항", "resistivity", "물질 자체가 전류 흐름을 방해하는 정도를 나타내는 고유 물성.", formula="R = ρL/A", unit="Ω·m", related="저항,전도도")
add("전기·자기", "전도도", "electrical conductivity", "물질이 전류를 얼마나 잘 흐르게 하는지 나타내며 비저항의 역수.", formula="σ = 1/ρ", unit="S/m", related="비저항,도체")
add("전기·자기", "옴 법칙", "Ohm's law", "온도 등 조건이 일정한 옴성 소자에서 전압이 전류에 비례한다.", formula="V = IR", related="저항,전류")
add("전기·자기", "직렬 연결", "series circuit", "소자들이 한 경로로 이어져 같은 전류가 흐르는 연결.", formula="R_eq = R₁+R₂+…", related="병렬 연결,회로")
add("전기·자기", "병렬 연결", "parallel circuit", "소자들이 같은 두 점에 연결되어 같은 전압이 걸리는 연결.", formula="1/R_eq = 1/R₁+1/R₂+…", related="직렬 연결,회로")
add("전기·자기", "전기 일률", "electric power", "회로에서 전기에너지가 전달되거나 변환되는 빠르기.", formula="P = VI = I²R = V²/R", unit="W", related="전력,줄열")
add("전기·자기", "줄열", "Joule heating", "저항을 지나는 전류 때문에 전기에너지가 열에너지로 바뀌는 현상.", formula="Q = I²Rt", unit="J", related="전기 일률,저항")
add("전기·자기", "기전력", "electromotive force", "전원이 단위 전하에 공급하는 에너지로, 실제 힘이 아니라 에너지/전하의 양.", formula="ε = W/q", unit="V", related="전압,전지")
add("전기·자기", "키르히호프 전류 법칙", "Kirchhoff's current law", "회로의 한 접점으로 들어오는 전류의 합과 나가는 전류의 합이 같다.", formula="ΣI_in = ΣI_out", related="전하 보존,회로")
add("전기·자기", "키르히호프 전압 법칙", "Kirchhoff's voltage law", "닫힌 회로 고리를 한 바퀴 돌며 전위차를 더한 값이 0이다.", formula="ΣΔV = 0", related="에너지 보존,회로")
add("전기·자기", "RC 회로", "RC circuit", "저항과 축전기로 이루어져 충전과 방전에 시간 지연이 나타나는 회로.", formula="τ = RC", related="축전기,시정수", level="고등")
add("전기·자기", "자기장", "magnetic field", "움직이는 전하와 자성체가 만드는 벡터장으로 움직이는 전하와 전류에 힘을 준다.", unit="T", related="자기력,로렌츠 힘")
add("전기·자기", "로렌츠 힘", "Lorentz force", "전기장과 자기장 속에서 전하가 받는 힘.", formula="F = q(E + v×B)", unit="N", related="전기장,자기장")
add("전기·자기", "자기력", "magnetic force", "자기장 속에서 움직이는 전하나 전류가 받는 힘.", formula="F = qvB sinθ; F=ILB sinθ", unit="N", related="로렌츠 힘,자기장")
add("전기·자기", "자기선속", "magnetic flux", "면을 통과하는 자기장의 정도를 나타내는 양.", formula="Φ_B = ∫B·dA", unit="Wb", related="전자기 유도,패러데이 법칙")
add("전기·자기", "전자기 유도", "electromagnetic induction", "회로를 지나는 자기선속이 변할 때 유도 기전력이 생기는 현상.", related="패러데이 법칙,렌츠 법칙")
add("전기·자기", "패러데이 유도 법칙", "Faraday's law of induction", "유도 기전력은 자기선속의 시간 변화율에 비례하고 부호는 렌츠 법칙을 따른다.", formula="ε = -dΦ_B/dt", related="전자기 유도,자기선속")
add("전기·자기", "렌츠 법칙", "Lenz's law", "유도 전류가 자기선속의 변화를 방해하는 방향으로 흐른다는 법칙.", related="패러데이 법칙,에너지 보존")
add("전기·자기", "인덕턴스", "inductance", "전류 변화에 의해 생기는 자기선속과 유도 기전력의 정도를 나타내는 양.", formula="ε = -L dI/dt", unit="H", related="자체 유도,코일")
add("전기·자기", "자체 유도", "self-induction", "한 회로의 전류 변화가 그 회로 자체에 유도 기전력을 만드는 현상.", related="인덕턴스,렌츠 법칙")
add("전기·자기", "상호 유도", "mutual induction", "한 회로의 전류 변화가 이웃 회로에 유도 기전력을 만드는 현상.", related="변압기,전자기 유도")
add("전기·자기", "교류", "alternating current", "크기와 방향이 시간에 따라 주기적으로 바뀌는 전류.", aliases="AC", related="직류,실효값")
add("전기·자기", "직류", "direct current", "전하가 한 방향으로 흐르며 방향이 바뀌지 않는 전류.", aliases="DC", related="교류,전류")
add("전기·자기", "실효값", "root mean square value", "교류가 저항에서 내는 평균 전력과 같은 효과를 내는 직류값.", formula="정현파에서 V_rms=V_max/√2", related="교류,전기 일률")
add("전기·자기", "변압기", "transformer", "상호 유도를 이용해 교류 전압과 전류의 크기를 바꾸는 장치.", formula="V_s/V_p = N_s/N_p (이상적)", related="상호 유도,교류")
add("전기·자기", "전자기파", "electromagnetic wave", "시간에 따라 변하는 전기장과 자기장이 서로를 만들어 공간을 전파하는 파동.", formula="c = 1/√(μ₀ε₀)", related="빛,맥스웰 방정식")
add("전기·자기", "전자기 스펙트럼", "electromagnetic spectrum", "진동수 또는 파장에 따라 배열한 전자기파 전체 범위.", example="라디오파, 마이크로파, 적외선, 가시광선, 자외선, X선, 감마선.", related="전자기파,빛")
add("전기·자기", "맥스웰 방정식", "Maxwell's equations", "전기장과 자기장의 생성 및 변화를 기술하는 네 개의 기본 방정식.", related="가우스 법칙,패러데이 법칙,전자기파", level="고등")
add("전기·자기", "홀 효과", "Hall effect", "전류가 흐르는 도체나 반도체에 수직 자기장을 걸면 옆 방향 전압이 생기는 현상.", related="자기력,전하 운반자", level="고등")
add("전기·자기", "반도체", "semiconductor", "전기전도도가 도체와 부도체 사이이며 도핑·온도·빛 등에 의해 크게 조절되는 물질.", example="실리콘.", related="도체,다이오드,트랜지스터")
add("전기·자기", "초전도", "superconductivity", "일부 물질이 임계온도 아래에서 전기저항이 0이 되고 자기장을 배제하는 현상.", related="마이스너 효과,임계온도", level="고등")
add("전기·자기", "마이스너 효과", "Meissner effect", "초전도체가 내부의 자기장을 밀어내는 현상.", related="초전도,자기장", level="고등")

# 빛·광학
add("빛·광학", "빛", "light", "사람의 눈에 보이는 전자기파를 중심으로, 넓게는 광자와 전자기복사를 가리키는 말.", related="전자기파,광자")
add("빛·광학", "빛의 속도", "speed of light", "진공에서 빛과 모든 전자기파가 이동하는 정확히 정의된 속도.", formula="c = 299,792,458 m/s", unit="m/s", related="특수상대성이론,굴절률")
add("빛·광학", "광선", "ray", "빛의 진행 방향을 선으로 나타낸 기하광학적 모델.", related="기하광학,파면")
add("빛·광학", "파면", "wavefront", "파동의 위상이 같은 점들을 이은 면.", related="광선,회절")
add("빛·광학", "반사의 법칙", "law of reflection", "반사각이 입사각과 같고 입사광선·반사광선·법선이 한 평면에 놓인다는 법칙.", formula="θ_i = θ_r", related="거울,법선")
add("빛·광학", "굴절", "refraction of light", "빛이 굴절률이 다른 매질의 경계를 지날 때 속력과 진행 방향이 변하는 현상.", related="스넬 법칙,굴절률")
add("빛·광학", "굴절률", "refractive index", "진공의 빛 속도를 매질 속 빛 속도로 나눈 값.", formula="n = c/v", unit="무차원", related="굴절,빛의 속도")
add("빛·광학", "스넬 법칙", "Snell's law", "두 매질 경계에서 입사각과 굴절각의 관계.", formula="n₁sinθ₁ = n₂sinθ₂", related="굴절,굴절률")
add("빛·광학", "전반사", "total internal reflection", "굴절률이 큰 매질에서 작은 매질로 나갈 때 입사각이 임계각보다 커지면 빛이 모두 반사되는 현상.", related="임계각,광섬유")
add("빛·광학", "임계각", "critical angle", "굴절각이 90°가 되어 전반사가 시작되는 최소 입사각.", formula="sinθ_c = n₂/n₁ (n₁>n₂)", related="전반사,스넬 법칙")
add("빛·광학", "분산", "dispersion", "매질의 굴절률이 파장에 따라 달라져 빛이 색별로 갈라지는 현상.", example="프리즘에서 백색광이 무지개색으로 나뉜다.", related="굴절률,스펙트럼")
add("빛·광학", "거울", "mirror", "빛을 규칙적으로 반사하여 상을 만드는 광학 소자.", related="평면거울,오목거울,볼록거울")
add("빛·광학", "렌즈", "lens", "굴절을 이용해 빛을 모으거나 퍼뜨리는 투명 광학 소자.", related="볼록렌즈,오목렌즈,초점")
add("빛·광학", "초점", "focus", "평행 광선이 렌즈나 거울을 지난 뒤 모이거나, 모이는 것처럼 보이는 점.", related="초점거리,렌즈")
add("빛·광학", "초점거리", "focal length", "렌즈 또는 거울의 기준점에서 초점까지의 거리.", unit="m", related="초점,렌즈 방정식")
add("빛·광학", "렌즈 방정식", "thin lens equation", "얇은 렌즈에서 물체거리, 상거리, 초점거리의 관계.", formula="1/f = 1/d_o + 1/d_i", related="배율,초점거리")
add("빛·광학", "배율", "magnification", "상의 크기와 물체 크기의 비.", formula="m = h_i/h_o = -d_i/d_o", unit="무차원", related="렌즈 방정식,상")
add("빛·광학", "실상", "real image", "실제 광선이 모여 스크린에 맺을 수 있는 상.", related="허상,렌즈")
add("빛·광학", "허상", "virtual image", "광선이 실제로 모이지 않고 연장선이 만나는 것처럼 보여 스크린에 직접 맺을 수 없는 상.", related="실상,거울")
add("빛·광학", "편광", "polarization", "횡파인 빛의 전기장 진동 방향이 특정 방향으로 정렬되는 현상.", related="횡파,편광판")
add("빛·광학", "간섭무늬", "interference pattern", "빛의 파동들이 중첩되어 밝고 어두운 부분이 규칙적으로 나타나는 무늬.", related="이중슬릿 실험,간섭")
add("빛·광학", "이중슬릿 실험", "double-slit experiment", "두 좁은 틈을 지난 파동이 간섭무늬를 만드는 실험으로 빛과 물질의 파동성을 보여 준다.", related="간섭,파동-입자 이중성")
add("빛·광학", "회절격자", "diffraction grating", "많은 평행한 틈이나 홈으로 빛을 파장별로 강하게 분리하는 광학 소자.", formula="d sinθ = mλ", related="회절,스펙트럼")
add("빛·광학", "광자", "photon", "전자기장의 양자로, 빛 에너지가 불연속적인 묶음으로 교환될 때의 입자적 표현.", formula="E = hf = hc/λ; p=h/λ", related="광전효과,파동-입자 이중성")
add("빛·광학", "광전효과", "photoelectric effect", "물질이 충분히 높은 진동수의 빛을 흡수해 전자를 방출하는 현상.", formula="K_max = hf - φ", related="광자,일함수", caution="빛의 세기보다 진동수가 문턱값을 넘는지가 전자 방출 여부를 결정한다.")
add("빛·광학", "레이저", "laser", "유도방출을 이용해 위상과 방향이 잘 맞고 좁은 파장 범위를 가진 강한 빛을 만드는 장치.", related="유도방출,코히런스")
add("빛·광학", "코히런스", "coherence", "파동들 사이의 위상 관계가 시간과 공간에서 안정적으로 유지되는 성질.", related="레이저,간섭")

# 상대성이론
add("상대성이론", "상대성 원리", "principle of relativity", "모든 관성계에서 물리 법칙의 형태가 같다는 원리.", related="관성계,특수상대성이론")
add("상대성이론", "특수상대성이론", "special relativity", "관성계에서 물리 법칙이 같고 진공의 빛 속도가 모든 관성 관찰자에게 같다는 두 원리에 기반한 이론.", related="시간 팽창,길이 수축,동시성")
add("상대성이론", "로런츠 인자", "Lorentz factor", "상대론적 시간·길이·에너지 식에 나타나는 속도 의존 인자.", formula="γ = 1/√(1-v²/c²)", unit="무차원", related="시간 팽창,길이 수축", level="고등")
add("상대성이론", "시간 팽창", "time dilation", "상대적으로 움직이는 시계가 관찰자 기준에서 더 느리게 가는 것으로 측정되는 현상.", formula="Δt = γΔτ", related="특수상대성이론,고유시간")
add("상대성이론", "고유시간", "proper time", "두 사건이 같은 위치에서 일어나는 기준계의 시계가 직접 재는 시간 간격.", unit="s", related="시간 팽창")
add("상대성이론", "길이 수축", "length contraction", "움직이는 물체의 운동 방향 길이가 관찰자 기준에서 더 짧게 측정되는 현상.", formula="L = L₀/γ", related="특수상대성이론,고유길이")
add("상대성이론", "동시성의 상대성", "relativity of simultaneity", "한 기준계에서 동시에 일어난 두 사건이 다른 움직이는 기준계에서는 동시에 아닐 수 있다는 성질.", related="특수상대성이론,기준계")
add("상대성이론", "질량-에너지 등가", "mass-energy equivalence", "질량이 에너지의 한 형태이며 정지한 물체도 정지에너지를 가진다는 관계.", formula="E₀ = mc²", aliases="E=mc²,E=mc2", related="정지에너지,핵반응")
add("상대성이론", "상대론적 운동량", "relativistic momentum", "빛의 속도에 가까운 물체에 적용되는 운동량.", formula="p = γmv", related="운동량,특수상대성이론", level="고등")
add("상대성이론", "시공간", "spacetime", "공간 세 차원과 시간 한 차원을 하나의 4차원 구조로 묶어 사건을 표현하는 개념.", related="사건,일반상대성이론")
add("상대성이론", "일반상대성이론", "general relativity", "중력을 질량과 에너지가 시공간을 휘게 하고 물체와 빛이 그 휜 시공간을 따라 움직이는 현상으로 설명하는 이론.", related="시공간,등가 원리,중력파")
add("상대성이론", "등가 원리", "equivalence principle", "국소적으로 중력 효과와 가속 기준계의 효과를 구별할 수 없다는 일반상대성이론의 핵심 원리.", related="일반상대성이론,중력")
add("상대성이론", "중력 시간 지연", "gravitational time dilation", "중력이 강한 곳의 시계가 약한 곳의 시계보다 느리게 가는 현상.", related="일반상대성이론,GPS")
add("상대성이론", "중력렌즈", "gravitational lensing", "질량이 휘게 한 시공간 때문에 배경 천체의 빛이 굽고 확대되거나 여러 상으로 보이는 현상.", related="일반상대성이론,암흑물질")
add("상대성이론", "중력파", "gravitational wave", "가속하는 비대칭 질량 분포가 만들어 빛의 속도로 퍼지는 시공간 곡률의 잔물결.", related="일반상대성이론,블랙홀")

# 양자·원자
add("양자·원자", "양자", "quantum", "에너지 같은 물리량이 상호작용에서 불연속적인 최소 묶음으로 교환되는 개념.", related="양자화,광자")
add("양자·원자", "플랑크 상수", "Planck constant", "광자의 에너지와 진동수를 연결하고 양자 효과의 크기를 정하는 기본상수.", formula="h = 6.62607015×10⁻³⁴ J·s (정확)", unit="J·s", related="광자,드브로이 파장")
add("양자·원자", "양자화", "quantization", "어떤 물리량이 연속적인 모든 값이 아니라 특정한 불연속 값만 가질 수 있는 성질.", example="원자의 에너지 준위.", related="양자,에너지 준위")
add("양자·원자", "파동-입자 이중성", "wave-particle duality", "빛과 물질이 실험 조건에 따라 파동적 또는 입자적 특성을 드러내는 성질.", related="이중슬릿 실험,광자,드브로이 파장")
add("양자·원자", "드브로이 파장", "de Broglie wavelength", "운동량을 가진 입자에 대응시키는 물질파의 파장.", formula="λ = h/p", unit="m", related="파동-입자 이중성,운동량")
add("양자·원자", "불확정성 원리", "Heisenberg uncertainty principle", "위치와 운동량처럼 짝을 이루는 물리량은 동시에 임의로 정확하게 정해질 수 없다는 원리.", formula="ΔxΔp ≥ ħ/2", related="파동함수,양자역학", caution="측정 기구가 나빠서 생기는 단순한 오차가 아니라 양자상태 자체의 성질이다.")
add("양자·원자", "파동함수", "wave function", "양자계의 상태를 나타내며 절댓값 제곱이 측정 결과의 확률밀도와 연결되는 복소함수.", aliases="ψ", related="확률밀도,슈뢰딩거 방정식", level="고등")
add("양자·원자", "확률밀도", "probability density", "특정 위치나 상태 근처에서 입자를 발견할 확률의 분포 밀도.", formula="ρ = |ψ|²", related="파동함수,보른 규칙", level="고등")
add("양자·원자", "슈뢰딩거 방정식", "Schrodinger equation", "비상대론적 양자계의 파동함수가 시간과 공간에서 어떻게 변하는지 정하는 기본 방정식.", formula="iħ∂ψ/∂t = Ĥψ", related="파동함수,해밀토니안", level="고등")
add("양자·원자", "에너지 준위", "energy level", "양자계가 가질 수 있는 허용된 불연속 에너지 값.", related="양자화,원자 스펙트럼")
add("양자·원자", "바닥상태", "ground state", "양자계가 가질 수 있는 가장 낮은 에너지 상태.", related="들뜬상태,에너지 준위")
add("양자·원자", "들뜬상태", "excited state", "바닥상태보다 높은 에너지를 가진 양자상태.", related="바닥상태,광자 방출")
add("양자·원자", "양자 터널링", "quantum tunneling", "고전적으로 넘을 에너지가 부족한 장벽을 양자 입자가 일정 확률로 통과하는 현상.", example="알파 붕괴, 주사 터널링 현미경.", related="파동함수,장벽")
add("양자·원자", "스핀", "spin", "입자가 지닌 고유한 양자 각운동량.", unit="ħ의 배수", related="각운동량,파울리 배타 원리", caution="작은 공이 실제로 자전하는 모습과 동일하게 이해하면 안 된다.")
add("양자·원자", "파울리 배타 원리", "Pauli exclusion principle", "동일한 페르미온 두 개가 한 양자계에서 완전히 같은 양자상태를 차지할 수 없다는 원리.", related="전자배치,페르미온")
add("양자·원자", "보손", "boson", "정수 스핀을 가지며 같은 양자상태를 여러 개가 함께 차지할 수 있는 입자.", related="페르미온,광자")
add("양자·원자", "페르미온", "fermion", "반정수 스핀을 가지며 파울리 배타 원리를 따르는 입자.", related="보손,전자,쿼크")
add("양자·원자", "원자", "atom", "양전하의 원자핵과 그 주위의 전자로 이루어진 물질의 기본 단위.", related="원자핵,전자")
add("양자·원자", "전자", "electron", "음의 기본전하를 가진 안정한 기본 렙톤.", unit="전하 -e", related="원자,렙톤")
add("양자·원자", "양성자", "proton", "양의 기본전하를 가진 바리온으로 원자핵의 구성 입자.", related="중성자,쿼크")
add("양자·원자", "중성자", "neutron", "전기적으로 중성이며 원자핵의 구성 입자인 바리온.", related="양성자,베타 붕괴")
add("양자·원자", "원자 스펙트럼", "atomic spectrum", "원자의 에너지 준위 사이 전이에서 흡수·방출되는 특정 파장의 빛 무늬.", related="에너지 준위,분광학")
add("양자·원자", "보어 모형", "Bohr model", "수소 원자의 전자가 특정 양자화된 궤도와 에너지만 가진다고 보는 초기 원자 모형.", related="원자,에너지 준위", caution="다전자 원자와 현대 양자역학을 완전히 설명하는 최종 모형은 아니다.")
add("양자·원자", "일함수", "work function", "고체 표면에서 전자 하나를 꺼내는 데 필요한 최소 에너지.", unit="J 또는 eV", related="광전효과,전자")
add("양자·원자", "전자볼트", "electronvolt", "전자 하나가 1 V의 전위차를 지나며 얻는 에너지.", formula="1 eV = 1.602176634×10⁻¹⁹ J", unit="eV", related="에너지,기본전하")

# 핵·입자
add("핵·입자", "원자핵", "atomic nucleus", "양성자와 중성자로 이루어지고 원자 질량의 대부분을 차지하는 매우 작은 중심 부분.", related="양성자,중성자,핵력")
add("핵·입자", "핵자", "nucleon", "원자핵을 이루는 양성자와 중성자를 함께 부르는 말.", related="원자핵,질량수")
add("핵·입자", "원자번호", "atomic number", "원자핵 속 양성자의 수로 원소의 종류를 결정한다.", aliases="Z", related="질량수,동위원소")
add("핵·입자", "질량수", "mass number", "원자핵 속 양성자 수와 중성자 수의 합.", aliases="A", related="원자번호,핵자")
add("핵·입자", "동위원소", "isotope", "양성자 수는 같지만 중성자 수가 달라 질량수가 다른 같은 원소의 원자.", related="원자번호,방사성 동위원소")
add("핵·입자", "핵력", "nuclear force", "원자핵 안에서 핵자들을 결합시키는 강한 상호작용의 유효한 힘.", related="강한 상호작용,결합에너지")
add("핵·입자", "질량결손", "mass defect", "결합된 원자핵의 질량이 분리된 핵자 질량의 합보다 작은 차이.", formula="Δm = Σm_nucleons - m_nucleus", related="결합에너지,질량-에너지 등가")
add("핵·입자", "핵결합에너지", "nuclear binding energy", "원자핵을 개별 핵자로 완전히 분리하는 데 필요한 에너지.", formula="E_b = Δmc²", unit="J 또는 MeV", related="질량결손,핵력")
add("핵·입자", "방사능", "radioactivity", "불안정한 원자핵이 입자나 전자기복사를 내며 더 안정한 상태로 변하는 성질.", unit="Bq", related="방사성 붕괴,반감기")
add("핵·입자", "방사성 붕괴", "radioactive decay", "불안정한 원자핵이 확률적으로 다른 핵이나 상태로 변하는 과정.", formula="N(t)=N₀e^{-λt}", related="반감기,붕괴상수")
add("핵·입자", "알파 붕괴", "alpha decay", "원자핵이 헬륨-4 원자핵인 알파입자를 방출하는 붕괴.", related="방사성 붕괴,양자 터널링")
add("핵·입자", "베타 붕괴", "beta decay", "약한 상호작용으로 중성자와 양성자가 서로 바뀌며 전자 또는 양전자와 중성미자가 방출되는 붕괴.", related="약한 상호작용,중성미자")
add("핵·입자", "감마 붕괴", "gamma decay", "들뜬 원자핵이 고에너지 광자를 방출하여 더 낮은 에너지 상태로 내려가는 과정.", related="감마선,들뜬상태")
add("핵·입자", "반감기", "half-life", "방사성 핵의 수 또는 방사능이 처음의 절반으로 줄어드는 데 걸리는 시간.", formula="t₁/₂ = ln2/λ", unit="s 등", related="방사성 붕괴,붕괴상수")
add("핵·입자", "활동도", "activity", "단위 시간당 일어나는 방사성 붕괴 횟수.", formula="A = λN", unit="Bq", aliases="방사능 세기", related="방사성 붕괴,반감기")
add("핵·입자", "핵분열", "nuclear fission", "무거운 원자핵이 두 개 이상의 가벼운 핵으로 갈라지며 에너지와 중성자를 방출하는 반응.", related="연쇄반응,핵결합에너지")
add("핵·입자", "핵융합", "nuclear fusion", "가벼운 원자핵들이 결합해 더 무거운 핵을 만들며 에너지를 방출하는 반응.", example="태양 중심의 수소 핵융합.", related="핵결합에너지,별")
add("핵·입자", "연쇄반응", "chain reaction", "한 핵반응에서 나온 입자가 다른 핵반응을 이어서 일으키는 과정.", related="핵분열,임계질량")
add("핵·입자", "기본입자", "elementary particle", "현재 알려진 한 더 작은 내부 구조가 없는 입자.", related="표준모형,쿼크,렙톤")
add("핵·입자", "표준모형", "Standard Model of particle physics", "전자기·강한·약한 상호작용과 기본입자들을 설명하는 현대 입자물리 이론 체계.", related="쿼크,렙톤,게이지 보손,힉스 보손", caution="중력과 암흑물질 등을 완전히 설명하지 못하므로 자연의 최종 이론은 아니다.")
add("핵·입자", "쿼크", "quark", "강한 상호작용을 하며 양성자와 중성자 같은 하드론을 이루는 기본 페르미온.", related="하드론,글루온")
add("핵·입자", "렙톤", "lepton", "강한 상호작용을 하지 않는 기본 페르미온 계열.", example="전자, 뮤온, 타우, 세 종류 중성미자.", related="전자,중성미자")
add("핵·입자", "하드론", "hadron", "강한 상호작용으로 결합된 쿼크들로 이루어진 입자.", related="바리온,중간자,쿼크")
add("핵·입자", "바리온", "baryon", "세 쿼크로 이루어진 하드론.", example="양성자와 중성자.", related="하드론,중간자")
add("핵·입자", "중간자", "meson", "쿼크 하나와 반쿼크 하나로 이루어진 하드론.", aliases="메손", related="하드론,바리온")
add("핵·입자", "게이지 보손", "gauge boson", "표준모형에서 기본 상호작용을 전달하는 보손.", example="광자, 글루온, W·Z 보손.", related="표준모형,보손")
add("핵·입자", "광자", "photon particle physics", "전자기 상호작용을 전달하는 질량 0의 게이지 보손.", related="전자기력,게이지 보손")
add("핵·입자", "글루온", "gluon", "쿼크 사이의 강한 상호작용을 전달하는 게이지 보손.", related="쿼크,강한 상호작용")
add("핵·입자", "W 보손", "W boson", "약한 상호작용을 전달하며 전하를 가진 무거운 게이지 보손.", related="Z 보손,약한 상호작용")
add("핵·입자", "Z 보손", "Z boson", "약한 상호작용의 중성 전류를 전달하는 전기적으로 중성인 무거운 게이지 보손.", related="W 보손,약한 상호작용")
add("핵·입자", "힉스 보손", "Higgs boson", "힉스 장의 양자이며 표준모형 입자들이 질량을 얻는 메커니즘과 관련된 입자.", related="힉스 장,표준모형")
add("핵·입자", "중성미자", "neutrino", "전기적으로 중성이며 질량이 매우 작고 약한 상호작용을 하는 기본 렙톤.", related="렙톤,베타 붕괴")
add("핵·입자", "반입자", "antiparticle", "대응하는 입자와 질량은 같고 전하 등 일부 양자수가 반대인 입자.", related="반물질,쌍소멸")
add("핵·입자", "반물질", "antimatter", "반입자들로 이루어진 물질.", related="반입자,쌍생성,쌍소멸")
add("핵·입자", "쌍생성", "pair production", "충분한 에너지의 광자 등이 입자와 반입자 쌍으로 변환되는 과정.", related="반물질,질량-에너지 등가")
add("핵·입자", "쌍소멸", "annihilation", "입자와 반입자가 만나 다른 입자나 광자로 에너지가 바뀌는 과정.", related="쌍생성,반입자")
add("핵·입자", "강한 상호작용", "strong interaction", "쿼크를 하드론 안에 묶고 원자핵의 결합에 관여하는 가장 강한 기본 상호작용.", related="글루온,쿼크,핵력")
add("핵·입자", "약한 상호작용", "weak interaction", "베타 붕괴와 중성미자 반응 등에 관여하며 입자의 종류를 바꿀 수 있는 기본 상호작용.", related="W 보손,Z 보손,베타 붕괴")
add("핵·입자", "전자기 상호작용", "electromagnetic interaction", "전하를 가진 입자 사이에 작용하며 광자가 전달하는 기본 상호작용.", related="광자,전기장,자기장")
add("핵·입자", "중력 상호작용", "gravitational interaction", "질량과 에너지를 가진 모든 것에 작용하는 기본 상호작용으로 큰 규모에서 지배적이다.", related="중력,일반상대성이론")
add("핵·입자", "가속기", "particle accelerator", "전기장으로 하전입자를 높은 에너지까지 가속하고 자기장으로 경로를 제어하는 장치.", related="입자 검출기,LHC")
add("핵·입자", "입자 검출기", "particle detector", "입자가 물질과 상호작용하며 남기는 신호를 측정해 에너지, 운동량, 전하 등을 추정하는 장치.", related="가속기,트랙")

# 천체·우주
add("천체·우주", "천문단위", "astronomical unit", "지구와 태양 사이 평균 거리 정도를 나타내는 길이 단위.", formula="1 au = 149,597,870,700 m (정확)", unit="au", related="광년,파섹")
add("천체·우주", "광년", "light-year", "빛이 진공에서 1년 동안 이동하는 거리.", unit="약 9.46×10¹⁵ m", related="파섹,빛의 속도", caution="시간 단위가 아니라 거리 단위다.")
add("천체·우주", "파섹", "parsec", "연주시차가 1각초인 천체까지의 거리.", formula="1 pc ≈ 3.26 ly", unit="pc", related="연주시차,광년")
add("천체·우주", "연주시차", "stellar parallax", "지구가 태양 주위를 공전하면서 가까운 별의 위치가 먼 배경별에 대해 주기적으로 달라 보이는 현상.", related="파섹,거리 측정")
add("천체·우주", "궤도", "orbit", "중력 등 중심력 아래에서 천체나 위성이 그리는 경로.", related="케플러 법칙,탈출속도")
add("천체·우주", "케플러 제1법칙", "Kepler's first law", "행성은 태양을 한 초점으로 하는 타원 궤도를 돈다.", aliases="타원 궤도 법칙", related="궤도,이심률")
add("천체·우주", "케플러 제2법칙", "Kepler's second law", "행성과 태양을 잇는 선분이 같은 시간 동안 쓸고 지나가는 면적은 같다.", aliases="면적 속도 일정 법칙", related="각운동량 보존,궤도")
add("천체·우주", "케플러 제3법칙", "Kepler's third law", "같은 중심천체를 도는 물체들의 공전주기 제곱은 궤도 긴반지름 세제곱에 비례한다.", formula="T² ∝ a³", related="만유인력,궤도")
add("천체·우주", "탈출속도", "escape velocity", "추가 추진 없이 천체의 중력에서 무한히 멀어질 수 있는 최소 초기 속력.", formula="v_e = √(2GM/R)", unit="m/s", related="중력 위치에너지,블랙홀")
add("천체·우주", "조석력", "tidal force", "중력장이 위치에 따라 달라 물체의 가까운 쪽과 먼 쪽에 서로 다른 가속도가 생기는 효과.", related="조석,스파게티화")
add("천체·우주", "별", "star", "중력으로 묶인 뜨거운 플라스마 천체로, 대부분 중심부 핵융합에서 에너지를 얻는다.", related="핵융합,주계열성")
add("천체·우주", "주계열성", "main-sequence star", "중심에서 수소 핵융합을 하며 비교적 안정하게 빛나는 별.", example="태양.", related="별,헤르츠스프룽-러셀도")
add("천체·우주", "백색왜성", "white dwarf", "태양 정도 질량의 별이 진화한 뒤 남을 수 있는 작고 밀도 높은 항성 잔해.", related="전자 축퇴압,초신성")
add("천체·우주", "중성자별", "neutron star", "무거운 별의 핵붕괴 뒤 남을 수 있는 매우 작고 밀도 높은 천체.", related="초신성,펄서")
add("천체·우주", "펄서", "pulsar", "강한 자기장과 빠른 회전을 가진 중성자별이 주기적인 전자기파 펄스를 보내는 천체.", related="중성자별,자기장")
add("천체·우주", "초신성", "supernova", "별이 진화 과정에서 일으키는 매우 밝고 강력한 폭발 현상.", related="중성자별,블랙홀,원소 합성")
add("천체·우주", "블랙홀", "black hole", "사건지평선 안쪽에서 빛조차 바깥으로 나올 수 없을 만큼 시공간이 강하게 휜 천체 영역.", related="사건지평선,일반상대성이론")
add("천체·우주", "사건지평선", "event horizon", "블랙홀에서 바깥으로 신호가 돌아올 수 없는 경계.", related="블랙홀,탈출속도")
add("천체·우주", "슈바르츠실트 반지름", "Schwarzschild radius", "회전과 전하가 없는 질량 M의 블랙홀 사건지평선 반지름.", formula="r_s = 2GM/c²", unit="m", related="블랙홀,사건지평선")
add("천체·우주", "적색편이", "redshift", "관측된 빛의 파장이 방출 때보다 길어지는 현상.", formula="z = (λ_obs-λ_emit)/λ_emit", related="도플러 효과,우주 팽창")
add("천체·우주", "청색편이", "blueshift", "관측된 빛의 파장이 방출 때보다 짧아지는 현상.", related="적색편이,도플러 효과")
add("천체·우주", "허블-르메트르 법칙", "Hubble-Lemaitre law", "충분히 큰 우주 규모에서 은하의 후퇴 속도가 거리와 거의 비례한다는 관측 관계.", formula="v = H₀d", related="우주 팽창,적색편이")
add("천체·우주", "우주 팽창", "expansion of the universe", "큰 규모에서 은하 사이의 공간적 거리가 시간에 따라 늘어나는 현상.", related="허블-르메트르 법칙,빅뱅")
add("천체·우주", "빅뱅 우주론", "Big Bang cosmology", "우주가 과거의 매우 뜨겁고 밀도 높은 상태에서 팽창·냉각해 왔다는 현대 우주론의 기본 모형.", related="우주 팽창,우주배경복사")
add("천체·우주", "우주배경복사", "cosmic microwave background", "초기 우주가 투명해질 때 방출되어 현재 마이크로파 영역에서 관측되는 거의 균일한 복사.", aliases="CMB", related="빅뱅 우주론,흑체복사")
add("천체·우주", "암흑물질", "dark matter", "빛을 거의 내거나 흡수하지 않지만 중력 효과로 존재가 추론되는 물질 성분.", related="은하 회전곡선,중력렌즈", caution="정체가 아직 확정되지 않은 연구 대상이다.")
add("천체·우주", "암흑에너지", "dark energy", "우주 팽창이 가속되는 현상을 설명하기 위해 도입된 우주의 에너지 성분에 대한 이름.", related="가속 팽창,우주상수", caution="물리적 정체와 성질은 아직 완전히 밝혀지지 않았다.")
add("천체·우주", "우주상수", "cosmological constant", "일반상대성이론 방정식에 들어갈 수 있으며 진공에너지와 우주 가속 팽창에 관련될 수 있는 상수.", aliases="Λ", related="암흑에너지,일반상대성이론")
add("천체·우주", "은하", "galaxy", "별, 가스, 먼지, 암흑물질 등이 중력으로 묶인 거대한 천체 계.", related="은하단,암흑물질")
add("천체·우주", "성운", "nebula", "성간 공간의 가스와 먼지 구름.", related="별 탄생,초신성 잔해")
add("천체·우주", "강착원반", "accretion disk", "중심 천체로 떨어지는 물질이 각운동량 때문에 원반을 이루며 가열되는 구조.", related="블랙홀,중성자별")
add("천체·우주", "외계행성", "exoplanet", "태양이 아닌 다른 별을 도는 행성.", related="통과법,시선속도법")

# Constants data: values formatted for learning, not machine metrology.
CONSTANTS = [
    {"name_ko":"진공에서의 빛의 속도","symbol":"c","value":"299 792 458","unit":"m/s","status":"정확","source":"nist"},
    {"name_ko":"플랑크 상수","symbol":"h","value":"6.626 070 15 × 10⁻³⁴","unit":"J·s","status":"정확","source":"nist"},
    {"name_ko":"환산 플랑크 상수","symbol":"ħ","value":"1.054 571 817… × 10⁻³⁴","unit":"J·s","status":"h/(2π)로 유도","source":"nist"},
    {"name_ko":"기본전하","symbol":"e","value":"1.602 176 634 × 10⁻¹⁹","unit":"C","status":"정확","source":"nist"},
    {"name_ko":"볼츠만 상수","symbol":"k_B","value":"1.380 649 × 10⁻²³","unit":"J/K","status":"정확","source":"nist"},
    {"name_ko":"아보가드로 상수","symbol":"N_A","value":"6.022 140 76 × 10²³","unit":"mol⁻¹","status":"정확","source":"nist"},
    {"name_ko":"기체상수","symbol":"R","value":"8.314 462 618…","unit":"J/(mol·K)","status":"N_A k_B로 유도","source":"nist"},
    {"name_ko":"중력상수","symbol":"G","value":"6.674 30(15) × 10⁻¹¹","unit":"m³/(kg·s²)","status":"측정값","source":"nist"},
    {"name_ko":"전자 질량","symbol":"m_e","value":"9.109 383 7139(28) × 10⁻³¹","unit":"kg","status":"2022 CODATA","source":"nist"},
    {"name_ko":"양성자 질량","symbol":"m_p","value":"1.672 621 925 95(52) × 10⁻²⁷","unit":"kg","status":"2022 CODATA","source":"nist"},
    {"name_ko":"미세구조상수","symbol":"α","value":"7.297 352 5643(11) × 10⁻³","unit":"무차원","status":"2022 CODATA","source":"nist"},
    {"name_ko":"표준 중력가속도","symbol":"g₀","value":"9.806 65","unit":"m/s²","status":"정확한 관례값","source":"bipm"},
    {"name_ko":"천문단위","symbol":"au","value":"149 597 870 700","unit":"m","status":"정확","source":"bipm"}
]

# Deduplicate English slugs if necessary.
seen = {}
for term in terms:
    base = term["id"]
    count = seen.get(base, 0)
    if count:
        term["id"] = f"{base}-{count+1}"
    seen[base] = count + 1

# Search text cached in JSON for fast startup.
for term in terms:
    searchable = " ".join([
        term["name_ko"], term["name_en"], *term["aliases"], term["category"],
        term["summary"], term["formula"], term["unit"], *term["related"]
    ])
    term["search_text"] = unicodedata.normalize("NFKC", searchable).lower()

terms.sort(key=lambda t: (t["category"], t["name_ko"]))

(DATA / "terms.json").write_text(json.dumps({"version":"2.0.0","count":len(terms),"terms":terms}, ensure_ascii=False, indent=2), encoding="utf-8")
(DATA / "sources.json").write_text(json.dumps({"sources":SOURCES}, ensure_ascii=False, indent=2), encoding="utf-8")
(DATA / "constants.json").write_text(json.dumps({"constants":CONSTANTS}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Generated {len(terms)} terms, {len(CONSTANTS)} constants")

# Re-apply the extended explanations used by Physics Pocket 2.0.
try:
    from enrich_core_terms import main as enrich_core_terms
    enrich_core_terms()
except Exception as exc:
    print(f"Warning: core-term enrichment was not applied: {exc}")
