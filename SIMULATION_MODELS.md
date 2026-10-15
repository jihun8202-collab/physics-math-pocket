# 3.5 Beta 과학 실험 모형과 범위

카탈로그는 **50개 과학 모형 × 모형마다100개 조건 조합 = 5,000개 조건별 실험**입니다. 독립적인 모형이5,000개라는 뜻이 아닙니다. 각 모형의 두 매개변수를 각각10단계로 조합하며 제목과 조절기에 초기값과 단위를 표시합니다. 보존된 기존 실험과 면역·인체 실험실은 이5,000개에 포함하지 않습니다.

400개 조건은 일정한 힘, 포물선, 비선형 진자, 감쇠 용수철의 움직이는 실험에 연결됩니다. 나머지4,600개는 관계식을 조절하며 곡선과 측정값을 비교하는 실험입니다. 관계 그래프가 장기 전체나 모든 분자 운동을 재현하는 것은 아닙니다.

## 수치 정확도와 실제 세계의 차이

각 식의 단위, 적용 범위, 생략한 효과를 아래에 적었습니다. 대부분은 명시한 가정의 해석식을 배정밀도 부동소수점으로 계산합니다. 비선형 진자는 작은 각도 근사 없이RK4로 초당240단계를 적분하며 그래프 표본 사이에는 선형 보간을 사용합니다. 진자는 큰 각도에서도 길이를 유지하는 질량 없는 강체 막대 모형입니다. 감쇠 용수철 그래프는 감쇠의 세 경우를 구분한 해석해이며 움직이는 실험은 같은 미분방정식을RK4로 계산합니다. 포물선 기본 조건은 진공이며 움직이는 실험에서 공기 저항을 추가할 수 있습니다.

자동 검사는 모든5,000개 조건의 경계와 중간값, 각 모형의 조절기 양 끝 조합에서 곡선의 유한성, 별도로 계산한 기준값, 물리 엔진의 초기 조건과 일부 동작을 확인합니다. 이 검사는 실제 측정 자료에 대한 보정이나 임상적 검증을 뜻하지 않습니다. PhET과 동등한 품질이나 현실 전체를 재현한다는 인증은 없습니다.

정수 조절기는 계산 전에 정수로 반올림합니다. 중점합의 분할 수와 병렬 처리기 수는 정수에서 해석합니다. 표본화 곡선은 영차 유지이므로 계단 형태이며 표본 사이의 직선 운동을 뜻하지 않습니다. 정의역 안에서만 계산하고 비유한 값과 범위를 벗어난 매개변수는 거절합니다. 외부 문자열을 식으로 실행하지 않습니다.

생명과학의 효소·결합·혈류·막전위 실험은 해당 관계를 배우는 구성 요소 모형입니다. 환자의 통증, 임상 중증도, 생존 시간이나 치료 결과를 예측하지 않습니다. 별도의 인체 실험실도 가상 교육 모형의 상태를 나타내며 실제 개인의 진료 판단에 사용할 수 없습니다.

상수는SI의 정확한Boltzmann 상수·기체 상수와NIST CODATA의 중력·복사 상수 등을 사용합니다. 천문 단위는149,597,870,700m, 1년은365.25일입니다. 항성·지구 질량과 반지름은 코드에 명시한 대표값을 사용하며 최신 천체 측정값 전체를 반영하는 천체력은 아닙니다.

## 모형별 명세

각 모형에는 아래 두 매개변수의10×10 조합으로100개 실험이 있습니다. 참고 링크는 관계식의 배경 자료이며 특정 조합을 실제 관측으로 보증한다는 뜻은 아닙니다.


### 1. 일정한 힘과 가속 운동 (물리, `force`)

- Formula: x(t)=Ft²/(2m)
- x: 시간 t (s), 0 ~ 10
- y: 위치 x (m)
- 일정한 힘: -45 ~ 45 N (10 levels: -45, -35, -25, -15, -5, 5, 15, 25, 35, 45)
- 질량: 0.5 ~ 9.5 kg (10 levels: 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5)
- 마찰 없는 수평면의 점질량. 처음 위치와 속도는0이며 경계 벽이 없습니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law)

### 2. 진공 포물선 운동 (물리, `projectile`)

- Formula: h(t)=max(0,v₀sinθ·t−gt²/2)
- x: 시간 t (s), 0 ~ 12
- y: 높이 h (m)
- 발사 속력: 6 ~ 60 m/s (10 levels: 6, 12, 18, 24, 30, 36, 42, 48, 54, 60)
- 발사 각도: 8 ~ 80 ° (10 levels: 8, 16, 24, 32, 40, 48, 56, 64, 72, 80)
- 진공 기준 실험. 처음 높이0m, g=9.80665m/s². 지면 접촉 후 높이0으로 고정합니다. 애니메이션에서 저항을 추가해 비교할 수 있습니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/4-3-projectile-motion)

### 3. 큰 각도 비선형 진자 (물리, `pendulum`)

- Formula: θ″=−(g/L)sinθ
- x: 시간 t (s), 0 ~ 12
- y: 각도 θ (°)
- 처음 각도: 5 ~ 113 ° (10 levels: 5, 17, 29, 41, 53, 65, 77, 89, 101, 113)
- 진자 길이: 0.5 ~ 5 m (10 levels: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)
- 작은 각도 근사 없이 sinθ를 계산합니다. 질량 없는 단단한 막대·점질량·감쇠0. 막대는90°를 넘어도 길이를 유지합니다. RK4 240Hz이며 중간 시각은 선형 보간합니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations)

### 4. 용수철과 점성 감쇠 (물리, `spring`)

- Formula: x″+cx′+kx=0; x(0)=0.6m
- x: 시간 t (s), 0 ~ 12
- y: 변위 x (m)
- 용수철 상수: 5 ~ 95 N/m (10 levels: 5, 15, 25, 35, 45, 55, 65, 75, 85, 95)
- 점성 감쇠 계수: 0 ~ 4.5 N·s/m (10 levels: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5)
- 질량1kg, 초기 속도0. 훅의 법칙과 점성 저항의 해석해로 임계·과감쇠도 계산합니다. 변형 한계·건조 마찰은 생략합니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations)

### 5. 정현파의 공간 파형 (물리, `wave`)

- Formula: y=A sin(2πx/λ)
- x: 위치 x (m), 0 ~ 10
- y: 변위 y (m)
- 진폭: 0.1 ~ 1 m (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 파장: 1 ~ 10 m (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 한 시각의 이상적인1차원 횡파. 파형 진행과 매질 입자의 이동은 구분해야 합니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/16-2-mathematics-of-waves)

### 6. 깊이에 따른 절대 압력 (물리, `hydrostatic`)

- Formula: P=P₀+ρgh
- x: 깊이 h (m), 0 ~ 100
- y: 절대 압력 P (Pa)
- 액체 밀도: 500 ~ 1400 kg/m³ (10 levels: 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400)
- 중력 가속도: 1.6 ~ 14.2 m/s² (10 levels: 1.6, 3, 4.4, 5.8, 7.2, 8.6, 10, 11.4, 12.8, 14.2)
- 비압축성 정지 유체. 표면 압력101325Pa, 밀도와 중력은 일정합니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/14-1-fluids-density-and-pressure)

### 7. 금속 저항의 온도와 전류 (물리, `ohmic_temperature`)

- Formula: I=V/[R₂₀(1+α(T−20))]
- x: 전압 V (V), -24 ~ 24
- y: 전류 I (A)
- 20°C 저항: 10 ~ 100 Ω (10 levels: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
- 도체 온도: 20 ~ 110 °C (10 levels: 20, 30, 40, 50, 60, 70, 80, 90, 100, 110)
- α=0.0039°C⁻¹인 도체의 선형 온도 근사. 자체 발열·온도 의존 α는 생략합니다.
- [Reference](https://openstax.org/books/university-physics-volume-2/pages/9-3-resistivity-and-resistance)

### 8. RC 회로 충전 (물리, `rc_charge`)

- Formula: V_C=5(1−exp(−t/RC))
- x: 시간 t (s), 0 ~ 5
- y: 축전기 전압 V_C (V)
- 저항: 1000 ~ 10000 Ω (10 levels: 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000)
- 정전 용량: 10 ~ 100 µF (10 levels: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
- 처음 방전된 이상 축전기와5V 직류 전원. 누설·내부 저항을 생략하고 µF를F로 환산합니다.
- [Reference](https://openstax.org/books/university-physics-volume-2/pages/10-5-rc-circuits)

### 9. 점전하 사이 전기력 (물리, `coulomb`)

- Formula: F=kₑq₁q₂/r²
- x: 전하 사이 거리 r (m), 0.05 ~ 2
- y: 방사 방향 힘 F (N)
- 첫 전하: -4.5 ~ 4.5 µC (10 levels: -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5)
- 둘째 전하: 0.5 ~ 5 µC (10 levels: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)
- 진공의 정지 점전하. 양수는 척력, 음수는 인력. 거리0은 정의역에서 제외합니다.
- [Reference](https://openstax.org/books/university-physics-volume-2/pages/5-3-coulombs-law)

### 10. 뉴턴 냉각 (물리, `newton_cooling`)

- Formula: T=T환경+(80−T환경)exp(−kt)
- x: 시간 t (min), 0 ~ 120
- y: 물체 온도 T (°C)
- 냉각률: 0.01 ~ 0.1 min⁻¹ (10 levels: 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
- 주변 온도: 0 ~ 45 °C (10 levels: 0, 5, 10, 15, 20, 25, 30, 35, 40, 45)
- 온도가 균일한 작은 물체의 집중 열용량 모형. 대류 조건과 주변 온도를 일정하게 둡니다.
- [Reference](https://openstax.org/books/university-physics-volume-2/pages/1-6-mechanisms-of-heat-transfer)

### 11. 회색체 복사 출력 (물리, `thermal_radiation`)

- Formula: P=εσA(T⁴−293.15⁴)
- x: 물체 절대 온도 T (K), 100 ~ 3000
- y: 순 복사 출력 P (W)
- 방사율: 0.1 ~ 1 무차원 (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 복사 표면적: 0.1 ~ 1 m² (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 주변293.15K, 파장에 무관한 방사율의 회색체. 음수는 주변에서 받는 순 복사열입니다.
- [Reference](https://physics.nist.gov/cuu/Constants/index.html)

### 12. 구면 음파의 거리 감쇠 (물리, `sound_intensity`)

- Formula: I=P exp(−αr)/(4πr²)
- x: 거리 r (m), 0.5 ~ 100
- y: 음향 강도 I (W/m²)
- 음향 출력: 0.1 ~ 1 W (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 강도 흡수 계수: 0 ~ 0.09 m⁻¹ (10 levels: 0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09)
- 무지향 점음원·자유 음장·일정한 흡수계수. 벽 반사와 주파수별 흡수는 생략합니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/16-2-mathematics-of-waves)

### 13. 스넬의 법칙 (물리, `snell`)

- Formula: θ₂=asin(n₁ sinθ₁/n₂)
- x: 입사각 θ₁ (°), 0 ~ 80
- y: 굴절각 θ₂ (°)
- 입사 매질 굴절률: 1 ~ 1.45 무차원 (10 levels: 1, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45)
- 굴절 매질 굴절률: 1.5 ~ 2.4 무차원 (10 levels: 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4)
- 평면 경계, 분산 생략. 선택 범위는 n₂>n₁이므로 전반사가 발생하지 않습니다.
- [Reference](https://openstax.org/books/university-physics-volume-3/pages/1-3-refraction)

### 14. 다가오는 음원의 도플러 이동 (물리, `doppler`)

- Formula: f′=f c/(c−v_s)
- x: 음원 접근 속력 v_s (m/s), 0 ~ 100
- y: 관측 주파수 f′ (Hz)
- 원래 주파수: 100 ~ 1000 Hz (10 levels: 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
- 매질 속 음속: 300 ~ 390 m/s (10 levels: 300, 310, 320, 330, 340, 350, 360, 370, 380, 390)
- 정지 관측자·정지 매질·일직선 접근·아음속. 음속은 매질 조건에 따라 달라집니다.
- [Reference](https://openstax.org/books/university-physics-volume-1/pages/17-7-the-doppler-effect)

### 15. 이상기체의 등온 압축 (화학, `ideal_gas`)

- Formula: P=nRT/V
- x: 부피 V (m³), 0.001 ~ 0.1
- y: 압력 P (Pa)
- 기체 양: 0.1 ~ 1 mol (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 절대 온도: 250 ~ 700 K (10 levels: 250, 300, 350, 400, 450, 500, 550, 600, 650, 700)
- 이상기체 가정. 실제 기체의 분자간 힘과 액화는 모형 밖입니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/9-2-relating-pressure-volume-amount-and-temperature-the-ideal-gas-law)

### 16. 1차 반응의 농도 변화 (화학, `first_order`)

- Formula: [A]=[A]₀ exp(−kt)
- x: 시간 t (s), 0 ~ 30
- y: 농도 [A] (mol/L)
- 처음 농도: 0.1 ~ 1 mol/L (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 1차 속도 상수: 0.01 ~ 0.1 s⁻¹ (10 levels: 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
- 일정한 온도·부피의 단일 비가역1차 반응. 평형·연쇄 반응은 포함하지 않습니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/12-4-integrated-rate-laws)

### 17. 2차 반응의 농도 변화 (화학, `second_order`)

- Formula: [A]=[A]₀/(1+k[A]₀t)
- x: 시간 t (s), 0 ~ 30
- y: 농도 [A] (mol/L)
- 처음 농도: 0.1 ~ 1 mol/L (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 2차 속도 상수: 0.05 ~ 0.5 L/(mol·s) (10 levels: 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5)
- 속도식−d[A]/dt=k[A]²의 적분해. 화학양론으로 정의하는 반응 속도와 구분합니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/12-4-integrated-rate-laws)

### 18. 아레니우스 온도 의존성 (화학, `arrhenius`)

- Formula: k=A exp(−Eₐ/RT)
- x: 절대 온도 T (K), 250 ~ 1000
- y: 속도 상수 k (s⁻¹)
- 빈도 인자 A: 1e+08 ~ 1e+09 s⁻¹ (10 levels: 1e+08, 2e+08, 3e+08, 4e+08, 5e+08, 6e+08, 7e+08, 8e+08, 9e+08, 1e+09)
- 활성화 에너지: 20 ~ 65 kJ/mol (10 levels: 20, 25, 30, 35, 40, 45, 50, 55, 60, 65)
- 온도에 무관한 A와Eₐ를 가정한1차 반응 모형. 특정 물질의 측정값은 아닙니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/12-5-collision-theory)

### 19. 완충액 농도비와 pH (화학, `buffer`)

- Formula: pH=pKₐ+log₁₀([A⁻]/[HA])
- x: 짝염기 농도 [A⁻] (mol/L), 0.0001 ~ 0.1
- y: pH (무차원)
- 산 해리 pKₐ: 3 ~ 7.5 무차원 (10 levels: 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5)
- 약산 농도 [HA]: 0.001 ~ 0.01 mol/L (10 levels: 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01)
- 헨더슨–하셀바흐 근사. 활동도≈농도이고 양쪽 성분이 충분한 완충 구간에 적용합니다. 극단 비율은 근사 한계를 보여줍니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/14-6-buffers)

### 20. 흡광도와 농도 (화학, `beer_lambert`)

- Formula: A=εlc
- x: 농도 c (mol/L), 0 ~ 0.01
- y: 흡광도 A (무차원)
- 몰 흡광 계수: 50 ~ 500 L/(mol·cm) (10 levels: 50, 100, 150, 200, 250, 300, 350, 400, 450, 500)
- 광로 길이: 0.1 ~ 1 cm (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 단색광·균질한 묽은 용액. 산란·기기 포화·농도에 따른 화학종 변화는 생략합니다.
- [Reference](https://goldbook.iupac.org/terms/view/A00028)

### 21. 전지 전위와 반응 지수 (화학, `nernst_cell`)

- Formula: E=E°−RT lnQ/(2F)
- x: 반응 지수 Q (무차원), 0.01 ~ 100
- y: 전지 전위 E (V)
- 표준 전지 전위: 0.1 ~ 1 V (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 절대 온도: 273 ~ 318 K (10 levels: 273, 278, 283, 288, 293, 298, 303, 308, 313, 318)
- 전자2개 전달의 평형 전위. Q는 활동도로 정의하며 과전압·전류 손실은 생략합니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/17-4-the-nernst-equation)

### 22. 묽은 용액의 삼투압 (화학, `osmotic`)

- Formula: π=i cRT
- x: 농도 c (mol/L), 0 ~ 0.5
- y: 삼투압 π (Pa)
- 반트호프 인자 i: 1 ~ 2.8 무차원 (10 levels: 1, 1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.4, 2.6, 2.8)
- 절대 온도: 273 ~ 318 K (10 levels: 273, 278, 283, 288, 293, 298, 303, 308, 313, 318)
- 이상적인 묽은 용액 근사. mol/L를mol/m³로 환산하며 고농도 비이상성은 생략합니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/11-4-colligative-properties)

### 23. 효소의 미하엘리스–멘텐 속도 (생명과학, `enzyme`)

- Formula: v=Vmax[S]/(Km+[S])
- x: 기질 농도 [S] (mmol/L), 0 ~ 10
- y: 초기 반응 속도 v (µmol/min)
- 최대 초기 속도: 0.5 ~ 5 µmol/min (10 levels: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)
- 미하엘리스 상수: 0.1 ~ 1 mmol/L (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 정상상태·초기 반응 속도·단일 기질. 억제제·기질 고갈은 포함하지 않습니다.
- [Reference](https://www.ncbi.nlm.nih.gov/books/NBK22330/)

### 24. 수용력에 제한된 개체군 (생명과학, `logistic`)

- Formula: N=K/[1+(K/10−1)exp(−rt)]
- x: 시간 t (day), 0 ~ 40
- y: 개체수 N (개체)
- 환경 수용력 K: 100 ~ 1000 개체 (10 levels: 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
- 성장률 r: 0.05 ~ 0.5 day⁻¹ (10 levels: 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5)
- 처음10개체인 연속 모형. 환경 일정·이입/이출 없음·무작위 멸종 없음.
- [Reference](https://openstax.org/books/biology-2e/pages/45-3-environmental-limits-to-population-growth)

### 25. 협동 결합의 힐 모형 (생명과학, `hill_binding`)

- Formula: Y=cⁿ/(K_dⁿ+cⁿ)
- x: 리간드 농도 c (µmol/L), 0 ~ 10
- y: 결합 분율 Y (0–1)
- 반포화 농도: 0.1 ~ 1 µmol/L (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 힐 계수 n: 1 ~ 10 무차원 (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 현상론적 평형 결합 곡선. 힐 계수는 분자별 결합 부위 수와 항상 같지는 않습니다.
- [Reference](https://www.ncbi.nlm.nih.gov/books/NBK22330/)

### 26. 막을 통한 확산 유량 (생명과학, `fick`)

- Formula: J_total=P A Δc
- x: 농도 차 Δc (mol/m³), -100 ~ 100
- y: 몰 유량 (mol/s)
- 막 투과 계수: 1e-06 ~ 1e-05 m/s (10 levels: 1e-06, 2e-06, 3e-06, 4e-06, 5e-06, 6e-06, 7e-06, 8e-06, 9e-06, 1e-05)
- 막 면적: 1 ~ 10 cm² (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 균일한 얇은 막의 수동 수송. cm²를m²로 환산합니다. 전위차·능동 수송은 생략합니다.
- [Reference](https://openstax.org/books/biology-2e/pages/5-2-passive-transport)

### 27. 칼륨의 평형 막전위 (생명과학, `potassium_nernst`)

- Formula: E_K=(RT/F)ln([K⁺]out/[K⁺]in)
- x: 세포 밖 K⁺ (mmol/L), 1 ~ 20
- y: 칼륨 평형 전위 E_K (mV)
- 세포 안 K⁺: 80 ~ 170 mmol/L (10 levels: 80, 90, 100, 110, 120, 130, 140, 150, 160, 170)
- 절대 온도: 300 ~ 318 K (10 levels: 300, 302, 304, 306, 308, 310, 312, 314, 316, 318)
- K⁺만 통과하는 막의 평형. 실제 세포의 안정막전위·증상·임상 위험을 예측하지 않습니다.
- [Reference](https://openstax.org/books/biology-2e/pages/5-2-passive-transport)

### 28. 산소 결합의 힐 근사 (생명과학, `oxygen_binding`)

- Formula: S=P_O₂ⁿ/(P50ⁿ+P_O₂ⁿ)
- x: 산소 분압 P_O₂ (mmHg), 0 ~ 100
- y: 산소 결합 분율 S (0–1)
- 반포화 분압 P50: 20 ~ 38 mmHg (10 levels: 20, 22, 24, 26, 28, 30, 32, 34, 36, 38)
- 힐 계수: 2 ~ 3.8 무차원 (10 levels: 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8)
- 헤모글로빈 결합의 현상론적 곡선. pH·온도 영향은P50에 묶은 조건입니다. 환자의 산소포화도나 생존 시간을 예측하지 않습니다.
- [Reference](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-5-transport-of-gases)

### 29. 질량당 심박출량 (생명과학, `cardiac_flow`)

- Formula: q=HR×SV/M
- x: 심박수 HR (min⁻¹), 40 ~ 180
- y: 질량당 혈류 q (mL/(kg·min))
- 1회 박출량: 40 ~ 130 mL (10 levels: 40, 50, 60, 70, 80, 90, 100, 110, 120, 130)
- 몸 질량: 30 ~ 120 kg (10 levels: 30, 40, 50, 60, 70, 80, 90, 100, 110, 120)
- 심박수와 박출량을 독립 설정하는 곱셈 관계의 교육 모형. 개인의 실제 순환 조절·건강 상태는 예측하지 않습니다.
- [Reference](https://openstax.org/books/anatomy-and-physiology-2e/pages/19-3-cardiac-cycle)

### 30. 생물 반응 속도의 Q₁₀ (생명과학, `q10`)

- Formula: r(T)=r₂₀ Q₁₀^((T−20)/10)
- x: 온도 T (°C), 0 ~ 40
- y: 상대 반응 속도 (단위/min)
- 20°C 반응 속도: 1 ~ 10 단위/min (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 10°C 증가 배수: 1.2 ~ 3 무차원 (10 levels: 1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.4, 2.6, 2.8, 3)
- 좁은 온도 범위의 경험적 민감도. 효소 변성·치사 온도·개인 체온 반응은 예측하지 않습니다.
- [Reference](https://doi.org/10.1093/jxb/49.325.697)

### 31. 등온 대기의 고도와 기압 (지구과학, `barometric`)

- Formula: P=P₀ exp(−Mgh/RT)
- x: 고도 h (km), 0 ~ 12
- y: 기압 P (hPa)
- 지표 기압: 900 ~ 1080 hPa (10 levels: 900, 920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080)
- 대기 온도: 240 ~ 330 K (10 levels: 240, 250, 260, 270, 280, 290, 300, 310, 320, 330)
- 건조한 이상기체·등온·중력 일정의 정역학 대기. 실제 층별 온도 변화는 생략합니다.
- [Reference](https://www.grc.nasa.gov/www/k-12/airplane/atmosmet.html)

### 32. 지진 P파–S파 도착 시차 (지구과학, `seismic_sp`)

- Formula: Δt=d(1/v_S−1/v_P)
- x: 진원 거리 d (km), 0 ~ 1000
- y: S−P 도착 시차 Δt (s)
- P파 속력: 5.5 ~ 10 km/s (10 levels: 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10)
- S파 속력: 3 ~ 4.8 km/s (10 levels: 3, 3.2, 3.4, 3.6, 3.8, 4, 4.2, 4.4, 4.6, 4.8)
- 균일 매질의 직선 경로. 실제 지구의 굴절·층별 구조·진원 깊이 효과는 생략합니다.
- [Reference](https://www.usgs.gov/programs/earthquake-hazards/science/earthquake-seismology)

### 33. 방사성 붕괴와 반감기 (지구과학, `radioactive`)

- Formula: N=N₀ 2^(−t/T½)
- x: 시간 t (year), 0 ~ 10000
- y: 기대 잔존 원자 수 N (개)
- 처음 원자 수: 100 ~ 1000 개 (10 levels: 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
- 반감기: 1000 ~ 10000 year (10 levels: 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000)
- 닫힌 계·단일 핵종의 기대값. 개별 원자의 무작위 붕괴나 딸핵종 붕괴는 생략합니다.
- [Reference](https://openstax.org/books/chemistry-2e/pages/12-4-integrated-rate-laws)

### 34. 다르시 지하수 흐름 (지구과학, `darcy`)

- Formula: Q=K A i
- x: 수리 경사 i (m/m), 0 ~ 0.1
- y: 유량 Q (m³/s)
- 수리 전도도: 1e-06 ~ 1e-05 m/s (10 levels: 1e-06, 2e-06, 3e-06, 4e-06, 5e-06, 6e-06, 7e-06, 8e-06, 9e-06, 1e-05)
- 흐름 단면적: 10 ~ 100 m² (10 levels: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
- 포화·균질 다공질 매질의 층류 유량. 실제 지하수 속도에는 공극률이 추가로 필요합니다.
- [Reference](https://pubs.usgs.gov/twri/twri3-b2/)

### 35. 유한 수심 중력파 분산 (지구과학, `water_wave`)

- Formula: c²=(g/k)tanh(kh), k=2π/λ
- x: 파장 λ (m), 0.5 ~ 200
- y: 위상 속력 c (m/s)
- 수심 h: 1 ~ 100 m (10 levels: 1, 12, 23, 34, 45, 56, 67, 78, 89, 100)
- 중력 가속도: 8 ~ 11.6 m/s² (10 levels: 8, 8.4, 8.8, 9.2, 9.6, 10, 10.4, 10.8, 11.2, 11.6)
- 진폭이 작은 선형 표면 중력파. 표면 장력·쇄파·해류 생략. 위상 속도와 군속도는 다릅니다.
- [Reference](https://ocw.mit.edu/courses/12-808-introduction-to-observational-physical-oceanography-fall-2004/)

### 36. 쌍성의 케플러 궤도 주기 (천문학, `binary_period`)

- Formula: T=2π√(a³/G(M₁+M₂))
- x: 상대 궤도 긴반지름 a (AU), 0.1 ~ 10
- y: 공전 주기 T (year)
- 첫 별 질량: 0.5 ~ 5 태양 질량 (10 levels: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)
- 둘째 별 질량: 0.1 ~ 1 태양 질량 (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 고립된 두 점질량의 뉴턴 중력. a는두 별 사이 상대 궤도의 긴반지름이며 섭동·상대론은 생략합니다.
- [Reference](https://openstax.org/books/astronomy-2e/pages/3-4-orbits-in-the-solar-system)

### 37. 별에서 받는 복사 유속 (천문학, `stellar_flux`)

- Formula: F=σT★⁴(R★/d)²
- x: 별까지 거리 d (AU), 0.1 ~ 10
- y: 복사 유속 F (W/m²)
- 항성 반지름: 0.2 ~ 2 태양 반지름 (10 levels: 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2)
- 항성 유효 온도: 3000 ~ 7500 K (10 levels: 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500)
- 구형 흑체 별·진공·등방 복사. 행성의 반사율·대기·표면 온도는 계산하지 않습니다.
- [Reference](https://physics.nist.gov/cuu/Constants/index.html)

### 38. 외계행성의 중앙 통과 광도 곡선 (천문학, `transit`)

- Formula: F/F₀=1−겹친 원판 면적/πR★²
- x: 중앙 통과 기준 시간 (h), -6 ~ 6
- y: 정규화 밝기 F/F₀
- 행성/항성 반지름비: 0.02 ~ 0.2 무차원 (10 levels: 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2)
- 첫 접촉부터 마지막 접촉: 2 ~ 6.5 h (10 levels: 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5)
- 일정한 투영 속도·중앙 통과·균일한 항성 밝기. 두 원의 겹친 면적을 계산하며 주변 감광·반점은 생략합니다.
- [Reference](https://heasarc.gsfc.nasa.gov/W3Browse/star-catalog/exoplanodb.html)

### 39. 상대론적 도플러와 우주 적색편이 (천문학, `redshift`)

- Formula: λobs=λ₀(1+z)√((1+β)/(1−β))
- x: 후퇴 속도 β=v/c, -0.9 ~ 0.9
- y: 관측 파장 λobs (nm)
- 정지계 파장: 400 ~ 850 nm (10 levels: 400, 450, 500, 550, 600, 650, 700, 750, 800, 850)
- 우주론적 적색편이 z: 0 ~ 0.9 무차원 (10 levels: 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
- 시선 방향 특수상대론 도플러 인자에 우주 팽창 인자를 곱합니다. 중력 적색편이는 생략합니다.
- [Reference](https://openstax.org/books/university-physics-volume-3/pages/5-7-doppler-effect-for-light)

### 40. 행성의 고도별 탈출 속력 (천문학, `escape`)

- Formula: vₑ=√(2GM/(R+h))
- x: 표면 위 고도 h (km), 0 ~ 10000
- y: 탈출 속력 vₑ (km/s)
- 행성 질량: 0.5 ~ 5 지구 질량 (10 levels: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)
- 행성 반지름: 0.5 ~ 2.3 지구 반지름 (10 levels: 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 1.9, 2.1, 2.3)
- 회전하지 않는 구형 행성·뉴턴 중력·진공. 대기 저항·다른 천체·로켓 연소는 생략합니다.
- [Reference](https://openstax.org/books/astronomy-2e/pages/3-4-orbits-in-the-solar-system)

### 41. 정규 확률 밀도 (수학, `normal_pdf`)

- Formula: f(x)=exp(−(x−μ)²/2σ²)/(σ√2π)
- x: 관측값 x (단위), -6 ~ 8
- y: 확률 밀도 (단위⁻¹)
- 평균 μ: -2 ~ 2.5 단위 (10 levels: -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5)
- 표준편차 σ: 0.2 ~ 2 단위 (10 levels: 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2)
- 곡선 높이가 확률은 아닙니다. 구간 아래 면적이 확률이며 표시 영역 바깥 꼬리도 존재합니다.
- [Reference](https://openstax.org/books/introductory-statistics-2e/pages/6-1-the-standard-normal-distribution)

### 42. 이차함수의 곡률과 평행 이동 (수학, `quadratic`)

- Formula: y=a(x−h)²
- x: 입력 x, -8 ~ 10
- y: 출력 y
- 이차항 계수 a: 0.5 ~ 5 무차원 (10 levels: 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)
- 꼭짓점 가로좌표 h: -4 ~ 5 무차원 (10 levels: -4, -3, -2, -1, 0, 1, 2, 3, 4, 5)
- 다항함수의 직접 평가. 꼭짓점은(h,0)이며 a가 커지면 같은 가로 변위의 함수값이 커집니다.
- [Reference](https://openstax.org/books/algebra-and-trigonometry-2e/pages/5-1-quadratic-functions)

### 43. 중점 적분의 실제 절대 오차 (수학, `midpoint_error`)

- Formula: 오차=|중점합_N sin(x)−(cos a−cos b)|
- x: 분할 수 N (개, 정수), 1 ~ 200
- y: 정적분 절대 오차
- 적분 아래 끝 a: 0 ~ 0.9 rad (10 levels: 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
- 적분 위 끝 b: 1 ~ 1.9 rad (10 levels: 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9)
- sin(x)의 정적분 해석해와 실제 중점합의 차이. 분할 수는 가장 가까운 정수로 읽습니다.
- [Reference](https://openstax.org/books/calculus-volume-2/pages/3-6-numerical-integration)

### 44. 베이즈 사후 확률 (수학, `bayes`)

- Formula: P(A|+) = se·p/[se·p+(1−sp)(1−p)]
- x: 사전 확률 p (0–1), 0 ~ 1
- y: 양성 뒤 사후 확률 (0–1)
- 검출 민감도 se: 0.5 ~ 0.95 확률 (10 levels: 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)
- 검출 특이도 sp: 0.9 ~ 0.99 확률 (10 levels: 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)
- 이진 분류기의 조건부 확률. 일정한 민감도·특이도의 모집단 모형이며 개인 진단 결과를 예측하지 않습니다.
- [Reference](https://openstax.org/books/introductory-statistics-2e/pages/3-3-two-basic-rules-of-probability)

### 45. 지수함수 테일러 절단 오차 (수학, `taylor_exp`)

- Formula: 오차=|exp(ax)−Σₖ₌₀ᴺ(ax)ᵏ/k!|
- x: 입력 x, -2 ~ 2
- y: 절대 오차
- 다항식 차수 N: 1 ~ 10 정수 (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 지수 계수 a: 0.1 ~ 1 무차원 (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 0을 중심으로 전개하며 정수 차수를 사용합니다. 작은 오차에는 부동소수점 반올림 한계가 포함됩니다.
- [Reference](https://openstax.org/books/calculus-volume-2/pages/6-3-taylor-and-maclaurin-series)

### 46. 열잡음 채널의 섀넌 용량 (정보과학, `channel_capacity`)

- Formula: C=B log₂(1+P/(kTB))
- x: 수신 신호 전력 P (dBm), -130 ~ -70
- y: 이론 채널 용량 C (Mbit/s)
- 대역폭 B: 1 ~ 10 MHz (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 잡음 온도 T: 200 ~ 380 K (10 levels: 200, 220, 240, 260, 280, 300, 320, 340, 360, 380)
- 대역 제한 AWGN 채널의 상한. kTB열잡음만 사용하며 간섭·부호 부담·장비 잡음 지수는 생략합니다.
- [Reference](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf)

### 47. 병렬화와 통신 부담 (정보과학, `amdahl`)

- Formula: S=1/[(1−p)+p/N+h(N−1)]
- x: 처리기 수 N (개, 정수), 1 ~ 128
- y: 실행 속도 향상 S
- 병렬 처리 가능한 비율 p: 0.1 ~ 1 비율 (10 levels: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
- 추가 처리기당 정규화 부담 h: 0 ~ 0.009 비율 (10 levels: 0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009)
- 고정 크기 문제의 Amdahl 모형에 처리기 수에 선형인 통신 부담을 더한 가정. 실제 장치 성능 측정값은 아닙니다.
- [Reference](https://doi.org/10.1145/1465482.1465560)

### 48. M/M/1 처리와 고정 전송 지연 (정보과학, `queue_latency`)

- Formula: T=1/(μ−λ)+d
- x: 평균 도착률 λ (작업/s), 0 ~ 9
- y: 평균 전체 지연 T (s)
- 평균 서비스율 μ: 10 ~ 100 작업/s (10 levels: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
- 고정 전송 지연 d: 0 ~ 0.9 s (10 levels: 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
- 포아송 도착·지수 서비스·단일 서버·무한 대기열·정상상태. λ<μ만 허용하며 평균값과 개별 요청 지연은 다릅니다.
- [Reference](https://web.mit.edu/dimitrib/www/Queueing_Data_Nets.pdf)

### 49. 정현파 표본화와 영차 유지 (정보과학, `sampling`)

- Formula: y(t)=sin(2πf floor(t f_s)/f_s)
- x: 시간 t (s), 0 ~ 0.05
- y: 유지한 표본값 y
- 원 신호 주파수 f: 50 ~ 500 Hz (10 levels: 50, 100, 150, 200, 250, 300, 350, 400, 450, 500)
- 표본화 주파수 f_s: 100 ~ 1000 Hz (10 levels: 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
- 진폭1인 신호를 일정 간격으로 읽고 다음 표본까지 유지합니다. 나이퀴스트 조건 위반 시 앨리어싱. 양자화·재구성 필터는 생략합니다.
- [Reference](https://ocw.mit.edu/courses/6-003-signals-and-systems-fall-2011/resources/lecture-21-sampling/)

### 50. 반복 부호의 프레임 오류 확률 (정보과학, `repetition_code`)

- Formula: pmaj=Σ C(r,k)pᵏ(1−p)ʳ⁻ᵏ; Pf=1−(1−pmaj)ⁿ
- x: 독립 비트 오류 확률 p, 0 ~ 0.05
- y: 프레임 오류 확률 (0–1)
- 원본 프레임 비트 수 n: 8 ~ 80 bit (10 levels: 8, 16, 24, 32, 40, 48, 56, 64, 72, 80)
- 반복 단계 j (r=2j−1): 1 ~ 10 정수 (10 levels: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- 홀수 반복 부호의 다수결 복호. 독립 비트 오류를 가정하며 상관 오류·전송 속도 비용은 별도입니다. j=1은 무부호 기준.
- [Reference](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/)

