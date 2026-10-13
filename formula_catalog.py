from __future__ import annotations

"""Formula catalog for Physics + Math Pocket 3.1.4.

The catalog combines equations already attached to dictionary terms with a curated
supplement.  Text is original/concise; source IDs point to the reference list in
``data/sources.json``.
"""

from typing import Dict, Iterable, List


def _f(fid: str, title: str, subject: str, category: str, formula: str, note: str = "", source: str = "openstax_math") -> dict:
    return {
        "id": fid,
        "title": title,
        "subject": subject,
        "category": category,
        "formula": formula,
        "note": note,
        "source": source,
        "term_id": "",
    }


def _supplements() -> List[dict]:
    rows: List[dict] = []
    add = rows.append

    # --- Algebra / functions ---
    algebra = [
        ("alg_sum_sq", "합의 제곱", "(a+b)^2=a^2+2ab+b^2"),
        ("alg_diff_sq", "차의 제곱", "(a-b)^2=a^2-2ab+b^2"),
        ("alg_diff_squares", "제곱의 차", "a^2-b^2=(a-b)(a+b)"),
        ("alg_sum_cube", "합의 세제곱", "(a+b)^3=a^3+3a^2b+3ab^2+b^3"),
        ("alg_diff_cube", "차의 세제곱", "(a-b)^3=a^3-3a^2b+3ab^2-b^3"),
        ("alg_sum_cubes", "세제곱의 합", "a^3+b^3=(a+b)(a^2-ab+b^2)"),
        ("alg_diff_cubes", "세제곱의 차", "a^3-b^3=(a-b)(a^2+ab+b^2)"),
        ("alg_quad", "근의 공식", "x=(-b±√(b^2-4ac))/(2a)"),
        ("alg_disc", "판별식", "D=b^2-4ac"),
        ("alg_vieta_sum", "이차방정식 근의 합", "α+β=-b/a"),
        ("alg_vieta_product", "이차방정식 근의 곱", "αβ=c/a"),
        ("alg_arith_seq", "등차수열 일반항", "a_n=a_1+(n-1)d"),
        ("alg_arith_sum", "등차수열 합", "S_n=n(a_1+a_n)/2"),
        ("alg_geom_seq", "등비수열 일반항", "a_n=a_1r^(n-1)"),
        ("alg_geom_sum", "등비수열 합", "S_n=a_1(1-r^n)/(1-r)"),
        ("alg_geom_inf", "무한등비급수", "S=a_1/(1-r), |r|<1"),
        ("alg_exp_prod", "지수법칙 곱", "a^m a^n=a^(m+n)"),
        ("alg_exp_div", "지수법칙 나눗셈", "a^m/a^n=a^(m-n)"),
        ("alg_exp_pow", "거듭제곱의 거듭제곱", "(a^m)^n=a^(mn)"),
        ("alg_exp_neg", "음의 지수", "a^(-n)=1/a^n"),
        ("alg_log_prod", "로그의 곱", "log_a(xy)=log_a x+log_a y"),
        ("alg_log_quot", "로그의 몫", "log_a(x/y)=log_a x-log_a y"),
        ("alg_log_pow", "로그의 거듭제곱", "log_a(x^r)=r log_a x"),
        ("alg_log_change", "로그 밑변환", "log_a x=log_b x/log_b a"),
        ("alg_compound", "복리 성장", "A=P(1+r/n)^(nt)"),
    ]
    for fid, title, formula in algebra:
        add(_f(fid, title, "수학", "대수", formula, source="openstax_math"))

    # --- Geometry ---
    geometry = [
        ("geo_tri_area", "삼각형 넓이", "A=bh/2"),
        ("geo_heron", "헤론의 공식", "A=√(s(s-a)(s-b)(s-c)), s=(a+b+c)/2"),
        ("geo_rect", "직사각형 넓이", "A=wh"),
        ("geo_square", "정사각형 넓이", "A=a^2"),
        ("geo_para", "평행사변형 넓이", "A=bh"),
        ("geo_trap", "사다리꼴 넓이", "A=(a+b)h/2"),
        ("geo_rhomb", "마름모 넓이", "A=d_1d_2/2"),
        ("geo_circle_area", "원의 넓이", "A=πr^2"),
        ("geo_circle_c", "원의 둘레", "C=2πr"),
        ("geo_sector_area", "부채꼴 넓이", "A=(θ/2)r^2 (θ: rad)"),
        ("geo_arc", "호의 길이", "s=rθ (θ: rad)"),
        ("geo_pyth", "피타고라스 정리", "a^2+b^2=c^2"),
        ("geo_dist2", "평면 두 점 거리", "d=√((x_2-x_1)^2+(y_2-y_1)^2)"),
        ("geo_mid", "중점 좌표", "M=((x_1+x_2)/2,(y_1+y_2)/2)"),
        ("geo_slope", "직선의 기울기", "m=(y_2-y_1)/(x_2-x_1)"),
        ("geo_line", "점-기울기 직선식", "y-y_1=m(x-x_1)"),
        ("geo_circle_eq", "원의 방정식", "(x-a)^2+(y-b)^2=r^2"),
        ("geo_sphere_area", "구의 겉넓이", "A=4πr^2"),
        ("geo_sphere_vol", "구의 부피", "V=4πr^3/3"),
        ("geo_cylinder_vol", "원기둥 부피", "V=πr^2h"),
        ("geo_cylinder_area", "원기둥 겉넓이", "A=2πr(r+h)"),
        ("geo_cone_vol", "원뿔 부피", "V=πr^2h/3"),
        ("geo_cone_area", "원뿔 겉넓이", "A=πr(r+l)"),
        ("geo_prism", "각기둥 부피", "V=B h"),
        ("geo_pyramid", "각뿔 부피", "V=B h/3"),
        ("geo_poly_angle", "n각형 내각의 합", "S=(n-2)180°"),
        ("geo_regular_angle", "정n각형 한 내각", "A=(n-2)180°/n"),
        ("geo_regular_area", "정n각형 넓이", "A=ns^2/(4tan(π/n))"),
        ("geo_ellipse", "타원 넓이", "A=πab"),
        ("geo_ellipse_eq", "타원 방정식", "x^2/a^2+y^2/b^2=1"),
        ("geo_hyperbola", "쌍곡선 표준형", "x^2/a^2-y^2/b^2=1"),
        ("geo_parabola", "포물선 표준형", "y^2=4px"),
        ("geo_coslaw", "코사인 법칙", "c^2=a^2+b^2-2ab cos C"),
        ("geo_sinlaw", "사인 법칙", "a/sin A=b/sin B=c/sin C=2R"),
        ("geo_tri_sine_area", "두 변과 끼인각으로 삼각형 넓이", "A=ab sin C/2"),
    ]
    for fid, title, formula in geometry:
        add(_f(fid, title, "수학", "기하", formula, source="openstax_math"))

    # --- Trigonometry ---
    trig = [
        ("trig_pyth", "삼각함수 피타고라스 항등식", "sin^2x+cos^2x=1"),
        ("trig_tan", "탄젠트 정의", "tan x=sin x/cos x"),
        ("trig_sec", "시컨트 항등식", "1+tan^2x=sec^2x"),
        ("trig_csc", "코시컨트 항등식", "1+cot^2x=csc^2x"),
        ("trig_sin_sum", "사인 덧셈정리", "sin(a+b)=sin a cos b+cos a sin b"),
        ("trig_sin_diff", "사인 뺄셈정리", "sin(a-b)=sin a cos b-cos a sin b"),
        ("trig_cos_sum", "코사인 덧셈정리", "cos(a+b)=cos a cos b-sin a sin b"),
        ("trig_cos_diff", "코사인 뺄셈정리", "cos(a-b)=cos a cos b+sin a sin b"),
        ("trig_tan_sum", "탄젠트 덧셈정리", "tan(a+b)=(tan a+tan b)/(1-tan a tan b)"),
        ("trig_tan_diff", "탄젠트 뺄셈정리", "tan(a-b)=(tan a-tan b)/(1+tan a tan b)"),
        ("trig_sin2", "사인 배각", "sin 2x=2 sin x cos x"),
        ("trig_cos2a", "코사인 배각 1", "cos 2x=cos^2x-sin^2x"),
        ("trig_cos2b", "코사인 배각 2", "cos 2x=2cos^2x-1"),
        ("trig_cos2c", "코사인 배각 3", "cos 2x=1-2sin^2x"),
        ("trig_tan2", "탄젠트 배각", "tan 2x=2tan x/(1-tan^2x)"),
        ("trig_half_sin", "사인 반각 제곱", "sin^2(x/2)=(1-cos x)/2"),
        ("trig_half_cos", "코사인 반각 제곱", "cos^2(x/2)=(1+cos x)/2"),
        ("trig_product_ss", "사인 곱을 합으로", "2sin A sin B=cos(A-B)-cos(A+B)"),
        ("trig_product_cc", "코사인 곱을 합으로", "2cos A cos B=cos(A-B)+cos(A+B)"),
        ("trig_product_sc", "사인·코사인 곱을 합으로", "2sin A cos B=sin(A+B)+sin(A-B)"),
        ("trig_euler", "오일러 공식", "e^(ix)=cos x+i sin x"),
        ("trig_demoivre", "드무아브르 정리", "(cos x+i sin x)^n=cos(nx)+i sin(nx)"),
        ("trig_period_sin", "사인의 주기", "sin(x+2π)=sin x"),
        ("trig_period_cos", "코사인의 주기", "cos(x+2π)=cos x"),
        ("trig_period_tan", "탄젠트의 주기", "tan(x+π)=tan x"),
    ]
    for fid, title, formula in trig:
        add(_f(fid, title, "수학", "삼각함수", formula, source="nist_dlmf"))

    # --- Calculus and analysis ---
    calc = [
        ("calc_der_const", "상수함수 미분", "d(c)/dx=0"),
        ("calc_der_xn", "거듭제곱 미분", "d(x^n)/dx=nx^(n-1)"),
        ("calc_der_exp", "지수함수 미분", "d(e^x)/dx=e^x"),
        ("calc_der_ax", "일반 지수함수 미분", "d(a^x)/dx=a^x ln a"),
        ("calc_der_ln", "자연로그 미분", "d(ln x)/dx=1/x"),
        ("calc_der_log", "로그함수 미분", "d(log_a x)/dx=1/(x ln a)"),
        ("calc_der_sin", "사인 미분", "d(sin x)/dx=cos x"),
        ("calc_der_cos", "코사인 미분", "d(cos x)/dx=-sin x"),
        ("calc_der_tan", "탄젠트 미분", "d(tan x)/dx=sec^2x"),
        ("calc_der_sec", "시컨트 미분", "d(sec x)/dx=sec x tan x"),
        ("calc_der_csc", "코시컨트 미분", "d(csc x)/dx=-csc x cot x"),
        ("calc_der_cot", "코탄젠트 미분", "d(cot x)/dx=-csc^2x"),
        ("calc_der_asin", "아크사인 미분", "d(arcsin x)/dx=1/√(1-x^2)"),
        ("calc_der_acos", "아크코사인 미분", "d(arccos x)/dx=-1/√(1-x^2)"),
        ("calc_der_atan", "아크탄젠트 미분", "d(arctan x)/dx=1/(1+x^2)"),
        ("calc_prod", "곱의 미분법", "(fg)'=f'g+fg'"),
        ("calc_quot", "몫의 미분법", "(f/g)'=(f'g-fg')/g^2"),
        ("calc_chain", "연쇄법칙", "d f(g(x))/dx=f'(g(x))g'(x)"),
        ("calc_int_power", "거듭제곱 적분", "∫x^n dx=x^(n+1)/(n+1)+C, n≠-1"),
        ("calc_int_inv", "1/x 적분", "∫dx/x=ln|x|+C"),
        ("calc_int_exp", "지수함수 적분", "∫e^x dx=e^x+C"),
        ("calc_int_ax", "a^x 적분", "∫a^x dx=a^x/ln a+C"),
        ("calc_int_sin", "사인 적분", "∫sin x dx=-cos x+C"),
        ("calc_int_cos", "코사인 적분", "∫cos x dx=sin x+C"),
        ("calc_int_sec2", "sec² 적분", "∫sec^2x dx=tan x+C"),
        ("calc_int_csc2", "csc² 적분", "∫csc^2x dx=-cot x+C"),
        ("calc_ftc", "미적분학 기본정리", "d/dx ∫_a^x f(t)dt=f(x)"),
        ("calc_ibp", "부분적분", "∫u dv=uv-∫v du"),
        ("calc_subst", "치환적분", "∫f(g(x))g'(x)dx=∫f(u)du"),
        ("calc_taylor", "테일러 급수", "f(x)=Σ f^(n)(a)(x-a)^n/n!"),
        ("calc_mac_exp", "e^x 맥클로린 급수", "e^x=Σ x^n/n!"),
        ("calc_mac_sin", "sin x 맥클로린 급수", "sin x=Σ(-1)^n x^(2n+1)/(2n+1)!"),
        ("calc_mac_cos", "cos x 맥클로린 급수", "cos x=Σ(-1)^n x^(2n)/(2n)!"),
        ("calc_grad", "그래디언트", "∇f=(∂f/∂x,∂f/∂y,∂f/∂z)"),
        ("calc_div", "발산", "∇·F=∂F_x/∂x+∂F_y/∂y+∂F_z/∂z"),
        ("calc_curl", "회전", "∇×F"),
        ("calc_lap", "라플라시안", "∇^2f=∂²f/∂x²+∂²f/∂y²+∂²f/∂z²"),
        ("calc_newton", "뉴턴 방법", "x_(n+1)=x_n-f(x_n)/f'(x_n)"),
        ("calc_euler_ode", "오일러 방법", "y_(n+1)=y_n+h f(x_n,y_n)"),
        ("calc_logistic", "로지스틱 방정식", "dP/dt=rP(1-P/K)"),
    ]
    for fid, title, formula in calc:
        add(_f(fid, title, "수학", "미적분", formula, source="nist_dlmf" if "sin" in fid or "cos" in fid or "tan" in fid else "openstax_math"))

    # --- Probability / statistics / linear algebra ---
    stats = [
        ("stat_mean", "산술평균", "x̄=(1/n)Σx_i"),
        ("stat_wmean", "가중평균", "x̄_w=Σw_ix_i/Σw_i"),
        ("stat_popvar", "모분산", "σ²=(1/N)Σ(x_i-μ)^2"),
        ("stat_sampvar", "표본분산", "s²=(1/(n-1))Σ(x_i-x̄)^2"),
        ("stat_sd", "표준편차", "σ=√(σ²)"),
        ("stat_z", "z점수", "z=(x-μ)/σ"),
        ("stat_comb", "조합", "nCr=n!/(r!(n-r)!)"),
        ("stat_perm", "순열", "nPr=n!/(n-r)!"),
        ("stat_binom", "이항분포 확률", "P(X=k)=C(n,k)p^k(1-p)^(n-k)"),
        ("stat_binom_mean", "이항분포 평균", "μ=np"),
        ("stat_binom_var", "이항분포 분산", "σ²=np(1-p)"),
        ("stat_poisson", "포아송분포", "P(X=k)=e^(-λ)λ^k/k!"),
        ("stat_normal", "정규분포 밀도", "f(x)=exp(-(x-μ)^2/(2σ²))/(σ√(2π))"),
        ("stat_bayes", "베이즈 정리", "P(A|B)=P(B|A)P(A)/P(B)"),
        ("stat_union", "확률의 합법칙", "P(A∪B)=P(A)+P(B)-P(A∩B)"),
        ("stat_indep", "독립사건 곱", "P(A∩B)=P(A)P(B)"),
        ("la_dot", "벡터 내적", "a·b=Σa_ib_i=|a||b|cosθ"),
        ("la_cross", "3차원 벡터 외적 크기", "|a×b|=|a||b|sinθ"),
        ("la_norm", "유클리드 노름", "||x||_2=√(Σx_i²)"),
        ("la_det2", "2×2 행렬식", "det([[a,b],[c,d]])=ad-bc"),
        ("la_inv2", "2×2 역행렬", "A^-1=(1/(ad-bc))[[d,-b],[-c,a]]"),
        ("la_eigen", "고유값 방정식", "det(A-λI)=0"),
        ("la_trace", "행렬의 대각합", "tr(A)=Σa_ii"),
        ("la_cauchy", "코시-슈바르츠 부등식", "|a·b|≤||a||||b||"),
    ]
    for fid, title, formula in stats:
        cat = "선형대수" if fid.startswith("la_") else "확률·통계"
        add(_f(fid, title, "수학", cat, formula, source="openstax_math"))

    # --- Physics ---
    physics = [
        ("phy_speed", "평균속력", "v=d/t", "운동학"),
        ("phy_vel", "평균속도", "v=Δx/Δt", "운동학"),
        ("phy_acc", "평균가속도", "a=Δv/Δt", "운동학"),
        ("phy_vat", "등가속도 속도", "v=v_0+at", "운동학"),
        ("phy_xat", "등가속도 위치", "x=x_0+v_0t+at²/2", "운동학"),
        ("phy_v2", "등가속도 무시간식", "v²=v_0²+2aΔx", "운동학"),
        ("phy_newton2", "뉴턴 제2법칙", "ΣF=ma", "힘·에너지"),
        ("phy_weight", "무게", "W=mg", "힘·에너지"),
        ("phy_fric", "운동마찰력", "f_k=μ_kN", "힘·에너지"),
        ("phy_hooke", "훅의 법칙", "F=-kx", "힘·에너지"),
        ("phy_work", "일", "W=Fd cosθ", "힘·에너지"),
        ("phy_ke", "병진 운동에너지", "K=mv²/2", "힘·에너지"),
        ("phy_pe", "중력 위치에너지", "U=mgh", "힘·에너지"),
        ("phy_spring_u", "탄성 위치에너지", "U_s=kx²/2", "힘·에너지"),
        ("phy_power", "평균 일률", "P=W/t", "힘·에너지"),
        ("phy_p", "선운동량", "p=mv", "힘·에너지"),
        ("phy_impulse", "충격량", "J=Δp=F_avgΔt", "힘·에너지"),
        ("phy_cent", "구심가속도", "a_c=v²/r=ω²r", "회전·평형"),
        ("phy_centf", "구심력", "F_c=mv²/r", "회전·평형"),
        ("phy_torque", "토크", "τ=rF sinθ", "회전·평형"),
        ("phy_rotke", "회전 운동에너지", "K_rot=Iω²/2", "회전·평형"),
        ("phy_angmom", "각운동량", "L=Iω", "회전·평형"),
        ("phy_grav", "만유인력", "F=Gm_1m_2/r²", "천체·우주"),
        ("phy_orbit", "원궤도 속력", "v=√(GM/r)", "천체·우주"),
        ("phy_escape", "탈출속도", "v_e=√(2GM/R)", "천체·우주"),
        ("phy_density", "밀도", "ρ=m/V", "유체"),
        ("phy_pressure", "압력", "P=F/A", "유체"),
        ("phy_hydro", "정수압", "P=P_0+ρgh", "유체"),
        ("phy_buoy", "아르키메데스 부력", "F_B=ρ_fluid gV_displaced", "유체"),
        ("phy_cont", "연속방정식", "A_1v_1=A_2v_2", "유체"),
        ("phy_bern", "베르누이 방정식", "P+ρv²/2+ρgh=constant", "유체"),
        ("phy_shm", "단순조화운동", "x=A cos(ωt+φ)", "진동·파동·소리"),
        ("phy_spring_t", "질량-용수철 주기", "T=2π√(m/k)", "진동·파동·소리"),
        ("phy_pend_t", "단진자 주기(소각)", "T=2π√(L/g)", "진동·파동·소리"),
        ("phy_wave", "파동 속력", "v=fλ", "진동·파동·소리"),
        ("phy_intensity", "구면파 세기", "I=P/(4πr²)", "진동·파동·소리"),
        ("phy_db", "소리 세기 레벨", "β=10log10(I/I_0)", "진동·파동·소리"),
        ("phy_heat", "현열", "Q=mcΔT", "열·열역학"),
        ("phy_latent", "잠열", "Q=mL", "열·열역학"),
        ("phy_idealgas", "이상기체 방정식", "PV=nRT", "열·열역학"),
        ("phy_firstlaw", "열역학 제1법칙", "ΔU=Q-W", "열·열역학"),
        ("phy_eff", "열기관 효율", "η=W/Q_h=1-Q_c/Q_h", "열·열역학"),
        ("phy_coulomb", "쿨롱 법칙", "F=k|q_1q_2|/r²", "전기·자기"),
        ("phy_efield", "점전하 전기장", "E=kQ/r²", "전기·자기"),
        ("phy_epot", "점전하 전위", "V=kQ/r", "전기·자기"),
        ("phy_cap", "전기용량", "C=Q/V", "전기·자기"),
        ("phy_cap_energy", "축전기 에너지", "U=CV²/2=Q²/(2C)", "전기·자기"),
        ("phy_ohm", "옴의 법칙", "V=IR", "전기·자기"),
        ("phy_epower", "전기전력", "P=VI=I²R=V²/R", "전기·자기"),
        ("phy_lorentz", "로렌츠 힘", "F=q(E+v×B)", "전기·자기"),
        ("phy_magwire", "전류 도선 자기력", "F=ILB sinθ", "전기·자기"),
        ("phy_flux", "자기선속", "Φ_B=BA cosθ", "전기·자기"),
        ("phy_faraday", "패러데이 법칙", "ε=-N dΦ_B/dt", "전기·자기"),
        ("phy_inductor", "인덕터 유도기전력", "ε_L=-L di/dt", "전기·자기"),
        ("phy_rc", "RC 시정수", "τ=RC", "전기·자기"),
        ("phy_lens", "얇은 렌즈 공식", "1/f=1/d_o+1/d_i", "빛·광학"),
        ("phy_mag", "렌즈 배율", "m=h_i/h_o=-d_i/d_o", "빛·광학"),
        ("phy_snell", "스넬 법칙", "n_1 sinθ_1=n_2 sinθ_2", "빛·광학"),
        ("phy_double", "이중슬릿 밝은무늬", "d sinθ=mλ", "빛·광학"),
        ("phy_diff", "단일슬릿 어두운무늬", "a sinθ=mλ", "빛·광학"),
        ("phy_photon", "광자 에너지", "E=hf=hc/λ", "양자·원자"),
        ("phy_debroglie", "드브로이 파장", "λ=h/p", "양자·원자"),
        ("phy_photo", "광전효과", "K_max=hf-φ", "양자·원자"),
        ("phy_uncert", "위치-운동량 불확정성", "ΔxΔp≥ħ/2", "양자·원자"),
        ("phy_massenergy", "질량-에너지 등가", "E=mc²", "상대성이론"),
        ("phy_gamma", "로런츠 인자", "γ=1/√(1-v²/c²)", "상대성이론"),
        ("phy_decay", "방사성 붕괴", "N=N_0e^(-λt)", "핵·입자"),
        ("phy_half", "반감기", "T_1/2=ln2/λ", "핵·입자"),
    ]
    for fid, title, formula, cat in physics:
        add(_f(fid, title, "물리", cat, formula, source="openstax"))

    # --- Chemistry ---
    chemistry = [
        ("chem_moles", "몰수", "n=m/M", "화학반응·양론"),
        ("chem_particles", "입자수와 몰", "N=nN_A", "화학반응·양론"),
        ("chem_molarity", "몰농도", "M=n/V", "용액·산염기"),
        ("chem_dilution", "희석식", "M_1V_1=M_2V_2", "용액·산염기"),
        ("chem_masspercent", "질량 백분율", "mass%=m_solute/m_solution×100", "용액·산염기"),
        ("chem_boyle", "보일 법칙", "P_1V_1=P_2V_2", "기체·열화학"),
        ("chem_charles", "샤를 법칙", "V_1/T_1=V_2/T_2", "기체·열화학"),
        ("chem_gay", "게이뤼삭 법칙", "P_1/T_1=P_2/T_2", "기체·열화학"),
        ("chem_combined", "기체 결합법칙", "P_1V_1/T_1=P_2V_2/T_2", "기체·열화학"),
        ("chem_ideal", "이상기체", "PV=nRT", "기체·열화학"),
        ("chem_dalton", "돌턴 분압 법칙", "P_total=ΣP_i", "기체·열화학"),
        ("chem_molefrac", "몰분율", "X_i=n_i/n_total", "기체·열화학"),
        ("chem_partial", "분압", "P_i=X_iP_total", "기체·열화학"),
        ("chem_heat", "열량", "q=mcΔT", "기체·열화학"),
        ("chem_hess", "헤스 법칙", "ΔH_rxn=ΣΔH_steps", "기체·열화학"),
        ("chem_rate", "평균 반응속도", "rate=-Δ[A]/Δt=Δ[P]/Δt", "평형·반응속도"),
        ("chem_rate_law", "속도식", "rate=k[A]^m[B]^n", "평형·반응속도"),
        ("chem_arr", "아레니우스 식", "k=Ae^(-E_a/RT)", "평형·반응속도"),
        ("chem_keq", "평형상수", "K_c=Π[products]^ν/Π[reactants]^ν", "평형·반응속도"),
        ("chem_ph", "pH", "pH=-log10[H^+]", "용액·산염기"),
        ("chem_poh", "pOH", "pOH=-log10[OH^-]", "용액·산염기"),
        ("chem_phsum", "25°C에서 pH+pOH", "pH+pOH=14.00", "용액·산염기"),
        ("chem_ka", "산 해리상수", "K_a=[H^+][A^-]/[HA]", "용액·산염기"),
        ("chem_kb", "염기 해리상수", "K_b=[BH^+][OH^-]/[B]", "용액·산염기"),
        ("chem_hh", "헨더슨-하셀바흐", "pH=pK_a+log([A^-]/[HA])", "용액·산염기"),
        ("chem_nernst", "네른스트 식", "E=E°-(RT/nF)lnQ", "전기화학"),
        ("chem_gibbs_e", "전지와 깁스에너지", "ΔG=-nFE", "전기화학"),
        ("chem_gibbs", "깁스 자유에너지", "ΔG=ΔH-TΔS", "기체·열화학"),
        ("chem_gibbs_k", "표준 깁스에너지와 평형상수", "ΔG°=-RT lnK", "평형·반응속도"),
        ("chem_beer", "비어-람베르트 법칙", "A=εbc", "용액·산염기"),
    ]
    for fid, title, formula, cat in chemistry:
        add(_f(fid, title, "화학", cat, formula, source="openstax_science"))

    return rows


FORMULA_SUPPLEMENTS = _supplements()


def build_formula_catalog(terms: Iterable[dict]) -> List[dict]:
    """Build a searchable formula list.

    Each dictionary term carrying a formula becomes one formula card, then the
    supplement fills common textbook relations that do not deserve a standalone
    dictionary entry. IDs are stable and unique.
    """
    rows: List[dict] = []
    used = set()
    for term in terms:
        formula = str(term.get("formula", "")).strip()
        if not formula:
            continue
        fid = "term:" + str(term.get("id", ""))
        if fid in used:
            continue
        used.add(fid)
        rows.append({
            "id": fid,
            "title": term.get("name_ko", "공식"),
            "subject": term.get("subject", "기타"),
            "category": term.get("category", "기타"),
            "formula": formula,
            "note": term.get("summary", ""),
            "source": (term.get("sources") or [""])[0],
            "term_id": term.get("id", ""),
        })
    for row in FORMULA_SUPPLEMENTS:
        if row["id"] not in used:
            used.add(row["id"])
            rows.append(dict(row))
    return rows


def search_formulas(rows: Iterable[dict], query: str = "", subject: str = "전체", category: str = "전체") -> List[dict]:
    q = (query or "").strip().casefold()
    out = []
    for row in rows:
        if subject != "전체" and row.get("subject") != subject:
            continue
        if category != "전체" and row.get("category") != category:
            continue
        hay = " ".join(str(row.get(k, "")) for k in ("title", "subject", "category", "formula", "note")).casefold()
        if q and q not in hay:
            continue
        out.append(row)
    return out
