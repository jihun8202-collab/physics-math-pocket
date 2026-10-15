"""50 scientific model families x100 explicit initial conditions =5,000 scenarios.

Scenarios are not independent models. Trusted callables perform calculations;
neither expressions from files nor user strings are executed. Display units are
part of each parameter definition. Four families route to the animated engine.
"""
from __future__ import annotations
from functools import lru_cache
import math
from typing import Mapping

G=6.67430e-11
R=8.31446261815324
FARADAY=96485.33212
SIGMA=5.670374419e-8
KB=1.380649e-23
AU=149597870700.0
SOLAR_MASS=1.98847e30
SOLAR_RADIUS=6.957e8
EARTH_MASS=5.9722e24
EARTH_RADIUS=6.371e6
STANDARD_G=9.80665
SOURCES={
 "mechanics":"https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law",
 "oscillation":"https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations",
 "projectile":"https://openstax.org/books/university-physics-volume-1/pages/4-3-projectile-motion",
 "wave":"https://openstax.org/books/university-physics-volume-1/pages/16-2-mathematics-of-waves",
 "fluid":"https://openstax.org/books/university-physics-volume-1/pages/14-1-fluids-density-and-pressure",
 "electric":"https://openstax.org/books/university-physics-volume-2/pages/9-3-resistivity-and-resistance",
 "rc":"https://openstax.org/books/university-physics-volume-2/pages/10-5-rc-circuits",
 "coulomb":"https://openstax.org/books/university-physics-volume-2/pages/5-3-coulombs-law",
 "thermal":"https://openstax.org/books/university-physics-volume-2/pages/1-6-mechanisms-of-heat-transfer",
 "optics":"https://openstax.org/books/university-physics-volume-3/pages/1-3-refraction",
 "sound":"https://openstax.org/books/university-physics-volume-1/pages/17-7-the-doppler-effect",
 "gas":"https://openstax.org/books/chemistry-2e/pages/9-2-relating-pressure-volume-amount-and-temperature-the-ideal-gas-law",
 "kinetics":"https://openstax.org/books/chemistry-2e/pages/12-4-integrated-rate-laws",
 "arrhenius":"https://openstax.org/books/chemistry-2e/pages/12-5-collision-theory",
 "buffer":"https://openstax.org/books/chemistry-2e/pages/14-6-buffers",
 "nernst":"https://openstax.org/books/chemistry-2e/pages/17-4-the-nernst-equation",
 "osmosis":"https://openstax.org/books/chemistry-2e/pages/11-4-colligative-properties",
 "enzyme":"https://www.ncbi.nlm.nih.gov/books/NBK22330/",
 "population":"https://openstax.org/books/biology-2e/pages/45-3-environmental-limits-to-population-growth",
 "membrane":"https://openstax.org/books/biology-2e/pages/5-2-passive-transport",
 "oxygen":"https://openstax.org/books/anatomy-and-physiology-2e/pages/22-5-transport-of-gases",
 "heart":"https://openstax.org/books/anatomy-and-physiology-2e/pages/19-3-cardiac-cycle",
 "atmosphere":"https://www.grc.nasa.gov/www/k-12/airplane/atmosmet.html",
 "darcy":"https://pubs.usgs.gov/twri/twri3-b2/",
 "transit":"https://heasarc.gsfc.nasa.gov/W3Browse/star-catalog/exoplanodb.html",
 "astronomy":"https://openstax.org/books/astronomy-2e/pages/3-4-orbits-in-the-solar-system",
 "redshift":"https://openstax.org/books/university-physics-volume-3/pages/5-7-doppler-effect-for-light",
 "statistics":"https://openstax.org/books/introductory-statistics-2e/pages/6-1-the-standard-normal-distribution",
 "calculus":"https://openstax.org/books/calculus-volume-2/pages/3-6-numerical-integration",
 "probability":"https://openstax.org/books/introductory-statistics-2e/pages/3-3-two-basic-rules-of-probability",
 "constants":"https://physics.nist.gov/cuu/Constants/index.html",
 "shannon":"https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf",
 "queue":"https://web.mit.edu/dimitrib/www/Queueing_Data_Nets.pdf",
 "sampling":"https://ocw.mit.edu/courses/6-003-signals-and-systems-fall-2011/resources/lecture-21-sampling/",
 "amdahl":"https://doi.org/10.1145/1465482.1465560"}
MODELS={}
_FUNCTIONS={}

def _p(name,label,unit,lo,hi,integer=False):
    # Keep endpoints exact: decimal grids can otherwise exceed a bound by1ulp.
    levels=tuple(lo if i==0 else hi if i==9 else lo+(hi-lo)*i/9 for i in range(10))
    if integer: levels=tuple(round(v) for v in levels)
    return dict(name=name,label=label,unit=unit,minimum=lo,maximum=hi,values=levels,integer=integer)

def _model(key,title,subject,formula,axes,domain,parameters,function,notes,source,dynamic=None,discrete=False):
    assert len(parameters)==2 and key not in MODELS
    MODELS[key]=dict(family=key,title=title,model_title=title,subject=subject,formula=formula,
        x_label=axes[0],y_label=axes[1],xmin=domain[0],xmax=domain[1],domain=domain,
        parameters=parameters,notes=notes,source=SOURCES.get(source,source),expr="",dynamic_kind=dynamic,discrete=discrete)
    _FUNCTIONS[key]=function

@lru_cache(maxsize=120)
def _pendulum_trace(angle,length):
    dt=1/240
    theta,omega=math.radians(angle),0.0
    trace=[theta]
    def accel(q): return -STANDARD_G/length*math.sin(q)
    for _ in range(2880):
        a,b=omega,accel(theta)
        c,d=omega+dt*b/2,accel(theta+dt*a/2)
        e,f=omega+dt*d/2,accel(theta+dt*c/2)
        g,h=omega+dt*f,accel(theta+dt*e)
        theta+=dt*(a+2*c+2*e+g)/6
        omega+=dt*(b+2*d+2*f+h)/6
        trace.append(theta)
    return tuple(trace)

def _pendulum(t,p):
    trace=_pendulum_trace(p['angle_degrees'],p['length'])
    pos=min(t*240,len(trace)-1); i=int(pos)
    theta=trace[i] if i==len(trace)-1 else trace[i]+(trace[i+1]-trace[i])*(pos-i)
    return math.degrees(theta)

def _spring(t,p):
    a=p['spring_damping']/2; delta=a*a-p['stiffness']
    if abs(delta)<1e-12: return 0.6*math.exp(-a*t)*(1+a*t)
    if delta<0:
        w=math.sqrt(-delta)
        return 0.6*math.exp(-a*t)*(math.cos(w*t)+a/w*math.sin(w*t))
    b=math.sqrt(delta); r1,r2=-a+b,-a-b
    return 0.6*(-r2*math.exp(r1*t)+r1*math.exp(r2*t))/(r1-r2)

def _transit(t,p):
    r=p['radius_ratio']; d=abs(t)*2*(1+r)/p['duration']
    if d>=1+r: return 1.0
    if d<=1-r: return 1-r*r
    a=math.acos(max(-1,min(1,(d*d+r*r-1)/(2*d*r))))
    b=math.acos(max(-1,min(1,(d*d+1-r*r)/(2*d))))
    area=r*r*a+b-0.5*math.sqrt(max(0,(-d+r+1)*(d+r-1)*(d-r+1)*(d+r+1)))
    return 1-area/math.pi

def _midpoint_error(x,p):
    n=max(1,int(round(x))); a,b=p['start'],p['end']; width=b-a
    approx=width/n*math.sin((a+b)/2)*math.sin(width/2)/math.sin(width/(2*n))
    return abs(approx-(math.cos(a)-math.cos(b)))

def _repetition_error(x,p):
    r=2*int(round(p['repeat_index']))-1
    majority=sum(math.comb(r,k)*x**k*(1-x)**(r-k) for k in range(r//2+1,r+1))
    return -math.expm1(int(round(p['bits']))*math.log1p(-majority)) if majority<1 else 1.0

# Physics: four high fidelity animated families plus ten analytic laws.
_model('force','일정한 힘과 가속 운동','물리','x(t)=Ft²/(2m)',('시간 t (s)','위치 x (m)'),(0,10),
 (_p('applied_force','일정한 힘','N',-45,45),_p('mass','질량','kg',0.5,9.5)),lambda x,p:p['applied_force']*x*x/(2*p['mass']),
 '마찰 없는 수평면의 점질량. 처음 위치와 속도는0이며 경계 벽이 없습니다.','mechanics',dynamic='force')
_model('projectile','진공 포물선 운동','물리','h(t)=max(0,v₀sinθ·t−gt²/2)',('시간 t (s)','높이 h (m)'),(0,12),
 (_p('launch_speed','발사 속력','m/s',6,60),_p('angle_degrees','발사 각도','°',8,80)),lambda x,p:max(0,p['launch_speed']*math.sin(math.radians(p['angle_degrees']))*x-STANDARD_G*x*x/2),
 '진공 기준 실험. 처음 높이0m, g=9.80665m/s². 지면 접촉 후 높이0으로 고정합니다. 애니메이션에서 저항을 추가해 비교할 수 있습니다.','projectile',dynamic='projectile')
_model('pendulum','큰 각도 비선형 진자','물리','θ″=−(g/L)sinθ',('시간 t (s)','각도 θ (°)'),(0,12),
 (_p('angle_degrees','처음 각도','°',5,113),_p('length','진자 길이','m',0.5,5)),_pendulum,
 '작은 각도 근사 없이 sinθ를 계산합니다. 질량 없는 단단한 막대·점질량·감쇠0. 막대는90°를 넘어도 길이를 유지합니다. RK4 240Hz이며 중간 시각은 선형 보간합니다.','oscillation',dynamic='pendulum')
_model('spring','용수철과 점성 감쇠','물리','x″+cx′+kx=0; x(0)=0.6m',('시간 t (s)','변위 x (m)'),(0,12),
 (_p('stiffness','용수철 상수','N/m',5,95),_p('spring_damping','점성 감쇠 계수','N·s/m',0,4.5)),_spring,
 '질량1kg, 초기 속도0. 훅의 법칙과 점성 저항의 해석해로 임계·과감쇠도 계산합니다. 변형 한계·건조 마찰은 생략합니다.','oscillation',dynamic='spring')
_model('wave','정현파의 공간 파형','물리','y=A sin(2πx/λ)',('위치 x (m)','변위 y (m)'),(0,10),
 (_p('amplitude','진폭','m',0.1,1),_p('wavelength','파장','m',1,10)),lambda x,p:p['amplitude']*math.sin(2*math.pi*x/p['wavelength']),
 '한 시각의 이상적인1차원 횡파. 파형 진행과 매질 입자의 이동은 구분해야 합니다.','wave')
_model('hydrostatic','깊이에 따른 절대 압력','물리','P=P₀+ρgh',('깊이 h (m)','절대 압력 P (Pa)'),(0,100),
 (_p('density','액체 밀도','kg/m³',500,1400),_p('gravity','중력 가속도','m/s²',1.6,14.2)),lambda x,p:101325+p['density']*p['gravity']*x,
 '비압축성 정지 유체. 표면 압력101325Pa, 밀도와 중력은 일정합니다.','fluid')
_model('ohmic_temperature','금속 저항의 온도와 전류','물리','I=V/[R₂₀(1+α(T−20))]',('전압 V (V)','전류 I (A)'),(-24,24),
 (_p('resistance','20°C 저항','Ω',10,100),_p('temperature','도체 온도','°C',20,110)),lambda x,p:x/(p['resistance']*(1+0.0039*(p['temperature']-20))),
 'α=0.0039°C⁻¹인 도체의 선형 온도 근사. 자체 발열·온도 의존 α는 생략합니다.','electric')
_model('rc_charge','RC 회로 충전','물리','V_C=5(1−exp(−t/RC))',('시간 t (s)','축전기 전압 V_C (V)'),(0,5),
 (_p('resistance','저항','Ω',1000,10000),_p('capacitance','정전 용량','µF',10,100)),lambda x,p:5*(-math.expm1(-x/(p['resistance']*p['capacitance']*1e-6))),
 '처음 방전된 이상 축전기와5V 직류 전원. 누설·내부 저항을 생략하고 µF를F로 환산합니다.','rc')
_model('coulomb','점전하 사이 전기력','물리','F=kₑq₁q₂/r²',('전하 사이 거리 r (m)','방사 방향 힘 F (N)'),(0.05,2),
 (_p('charge1','첫 전하','µC',-4.5,4.5),_p('charge2','둘째 전하','µC',0.5,5)),lambda x,p:8.9875517923e9*p['charge1']*p['charge2']*1e-12/(x*x),
 '진공의 정지 점전하. 양수는 척력, 음수는 인력. 거리0은 정의역에서 제외합니다.','coulomb')
_model('newton_cooling','뉴턴 냉각','물리','T=T환경+(80−T환경)exp(−kt)',('시간 t (min)','물체 온도 T (°C)'),(0,120),
 (_p('cooling_rate','냉각률','min⁻¹',0.01,0.1),_p('ambient','주변 온도','°C',0,45)),lambda x,p:p['ambient']+(80-p['ambient'])*math.exp(-p['cooling_rate']*x),
 '온도가 균일한 작은 물체의 집중 열용량 모형. 대류 조건과 주변 온도를 일정하게 둡니다.','thermal')
_model('thermal_radiation','회색체 복사 출력','물리','P=εσA(T⁴−293.15⁴)',('물체 절대 온도 T (K)','순 복사 출력 P (W)'),(100,3000),
 (_p('emissivity','방사율','무차원',0.1,1),_p('area','복사 표면적','m²',0.1,1)),lambda x,p:p['emissivity']*SIGMA*p['area']*(x**4-293.15**4),
 '주변293.15K, 파장에 무관한 방사율의 회색체. 음수는 주변에서 받는 순 복사열입니다.','constants')
_model('sound_intensity','구면 음파의 거리 감쇠','물리','I=P exp(−αr)/(4πr²)',('거리 r (m)','음향 강도 I (W/m²)'),(0.5,100),
 (_p('power','음향 출력','W',0.1,1),_p('absorption','강도 흡수 계수','m⁻¹',0,0.09)),lambda x,p:p['power']*math.exp(-p['absorption']*x)/(4*math.pi*x*x),
 '무지향 점음원·자유 음장·일정한 흡수계수. 벽 반사와 주파수별 흡수는 생략합니다.','wave')
_model('snell','스넬의 법칙','물리','θ₂=asin(n₁ sinθ₁/n₂)',('입사각 θ₁ (°)','굴절각 θ₂ (°)'),(0,80),
 (_p('index1','입사 매질 굴절률','무차원',1,1.45),_p('index2','굴절 매질 굴절률','무차원',1.5,2.4)),lambda x,p:math.degrees(math.asin(p['index1']*math.sin(math.radians(x))/p['index2'])),
 '평면 경계, 분산 생략. 선택 범위는 n₂>n₁이므로 전반사가 발생하지 않습니다.','optics')
_model('doppler','다가오는 음원의 도플러 이동','물리','f′=f c/(c−v_s)',('음원 접근 속력 v_s (m/s)','관측 주파수 f′ (Hz)'),(0,100),
 (_p('frequency','원래 주파수','Hz',100,1000),_p('wave_speed','매질 속 음속','m/s',300,390)),lambda x,p:p['frequency']*p['wave_speed']/(p['wave_speed']-x),
 '정지 관측자·정지 매질·일직선 접근·아음속. 음속은 매질 조건에 따라 달라집니다.','sound')

# Chemistry (8).
_model('ideal_gas','이상기체의 등온 압축','화학','P=nRT/V',('부피 V (m³)','압력 P (Pa)'),(0.001,0.1),
 (_p('amount','기체 양','mol',0.1,1),_p('temperature','절대 온도','K',250,700)),lambda x,p:p['amount']*R*p['temperature']/x,
 '이상기체 가정. 실제 기체의 분자간 힘과 액화는 모형 밖입니다.','gas')
_model('first_order','1차 반응의 농도 변화','화학','[A]=[A]₀ exp(−kt)',('시간 t (s)','농도 [A] (mol/L)'),(0,30),
 (_p('initial','처음 농도','mol/L',0.1,1),_p('rate','1차 속도 상수','s⁻¹',0.01,0.1)),lambda x,p:p['initial']*math.exp(-p['rate']*x),
 '일정한 온도·부피의 단일 비가역1차 반응. 평형·연쇄 반응은 포함하지 않습니다.','kinetics')
_model('second_order','2차 반응의 농도 변화','화학','[A]=[A]₀/(1+k[A]₀t)',('시간 t (s)','농도 [A] (mol/L)'),(0,30),
 (_p('initial','처음 농도','mol/L',0.1,1),_p('rate','2차 속도 상수','L/(mol·s)',0.05,0.5)),lambda x,p:p['initial']/(1+p['rate']*p['initial']*x),
 '속도식−d[A]/dt=k[A]²의 적분해. 화학양론으로 정의하는 반응 속도와 구분합니다.','kinetics')
_model('arrhenius','아레니우스 온도 의존성','화학','k=A exp(−Eₐ/RT)',('절대 온도 T (K)','속도 상수 k (s⁻¹)'),(250,1000),
 (_p('prefactor','빈도 인자 A','s⁻¹',1e8,1e9),_p('activation','활성화 에너지','kJ/mol',20,65)),lambda x,p:p['prefactor']*math.exp(-1000*p['activation']/(R*x)),
 '온도에 무관한 A와Eₐ를 가정한1차 반응 모형. 특정 물질의 측정값은 아닙니다.','arrhenius')
_model('buffer','완충액 농도비와 pH','화학','pH=pKₐ+log₁₀([A⁻]/[HA])',('짝염기 농도 [A⁻] (mol/L)','pH (무차원)'),(0.0001,0.1),
 (_p('pka','산 해리 pKₐ','무차원',3,7.5),_p('acid','약산 농도 [HA]','mol/L',0.001,0.01)),lambda x,p:p['pka']+math.log10(x/p['acid']),
 '헨더슨–하셀바흐 근사. 활동도≈농도이고 양쪽 성분이 충분한 완충 구간에 적용합니다. 극단 비율은 근사 한계를 보여줍니다.','buffer')
_model('beer_lambert','흡광도와 농도','화학','A=εlc',('농도 c (mol/L)','흡광도 A (무차원)'),(0,0.01),
 (_p('absorptivity','몰 흡광 계수','L/(mol·cm)',50,500),_p('path','광로 길이','cm',0.1,1)),lambda x,p:p['absorptivity']*p['path']*x,
 '단색광·균질한 묽은 용액. 산란·기기 포화·농도에 따른 화학종 변화는 생략합니다.','https://goldbook.iupac.org/terms/view/A00028')
_model('nernst_cell','전지 전위와 반응 지수','화학','E=E°−RT lnQ/(2F)',('반응 지수 Q (무차원)','전지 전위 E (V)'),(0.01,100),
 (_p('standard','표준 전지 전위','V',0.1,1),_p('temperature','절대 온도','K',273,318)),lambda x,p:p['standard']-R*p['temperature']*math.log(x)/(2*FARADAY),
 '전자2개 전달의 평형 전위. Q는 활동도로 정의하며 과전압·전류 손실은 생략합니다.','nernst')
_model('osmotic','묽은 용액의 삼투압','화학','π=i cRT',('농도 c (mol/L)','삼투압 π (Pa)'),(0,0.5),
 (_p('factor','반트호프 인자 i','무차원',1,2.8),_p('temperature','절대 온도','K',273,318)),lambda x,p:p['factor']*x*1000*R*p['temperature'],
 '이상적인 묽은 용액 근사. mol/L를mol/m³로 환산하며 고농도 비이상성은 생략합니다.','osmosis')

# Biology (8): component models, never patient-specific forecasts.
_model('enzyme','효소의 미하엘리스–멘텐 속도','생명과학','v=Vmax[S]/(Km+[S])',('기질 농도 [S] (mmol/L)','초기 반응 속도 v (µmol/min)'),(0,10),
 (_p('vmax','최대 초기 속도','µmol/min',0.5,5),_p('km','미하엘리스 상수','mmol/L',0.1,1)),lambda x,p:p['vmax']*x/(p['km']+x),
 '정상상태·초기 반응 속도·단일 기질. 억제제·기질 고갈은 포함하지 않습니다.','enzyme')
_model('logistic','수용력에 제한된 개체군','생명과학','N=K/[1+(K/10−1)exp(−rt)]',('시간 t (day)','개체수 N (개체)'),(0,40),
 (_p('capacity','환경 수용력 K','개체',100,1000),_p('growth','성장률 r','day⁻¹',0.05,0.5)),lambda x,p:p['capacity']/(1+(p['capacity']/10-1)*math.exp(-p['growth']*x)),
 '처음10개체인 연속 모형. 환경 일정·이입/이출 없음·무작위 멸종 없음.','population')
_model('hill_binding','협동 결합의 힐 모형','생명과학','Y=cⁿ/(K_dⁿ+cⁿ)',('리간드 농도 c (µmol/L)','결합 분율 Y (0–1)'),(0,10),
 (_p('kd','반포화 농도','µmol/L',0.1,1),_p('hill','힐 계수 n','무차원',1,10)),lambda x,p:x**p['hill']/(p['kd']**p['hill']+x**p['hill']),
 '현상론적 평형 결합 곡선. 힐 계수는 분자별 결합 부위 수와 항상 같지는 않습니다.','enzyme')
_model('fick','막을 통한 확산 유량','생명과학','J_total=P A Δc',('농도 차 Δc (mol/m³)','몰 유량 (mol/s)'),(-100,100),
 (_p('permeability','막 투과 계수','m/s',1e-6,1e-5),_p('area','막 면적','cm²',1,10)),lambda x,p:p['permeability']*p['area']*1e-4*x,
 '균일한 얇은 막의 수동 수송. cm²를m²로 환산합니다. 전위차·능동 수송은 생략합니다.','membrane')
_model('potassium_nernst','칼륨의 평형 막전위','생명과학','E_K=(RT/F)ln([K⁺]out/[K⁺]in)',('세포 밖 K⁺ (mmol/L)','칼륨 평형 전위 E_K (mV)'),(1,20),
 (_p('inside','세포 안 K⁺','mmol/L',80,170),_p('temperature','절대 온도','K',300,318)),lambda x,p:1000*R*p['temperature']*math.log(x/p['inside'])/FARADAY,
 'K⁺만 통과하는 막의 평형. 실제 세포의 안정막전위·증상·임상 위험을 예측하지 않습니다.','membrane')
_model('oxygen_binding','산소 결합의 힐 근사','생명과학','S=P_O₂ⁿ/(P50ⁿ+P_O₂ⁿ)',('산소 분압 P_O₂ (mmHg)','산소 결합 분율 S (0–1)'),(0,100),
 (_p('p50','반포화 분압 P50','mmHg',20,38),_p('hill','힐 계수','무차원',2,3.8)),lambda x,p:x**p['hill']/(p['p50']**p['hill']+x**p['hill']),
 '헤모글로빈 결합의 현상론적 곡선. pH·온도 영향은P50에 묶은 조건입니다. 환자의 산소포화도나 생존 시간을 예측하지 않습니다.','oxygen')
_model('cardiac_flow','질량당 심박출량','생명과학','q=HR×SV/M',('심박수 HR (min⁻¹)','질량당 혈류 q (mL/(kg·min))'),(40,180),
 (_p('stroke','1회 박출량','mL',40,130),_p('body_mass','몸 질량','kg',30,120)),lambda x,p:x*p['stroke']/p['body_mass'],
 '심박수와 박출량을 독립 설정하는 곱셈 관계의 교육 모형. 개인의 실제 순환 조절·건강 상태는 예측하지 않습니다.','heart')
_model('q10','생물 반응 속도의 Q₁₀','생명과학','r(T)=r₂₀ Q₁₀^((T−20)/10)',('온도 T (°C)','상대 반응 속도 (단위/min)'),(0,40),
 (_p('baseline','20°C 반응 속도','단위/min',1,10),_p('q10','10°C 증가 배수','무차원',1.2,3)),lambda x,p:p['baseline']*p['q10']**((x-20)/10),
 '좁은 온도 범위의 경험적 민감도. 효소 변성·치사 온도·개인 체온 반응은 예측하지 않습니다.','https://doi.org/10.1093/jxb/49.325.697')

# Earth science (5).
_model('barometric','등온 대기의 고도와 기압','지구과학','P=P₀ exp(−Mgh/RT)',('고도 h (km)','기압 P (hPa)'),(0,12),
 (_p('surface','지표 기압','hPa',900,1080),_p('temperature','대기 온도','K',240,330)),lambda x,p:p['surface']*math.exp(-0.0289644*STANDARD_G*x*1000/(R*p['temperature'])),
 '건조한 이상기체·등온·중력 일정의 정역학 대기. 실제 층별 온도 변화는 생략합니다.','atmosphere')
_model('seismic_sp','지진 P파–S파 도착 시차','지구과학','Δt=d(1/v_S−1/v_P)',('진원 거리 d (km)','S−P 도착 시차 Δt (s)'),(0,1000),
 (_p('vp','P파 속력','km/s',5.5,10),_p('vs','S파 속력','km/s',3,4.8)),lambda x,p:x*(1/p['vs']-1/p['vp']),
 '균일 매질의 직선 경로. 실제 지구의 굴절·층별 구조·진원 깊이 효과는 생략합니다.','https://www.usgs.gov/programs/earthquake-hazards/science/earthquake-seismology')
_model('radioactive','방사성 붕괴와 반감기','지구과학','N=N₀ 2^(−t/T½)',('시간 t (year)','기대 잔존 원자 수 N (개)'),(0,10000),
 (_p('initial','처음 원자 수','개',100,1000,True),_p('half_life','반감기','year',1000,10000)),lambda x,p:p['initial']*2**(-x/p['half_life']),
 '닫힌 계·단일 핵종의 기대값. 개별 원자의 무작위 붕괴나 딸핵종 붕괴는 생략합니다.','kinetics')
_model('darcy','다르시 지하수 흐름','지구과학','Q=K A i',('수리 경사 i (m/m)','유량 Q (m³/s)'),(0,0.1),
 (_p('conductivity','수리 전도도','m/s',1e-6,1e-5),_p('area','흐름 단면적','m²',10,100)),lambda x,p:p['conductivity']*p['area']*x,
 '포화·균질 다공질 매질의 층류 유량. 실제 지하수 속도에는 공극률이 추가로 필요합니다.','darcy')
_model('water_wave','유한 수심 중력파 분산','지구과학','c²=(g/k)tanh(kh), k=2π/λ',('파장 λ (m)','위상 속력 c (m/s)'),(0.5,200),
 (_p('depth','수심 h','m',1,100),_p('gravity','중력 가속도','m/s²',8,11.6)),lambda x,p:math.sqrt(p['gravity']*x/(2*math.pi)*math.tanh(2*math.pi*p['depth']/x)),
 '진폭이 작은 선형 표면 중력파. 표면 장력·쇄파·해류 생략. 위상 속도와 군속도는 다릅니다.','https://ocw.mit.edu/courses/12-808-introduction-to-observational-physical-oceanography-fall-2004/')

# Astronomy (5).
_model('binary_period','쌍성의 케플러 궤도 주기','천문학','T=2π√(a³/G(M₁+M₂))',('상대 궤도 긴반지름 a (AU)','공전 주기 T (year)'),(0.1,10),
 (_p('mass1','첫 별 질량','태양 질량',0.5,5),_p('mass2','둘째 별 질량','태양 질량',0.1,1)),lambda x,p:2*math.pi*math.sqrt((x*AU)**3/(G*SOLAR_MASS*(p['mass1']+p['mass2'])))/(365.25*86400),
 '고립된 두 점질량의 뉴턴 중력. a는두 별 사이 상대 궤도의 긴반지름이며 섭동·상대론은 생략합니다.','astronomy')
_model('stellar_flux','별에서 받는 복사 유속','천문학','F=σT★⁴(R★/d)²',('별까지 거리 d (AU)','복사 유속 F (W/m²)'),(0.1,10),
 (_p('radius','항성 반지름','태양 반지름',0.2,2),_p('temperature','항성 유효 온도','K',3000,7500)),lambda x,p:SIGMA*p['temperature']**4*(p['radius']*SOLAR_RADIUS/(x*AU))**2,
 '구형 흑체 별·진공·등방 복사. 행성의 반사율·대기·표면 온도는 계산하지 않습니다.','constants')
_model('transit','외계행성의 중앙 통과 광도 곡선','천문학','F/F₀=1−겹친 원판 면적/πR★²',('중앙 통과 기준 시간 (h)','정규화 밝기 F/F₀'),(-6,6),
 (_p('radius_ratio','행성/항성 반지름비','무차원',0.02,0.2),_p('duration','첫 접촉부터 마지막 접촉','h',2,6.5)),_transit,
 '일정한 투영 속도·중앙 통과·균일한 항성 밝기. 두 원의 겹친 면적을 계산하며 주변 감광·반점은 생략합니다.','transit')
_model('redshift','상대론적 도플러와 우주 적색편이','천문학','λobs=λ₀(1+z)√((1+β)/(1−β))',('후퇴 속도 β=v/c','관측 파장 λobs (nm)'),(-0.9,0.9),
 (_p('wavelength','정지계 파장','nm',400,850),_p('cosmological','우주론적 적색편이 z','무차원',0,0.9)),lambda x,p:p['wavelength']*(1+p['cosmological'])*math.sqrt((1+x)/(1-x)),
 '시선 방향 특수상대론 도플러 인자에 우주 팽창 인자를 곱합니다. 중력 적색편이는 생략합니다.','redshift')
_model('escape','행성의 고도별 탈출 속력','천문학','vₑ=√(2GM/(R+h))',('표면 위 고도 h (km)','탈출 속력 vₑ (km/s)'),(0,10000),
 (_p('mass','행성 질량','지구 질량',0.5,5),_p('radius','행성 반지름','지구 반지름',0.5,2.3)),lambda x,p:math.sqrt(2*G*p['mass']*EARTH_MASS/(p['radius']*EARTH_RADIUS+x*1000))/1000,
 '회전하지 않는 구형 행성·뉴턴 중력·진공. 대기 저항·다른 천체·로켓 연소는 생략합니다.','astronomy')

# Mathematics (5).
_model('normal_pdf','정규 확률 밀도','수학','f(x)=exp(−(x−μ)²/2σ²)/(σ√2π)',('관측값 x (단위)','확률 밀도 (단위⁻¹)'),(-6,8),
 (_p('mean','평균 μ','단위',-2,2.5),_p('sigma','표준편차 σ','단위',0.2,2)),lambda x,p:math.exp(-0.5*((x-p['mean'])/p['sigma'])**2)/(p['sigma']*math.sqrt(2*math.pi)),
 '곡선 높이가 확률은 아닙니다. 구간 아래 면적이 확률이며 표시 영역 바깥 꼬리도 존재합니다.','statistics')
_model('quadratic','이차함수의 곡률과 평행 이동','수학','y=a(x−h)²',('입력 x','출력 y'),(-8,10),
 (_p('scale','이차항 계수 a','무차원',0.5,5),_p('shift','꼭짓점 가로좌표 h','무차원',-4,5)),lambda x,p:p['scale']*(x-p['shift'])**2,
 '다항함수의 직접 평가. 꼭짓점은(h,0)이며 a가 커지면 같은 가로 변위의 함수값이 커집니다.','https://openstax.org/books/algebra-and-trigonometry-2e/pages/5-1-quadratic-functions')
_model('midpoint_error','중점 적분의 실제 절대 오차','수학','오차=|중점합_N sin(x)−(cos a−cos b)|',('분할 수 N (개, 정수)','정적분 절대 오차'),(1,200),
 (_p('start','적분 아래 끝 a','rad',0,0.9),_p('end','적분 위 끝 b','rad',1,1.9)),_midpoint_error,
 'sin(x)의 정적분 해석해와 실제 중점합의 차이. 분할 수는 가장 가까운 정수로 읽습니다.','calculus',discrete=True)
_model('bayes','베이즈 사후 확률','수학','P(A|+) = se·p/[se·p+(1−sp)(1−p)]',('사전 확률 p (0–1)','양성 뒤 사후 확률 (0–1)'),(0,1),
 (_p('sensitivity','검출 민감도 se','확률',0.5,0.95),_p('specificity','검출 특이도 sp','확률',0.9,0.99)),lambda x,p:p['sensitivity']*x/(p['sensitivity']*x+(1-p['specificity'])*(1-x)),
 '이진 분류기의 조건부 확률. 일정한 민감도·특이도의 모집단 모형이며 개인 진단 결과를 예측하지 않습니다.','probability')
_model('taylor_exp','지수함수 테일러 절단 오차','수학','오차=|exp(ax)−Σₖ₌₀ᴺ(ax)ᵏ/k!|',('입력 x','절대 오차'),(-2,2),
 (_p('order','다항식 차수 N','정수',1,10,True),_p('scale','지수 계수 a','무차원',0.1,1)),lambda x,p:abs(math.exp(p['scale']*x)-math.fsum((p['scale']*x)**k/math.factorial(k) for k in range(int(round(p['order']))+1))),
 '0을 중심으로 전개하며 정수 차수를 사용합니다. 작은 오차에는 부동소수점 반올림 한계가 포함됩니다.','https://openstax.org/books/calculus-volume-2/pages/6-3-taylor-and-maclaurin-series')

# Information science (5).
_model('channel_capacity','열잡음 채널의 섀넌 용량','정보과학','C=B log₂(1+P/(kTB))',('수신 신호 전력 P (dBm)','이론 채널 용량 C (Mbit/s)'),(-130,-70),
 (_p('bandwidth','대역폭 B','MHz',1,10),_p('temperature','잡음 온도 T','K',200,380)),lambda x,p:p['bandwidth']*math.log2(1+10**((x-30)/10)/(KB*p['temperature']*p['bandwidth']*1e6)),
 '대역 제한 AWGN 채널의 상한. kTB열잡음만 사용하며 간섭·부호 부담·장비 잡음 지수는 생략합니다.','shannon')
_model('amdahl','병렬화와 통신 부담','정보과학','S=1/[(1−p)+p/N+h(N−1)]',('처리기 수 N (개, 정수)','실행 속도 향상 S'),(1,128),
 (_p('parallel','병렬 처리 가능한 비율 p','비율',0.1,1),_p('overhead','추가 처리기당 정규화 부담 h','비율',0,0.009)),lambda x,p:1/(1-p['parallel']+p['parallel']/max(1,int(round(x)))+p['overhead']*(max(1,int(round(x)))-1)),
 '고정 크기 문제의 Amdahl 모형에 처리기 수에 선형인 통신 부담을 더한 가정. 실제 장치 성능 측정값은 아닙니다.','amdahl',discrete=True)
_model('queue_latency','M/M/1 처리와 고정 전송 지연','정보과학','T=1/(μ−λ)+d',('평균 도착률 λ (작업/s)','평균 전체 지연 T (s)'),(0,9),
 (_p('service','평균 서비스율 μ','작업/s',10,100),_p('latency','고정 전송 지연 d','s',0,0.9)),lambda x,p:1/(p['service']-x)+p['latency'],
 '포아송 도착·지수 서비스·단일 서버·무한 대기열·정상상태. λ<μ만 허용하며 평균값과 개별 요청 지연은 다릅니다.','queue')
_model('sampling','정현파 표본화와 영차 유지','정보과학','y(t)=sin(2πf floor(t f_s)/f_s)',('시간 t (s)','유지한 표본값 y'),(0,0.05),
 (_p('frequency','원 신호 주파수 f','Hz',50,500),_p('sample_rate','표본화 주파수 f_s','Hz',100,1000)),lambda x,p:math.sin(2*math.pi*p['frequency']*math.floor(x*p['sample_rate']+1e-12)/p['sample_rate']),
 '진폭1인 신호를 일정 간격으로 읽고 다음 표본까지 유지합니다. 나이퀴스트 조건 위반 시 앨리어싱. 양자화·재구성 필터는 생략합니다.','sampling')
_model('repetition_code','반복 부호의 프레임 오류 확률','정보과학','pmaj=Σ C(r,k)pᵏ(1−p)ʳ⁻ᵏ; Pf=1−(1−pmaj)ⁿ',('독립 비트 오류 확률 p','프레임 오류 확률 (0–1)'),(0,0.05),
 (_p('bits','원본 프레임 비트 수 n','bit',8,80,True),_p('repeat_index','반복 단계 j (r=2j−1)','정수',1,10,True)),_repetition_error,
 '홀수 반복 부호의 다수결 복호. 독립 비트 오류를 가정하며 상관 오류·전송 속도 비용은 별도입니다. j=1은 무부호 기준.','https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/')

def _dynamic_settings(family,condition):
    if family=='force': return {**condition,'initial_velocity':0.0}
    if family=='projectile': return {**condition,'gravity':STANDARD_G,'quadratic_drag':0.0,'initial_height':0.0,'mass':1.0}
    if family=='pendulum': return {**condition,'gravity':STANDARD_G,'angular_damping':0.0,'mass':1.0}
    if family=='spring': return {**condition,'mass':1.0,'amplitude':0.6}
    return None

SCENARIOS={}
for _family,_m in MODELS.items():
    _p1,_p2=_m['parameters']
    for _i,_a in enumerate(_p1['values']):
        for _j,_b in enumerate(_p2['values']):
            _condition={_p1['name']:float(_a),_p2['name']:float(_b)}
            _index=_i*10+_j+1; _sid=f'sci_{_family}_{_index:03d}'
            _label=' · '.join(f"{p['label']}={_condition[p['name']]:.6g} {p['unit']}" for p in (_p1,_p2))
            _settings=_dynamic_settings(_family,_condition)
            SCENARIOS[_sid]={**_m,'id':_sid,'title':f"{_m['title']} · {_label}",'term':_m['title'],
                'condition':_condition,'condition_label':_label,'scenario_index':_index,
                'sliders':[(f"{p['label']} ({p['unit']})",p['name'],p['minimum'],p['maximum'],_condition[p['name']]) for p in (_p1,_p2)],
                'dynamic':{'kind':_family,'settings':_settings} if _settings is not None else None,
                'catalog_kind':'50개 모형의 조건별 실험','scenario_count_in_family':100}
BETA_SIM_SPECS=SCENARIOS

def _resolve(spec_or_sid):
    if isinstance(spec_or_sid,str): return SCENARIOS[spec_or_sid]
    if not isinstance(spec_or_sid,Mapping) or spec_or_sid.get('family') not in MODELS:
        raise ValueError('Unknown scientific model')
    return spec_or_sid

def _validated_parameters(spec,params):
    definitions=MODELS[spec['family']]['parameters']
    values=dict(spec.get('condition',{})) or {p['name']:float(p['values'][0]) for p in definitions}
    if params is not None:
        if set(params)-{p['name'] for p in definitions}: raise ValueError('Unknown scientific parameter')
        values.update(params)
    for p in definitions:
        value=values[p['name']]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError('Scientific parameters must be finite numbers')
        if not p['minimum']<=value<=p['maximum']: raise ValueError('Parameter outside model range')
        if p['integer']: values[p['name']]=float(round(value))
    return values

def evaluate(spec_or_sid,x:float,params:Mapping[str,float]|None=None)->float:
    """Trusted dispatch; invalid domain/parameter values raise ValueError."""
    spec=_resolve(spec_or_sid); model=MODELS[spec['family']]
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x): raise ValueError('Input must be finite')
    if not model['xmin']-1e-12<=x<=model['xmax']+1e-12: raise ValueError('Input outside model domain')
    result=float(_FUNCTIONS[spec['family']](x,_validated_parameters(spec,params)))
    if not math.isfinite(result): raise ValueError('Nonfinite model result')
    return result

def samples(spec_or_sid,params:Mapping[str,float]|None=None,count:int=640):
    """Reproducible samples, including both boundaries, with no hidden rescaling."""
    if isinstance(count,bool) or not isinstance(count,int) or not 2<=count<=10000: raise ValueError('Sample count must be2through10000')
    spec=_resolve(spec_or_sid); m=MODELS[spec['family']]; lo,hi=m['xmin'],m['xmax']
    return [(lo+(hi-lo)*i/(count-1),evaluate(spec,lo+(hi-lo)*i/(count-1),params)) for i in range(count)]

assert len(MODELS)==50
assert len(SCENARIOS)==5000
assert sum(s['dynamic'] is not None for s in SCENARIOS.values())==400
