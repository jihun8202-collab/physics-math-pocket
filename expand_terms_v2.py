from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "terms.json"

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
    "천체·우주": ["nasa", "openstax", "korean_terms"],
}

CATEGORY_DETAIL = {
    "측정·기초": "측정값, 단위, 모델과 수학적 표현을 정확히 연결하는 데 쓰인다.",
    "운동학": "물체의 위치와 시간 변화를 원인과 분리해 기술하는 데 쓰인다.",
    "힘·에너지": "힘, 운동량, 에너지의 전달과 보존을 분석하는 데 쓰인다.",
    "회전·평형": "회전 운동과 물체가 균형을 이루는 조건을 분석하는 데 쓰인다.",
    "유체": "액체와 기체의 압력, 흐름과 변형을 설명하는 데 쓰인다.",
    "진동·파동·소리": "진동과 파동이 시간과 공간에서 변하는 방식을 설명한다.",
    "열·열역학": "열, 온도, 내부에너지와 상태 변화의 관계를 설명한다.",
    "전기·자기": "전하, 장, 회로와 전자기파의 관계를 설명한다.",
    "빛·광학": "빛의 진행, 영상 형성, 간섭과 분광 현상을 설명한다.",
    "상대성이론": "빠른 운동과 중력이 시공간 측정에 미치는 영향을 설명한다.",
    "양자·원자": "원자 규모에서 상태와 측정 결과가 확률적으로 나타나는 방식을 설명한다.",
    "핵·입자": "원자핵과 기본입자의 반응, 붕괴와 상호작용을 설명한다.",
    "천체·우주": "별, 은하와 우주의 구조와 진화를 물리 법칙으로 설명한다.",
}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-").lower()
    return text or "term"


def make(cat: str, ko: str, en: str, summary: str, *, formula: str = "", unit: str = "", example: str = "", aliases: str = "", related: str = "", level: str = "고등", caution: str = "") -> dict:
    detail = summary + " " + CATEGORY_DETAIL[cat]
    if formula:
        detail += " 대표식은 기호의 뜻, 단위와 적용 조건을 확인한 뒤 사용해야 한다."
    return {
        "id": slug(en),
        "name_ko": ko,
        "name_en": en,
        "aliases": [x.strip() for x in aliases.split(",") if x.strip()],
        "category": cat,
        "level": level,
        "summary": summary,
        "detail": detail,
        "formula": formula,
        "unit": unit,
        "example": example,
        "caution": caution,
        "related": [x.strip() for x in related.split(",") if x.strip()],
        "sources": CATEGORY_SOURCES[cat],
    }


CANDIDATES = [
    # 측정·기초
    make("측정·기초", "무차원량", "dimensionless quantity", "같은 차원의 양을 나누어 단위가 사라진 물리량.", unit="1", example="굴절률, 마찰계수, 상대밀도.", related="차원,차원 분석"),
    make("측정·기초", "크기 차수", "order of magnitude", "어떤 값이 가장 가까운 10의 거듭제곱으로 어느 정도 크기인지 나타내는 방법.", example="3×10⁸은 10⁸ 정도의 크기다.", aliases="오더", related="과학적 표기법,근사"),
    make("측정·기초", "교정", "calibration", "측정 기기의 표시값을 신뢰할 수 있는 기준과 비교해 관계를 정하는 과정.", example="표준 질량으로 저울의 표시값을 확인한다.", related="측정,측정 불확도"),
    make("측정·기초", "분해능", "measurement resolution", "측정 기기가 구별하여 표시할 수 있는 가장 작은 변화량.", unit="측정량과 같은 단위", related="정밀도,측정 불확도"),
    make("측정·기초", "계통 오차", "systematic error", "반복 측정에서도 일정한 방향이나 규칙으로 나타나는 측정 편향.", example="영점이 어긋난 저울.", related="우연 오차,교정"),
    make("측정·기초", "우연 오차", "random error", "측정할 때마다 예측하기 어렵게 달라지는 변동 때문에 생기는 오차.", related="계통 오차,평균값"),
    make("측정·기초", "오차 전파", "propagation of uncertainty", "여러 측정값으로 계산한 결과의 불확도를 입력값들의 불확도로부터 구하는 방법.", related="측정 불확도,상대오차", level="심화"),
    make("측정·기초", "텐서", "tensor", "좌표계가 바뀔 때 정해진 규칙으로 성분이 변하는 다성분 물리량.", example="응력 텐서, 관성 텐서.", related="스칼라,벡터", level="심화"),

    # 운동학
    make("운동학", "저크", "jerk", "가속도가 시간에 따라 변하는 비율.", formula="j = da/dt", unit="m/s³", related="가속도,운동학", level="심화"),
    make("운동학", "곡선 운동", "curvilinear motion", "물체의 이동 경로가 직선이 아닌 곡선인 운동.", related="접선 속도,구심가속도"),
    make("운동학", "상대 가속도", "relative acceleration", "한 물체에서 보았을 때 다른 물체의 가속도.", formula="a_AB = a_A - a_B", unit="m/s²", related="상대속도,기준계"),
    make("운동학", "접선 가속도", "tangential acceleration", "속력의 크기를 변화시키는 경로의 접선 방향 가속도 성분.", formula="a_t = dv/dt", unit="m/s²", related="구심가속도,곡선 운동"),
    make("운동학", "법선 가속도", "normal acceleration", "곡선 운동에서 속도의 방향을 변화시키는 곡률 중심 방향 가속도 성분.", formula="a_n = v²/r", unit="m/s²", aliases="구심가속도", related="접선 가속도,원운동"),
    make("운동학", "등속 원운동", "uniform circular motion", "속력은 일정하지만 속도 방향이 계속 바뀌는 원운동.", formula="a_c = v²/r = ω²r", related="구심가속도,각속도"),

    # 힘·에너지
    make("힘·에너지", "충격량-운동량 정리", "impulse-momentum theorem", "알짜힘의 충격량이 물체의 운동량 변화와 같다는 관계.", formula="J = Δp = ∫F dt", unit="N·s", related="충격량,운동량"),
    make("힘·에너지", "보존력", "conservative force", "한 점에서 다른 점까지 한 일이 경로가 아니라 처음과 끝 위치에만 의존하는 힘.", example="중력, 이상적인 용수철 힘.", related="위치에너지,비보존력"),
    make("힘·에너지", "비보존력", "non-conservative force", "한 일이 이동 경로에 의존하여 기계적 에너지를 다른 형태로 바꿀 수 있는 힘.", example="마찰력.", related="보존력,기계적 에너지"),
    make("힘·에너지", "퍼텐셜 우물", "potential well", "위치에너지 그래프에서 주변보다 낮아 물체나 입자가 갇힐 수 있는 영역.", related="위치에너지,안정 평형", level="심화"),
    make("힘·에너지", "일-에너지 정리", "work-energy theorem", "물체에 작용한 알짜일이 운동에너지 변화와 같다는 정리.", formula="W_net = ΔK", unit="J", related="일,운동에너지"),
    make("힘·에너지", "기계적 이득", "mechanical advantage", "기계가 입력 힘을 얼마나 크게 바꾸는지 나타내는 출력 힘과 입력 힘의 비.", formula="MA = F_out/F_in", unit="무차원", related="지레,도르래"),
    make("힘·에너지", "응력", "stress", "물체 내부에서 단면적당 작용하는 힘.", formula="σ = F/A", unit="Pa", related="변형률,영률"),
    make("힘·에너지", "변형률", "strain", "원래 길이에 대한 길이 변화의 비.", formula="ε = ΔL/L₀", unit="무차원", related="응력,영률"),
    make("힘·에너지", "영률", "Young modulus", "인장 또는 압축의 탄성 범위에서 응력을 변형률로 나눈 탄성계수.", formula="E = σ/ε", unit="Pa", aliases="영의 계수", related="응력,변형률"),
    make("힘·에너지", "탄성 한계", "elastic limit", "힘을 제거했을 때 물체가 원래 모양으로 완전히 돌아올 수 있는 최대 범위의 경계.", related="탄성 변형,소성 변형"),
    make("힘·에너지", "소성 변형", "plastic deformation", "힘을 제거한 뒤에도 남는 영구적인 변형.", related="탄성 변형,항복점"),
    make("힘·에너지", "항복점", "yield point", "재료가 탄성 변형을 벗어나 뚜렷한 소성 변형을 시작하는 지점.", related="응력,소성 변형"),

    # 회전·평형
    make("회전·평형", "각변위", "angular displacement", "회전하는 물체의 각 위치가 얼마나 변했는지 나타내는 양.", formula="Δθ = θ_f - θ_i", unit="rad", related="각속도,각가속도"),
    make("회전·평형", "각속도", "angular velocity", "각변위가 시간에 따라 변하는 비율.", formula="ω = dθ/dt", unit="rad/s", related="각변위,접선 속도"),
    make("회전·평형", "각가속도", "angular acceleration", "각속도가 시간에 따라 변하는 비율.", formula="α = dω/dt", unit="rad/s²", related="각속도,토크"),
    make("회전·평형", "회전 운동에너지", "rotational kinetic energy", "회전하는 강체가 가진 운동에너지.", formula="K_rot = ½Iω²", unit="J", related="관성모멘트,각속도"),
    make("회전·평형", "회전반경", "radius of gyration", "전체 질량이 한 거리에서 회전한다고 보았을 때 같은 관성모멘트를 주는 거리.", formula="k = √(I/M)", unit="m", related="관성모멘트", level="심화"),
    make("회전·평형", "구름 운동", "rolling motion", "물체가 회전하면서 동시에 병진하는 운동.", related="미끄럼 없는 구름,각속도"),
    make("회전·평형", "미끄럼 없는 구름", "rolling without slipping", "접촉점이 바닥에 대해 순간적으로 정지하는 이상적인 구름 운동.", formula="v_cm = ωR", related="구름 운동,정지 마찰력"),
    make("회전·평형", "세차 운동", "precession", "회전축의 방향이 외부 토크 때문에 천천히 원뿔 모양으로 도는 운동.", example="팽이의 축이 빙글도는 현상.", related="각운동량,자이로스코프"),
    make("회전·평형", "자이로스코프", "gyroscope", "회전하는 물체의 각운동량 성질을 이용해 방향을 유지하거나 측정하는 장치.", related="세차 운동,각운동량"),
    make("회전·평형", "힘의 우력", "couple", "크기가 같고 방향이 반대이며 작용선이 다른 두 힘이 만드는 순수한 회전 효과.", unit="N·m", aliases="우력", related="토크,평형"),

    # 유체
    make("유체", "비중", "specific gravity", "물질의 밀도를 기준 물질의 밀도로 나눈 비.", formula="SG = ρ/ρ_ref", unit="무차원", related="밀도,상대밀도"),
    make("유체", "정수압", "hydrostatic pressure", "정지한 유체에서 깊이에 따라 증가하는 압력.", formula="p = p₀ + ρgh", unit="Pa", related="압력,파스칼 원리"),
    make("유체", "연속 방정식", "continuity equation fluid", "정상 흐름에서 질량 보존을 나타내는 관계.", formula="ρAv = constant", related="유량,베르누이 방정식"),
    make("유체", "체적 유량", "volume flow rate", "단위 시간 동안 단면을 통과하는 유체 부피.", formula="Q = Av", unit="m³/s", aliases="유량", related="연속 방정식"),
    make("유체", "레이놀즈 수", "Reynolds number", "관성 효과와 점성 효과의 상대적 크기를 나타내는 무차원수.", formula="Re = ρvL/μ", unit="무차원", related="층류,난류", level="심화"),
    make("유체", "층류", "laminar flow", "유체가 서로 섞이는 큰 소용돌이 없이 층을 이루어 매끄럽게 흐르는 상태.", related="난류,레이놀즈 수"),
    make("유체", "난류", "turbulent flow", "속도와 압력이 불규칙하게 변하고 다양한 크기의 소용돌이가 생기는 흐름.", related="층류,레이놀즈 수"),
    make("유체", "표면장력", "surface tension", "액체 표면이 면적을 줄이려는 것처럼 작용하게 하는 단위 길이당 힘 또는 단위 면적당 에너지.", unit="N/m", related="모세관 현상,계면"),
    make("유체", "모세관 현상", "capillary action", "가느다란 관이나 틈에서 표면장력과 젖음성 때문에 액체 높이가 오르거나 내려가는 현상.", related="표면장력,접촉각"),
    make("유체", "압축률", "compressibility", "압력 변화에 대해 물질의 부피가 얼마나 쉽게 변하는지 나타내는 성질.", unit="Pa⁻¹", related="체적 탄성률,음속"),
    make("유체", "체적 탄성률", "bulk modulus", "압축에 대한 저항을 나타내는 압력 변화와 상대 부피 변화의 비.", formula="K = -Δp/(ΔV/V)", unit="Pa", related="압축률,음속"),
    make("유체", "마하 수", "Mach number", "물체나 흐름의 속력을 그 매질의 음속으로 나눈 값.", formula="Ma = v/c_s", unit="무차원", related="음속,충격파"),

    # 파동
    make("진동·파동·소리", "파동 속력", "wave speed", "파형의 특정 위상이 매질이나 공간을 따라 이동하는 속력.", formula="v = fλ", unit="m/s", related="진동수,파장"),
    make("진동·파동·소리", "위상 속도", "phase velocity", "같은 위상의 점이 이동하는 속도.", formula="v_p = ω/k", unit="m/s", related="군속도,분산", level="심화"),
    make("진동·파동·소리", "군속도", "group velocity", "여러 파동이 만든 파동 묶음이나 에너지 포락선이 이동하는 속도.", formula="v_g = dω/dk", unit="m/s", related="위상 속도,분산", level="심화"),
    make("진동·파동·소리", "분산", "wave dispersion", "파동 속력이 진동수나 파장에 따라 달라져 파동 묶음의 모양이 변하는 현상.", related="군속도,위상 속도"),
    make("진동·파동·소리", "맥놀이", "beats", "진동수가 조금 다른 두 파동이 겹쳐 진폭이 주기적으로 커졌다 작아지는 현상.", formula="f_beat = |f₁-f₂|", unit="Hz", related="간섭,진동수"),
    make("진동·파동·소리", "정상파", "standing wave", "반대 방향으로 진행하는 같은 진동수의 파동이 겹쳐 마디와 배가 고정된 파동.", related="마디,배,공명"),
    make("진동·파동·소리", "마디", "node wave", "정상파에서 변위가 항상 0인 위치.", related="배,정상파"),
    make("진동·파동·소리", "배", "antinode", "정상파에서 진폭이 최대인 위치.", related="마디,정상파"),
    make("진동·파동·소리", "기본 진동", "fundamental mode", "경계 조건을 만족하는 가장 낮은 진동수의 정상파 모드.", aliases="기본음", related="배음,고유진동수"),
    make("진동·파동·소리", "배음", "harmonic", "기본 진동수의 정수배 관계를 이루는 진동 성분.", related="기본 진동,음색"),
    make("진동·파동·소리", "소리 세기 준위", "sound intensity level", "기준 소리 세기에 대한 비를 로그로 나타낸 값.", formula="β = 10 log₁₀(I/I₀)", unit="dB", related="소리 세기,데시벨"),
    make("진동·파동·소리", "충격파", "shock wave", "압력과 밀도 등이 매우 짧은 거리에서 급격히 변하는 파동 전선.", example="초음속 비행체의 소닉붐.", related="마하 수,음속"),

    # 열역학
    make("열·열역학", "열용량", "heat capacity", "물체의 온도를 1 K 높이는 데 필요한 열량.", formula="C = Q/ΔT", unit="J/K", related="비열,열량"),
    make("열·열역학", "비열", "specific heat capacity", "단위 질량 물질의 온도를 1 K 높이는 데 필요한 열량.", formula="Q = mcΔT", unit="J/(kg·K)", related="열용량,열량"),
    make("열·열역학", "몰열용량", "molar heat capacity", "물질 1 mol의 온도를 1 K 높이는 데 필요한 열량.", unit="J/(mol·K)", related="비열,몰"),
    make("열·열역학", "잠열", "latent heat", "온도 변화 없이 상이 변할 때 단위 질량당 흡수하거나 방출하는 에너지.", formula="Q = mL", unit="J/kg", related="상전이,융해열"),
    make("열·열역학", "상전이", "phase transition", "물질이 고체, 액체, 기체 등 서로 다른 상 사이에서 변하는 과정.", related="잠열,임계점"),
    make("열·열역학", "삼중점", "triple point", "고체, 액체, 기체 세 상이 평형으로 동시에 존재하는 온도와 압력.", related="상평형,임계점"),
    make("열·열역학", "임계점", "critical point", "액체와 기체의 구분이 사라지는 임계 온도와 임계 압력의 상태.", related="상전이,초임계 유체"),
    make("열·열역학", "열팽창", "thermal expansion", "온도가 변할 때 물체의 길이, 넓이 또는 부피가 변하는 현상.", formula="ΔL = αL₀ΔT", related="선팽창계수,온도"),
    make("열·열역학", "선팽창계수", "linear expansion coefficient", "온도 1 K 변화에 대한 단위 길이당 길이 변화율.", formula="α = ΔL/(L₀ΔT)", unit="K⁻¹", related="열팽창"),
    make("열·열역학", "등온 과정", "isothermal process", "온도가 일정하게 유지되는 열역학 과정.", formula="T = constant", related="이상기체,단열 과정"),
    make("열·열역학", "등압 과정", "isobaric process", "압력이 일정하게 유지되는 열역학 과정.", formula="p = constant", related="열역학 과정"),
    make("열·열역학", "등적 과정", "isochoric process", "부피가 일정하게 유지되는 열역학 과정.", formula="V = constant", aliases="정적 과정", related="열역학 제1법칙"),
    make("열·열역학", "단열 과정", "adiabatic process", "계와 주변 사이에 열 전달이 없는 과정.", formula="Q = 0", related="등온 과정,열역학 제1법칙"),
    make("열·열역학", "카르노 기관", "Carnot engine", "두 열원 사이에서 가역 과정으로 작동하는 이상적인 최대 효율 열기관.", formula="η = 1 - T_c/T_h", related="열기관,열역학 제2법칙", level="심화"),
    make("열·열역학", "성능계수", "coefficient of performance", "냉동기나 열펌프가 투입 일에 비해 얼마나 많은 열을 옮기는지 나타내는 비.", formula="COP = Q/W", unit="무차원", related="냉동기,열펌프"),

    # 전기·자기
    make("전기·자기", "전기선속", "electric flux", "면을 통과하는 전기장의 법선 성분을 면적에 대해 합한 양.", formula="Φ_E = ∫E·dA", unit="N·m²/C", related="가우스 법칙,전기장"),
    make("전기·자기", "전기 퍼텐셜", "electric potential", "단위 양전하당 전기적 위치에너지.", formula="V = U/q", unit="V", aliases="전위", related="전위차,전기장"),
    make("전기·자기", "전기용량", "capacitance", "축전기가 전위차당 저장하는 전하량.", formula="C = Q/V", unit="F", aliases="정전용량", related="축전기,유전체"),
    make("전기·자기", "유전율", "permittivity", "물질 속 전기장이 전하와 어떻게 관계되는지 나타내는 물질 상수.", unit="F/m", related="유전체,쿨롱 법칙"),
    make("전기·자기", "유전분극", "dielectric polarization", "유전체 내부의 양전하와 음전하 중심이 상대적으로 어긋나 전기쌍극자가 정렬되는 현상.", related="유전체,전기장"),
    make("전기·자기", "기전력", "electromotive force", "전원이 단위 전하에 공급하는 에너지.", formula="ℰ = W/q", unit="V", aliases="EMF", related="전압,전원"),
    make("전기·자기", "전류밀도", "current density", "단면적당 흐르는 전류의 크기와 방향을 나타내는 벡터.", formula="J = I/A", unit="A/m²", related="전류,전도도"),
    make("전기·자기", "전도도", "electrical conductivity", "물질이 전류를 얼마나 잘 흐르게 하는지 나타내는 물질 상수.", formula="σ = 1/ρ", unit="S/m", related="비저항,옴의 법칙"),
    make("전기·자기", "RC 회로", "RC circuit", "저항과 축전기로 이루어져 충전과 방전이 지수적으로 진행되는 회로.", formula="τ = RC", unit="s", related="시정수,축전기"),
    make("전기·자기", "RL 회로", "RL circuit", "저항과 인덕터로 이루어져 전류 변화가 지수적으로 진행되는 회로.", formula="τ = L/R", unit="s", related="인덕턴스,시정수"),
    make("전기·자기", "LC 회로", "LC circuit", "인덕터와 축전기 사이에서 전기장 에너지와 자기장 에너지가 교환되는 회로.", formula="ω₀ = 1/√(LC)", related="공진,RLC 회로"),
    make("전기·자기", "RLC 회로", "RLC circuit", "저항, 인덕터, 축전기를 포함해 감쇠와 공진을 보이는 회로.", related="임피던스,공진"),
    make("전기·자기", "용량 리액턴스", "capacitive reactance", "교류에서 축전기가 전류 변화를 방해하는 정도.", formula="X_C = 1/(ωC)", unit="Ω", related="유도 리액턴스,임피던스"),
    make("전기·자기", "유도 리액턴스", "inductive reactance", "교류에서 인덕터가 전류 변화를 방해하는 정도.", formula="X_L = ωL", unit="Ω", related="용량 리액턴스,임피던스"),
    make("전기·자기", "임피던스", "impedance", "교류 회로에서 저항과 리액턴스를 함께 나타내는 복소량.", unit="Ω", related="리액턴스,위상차", level="심화"),
    make("전기·자기", "위상자", "phasor", "같은 진동수의 교류 진폭과 위상을 복소평면의 회전 벡터로 나타내는 표현.", aliases="페이저", related="임피던스,교류", level="심화"),
    make("전기·자기", "변압기", "transformer", "전자기 유도로 교류 전압과 전류의 크기를 바꾸는 장치.", formula="V_s/V_p = N_s/N_p", related="전자기 유도,교류"),
    make("전기·자기", "변위전류", "displacement current", "시간에 따라 변하는 전기장이 자기장을 만드는 효과를 전류와 같은 형태로 나타낸 양.", related="맥스웰 방정식,전자기파", level="심화"),
    make("전기·자기", "포인팅 벡터", "Poynting vector", "전자기장이 단위 면적당 운반하는 에너지 흐름의 방향과 크기.", formula="S = E×H", unit="W/m²", related="전자기파,에너지 밀도", level="심화"),

    # 광학
    make("빛·광학", "광학적 경로 길이", "optical path length", "빛이 지나간 실제 거리와 매질의 굴절률을 곱해 위상 변화를 나타내는 길이.", formula="OPL = ∫n ds", unit="m", related="굴절률,간섭"),
    make("빛·광학", "초점거리", "focal length", "렌즈나 거울의 기준점에서 초점까지의 거리.", unit="m", related="렌즈 공식,광학적 세기"),
    make("빛·광학", "광학적 세기", "optical power", "렌즈가 빛을 모으거나 퍼뜨리는 정도로 초점거리의 역수.", formula="P = 1/f", unit="D", aliases="굴절력,디옵터", related="초점거리,렌즈"),
    make("빛·광학", "개구", "aperture optics", "광학계에서 빛이 통과할 수 있는 유효한 구멍 또는 지름.", related="조리개,F수"),
    make("빛·광학", "F수", "f-number", "렌즈 초점거리를 입사동공 지름으로 나눈 값.", formula="N = f/D", unit="무차원", aliases="조리개값", related="개구,피사계 심도"),
    make("빛·광학", "분해능", "optical resolution", "서로 가까운 두 점이나 두 파장을 구별할 수 있는 능력.", related="레이리 기준,회절"),
    make("빛·광학", "레이리 기준", "Rayleigh criterion", "두 회절 무늬를 간신히 구별할 수 있다고 보는 대표적인 분해능 기준.", formula="θ ≈ 1.22λ/D", related="분해능,회절"),
    make("빛·광학", "브루스터 각", "Brewster angle", "반사광이 완전히 선편광되는 입사각.", formula="tan θ_B = n₂/n₁", related="편광,반사"),
    make("빛·광학", "소멸파", "evanescent wave", "전반사 경계 너머로 짧은 거리만 침투하며 지수적으로 약해지는 장.", aliases="에바네슨트 파", related="전반사,광섬유", level="심화"),
    make("빛·광학", "광섬유", "optical fiber", "전반사를 이용해 빛을 긴 거리로 안내하는 투명한 가는 섬유.", related="전반사,굴절률"),
    make("빛·광학", "분광학", "spectroscopy", "빛의 파장 또는 진동수별 세기를 측정해 물질의 구조와 상태를 연구하는 방법.", related="스펙트럼,회절격자"),
    make("빛·광학", "회절격자", "diffraction grating", "많은 평행 슬릿이나 홈을 이용해 파장별로 빛을 분리하는 광학 소자.", formula="d sinθ = mλ", related="회절,분광학"),

    # 상대론
    make("상대성이론", "세계선", "worldline", "시공간에서 한 물체가 시간에 따라 지나가는 사건들의 경로.", related="시공간,고유시간"),
    make("상대성이론", "빛원뿔", "light cone", "한 사건과 빛이나 그보다 느린 신호로 인과적으로 연결될 수 있는 시공간 영역의 경계.", related="인과율,시공간"),
    make("상대성이론", "불변 간격", "spacetime interval", "관성계가 달라도 값이 같은 두 사건 사이의 시공간 간격.", formula="s² = c²Δt² - Δx² - Δy² - Δz²", related="로런츠 변환,고유시간", level="심화"),
    make("상대성이론", "사차원 벡터", "four-vector", "로런츠 변환 아래에서 시공간 좌표처럼 변하는 네 성분 벡터.", example="사운동량, 사속도.", related="시공간,로런츠 변환", level="심화"),
    make("상대성이론", "상대론적 에너지", "relativistic energy", "정지에너지와 운동에너지를 함께 포함하는 입자의 총에너지.", formula="E² = (pc)² + (mc²)²", unit="J 또는 eV", related="질량-에너지 등가,상대론적 운동량"),
    make("상대성이론", "슈바르츠실트 반지름", "Schwarzschild radius", "회전하지 않고 전하가 없는 질량의 사건지평선 반지름.", formula="r_s = 2GM/c²", unit="m", related="블랙홀,사건지평선"),
    make("상대성이론", "측지선", "geodesic", "휘어진 시공간에서 자유롭게 움직이는 물체나 빛이 따르는 가장 곧은 경로.", related="일반상대성이론,시공간"),
    make("상대성이론", "중력 적색편이", "gravitational redshift", "강한 중력장에서 빠져나오는 빛의 진동수가 낮아지는 현상.", related="중력 시간 지연,일반상대성이론"),

    # 양자
    make("양자·원자", "관측가능량", "observable quantum mechanics", "양자역학에서 측정할 수 있는 물리량으로 에르미트 연산자에 대응한다.", aliases="옵저버블", related="연산자,고유값", level="심화"),
    make("양자·원자", "연산자", "operator quantum mechanics", "양자상태에 작용하여 다른 상태나 측정 가능한 정보를 만드는 수학적 규칙.", related="관측가능량,파동함수", level="심화"),
    make("양자·원자", "고유값", "eigenvalue quantum", "연산자가 고유상태에 작용할 때 상태를 바꾸지 않고 곱해지는 값.", formula="Â|a⟩ = a|a⟩", related="고유상태,관측가능량", level="심화"),
    make("양자·원자", "고유상태", "eigenstate", "어떤 관측가능량을 측정하면 확정된 고유값을 주는 양자상태.", related="고유값,측정", level="심화"),
    make("양자·원자", "중첩 원리", "quantum superposition", "여러 가능한 양자상태의 선형 결합도 하나의 허용된 상태가 된다는 원리.", related="파동함수,양자 측정"),
    make("양자·원자", "양자 측정", "quantum measurement", "양자상태에서 관측가능량의 결과가 확률에 따라 나타나는 과정.", related="보른 규칙,고유상태"),
    make("양자·원자", "결어긋남", "quantum decoherence", "양자계가 환경과 상호작용해 서로 다른 상태 사이의 위상 관계가 사실상 사라지는 과정.", aliases="데코히런스", related="중첩 원리,양자 얽힘", level="심화"),
    make("양자·원자", "양자 얽힘", "quantum entanglement", "여러 입자의 상태를 각 입자의 독립된 상태로 나눌 수 없는 강한 양자 상관관계.", related="벨 부등식,중첩 원리"),
    make("양자·원자", "양자수", "quantum number", "양자상태를 구별하기 위해 허용된 불연속 값을 갖는 수.", example="주양자수 n, 방위양자수 l, 자기양자수 m.", related="원자 궤도함수,에너지 준위"),
    make("양자·원자", "원자 궤도함수", "atomic orbital", "원자 속 전자의 공간적 파동함수와 확률분포를 나타내는 상태.", aliases="오비탈", related="양자수,전자배치"),
    make("양자·원자", "제만 효과", "Zeeman effect", "자기장 때문에 원자의 에너지 준위와 스펙트럼선이 갈라지는 현상.", related="스핀,원자 스펙트럼"),
    make("양자·원자", "스타크 효과", "Stark effect", "전기장 때문에 원자나 분자의 에너지 준위와 스펙트럼선이 이동하거나 갈라지는 현상.", related="전기장,원자 스펙트럼"),
    make("양자·원자", "스핀-궤도 결합", "spin-orbit coupling", "입자의 스핀과 궤도 각운동량 사이의 상호작용.", related="미세구조,스핀", level="심화"),
    make("양자·원자", "페르미-디랙 분포", "Fermi-Dirac distribution", "열평형에서 페르미온이 에너지 상태를 차지할 평균 확률을 나타내는 분포.", related="페르미온,파울리 배타 원리", level="심화"),
    make("양자·원자", "보스-아인슈타인 분포", "Bose-Einstein distribution", "열평형에서 보손이 에너지 상태를 차지하는 평균 개수를 나타내는 분포.", related="보손,보스-아인슈타인 응축", level="심화"),

    # 입자
    make("핵·입자", "반응 단면적", "cross section particle physics", "입자 반응이 일어날 가능성을 유효 면적으로 나타낸 양.", unit="m² 또는 barn", aliases="단면적", related="충돌,산란"),
    make("핵·입자", "붕괴폭", "decay width", "불안정한 입자의 수명과 연결되는 에너지 폭.", formula="Γ ≈ ħ/τ", unit="eV", related="평균수명,붕괴"),
    make("핵·입자", "분기비", "branching ratio", "한 입자가 여러 붕괴 경로 중 특정 경로로 붕괴하는 비율.", unit="무차원 또는 %", related="방사성 붕괴,붕괴폭"),
    make("핵·입자", "색전하", "color charge", "양자색역학에서 쿼크와 글루온이 강한 상호작용에 참여하게 하는 전하.", related="쿼크,글루온", level="심화"),
    make("핵·입자", "쿼크 가둠", "quark confinement", "낮은 에너지에서 쿼크와 글루온을 고립된 자유입자로 꺼낼 수 없는 성질.", aliases="색가둠", related="강한 상호작용,하드론", level="심화"),
    make("핵·입자", "점근적 자유", "asymptotic freedom", "매우 높은 에너지나 짧은 거리에서 쿼크 사이 강한 상호작용이 약해지는 성질.", related="강한 상호작용,쿼크", level="심화"),
    make("핵·입자", "중성미자 진동", "neutrino oscillation", "이동하는 중성미자가 서로 다른 맛 상태로 바뀔 확률이 주기적으로 변하는 현상.", related="중성미자,질량 고유상태", level="심화"),
    make("핵·입자", "CP 위반", "CP violation", "입자와 반입자를 바꾸고 공간을 반전하는 변환에서 물리 과정이 완전히 같지 않은 현상.", related="반물질,약한 상호작용", level="심화"),
    make("핵·입자", "충돌형 가속기", "collider", "서로 반대 방향으로 가속한 입자 빔을 충돌시켜 높은 중심질량 에너지를 만드는 가속기.", related="가속기,LHC"),
    make("핵·입자", "싱크로트론 복사", "synchrotron radiation", "상대론적 하전입자가 자기장 속에서 휘어진 경로를 따라 움직일 때 내는 전자기복사.", related="가속기,자기장"),

    # 천체
    make("천체·우주", "겉보기등급", "apparent magnitude", "지구에서 보이는 천체의 밝기를 로그 척도로 나타낸 값.", related="절대등급,광도"),
    make("천체·우주", "절대등급", "absolute magnitude", "천체를 10 pc 거리에 두었다고 가정했을 때의 겉보기등급.", related="겉보기등급,거리 지수"),
    make("천체·우주", "광도", "luminosity astronomy", "천체가 단위 시간에 모든 방향으로 방출하는 총에너지.", unit="W", related="복사 플럭스,별"),
    make("천체·우주", "복사 플럭스", "radiative flux astronomy", "관측 위치에서 단위 면적당 단위 시간에 받는 복사 에너지.", formula="F = L/(4πd²)", unit="W/m²", related="광도,역제곱 법칙"),
    make("천체·우주", "헤르츠스프룽-러셀도", "Hertzsprung-Russell diagram", "별의 광도 또는 절대등급을 표면온도나 색과 함께 나타낸 분포도.", aliases="HR도,H-R도", related="주계열성,별의 진화"),
    make("천체·우주", "주계열성", "main-sequence star", "중심에서 수소 핵융합을 하며 H-R도 주계열에 놓인 별.", related="헤르츠스프룽-러셀도,별의 진화"),
    make("천체·우주", "적색거성", "red giant", "중심 수소가 고갈된 뒤 바깥층이 크게 팽창하고 표면이 비교적 차가워진 별.", related="별의 진화,백색왜성"),
    make("천체·우주", "백색왜성", "white dwarf", "낮거나 중간 질량 별이 진화한 뒤 남기는 작고 뜨거운 전자 축퇴 천체.", related="전자 축퇴압,찬드라세카르 한계"),
    make("천체·우주", "중성자별", "neutron star", "무거운 별의 핵붕괴 뒤 남을 수 있는 매우 조밀한 천체.", related="초신성,펄서"),
    make("천체·우주", "초신성", "supernova", "별이 진화 끝에 폭발적으로 밝아지며 큰 에너지를 방출하는 현상.", related="중성자별,별의 진화"),
    make("천체·우주", "강착원반", "accretion disk", "중심 천체로 떨어지는 물질이 각운동량 때문에 원반을 이루며 가열된 구조.", related="블랙홀,각운동량"),
    make("천체·우주", "에딩턴 광도", "Eddington luminosity", "복사압과 중력이 균형을 이루는 천체의 대표적인 최대 정상 광도.", related="강착원반,복사압", level="심화"),
    make("천체·우주", "우주 적색편이", "cosmological redshift", "우주 팽창으로 멀리서 온 빛의 파장이 늘어나는 현상.", formula="1+z = λ_obs/λ_emit", related="허블 법칙,우주 팽창"),
    make("천체·우주", "허블 법칙", "Hubble law", "가까운 우주에서 은하의 후퇴 속도가 거리와 대체로 비례한다는 관계.", formula="v = H₀d", related="우주 팽창,적색편이"),
    make("천체·우주", "우주배경복사", "cosmic microwave background", "뜨거운 초기 우주에서 방출되어 오늘날 마이크로파로 관측되는 거의 균일한 복사.", aliases="CMB,우주 마이크로파 배경", related="빅뱅,우주론"),
    make("천체·우주", "암흑에너지", "dark energy", "우주 팽창이 가속되는 현상을 설명하기 위해 도입된 에너지 성분의 이름.", related="우주 팽창,우주상수"),
    make("천체·우주", "외계행성", "exoplanet", "태양이 아닌 다른 별 주위를 도는 행성.", related="통과법,시선속도법"),
    make("천체·우주", "통과법", "transit method", "행성이 별 앞을 지날 때 별빛이 주기적으로 조금 감소하는 현상으로 외계행성을 찾는 방법.", related="외계행성,광도곡선"),
]


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    terms = payload["terms"]
    names = {t["name_ko"] for t in terms}
    ids = {t["id"] for t in terms}
    added = 0
    for term in CANDIDATES:
        if term["name_ko"] in names:
            continue
        base = term["id"]
        suffix = 2
        while term["id"] in ids:
            term["id"] = f"{base}-{suffix}"
            suffix += 1
        pieces = [
            term["name_ko"], term["name_en"], term["category"], term["level"],
            term["summary"], term["detail"], term["formula"], term["unit"],
            term["example"], term["caution"], " ".join(term["aliases"]), " ".join(term["related"]),
        ]
        term["search_text"] = " ".join(x for x in pieces if x)
        terms.append(term)
        names.add(term["name_ko"])
        ids.add(term["id"])
        added += 1
    terms.sort(key=lambda x: (x.get("category", ""), x.get("name_ko", "")))
    payload["terms"] = terms
    payload["meta"] = {
        **payload.get("meta", {}),
        "version": "2.0.0",
        "count": len(terms),
        "note": "Physics Pocket 2.0 curated offline physics dictionary",
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Added {added}; total {len(terms)}")


if __name__ == "__main__":
    main()
