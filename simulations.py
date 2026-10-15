from __future__ import annotations

import math
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional
from physics_engine import FIXED_DT, constant_force_motion
from beta_simulations import BETA_SIM_SPECS

SIM_TITLES = {
    "newton2": "힘·질량·가속도",
    "projectile": "포물선 운동",
    "spring": "용수철 진동",
    "wave": "파동",
    "refraction": "빛의 굴절",
    "electric_field": "전하와 전기력",
    "energy": "역학적 에너지",
    "linear_function": "일차함수 그래프",
    "quadratic": "이차함수 그래프",
    "unit_circle": "단위원·삼각함수",
    "vectors": "벡터 합성",
    "derivative": "미분·접선",
    "integral": "리만합·정적분",
    "matrix": "2×2 선형변환",
    "sequence": "수열",
}

PHYSICS_FALLBACK = {
    "운동학": "projectile", "힘·에너지": "newton2", "진동·파동·소리": "wave",
    "빛·광학": "refraction", "전기·자기": "electric_field",
}
MATH_FALLBACK = {
    "함수": "linear_function", "삼각함수": "unit_circle", "미적분": "derivative",
    "기하": "vectors", "선형대수": "matrix", "수열": "sequence",
}


# 3.5 Beta: lightweight relationship simulators.  They share one tested plotting
# engine, but each entry has its own variables, relation and subject.  This keeps
# the beta compact while expanding the number of concepts students can manipulate.
def _spec(title, subject, term, formula, x_label, y_label, xmin, xmax, expr, sliders=()):
    return {
        "title": title, "subject": subject, "term": term, "formula": formula,
        "x_label": x_label, "y_label": y_label, "xmin": xmin, "xmax": xmax,
        "expr": expr, "sliders": list(sliders),
    }

GENERIC_SIM_SPECS = {
    # Physics (25)
    "free_fall": _spec("자유낙하", "물리", "자유낙하", "h = h₀ - ½gt²", "t", "h", 0, 5, "max(0,h0-0.5*g*x*x)", (("초기높이 h₀","h0",5,100,40),("중력 g","g",1.6,15,9.8))),
    "uniform_motion": _spec("등속 직선 운동", "물리", "등속 직선 운동", "x = x₀ + vt", "t", "x", 0, 10, "x0+v*x", (("초기위치 x₀","x0",-10,10,0),("속도 v","v",-10,10,3))),
    "circular_motion": _spec("등속 원운동", "물리", "원운동", "a_c = v²/r", "v", "a_c", 0, 20, "x*x/r", (("반지름 r","r",0.5,10,3),)),
    "gravity_inverse_square": _spec("만유인력 역제곱", "물리", "만유인력", "F ∝ 1/r²", "r", "상대 힘", 0.2, 8, "m/(x*x)", (("질량계수","m",0.5,5,1),)),
    "momentum": _spec("운동량", "물리", "운동량", "p = mv", "v", "p", -10, 10, "m*x", (("질량 m","m",0.5,10,2),)),
    "impulse": _spec("충격량", "물리", "충격량", "J = FΔt", "Δt", "J", 0, 5, "F*x", (("힘 F","F",-20,20,8),)),
    "elastic_collision": _spec("1차원 탄성충돌", "물리", "탄성 충돌", "v₁' = ((m₁-m₂)/(m₁+m₂))v₁", "m₂", "v₁'", 0.2, 10, "((m1-x)/(m1+x))*v1", (("m₁","m1",0.5,10,2),("v₁","v1",-10,10,5))),
    "pendulum": _spec("단진자 주기", "물리", "단진자", "T = 2π√(L/g)", "L", "T", 0.1, 5, "2*pi*sqrt(x/g)", (("중력 g","g",1.6,15,9.8),)),
    "damping": _spec("감쇠진동", "물리", "감쇠 진동", "A(t)=A₀e^{-bt}", "t", "진폭", 0, 10, "A*exp(-b*x)*cos(w*x)", (("A₀","A",0.5,3,1),("감쇠 b","b",0.02,1,0.2),("각진동수 ω","w",0.5,5,2))),
    "resonance": _spec("공명 곡선", "물리", "공명", "A ∝ 1/√((ω₀²-ω²)²+(2βω)²)", "ω", "진폭", 0.05, 6, "1/sqrt((w0*w0-x*x)**2+(2*b*x)**2)", (("고유ω₀","w0",0.5,5,2),("감쇠 β","b",0.05,1,0.25))),
    "standing_wave": _spec("정상파", "물리", "정상파", "y = A sin(kx)", "x", "y", 0, 6.283, "A*sin(n*x)", (("진폭 A","A",0.5,3,1),("모드 n","n",1,6,2))),
    "doppler": _spec("도플러 효과", "물리", "도플러 효과", "f' = f v/(v-v_s)", "v_s", "f'", -80, 80, "f*v/(v-x)", (("원주파수 f","f",100,1000,440),("파동속력 v","v",250,400,343))),
    "buoyancy": _spec("부력", "물리", "부력", "F_B = ρgV", "V", "F_B", 0, 0.02, "rho*g*x", (("유체밀도 ρ","rho",500,1500,1000),("중력 g","g",1.6,15,9.8))),
    "pressure_depth": _spec("유체의 깊이와 압력", "물리", "정수압", "P = ρgh", "h", "P", 0, 20, "rho*g*x", (("밀도 ρ","rho",500,1500,1000),("중력 g","g",1.6,15,9.8))),
    "bernoulli": _spec("베르누이 관계", "물리", "베르누이 정리", "P + ½ρv² = const", "v", "상대 압력", 0, 20, "P0-0.5*rho*x*x", (("기준압 P₀","P0",50000,200000,100000),("밀도 ρ","rho",0.8,1200,1000))),
    "ideal_gas_physics": _spec("이상기체 상태", "물리", "이상 기체 법칙", "P = nRT/V", "T", "P", 100, 800, "n*8.314*x/V", (("몰수 n","n",0.2,5,1),("부피 V","V",0.005,0.1,0.024))),
    "thermal_expansion": _spec("선팽창", "물리", "열팽창", "ΔL = αL₀ΔT", "ΔT", "ΔL", -100, 300, "alpha*L*x", (("α (×10⁻⁵)","alpha_u",0.1,3,1.2),("길이 L₀","L",0.5,10,1))),
    "heat_conduction": _spec("열전도", "물리", "열전도", "Q/t ∝ kAΔT/L", "ΔT", "열전달률", 0, 200, "k*A*x/L", (("전도율 k","k",0.1,400,20),("면적 A","A",0.01,1,0.1),("두께 L","L",0.01,1,0.1))),
    "ohm_law": _spec("옴의 법칙", "물리", "옴의 법칙", "I = V/R", "V", "I", -20, 20, "x/R", (("저항 R","R",0.5,50,10),)),
    "series_resistors": _spec("직렬 저항", "물리", "직렬 회로", "R_eq = R₁ + R₂", "R₂", "R_eq", 0, 100, "R1+x", (("R₁","R1",0,100,20),)),
    "parallel_resistors": _spec("병렬 저항", "물리", "병렬 회로", "R_eq = R₁R₂/(R₁+R₂)", "R₂", "R_eq", 0.1, 100, "R1*x/(R1+x)", (("R₁","R1",0.1,100,20),)),
    "capacitor_charge": _spec("RC 충전", "물리", "RC 회로", "V_C=V₀(1-e^{-t/RC})", "t", "V_C", 0, 10, "V0*(1-exp(-x/(R*C)))", (("V₀","V0",1,20,5),("R","R",0.2,5,1),("C","C",0.2,5,1))),
    "magnetic_force": _spec("자기력", "물리", "로런츠 힘", "F = qvB", "v", "F", -20, 20, "q*x*B", (("전하계수 q","q",-5,5,1),("자기장 B","B",0,3,1))),
    "induction": _spec("전자기 유도", "물리", "전자기 유도", "|ε| = N|dΦ/dt|", "|dΦ/dt|", "|ε|", 0, 10, "N*x", (("감은수 N","N",1,200,50),)),
    "thin_lens": _spec("얇은 렌즈", "물리", "얇은 렌즈 공식", "1/f = 1/d_o + 1/d_i", "d_o", "d_i", 1.1, 20, "1/(1/f-1/x)", (("초점거리 f","f",0.5,10,2),)),

    # Chemistry (15)
    "boyle_law": _spec("보일 법칙", "화학", "보일 법칙", "P ∝ 1/V", "V", "P", 0.2, 5, "K/x", (("PV 상수","K",1,20,5),)),
    "charles_law": _spec("샤를 법칙", "화학", "샤를 법칙", "V ∝ T", "T(K)", "V", 100, 600, "k*x", (("비례상수","k",0.001,0.02,0.004),)),
    "ideal_gas_chem": _spec("이상기체 법칙", "화학", "이상 기체", "P=nRT/V", "T", "P", 100, 800, "n*8.314*x/V", (("n","n",0.2,5,1),("V","V",0.005,0.1,0.024))),
    "molarity": _spec("몰농도", "화학", "몰농도", "M=n/V", "V(L)", "M", 0.1, 5, "n/x", (("용질 mol","n",0.01,5,1),)),
    "dilution": _spec("희석 관계", "화학", "희석", "M₂=M₁V₁/V₂", "V₂", "M₂", 0.1, 5, "M1*V1/x", (("M₁","M1",0.1,5,1),("V₁","V1",0.1,2,0.5))),
    "ph_scale": _spec("pH 척도", "화학", "pH", "pH=-log₁₀[H⁺]", "log₁₀[H⁺]", "pH", -14, 0, "-x"),
    "buffer_response": _spec("완충 용액의 변화", "화학", "완충 용액", "pH≈pKₐ+log(base/acid)", "base/acid", "pH", 0.05, 10, "pka+log10(x)", (("pKₐ","pka",2,12,4.76),)),
    "reaction_rate": _spec("반응 속도", "화학", "반응 속도", "rate=k[A]^n", "[A]", "rate", 0, 5, "k*(x**n)", (("k","k",0.1,5,1),("차수 n","n",0.5,3,1))),
    "arrhenius": _spec("아레니우스 관계", "화학", "아레니우스 식", "k=Ae^{-Eₐ/RT}", "T", "k", 250, 1000, "A*exp(-Ea/(8.314*x))", (("A (축약)","A",0.5,5,1),("Eₐ(kJ/mol)","Ea_k",5,100,40))),
    "equilibrium": _spec("평형 이동", "화학", "화학 평형", "Q와 K 비교", "Q/K", "평형 경향", 0.1, 3, "log10(x)"),
    "beer_lambert": _spec("비어-람베르트 법칙", "화학", "비어-람베르트 법칙", "A=εbc", "c", "흡광도 A", 0, 2, "eps*b*x", (("ε","eps",0.1,5,1),("b","b",0.1,5,1))),
    "nernst": _spec("네른스트 관계", "화학", "네른스트 식", "E=E°-(RT/nF)lnQ", "ln Q", "E", -5, 5, "E0-(8.314*T/(n*96485))*x", (("E°","E0",-2,2,0.5),("T","T",250,350,298),("전자수 n","n",1,6,2))),
    "solubility": _spec("용해도와 온도", "화학", "용해도", "간단한 온도-용해도 모델", "T", "상대 용해도", 0, 100, "s0+slope*x", (("기준 용해도","s0",0,100,20),("온도계수","slope",-1,3,0.5))),
    "colligative": _spec("어는점 내림", "화학", "총괄성", "ΔT_f=iK_f m", "몰랄농도 m", "ΔT_f", 0, 5, "i*K*x", (("반트호프 i","i",1,4,1),("K_f","K",0.5,5,1.86))),
    "electrolysis_charge": _spec("전기분해 전하량", "화학", "전기분해", "Q=It", "t", "Q", 0, 600, "I*x", (("전류 I","I",0.1,10,1),)),

    # Biology (15)
    "enzyme_rate": _spec("효소 반응 속도", "생명과학", "효소", "v=Vmax[S]/(Km+[S])", "[S]", "v", 0, 10, "V*x/(K+x)", (("Vmax","V",0.5,10,4),("Km","K",0.1,5,1))),
    "michaelis_menten": _spec("미하엘리스-멘텐", "생명과학", "미하엘리스-멘텐 식", "v=Vmax[S]/(Km+[S])", "[S]", "v", 0, 10, "V*x/(K+x)", (("Vmax","V",0.5,10,5),("Km","K",0.1,5,2))),
    "population_logistic": _spec("로지스틱 개체군 성장", "생명과학", "로지스틱 성장", "N=K/(1+Ae^{-rt})", "t", "N", 0, 20, "K/(1+A*exp(-r*x))", (("수용력 K","K",100,2000,1000),("초기계수 A","A",1,50,20),("성장률 r","r",0.05,1,0.35))),
    "exponential_growth_bio": _spec("지수적 개체군 성장", "생명과학", "지수 성장", "N=N₀e^{rt}", "t", "N", 0, 10, "N0*exp(r*x)", (("N₀","N0",1,100,10),("r","r",0.01,0.8,0.25))),
    "mendel_mono": _spec("단일유전자 분리", "생명과학", "멘델 유전", "Aa×Aa의 우성 표현형 비율", "우성확률 p", "표현형 비율", 0, 1, "x*x+2*x*(1-x)"),
    "hardy_weinberg": _spec("하디-바인베르크", "생명과학", "하디-바인베르크 평형", "p²+2pq+q²=1", "p", "2pq", 0, 1, "2*x*(1-x)"),
    "membrane_diffusion": _spec("막을 통한 확산", "생명과학", "확산", "flux ∝ ΔC", "농도차 ΔC", "상대 flux", -10, 10, "P*x", (("투과계수 P","P",0.1,5,1),)),
    "osmosis_bio": _spec("삼투압", "생명과학", "삼투", "π≈iMRT", "M", "π", 0, 2, "i*8.314*T*x", (("i","i",1,3,1),("T","T",273,320,298))),
    "action_potential": _spec("활동전위 모형", "생명과학", "활동전위", "막전위의 시간 변화(개념 모형)", "t", "막전위", 0, 10, "-70+110*exp(-((x-4)/0.8)**2)-20*exp(-((x-5.5)/1.1)**2)"),
    "cardiac_output": _spec("심박출량", "생명과학", "심박출량", "CO=HR×SV", "HR", "CO", 40, 200, "x*SV", (("1회박출량 SV","SV",30,120,70),)),
    "photosynthesis_light": _spec("광합성 광포화", "생명과학", "광합성", "속도≈Pmax I/(K+I)", "광세기 I", "광합성률", 0, 1000, "P*x/(K+x)", (("Pmax","P",1,20,10),("반포화 K","K",10,500,150))),
    "respiration_rate": _spec("세포호흡과 기질", "생명과학", "세포호흡", "속도 포화 모형", "기질", "호흡률", 0, 10, "V*x/(K+x)", (("Vmax","V",0.5,10,4),("K","K",0.1,5,1))),
    "predator_prey": _spec("포식-피식 진동", "생명과학", "포식자-피식자 관계", "개념적 주기 모형", "t", "개체수 편차", 0, 20, "A*sin(w*x)*exp(-d*x)", (("진폭 A","A",10,100,60),("주기계수 ω","w",0.2,2,0.7),("감쇠 d","d",0,0.1,0.01))),
    "gene_expression": _spec("유전자 발현 유도", "생명과학", "유전자 발현", "발현≈x^n/(K^n+x^n)", "신호 x", "발현", 0, 10, "(x**n)/(K**n+x**n)", (("K","K",0.2,8,3),("Hill n","n",1,6,2))),
    "immune_response": _spec("면역반응 시간 변화", "생명과학", "적응면역", "증가 후 감소하는 개념 모형", "시간", "상대 반응", 0, 20, "A*(x**2)*exp(-k*x)", (("반응계수 A","A",0.1,5,1),("감쇠 k","k",0.1,1,0.35))),

    # Earth science (10)
    "seismic_wave": _spec("지진파 도달시간", "지구과학", "지진파", "t=d/v", "거리 d", "도달시간", 0, 1000, "x/v", (("파속 v","v",2,12,6),)),
    "plate_spreading": _spec("해저 확장", "지구과학", "해저 확장", "거리=확장속도×시간", "시간", "거리", 0, 200, "rate*x", (("확장속도","rate",0.1,10,3),)),
    "geothermal_gradient": _spec("지온 구배", "지구과학", "지온 구배", "T=T₀+Gd", "깊이", "온도", 0, 50, "T0+G*x", (("지표온도","T0",-20,40,15),("구배 G","G",5,40,25))),
    "pressure_altitude": _spec("고도와 기압", "지구과학", "기압", "P≈P₀e^{-h/H}", "고도", "기압", 0, 20, "P0*exp(-x/H)", (("P₀","P0",900,1050,1013),("척도고 H","H",5,10,8.4))),
    "humidity_dewpoint": _spec("온도와 포화수증기", "지구과학", "상대습도", "포화수증기량의 개념 곡선", "온도", "상대 포화량", -20, 40, "exp(0.06*x)"),
    "coriolis": _spec("코리올리 효과", "지구과학", "코리올리 효과", "f=2Ωsinφ", "위도 φ", "상대 f", -90, 90, "2*omega*sin(x*pi/180)", (("Ω(축약)","omega",0.5,2,1),)),
    "ocean_wave": _spec("해양 표면파", "지구과학", "파랑", "y=A sin(kx)", "x", "y", 0, 12.56, "A*sin(k*x)", (("A","A",0.2,3,1),("k","k",0.2,3,1))),
    "tide": _spec("조석 주기", "지구과학", "조석", "h≈A sin(ωt)", "시간", "해수면 편차", 0, 24, "A*sin(2*pi*x/T)", (("진폭 A","A",0.2,5,1),("주기 T","T",10,25,12.42))),
    "greenhouse": _spec("온실효과 개념", "지구과학", "온실효과", "평형온도의 단순 민감도", "복사강제력", "온도변화", -5, 10, "lambda_*x", (("민감도 λ","lambda_",0.2,1.5,0.8),)),
    "radiometric_age": _spec("방사성 연대", "지구과학", "방사성 연대측정", "N/N₀=2^{-t/T½}", "t/T½", "남은 비율", 0, 10, "2**(-x)"),

    # Astronomy (10)
    "kepler3": _spec("케플러 제3법칙", "천문학", "케플러 제3법칙", "T²∝a³", "a", "T", 0.2, 10, "sqrt(x**3/M)", (("중심질량계수 M","M",0.2,5,1),)),
    "orbital_speed": _spec("원궤도 속력", "천문학", "궤도 속도", "v∝√(M/r)", "r", "v", 0.2, 20, "sqrt(M/x)", (("질량계수 M","M",0.2,10,1),)),
    "escape_velocity": _spec("탈출속도", "천문학", "탈출 속도", "v_e∝√(M/r)", "r", "v_e", 0.2, 20, "sqrt(2*M/x)", (("질량계수 M","M",0.2,10,1),)),
    "stellar_luminosity": _spec("별의 광도", "천문학", "광도", "L∝R²T⁴", "T(상대)", "L", 0.3, 2, "R*R*x**4", (("반지름 R","R",0.2,5,1),)),
    "brightness_inverse_square": _spec("밝기의 역제곱", "천문학", "겉보기 밝기", "F∝L/d²", "거리 d", "밝기", 0.2, 20, "L/(x*x)", (("광도 L","L",0.2,10,1),)),
    "blackbody_peak": _spec("빈 변위 법칙", "천문학", "흑체복사", "λmax=b/T", "T", "λmax", 1000, 15000, "b/x", (("b(축약)","b",2000,4000,2898),)),
    "parallax": _spec("연주시차", "천문학", "연주시차", "d(pc)=1/p(arcsec)", "시차 p", "거리 d", 0.02, 1, "1/x"),
    "redshift": _spec("저속 적색편이", "천문학", "적색편이", "z≈v/c", "v/c", "z", -0.1, 0.1, "x"),
    "hubble": _spec("허블-르메트르 법칙", "천문학", "허블-르메트르 법칙", "v=H₀d", "거리 d", "후퇴속도", 0, 500, "H*x", (("H₀(축약)","H",0.05,0.1,0.07),)),
    "transit": _spec("외계행성 통과", "천문학", "통과법", "깊이≈(R_p/R_s)²", "R_p/R_s", "밝기 감소", 0, 0.3, "x*x"),

    # Mathematics (10)
    "exponential_function": _spec("지수함수", "수학", "지수함수", "y=a^x", "x", "y", -4, 4, "a**x", (("밑 a","a",0.2,4,2),)),
    "logarithm": _spec("로그함수", "수학", "로그함수", "y=log_a x", "x", "y", 0.05, 10, "log(x)/log(a)", (("밑 a","a",1.1,5,2),)),
    "absolute_value": _spec("절댓값 함수", "수학", "절댓값", "y=|x-h|+k", "x", "y", -6, 6, "abs(x-h)+k", (("h","h",-3,3,0),("k","k",-3,3,0))),
    "rational_function": _spec("유리함수", "수학", "유리함수", "y=a/(x-h)+k", "x", "y", -6, 6, "a/(x-h) if abs(x-h)>0.08 else nan", (("a","a",-5,5,1),("h","h",-2,2,0),("k","k",-3,3,0))),
    "polynomial_roots": _spec("삼차다항식과 근", "수학", "다항함수", "y=(x-r₁)(x-r₂)(x-r₃)", "x", "y", -5, 5, "(x-r1)*(x-r2)*(x-r3)", (("r₁","r1",-4,4,-2),("r₂","r2",-4,4,0),("r₃","r3",-4,4,2))),
    "normal_distribution": _spec("정규분포", "수학", "정규분포", "정규밀도곡선", "x", "밀도", -5, 5, "exp(-0.5*((x-mu)/sigma)**2)/(sigma*sqrt(2*pi))", (("평균 μ","mu",-2,2,0),("표준편차 σ","sigma",0.3,2,1))),
    "binomial_distribution": _spec("이항분포 형태", "수학", "이항분포", "평균=np, 분산=np(1-p)", "p", "분산", 0, 1, "n*x*(1-x)", (("시행수 n","n",1,100,20),)),
    "taylor_series": _spec("테일러 근사 오차", "수학", "테일러 급수", "e^x의 절단 오차(개념)", "x", "오차", -2, 2, "abs(exp(x)-sum((x**k)/factorial(k) for k in range(int(n)+1)))", (("차수 n","n",1,10,4),)),
    "newton_method": _spec("뉴턴 방법", "수학", "뉴턴 방법", "x_{n+1}=x_n-f/f'", "초깃값 x₀", "한 번 갱신", -4, 4, "x-(x*x-a)/(2*x) if abs(x)>0.05 else nan", (("목표 a","a",0.2,10,2),)),
    "fourier_series": _spec("푸리에 급수", "수학", "푸리에 급수", "사각파의 유한 사인합", "x", "합", -3.1416, 3.1416, "sum(sin((2*k+1)*x)/(2*k+1) for k in range(int(n)))", (("항 수 n","n",1,12,5),)),
}

# 3.5: 5,000 explicit scenarios from 50 scientific model families. The enhanced
# factory routes them to their analytic viewer or deterministic physics engine.
# The original 100 entries remain available; beta 3.1.8's mislabeled clones
# have been replaced, rather than multiplied under unrelated scientific names.
GENERIC_SIM_SPECS.update(BETA_SIM_SPECS)

# Merge into the public registry used by the UI.
SIM_TITLES.update({sid: spec["title"] for sid, spec in GENERIC_SIM_SPECS.items()})
SIM_SUBJECTS = {
    **{sid: ("수학" if sid in {"linear_function","quadratic","unit_circle","vectors","derivative","integral","matrix","sequence"} else "물리") for sid in SIM_TITLES if sid not in GENERIC_SIM_SPECS},
    **{sid: spec["subject"] for sid, spec in GENERIC_SIM_SPECS.items()},
}


def simulator_for_term(term: dict) -> str:
    # Simulations are attached only when the concept really matches the model.
    # A broad category fallback (e.g. every geometry term -> vector simulator)
    # would be visually attractive but scientifically misleading.
    explicit = str(term.get("simulator", "")).strip()
    return explicit if explicit in SIM_TITLES else ""


class MiniSimulator(tk.Frame):
    def __init__(self, master: tk.Misc, sim_id: str, theme: dict, fps: int = 30) -> None:
        super().__init__(master, bg=theme["surface"])
        self.sim_id = sim_id
        self.theme = theme
        self.fps = 60 if fps >= 60 else 30
        self.running = False
        self.t = 0.0
        self._steps = 0
        self._accumulator = 0.0
        self._last_clock = 0.0
        self._building = True
        self._job: Optional[str] = None
        self._vars: Dict[str, tk.DoubleVar] = {}
        self._build()
        self._building = False

    def destroy(self) -> None:
        self.stop()
        super().destroy()

    def _v(self, name: str, value: float) -> tk.DoubleVar:
        var = tk.DoubleVar(value=value)
        self._vars[name] = var
        var.trace_add("write", lambda *_: self._parameter_changed())
        return var

    def _slider(self, master: tk.Misc, label: str, name: str, lo: float, hi: float, value: float, digits: int = 2) -> None:
        t = self.theme
        row = tk.Frame(master, bg=t["surface"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 9), width=12, anchor="w").pack(side="left")
        var = self._v(name, value)
        ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal").pack(side="left", fill="x", expand=True, padx=6)
        out = tk.Label(row, bg=t["surface"], fg=t["text"], font=("Consolas", 9), width=9, anchor="e")
        out.pack(side="right")
        def show(*_):
            try: out.configure(text=f"{var.get():.{digits}f}")
            except Exception: pass
        var.trace_add("write", show); show()

    def _build(self) -> None:
        t = self.theme
        head = tk.Frame(self, bg=t["surface"])
        head.pack(fill="x", pady=(0, 8))
        tk.Label(head, text="▸ " + SIM_TITLES.get(self.sim_id, "미니 시뮬레이터"), bg=t["surface"], fg=t["text"], font=("Malgun Gothic", 12, "bold")).pack(side="left")
        tk.Label(head, text="값을 움직여 바로 확인", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 8)).pack(side="left", padx=10)
        self.play_btn = tk.Button(head, text="▶ 재생", command=self.toggle, relief="flat", bd=0, bg=t["accent_soft"], fg=t["accent2"], activebackground=t["accent_soft"], font=("Malgun Gothic", 9, "bold"), padx=10, pady=5, cursor="hand2")
        self.play_btn.pack(side="right")
        tk.Button(head, text="초기화", command=self.reset, relief="flat", bg=t["surface2"], fg=t["text"]).pack(side="right", padx=6)

        body = tk.Frame(self, bg=t["surface"])
        body.pack(fill="x")
        self.controls = tk.Frame(body, bg=t["surface"], width=250)
        self.controls.pack(side="left", fill="y", padx=(0, 12))
        self.controls.pack_propagate(False)
        self.canvas = tk.Canvas(body, width=600, height=270, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
        self.canvas.pack(side="left", fill="both", expand=True)
        self.info = tk.Label(self, text="", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 9), anchor="w", justify="left")
        self.info.pack(fill="x", pady=(8, 0))

        builders = {
            "newton2": self._setup_newton, "projectile": self._setup_projectile, "spring": self._setup_spring,
            "wave": self._setup_wave, "refraction": self._setup_refraction, "electric_field": self._setup_electric,
            "energy": self._setup_energy, "linear_function": self._setup_linear, "quadratic": self._setup_quadratic,
            "unit_circle": self._setup_unit_circle, "vectors": self._setup_vectors, "derivative": self._setup_derivative,
            "integral": self._setup_integral, "matrix": self._setup_matrix, "sequence": self._setup_sequence,
        }
        if self.sim_id in builders:
            builders[self.sim_id]()
        elif self.sim_id in GENERIC_SIM_SPECS:
            self._setup_generic()
        else:
            self._setup_linear()
        self.redraw()

    def toggle(self) -> None:
        self.stop() if self.running else self.start()

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._last_clock = time.perf_counter()
        self.play_btn.configure(text="❚❚ 일시정지")
        self._job = self.after(max(1, round(1000 / self.fps)), self._tick)

    def stop(self) -> None:
        self.running = False
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        if hasattr(self, "play_btn"):
            self.play_btn.configure(text="▶ 재생")

    def reset(self) -> None:
        self.stop()
        self.t = 0.0
        self._steps = 0
        self._accumulator = 0.0
        self.redraw()

    def _parameter_changed(self) -> None:
        if self._building:
            return
        # A changed initial condition begins a new experiment explicitly.
        self.reset()

    def step_once(self) -> None:
        self.stop()
        self._advance(FIXED_DT)
        self.redraw()

    def _advance(self, elapsed: float) -> None:
        self._accumulator += max(0.0, elapsed)
        count = int((self._accumulator + 1e-12) / FIXED_DT)
        self._accumulator -= count * FIXED_DT
        self._steps += count
        self.t = self._steps * FIXED_DT
        if self.sim_id in GENERIC_SIM_SPECS:
            spec = GENERIC_SIM_SPECS[self.sim_id]
            duration = float(spec["xmax"])-float(spec["xmin"]) if self._time_axis() else 6.0
            if self.t >= duration:
                self.t = duration
                self.stop()
        elif self.sim_id == "projectile":
            duration = 2*self._vars["v"].get()*math.sin(math.radians(self._vars["ang"].get()))/self._vars["g"].get()
            if self.t >= duration:
                self.t = duration
                self.stop()

    def _tick(self) -> None:
        self._job = None
        if not self.running or not self.winfo_exists():
            return
        now = time.perf_counter()
        elapsed = now-self._last_clock
        self._last_clock = now
        if elapsed > 2.0:
            self.stop()
            return
        self._advance(elapsed)
        self.redraw()
        if self.running:
            self._job = self.after(max(1, round(1000 / self.fps)), self._tick)

    def _setup_newton(self):
        self._slider(self.controls,"힘 F (N)","F",-20,20,8)
        self._slider(self.controls,"질량 m (kg)","m",0.5,10,2)
    def _setup_projectile(self):
        self._slider(self.controls,"초기속력 (m/s)","v",5,40,20)
        self._slider(self.controls,"발사각 (°)","ang",5,85,45,1)
        self._slider(self.controls,"중력 g", "g",1.6,15,9.8)
    def _setup_spring(self):
        self._slider(self.controls,"용수철 k", "k",1,40,10)
        self._slider(self.controls,"질량 m", "m",0.2,5,1)
        self._slider(self.controls,"진폭 A", "A",0.2,2,1)
    def _setup_wave(self):
        self._slider(self.controls,"진폭 A", "A",10,80,40,1)
        self._slider(self.controls,"공간주파수 k", "k",0.5,4,1.4)
        self._slider(self.controls,"진동수 f", "f",0.2,3,1)
    def _setup_refraction(self):
        self._slider(self.controls,"굴절률 n₁", "n1",1,2.5,1)
        self._slider(self.controls,"굴절률 n₂", "n2",1,2.5,1.5)
        self._slider(self.controls,"입사각 θ₁", "ang",0,80,40,1)
    def _setup_electric(self):
        self._slider(self.controls,"전하 q₁ (μC)","q1",-5,5,2)
        self._slider(self.controls,"전하 q₂ (μC)","q2",-5,5,-2)
        self._slider(self.controls,"거리 r (m)","r",0.2,3,1)
    def _setup_energy(self):
        self._slider(self.controls,"질량 m", "m",0.5,10,2)
        self._slider(self.controls,"높이 h", "h",0,10,5)
        self._slider(self.controls,"속력 v", "v",0,15,5)
    def _setup_linear(self):
        self._slider(self.controls,"기울기 m", "m",-4,4,1)
        self._slider(self.controls,"절편 b", "b",-5,5,0)
    def _setup_quadratic(self):
        self._slider(self.controls,"a", "a",-3,3,1)
        self._slider(self.controls,"b", "b",-5,5,0)
        self._slider(self.controls,"c", "c",-5,5,0)
    def _setup_unit_circle(self):
        self._slider(self.controls,"각도 θ (°)", "ang",0,360,45,1)
    def _setup_vectors(self):
        self._slider(self.controls,"aₓ", "ax",-5,5,3)
        self._slider(self.controls,"aᵧ", "ay",-5,5,2)
        self._slider(self.controls,"bₓ", "bx",-5,5,-1)
        self._slider(self.controls,"bᵧ", "by",-5,5,3)
    def _setup_derivative(self):
        self._slider(self.controls,"접점 x₀", "x0",-3,3,1)
        self._slider(self.controls,"곡률 a", "a",-2,2,1)
        self._slider(self.controls,"1차항 b", "b",-3,3,0)
    def _setup_integral(self):
        self._slider(self.controls,"구간 끝 b", "b",0.5,4,2)
        self._slider(self.controls,"분할 수 n", "n",2,30,8,0)
    def _setup_matrix(self):
        for label,name,value in [("a₁₁","a",1),("a₁₂","b",0.5),("a₂₁","c",0),("a₂₂","d",1)]:
            self._slider(self.controls,label,name,-2,2,value)
    def _setup_sequence(self):
        self._slider(self.controls,"첫째항 a₁", "a1",-5,10,1)
        self._slider(self.controls,"공차 d", "d",-3,5,2)
        self._slider(self.controls,"공비 r", "r",-2,2,1.2)
        self.seq_mode = tk.StringVar(value="등차")
        box = ttk.Combobox(self.controls, textvariable=self.seq_mode, values=["등차","등비"], state="readonly")
        box.pack(fill="x", pady=6); box.bind("<<ComboboxSelected>>", lambda _e:self.redraw())

    def _setup_generic(self):
        spec = GENERIC_SIM_SPECS[self.sim_id]
        for label, name, lo, hi, value in spec.get("sliders", []):
            self._slider(self.controls, label, name, float(lo), float(hi), float(value), 3)

    def _generic_eval(self, x: float):
        spec = GENERIC_SIM_SPECS[self.sim_id]
        env = {
            "x": x, "pi": math.pi, "e": math.e, "nan": float("nan"),
            "sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt,
            "exp": math.exp, "log": math.log, "log10": math.log10, "abs": abs,
            "max": max, "min": min, "sum": sum, "range": range, "int": int,
            "factorial": math.factorial,
        }
        env.update({k: v.get() for k, v in self._vars.items()})
        # Convenience conversions for specs that display human-friendly slider units.
        if "alpha_u" in env:
            env["alpha"] = env["alpha_u"] * 1e-5
        if "Ea_k" in env:
            env["Ea"] = env["Ea_k"] * 1000.0
        try:
            value = eval(spec["expr"], {"__builtins__": {}, **env}, env)
            return float(value)
        except Exception:
            return float("nan")

    def _draw_generic(self):
        spec = GENERIC_SIM_SPECS[self.sim_id]
        c, t = self.canvas, self.theme
        xmin, xmax = float(spec["xmin"]), float(spec["xmax"])
        plot_segments = self._plot_segments()
        values = [point for segment in plot_segments for point in segment]
        if not values:
            c.create_text(300,135,text="현재 값에서는 그래프를 표시할 수 없습니다.",fill=t["muted"],font=("Malgun Gothic",10))
            self.info.configure(text=spec["formula"])
            return
        ys=[y for _,y in values]; ymin,ymax=min(ys),max(ys)
        if math.isclose(ymin,ymax): ymin-=1; ymax+=1
        pad=(ymax-ymin)*0.08; ymin-=pad; ymax+=pad
        left,right,top,bottom=48,575,22,225
        c.create_rectangle(left,top,right,bottom,outline=t["line"])
        if ymin <= 0 <= ymax:
            zy=bottom-(0-ymin)/(ymax-ymin)*(bottom-top); c.create_line(left,zy,right,zy,fill=t["line"])
        if xmin <= 0 <= xmax:
            zx=left+(0-xmin)/(xmax-xmin)*(right-left); c.create_line(zx,top,zx,bottom,fill=t["line"])
        for segment in plot_segments:
            points=[]
            for x,y in segment:
                points.extend([left+(x-xmin)/(xmax-xmin)*(right-left),bottom-(y-ymin)/(ymax-ymin)*(bottom-top)])
            if len(points)>=4:
                c.create_line(*points,fill=t["accent"],width=3,smooth=False)
        xp=self._probe_x(); yp=self._generic_eval(xp)
        if math.isfinite(yp) and ymin <= yp <= ymax:
            px=left+(xp-xmin)/(xmax-xmin)*(right-left); py=bottom-(yp-ymin)/(ymax-ymin)*(bottom-top)
            c.create_oval(px-5,py-5,px+5,py+5,fill=t["blue"],outline="")
        c.create_text((left+right)/2,250,text=spec["x_label"],fill=t["muted"],font=("Malgun Gothic",8))
        c.create_text(16,(top+bottom)/2,text=spec["y_label"],fill=t["muted"],font=("Malgun Gothic",8),angle=90)
        params=" · ".join(f"{k}={v.get():.3g}" for k,v in self._vars.items())
        model = "시간은 순방향으로 진행" if self._time_axis() else "관계식 탐색 · 점은 입력값을 읽는 표시"
        self.info.configure(text=spec["formula"] + (" · " + params if params else "") + f"\n{model} · {spec['x_label']}={xp:.6g}, {spec['y_label']}={yp:.6g}")

    def _time_axis(self) -> bool:
        return GENERIC_SIM_SPECS[self.sim_id]["x_label"] in {"t", "시간", "t/T½"}

    def _probe_x(self) -> float:
        spec = GENERIC_SIM_SPECS[self.sim_id]
        lo, hi = float(spec["xmin"]), float(spec["xmax"])
        return min(hi, lo+self.t) if self._time_axis() else lo+(hi-lo)*min(1.0,self.t/6.0)

    def _plot_segments(self):
        """Preserve undefined samples and never connect across a known pole."""
        spec = GENERIC_SIM_SPECS[self.sim_id]
        lo, hi = float(spec["xmin"]), float(spec["xmax"])
        pole = (self._vars["f"].get() if self.sim_id == "thin_lens" else
                self._vars["h"].get() if self.sim_id == "rational_function" else
                0.0 if self.sim_id == "newton_method" else None)
        segments, current, previous = [], [], None
        for i in range(321):
            x = lo+(hi-lo)*i/320
            y = self._generic_eval(x)
            crossed = pole is not None and previous is not None and previous <= pole <= x
            valid = math.isfinite(y) and abs(y) < 1e12 and (pole is None or not math.isclose(x,pole,abs_tol=1e-12))
            if crossed or not valid:
                if current:
                    segments.append(current)
                current = []
            if valid:
                current.append((x,y))
            previous = x
        if current:
            segments.append(current)
        return segments

    def _xy(self, x: float, y: float, sx: float = 45, sy: float = 30, cx: float = 300, cy: float = 135):
        return cx + x*sx, cy - y*sy

    def _axes(self, sx=45, sy=30, cx=300, cy=135):
        c=self.canvas; t=self.theme
        c.create_line(20,cy,580,cy,fill=t["line"],width=1); c.create_line(cx,15,cx,255,fill=t["line"],width=1)
        for x in range(-6,7):
            px=cx+x*sx
            if 20<px<580: c.create_line(px,cy-3,px,cy+3,fill=t["muted"])
        for y in range(-4,5):
            py=cy-y*sy
            if 15<py<255: c.create_line(cx-3,py,cx+3,py,fill=t["muted"])

    def redraw(self) -> None:
        if not hasattr(self,"canvas"): return
        self.canvas.delete("all")
        fn=getattr(self,"_draw_"+self.sim_id,None)
        if fn:
            fn()
        elif self.sim_id in GENERIC_SIM_SPECS:
            self._draw_generic()

    def _draw_newton2(self):
        c=self.canvas; t=self.theme; F=self._vars['F'].get(); m=max(.1,self._vars['m'].get()); a=F/m
        world_x, velocity = constant_force_motion(F,m,self.t)
        viewport = math.floor(world_x/8.0)*8.0
        x=90+(world_x-viewport)*55
        for i in range(9):
            px=90+i*55
            c.create_text(px,225,text=f"{viewport+i:g} m",fill=t['muted'],font=('Consolas',8))
        c.create_line(30,205,570,205,fill=t['muted'],width=2); c.create_rectangle(x-45,160,x+45,205,fill=t['accent_soft'],outline=t['accent'],width=2)
        c.create_text(x,182,text=f"m={m:.1f} kg",fill=t['text'],font=('Consolas',10,'bold'))
        if F:
            end=x+max(-120,min(120,F*6)); c.create_line(x,145,end,145,arrow='last',fill=t['blue'],width=4)
        self.info.configure(text=f"F = ma · a = {a:.6f} m/s² · t={self.t:.6f} s\nx={world_x:.6f} m · v={velocity:.6f} m/s · 화면이 이동해도 실제 좌표는 유지")
    def _draw_projectile(self):
        c=self.canvas; t=self.theme; v=self._vars['v'].get(); ang=math.radians(self._vars['ang'].get()); g=self._vars['g'].get()
        vx=v*math.cos(ang); vy=v*math.sin(ang); T=max(.01,2*vy/g); R=vx*T; H=vy*vy/(2*g)
        pts=[]
        scale=min(520/max(R,1), 180/max(H,1), 18)
        for i in range(101):
            tt=T*i/100; x=vx*tt; y=max(0,vy*tt-.5*g*tt*tt); pts.extend([35+x*scale,230-y*scale])
        c.create_line(25,230,570,230,fill=t['muted']);
        if len(pts)>=4: c.create_line(*pts,fill=t['accent'],width=3,smooth=True)
        tt=min(self.t,T); x=vx*tt; y=max(0,vy*tt-.5*g*tt*tt); c.create_oval(29+x*scale,224-y*scale,41+x*scale,236-y*scale,fill=t['blue'],outline='')
        self.info.configure(text=f"비행시간 {T:.2f} s · 사거리 {R:.2f} m · 최고높이 {H:.2f} m")
    def _draw_spring(self):
        c=self.canvas; t=self.theme; k=self._vars['k'].get(); m=self._vars['m'].get(); A=self._vars['A'].get(); w=math.sqrt(k/m); x=A*math.cos(w*self.t)
        center=300; px=center+x*75
        c.create_line(40,135,90,135,fill=t['muted'],width=6)
        points=[90,135]
        n=12
        for i in range(1,n+1):
            xx=90+(px-130)*i/n; yy=135+(18 if i%2 else -18); points.extend([xx,yy])
        points.extend([px-40,135]); c.create_line(*points,fill=t['accent'],width=2); c.create_rectangle(px-40,105,px+40,165,fill=t['accent_soft'],outline=t['accent'])
        self.info.configure(text=f"ω=√(k/m)={w:.3f} rad/s · T={2*math.pi/w:.3f} s · x={x:.3f}")
    def _draw_wave(self):
        c=self.canvas; t=self.theme; A=self._vars['A'].get(); k=self._vars['k'].get(); f=self._vars['f'].get(); phase=2*math.pi*f*self.t
        pts=[]
        for px in range(20,581,3):
            x=(px-20)/560*4*math.pi; y=135-A*math.sin(k*x-phase); pts.extend([px,y])
        c.create_line(20,135,580,135,fill=t['line']); c.create_line(*pts,fill=t['accent'],width=3,smooth=True)
        self.info.configure(text=f"y=A sin(kx-ωt) · A={A:.1f}px · k={k:.2f} · f={f:.2f} Hz")
    def _draw_refraction(self):
        c=self.canvas; t=self.theme; n1=self._vars['n1'].get(); n2=self._vars['n2'].get(); a1=math.radians(self._vars['ang'].get()); s=n1/n2*math.sin(a1)
        cx,cy=300,135; c.create_rectangle(0,0,600,135,fill=t['surface2'],outline=''); c.create_rectangle(0,135,600,270,fill=t['accent_soft'],outline=''); c.create_line(0,135,600,135,fill=t['line']); c.create_line(cx,15,cx,255,fill=t['muted'],dash=(4,4))
        L=130; c.create_line(cx-math.sin(a1)*L,cy-math.cos(a1)*L,cx,cy,fill=t['blue'],width=3,arrow='last')
        if abs(s)<=1:
            a2=math.asin(s); c.create_line(cx,cy,cx+math.sin(a2)*L,cy+math.cos(a2)*L,fill=t['accent'],width=3,arrow='last'); msg=f"θ₂={math.degrees(a2):.2f}°"
        else:
            c.create_line(cx,cy,cx+math.sin(a1)*L,cy-math.cos(a1)*L,fill=t['accent'],width=3,arrow='last'); msg="전반사 조건"
        self.info.configure(text=f"n₁ sinθ₁ = n₂ sinθ₂ · {msg}")
    def _draw_electric_field(self):
        c=self.canvas; t=self.theme; q1=self._vars['q1'].get(); q2=self._vars['q2'].get(); r=max(.05,self._vars['r'].get()); F=8.9875517923e9*(q1*1e-6)*(q2*1e-6)/(r*r)
        x1,x2=210,390
        for x,q in [(x1,q1),(x2,q2)]:
            fill=t['blue'] if q>=0 else t['danger']; c.create_oval(x-28,107,x+28,163,fill=fill,outline=''); c.create_text(x,135,text=('+' if q>=0 else '−')+f"{abs(q):.1f}",fill='white',font=('Segoe UI',11,'bold'))
        if F<0:
            c.create_line(x1,180,x1+70,180,arrow='last',fill=t['accent'],width=3)
            c.create_line(x2,180,x2-70,180,arrow='last',fill=t['accent'],width=3)
        elif F>0:
            c.create_line(x1,180,x1-70,180,arrow='last',fill=t['accent'],width=3)
            c.create_line(x2,180,x2+70,180,arrow='last',fill=t['accent'],width=3)
        self.info.configure(text=f"F = k q₁q₂/r² = {F:.4g} N · {'인력' if F<0 else '척력' if F>0 else '힘 0'} · 화살표는 각 전하에 작용하는 힘")
    def _draw_energy(self):
        c=self.canvas; t=self.theme; m=self._vars['m'].get(); h=self._vars['h'].get(); v=self._vars['v'].get(); pe=m*9.80665*h; ke=.5*m*v*v; total=pe+ke; scale=180/max(total,1)
        c.create_text(95,230,text='위치E',fill=t['muted']); c.create_rectangle(60,220-pe*scale,130,220,fill=t['blue'],outline='')
        c.create_text(250,230,text='운동E',fill=t['muted']); c.create_rectangle(215,220-ke*scale,285,220,fill=t['accent'],outline='')
        c.create_text(430,230,text='합계',fill=t['muted']); c.create_rectangle(395,220-total*scale,465,220,fill=t['accent_soft'],outline=t['accent'])
        self.info.configure(text=f"PE=mgh={pe:.2f} J · KE=½mv²={ke:.2f} J · 합계={total:.2f} J")
    def _draw_linear_function(self):
        self._axes(); c=self.canvas; t=self.theme; m=self._vars['m'].get(); b=self._vars['b'].get(); pts=[]
        for i in range(-60,61):
            x=i/10; y=m*x+b; px,py=self._xy(x,y); pts.extend([px,py])
        c.create_line(*pts,fill=t['accent'],width=3); self.info.configure(text=f"y = {m:.2f}x + {b:.2f} · 기울기 {m:.2f}")
    def _draw_quadratic(self):
        self._axes(); c=self.canvas; t=self.theme; a=self._vars['a'].get(); b=self._vars['b'].get(); cc=self._vars['c'].get(); pts=[]
        for i in range(-60,61):
            x=i/10; y=a*x*x+b*x+cc; px,py=self._xy(x,y); pts.extend([px,py])
        c.create_line(*pts,fill=t['accent'],width=3,smooth=True); xv=-b/(2*a) if abs(a)>.03 else float('nan'); self.info.configure(text=f"y={a:.2f}x²+{b:.2f}x+{cc:.2f} · 꼭짓점 x≈{xv:.3g}")
    def _draw_unit_circle(self):
        c=self.canvas; t=self.theme; ang=(self._vars['ang'].get()+self.t*45)%360; th=math.radians(ang); cx,cy,R=300,135,95; x=cx+R*math.cos(th); y=cy-R*math.sin(th)
        c.create_oval(cx-R,cy-R,cx+R,cy+R,outline=t['muted'],width=2); c.create_line(cx-R-20,cy,cx+R+20,cy,fill=t['line']); c.create_line(cx,cy-R-20,cx,cy+R+20,fill=t['line']); c.create_line(cx,cy,x,y,fill=t['accent'],width=3); c.create_line(x,cy,x,y,fill=t['blue'],dash=(4,3)); c.create_oval(x-6,y-6,x+6,y+6,fill=t['accent'],outline='')
        self.info.configure(text=f"θ={ang:.1f}° · cosθ={math.cos(th):.4f} · sinθ={math.sin(th):.4f}")
    def _arrow(self,x1,y1,x2,y2,color): self.canvas.create_line(x1,y1,x2,y2,arrow='last',fill=color,width=3)
    def _draw_vectors(self):
        self._axes(sx=35,sy=25); t=self.theme; ax=self._vars['ax'].get(); ay=self._vars['ay'].get(); bx=self._vars['bx'].get(); by=self._vars['by'].get(); cx,cy=300,135
        self._arrow(cx,cy,cx+ax*35,cy-ay*25,t['blue']); self._arrow(cx,cy,cx+bx*35,cy-by*25,t['accent']); self._arrow(cx,cy,cx+(ax+bx)*35,cy-(ay+by)*25,t['danger'])
        dot=ax*bx+ay*by; self.info.configure(text=f"a+b=({ax+bx:.2f}, {ay+by:.2f}) · a·b={dot:.3f}")
    def _draw_derivative(self):
        self._axes(); c=self.canvas; t=self.theme; x0=self._vars['x0'].get(); a=self._vars['a'].get(); b=self._vars['b'].get(); pts=[]
        f=lambda x:a*x*x+b*x; slope=2*a*x0+b; y0=f(x0)
        for i in range(-60,61):
            x=i/10; px,py=self._xy(x,f(x)); pts.extend([px,py])
        c.create_line(*pts,fill=t['accent'],width=3,smooth=True); xL,xR=-5,5; p1=self._xy(xL,y0+slope*(xL-x0)); p2=self._xy(xR,y0+slope*(xR-x0)); c.create_line(*p1,*p2,fill=t['blue'],width=2,dash=(5,3)); px,py=self._xy(x0,y0); c.create_oval(px-5,py-5,px+5,py+5,fill=t['danger'],outline='')
        self.info.configure(text=f"f(x)={a:.2f}x²+{b:.2f}x · f'({x0:.2f})={slope:.3f}")
    def _draw_integral(self):
        c=self.canvas; t=self.theme; b=self._vars['b'].get(); n=max(2,int(round(self._vars['n'].get()))); left=60; base=220; width=480; sx=width/max(b,.1); sy=45; dx=b/n; approx=0
        c.create_line(left,base,left+width,base,fill=t['muted']); pts=[]
        for i in range(121):
            x=b*i/120; y=x*x; pts.extend([left+x*sx,base-y*sy])
        for i in range(n):
            x=i*dx; y=x*x; approx+=y*dx; x1=left+x*sx; x2=left+(x+dx)*sx; c.create_rectangle(x1,base-y*sy,x2,base,outline=t['blue'],fill=t['accent_soft'])
        c.create_line(*pts,fill=t['accent'],width=3,smooth=True); exact=b**3/3
        self.info.configure(text=f"f(x)=x², [0,{b:.2f}] · 좌리만합≈{approx:.4f} · 정확한 적분={exact:.4f} · n={n}")
    def _draw_matrix(self):
        c=self.canvas; t=self.theme; a=self._vars['a'].get(); b=self._vars['b'].get(); cc=self._vars['c'].get(); d=self._vars['d'].get(); cx,cy=300,135; s=35
        def tr(x,y): return cx+(a*x+b*y)*s, cy-(cc*x+d*y)*s
        for k in range(-4,5):
            pts=[]
            for j in range(-40,41):
                x=k; y=j/10; pts.extend(tr(x,y))
            c.create_line(*pts,fill=t['line'])
            pts=[]
            for j in range(-40,41):
                x=j/10; y=k; pts.extend(tr(x,y))
            c.create_line(*pts,fill=t['line'])
        self._arrow(cx,cy,*tr(1,0),t['blue']); self._arrow(cx,cy,*tr(0,1),t['accent']); det=a*d-b*cc
        self.info.configure(text=f"A=[[{a:.2f},{b:.2f}],[{cc:.2f},{d:.2f}]] · det(A)={det:.3f} · 면적 배율 |det|={abs(det):.3f}")
    def _draw_sequence(self):
        c=self.canvas; t=self.theme; a1=self._vars['a1'].get(); d=self._vars['d'].get(); r=self._vars['r'].get(); mode=self.seq_mode.get(); vals=[]
        for n in range(1,11): vals.append(a1+(n-1)*d if mode=='등차' else a1*(r**(n-1)))
        M=max(1,max(abs(x) for x in vals)); base=135
        for i,v in enumerate(vals):
            x=45+i*52; h=v/M*100; c.create_line(x,base,x,base-h,fill=t['accent'],width=5); c.create_oval(x-4,base-h-4,x+4,base-h+4,fill=t['blue'],outline=''); c.create_text(x,245,text=str(i+1),fill=t['muted'])
        expr=f"aₙ={a1:.2f}+(n-1){d:+.2f}" if mode=='등차' else f"aₙ={a1:.2f}·({r:.2f})^(n-1)"
        self.info.configure(text=expr+" · 처음 10개 항을 표시")


def build_simulator(master: tk.Misc, term: dict, theme: dict, fps: int = 30) -> Optional[MiniSimulator]:
    sim_id = simulator_for_term(term)
    if not sim_id:
        return None
    return MiniSimulator(master, sim_id, theme, fps=fps)
