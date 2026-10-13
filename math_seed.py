from __future__ import annotations

"""Generate original Korean math glossary entries.

The terms are arranged by the Korean 2022 revised curriculum at school level and
common university mathematics topics. Explanations are original summaries, not
copied from reference sites.
"""

from typing import Dict, List, Tuple

SOURCE_SCHOOL = ["moe_math", "openstax_math"]
SOURCE_UNIV = ["openstax_math", "mit_math"]

# ko, en, short definition, formula, related
CORE: List[Tuple[str, str, str, str, List[str], str, str]] = [
    # Middle school / foundations
    ("자연수", "natural number", "수를 세거나 순서를 나타낼 때 쓰는 1, 2, 3, …과 같은 수.", "", ["정수", "소수", "약수"], "수와 연산", "중등"),
    ("정수", "integer", "양의 정수, 0, 음의 정수를 모두 포함하는 수의 집합.", "…,-2,-1,0,1,2,…", ["자연수", "유리수", "절댓값"], "수와 연산", "중등"),
    ("유리수", "rational number", "두 정수의 비 a/b(b≠0)로 나타낼 수 있는 수.", "a/b, b≠0", ["정수", "무리수", "실수"], "수와 연산", "중등"),
    ("무리수", "irrational number", "두 정수의 비로 나타낼 수 없는 실수.", "", ["유리수", "실수", "제곱근"], "수와 연산", "중등"),
    ("실수", "real number", "수직선의 한 점과 대응하는 모든 유리수와 무리수.", "R", ["유리수", "무리수", "수직선"], "수와 연산", "중등"),
    ("절댓값", "absolute value", "수직선에서 어떤 수가 0으로부터 떨어진 거리.", "|x|", ["정수", "거리", "절댓값 함수"], "수와 연산", "중등"),
    ("소인수분해", "prime factorization", "자연수를 소수들의 곱으로 나타내는 것.", "n=p₁^a₁p₂^a₂…", ["소수", "최대공약수", "최소공배수"], "수와 연산", "중등"),
    ("소수", "prime number", "1보다 크고 약수가 1과 자기 자신뿐인 자연수.", "", ["합성수", "소인수분해", "약수"], "수와 연산", "중등"),
    ("합성수", "composite number", "1보다 크면서 소수가 아닌 자연수.", "", ["소수", "소인수분해"], "수와 연산", "중등"),
    ("최대공약수", "greatest common divisor", "둘 이상의 정수를 모두 나누는 공약수 중 가장 큰 양의 정수.", "gcd(a,b)", ["최소공배수", "소인수분해"], "수와 연산", "중등"),
    ("최소공배수", "least common multiple", "둘 이상의 정수의 공배수 중 가장 작은 양의 정수.", "lcm(a,b)", ["최대공약수", "소인수분해"], "수와 연산", "중등"),
    ("제곱근", "square root", "제곱하여 주어진 수가 되는 수.", "x²=a ⇔ x=±√a", ["무리수", "근호", "거듭제곱"], "수와 연산", "중등"),
    ("거듭제곱", "power", "같은 수를 여러 번 곱한 것을 지수를 이용해 나타낸 표현.", "a^n", ["지수", "지수법칙", "제곱근"], "수와 연산", "중등"),
    ("지수법칙", "laws of exponents", "같은 밑의 거듭제곱을 곱하거나 나눌 때 지수를 다루는 규칙.", "a^m a^n=a^(m+n)", ["거듭제곱", "지수함수"], "수와 연산", "중등"),
    ("문자와 식", "algebraic expression", "수와 문자를 연산 기호로 연결하여 수량의 관계를 나타낸 식.", "", ["항", "계수", "다항식"], "대수", "중등"),
    ("항", "term", "덧셈이나 뺄셈 기호를 기준으로 나뉘는 식의 한 부분.", "", ["계수", "상수항", "다항식"], "대수", "중등"),
    ("계수", "coefficient", "문자를 포함한 항에서 문자에 곱해진 수.", "", ["항", "상수항"], "대수", "중등"),
    ("동류항", "like terms", "문자와 그 지수가 같은 항들.", "", ["항", "다항식"], "대수", "중등"),
    ("일차식", "linear expression", "문자의 최고 차수가 1인 식.", "ax+b", ["일차방정식", "일차함수"], "대수", "중등"),
    ("일차방정식", "linear equation", "미지수의 최고 차수가 1인 방정식.", "ax+b=0", ["방정식", "해", "일차함수"], "대수", "중등"),
    ("연립일차방정식", "system of linear equations", "둘 이상의 일차방정식을 동시에 만족하는 값을 찾는 문제.", "{a₁x+b₁y=c₁; a₂x+b₂y=c₂}", ["일차방정식", "교점", "행렬"], "대수", "중등"),
    ("부등식", "inequality", "두 수나 식의 크기 관계를 <, >, ≤, ≥ 등으로 나타낸 식.", "", ["일차부등식", "연립부등식"], "대수", "중등"),
    ("일차부등식", "linear inequality", "미지수의 최고 차수가 1인 부등식.", "ax+b>0", ["부등식", "수직선"], "대수", "중등"),
    ("정비례", "direct proportion", "한 양이 일정한 배율로 변할 때 다른 양도 같은 배율로 변하는 관계.", "y=ax", ["반비례", "일차함수"], "함수", "중등"),
    ("반비례", "inverse proportion", "한 양이 일정한 배율로 커질 때 다른 양이 그 역배율로 작아지는 관계.", "y=a/x", ["정비례", "유리함수"], "함수", "중등"),
    ("함수", "function", "한 집합의 각 입력에 다른 집합의 출력이 정확히 하나씩 대응하는 관계.", "y=f(x)", ["정의역", "공역", "치역"], "함수", "중등"),
    ("정의역", "domain", "함수에 넣을 수 있도록 정한 모든 입력값의 집합.", "", ["함수", "치역", "공역"], "함수", "중등"),
    ("공역", "codomain", "함수의 출력값이 속하도록 미리 정한 집합.", "", ["함수", "정의역", "치역"], "함수", "중등"),
    ("치역", "range", "실제로 함수가 만들어 내는 출력값들의 집합.", "", ["함수", "정의역", "공역"], "함수", "중등"),
    ("좌표평면", "coordinate plane", "서로 수직인 x축과 y축으로 점의 위치를 순서쌍으로 나타내는 평면.", "(x,y)", ["좌표", "원점", "그래프"], "기하", "중등"),
    ("기울기", "slope", "직선에서 x의 변화량에 대한 y의 변화량의 비.", "m=Δy/Δx", ["일차함수", "직선의 방정식", "미분계수"], "함수", "중등"),
    ("일차함수", "linear function", "그래프가 직선이 되는 함수로 보통 y=ax+b 꼴로 나타낸다.", "y=ax+b", ["기울기", "절편", "일차방정식"], "함수", "중등"),
    ("이차함수", "quadratic function", "최고 차수가 2인 다항함수.", "y=ax²+bx+c, a≠0", ["포물선", "꼭짓점", "판별식"], "함수", "중등"),
    ("삼각형", "triangle", "세 선분으로 둘러싸인 다각형.", "∠A+∠B+∠C=180°", ["합동", "닮음", "피타고라스 정리"], "기하", "중등"),
    ("삼각형의 합동", "triangle congruence", "두 삼각형의 대응하는 변과 각의 크기가 모두 같아 완전히 포개지는 관계.", "SSS, SAS, ASA", ["삼각형", "닮음"], "기하", "중등"),
    ("삼각형의 닮음", "triangle similarity", "대응각이 같고 대응변의 길이가 같은 비율인 두 삼각형의 관계.", "AA, SAS, SSS similarity", ["삼각형", "비례", "합동"], "기하", "중등"),
    ("피타고라스 정리", "Pythagorean theorem", "직각삼각형에서 빗변의 제곱은 나머지 두 변의 제곱합과 같다.", "a²+b²=c²", ["직각삼각형", "거리공식"], "기하", "중등"),
    ("원의 중심각", "central angle", "원의 중심을 꼭짓점으로 하는 각.", "", ["원주각", "호", "부채꼴"], "기하", "중등"),
    ("원주각", "inscribed angle", "원의 둘레 위의 점을 꼭짓점으로 하고 두 변이 현을 이루는 각.", "원주각=중심각/2", ["중심각", "호", "원"], "기하", "중등"),
    ("확률", "probability", "우연한 사건이 일어날 가능성을 0과 1 사이의 수로 나타낸 값.", "P(A)=유리한 경우/전체 경우", ["사건", "표본공간", "경우의 수"], "확률·통계", "중등"),
    ("평균", "mean", "자료의 합을 자료의 개수로 나눈 대표값.", "x̄=(Σxᵢ)/n", ["중앙값", "최빈값", "분산"], "확률·통계", "중등"),
    ("중앙값", "median", "자료를 크기순으로 놓았을 때 가운데에 위치하는 값.", "", ["평균", "최빈값"], "확률·통계", "중등"),
    ("최빈값", "mode", "자료에서 가장 자주 나타나는 값.", "", ["평균", "중앙값"], "확률·통계", "중등"),
    ("분산", "variance", "자료가 평균에서 얼마나 퍼져 있는지 나타내는 제곱편차의 평균.", "σ²=(Σ(xᵢ-μ)²)/n", ["표준편차", "평균"], "확률·통계", "중등"),
    ("표준편차", "standard deviation", "분산의 양의 제곱근으로 자료의 퍼짐 정도를 원래 단위로 나타낸 값.", "σ=√(σ²)", ["분산", "정규분포"], "확률·통계", "중등"),

    # High school algebra/functions/geometry/probability/calculus
    ("다항식", "polynomial", "문자의 음이 아닌 정수 지수 거듭제곱들의 유한한 합으로 이루어진 식.", "aₙxⁿ+…+a₁x+a₀", ["단항식", "인수분해", "다항함수"], "대수", "고등"),
    ("다항식의 나눗셈", "polynomial division", "다항식을 다른 다항식으로 나누어 몫과 나머지를 구하는 연산.", "P(x)=Q(x)D(x)+R(x)", ["나머지정리", "인수정리"], "대수", "고등"),
    ("나머지정리", "remainder theorem", "다항식 P(x)를 x-a로 나눈 나머지는 P(a)이다.", "R=P(a)", ["인수정리", "조립제법"], "대수", "고등"),
    ("인수정리", "factor theorem", "P(a)=0이면 x-a는 다항식 P(x)의 인수라는 정리.", "P(a)=0 ⇔ (x-a)|P(x)", ["나머지정리", "인수분해"], "대수", "고등"),
    ("복소수", "complex number", "실수부와 허수부를 가지며 a+bi 꼴로 나타내는 수.", "z=a+bi, i²=-1", ["허수단위", "켤레복소수", "복소평면"], "수와 연산", "고등"),
    ("켤레복소수", "complex conjugate", "복소수 a+bi에서 허수부의 부호만 바꾼 a-bi.", "z̄=a-bi", ["복소수", "절댓값"], "수와 연산", "고등"),
    ("이차방정식", "quadratic equation", "미지수의 최고 차수가 2인 방정식.", "ax²+bx+c=0", ["근의 공식", "판별식", "이차함수"], "대수", "고등"),
    ("근의 공식", "quadratic formula", "일반적인 이차방정식의 두 근을 계수로 직접 구하는 공식.", "x=(-b±√(b²-4ac))/(2a)", ["이차방정식", "판별식"], "대수", "고등"),
    ("판별식", "discriminant", "이차방정식의 실근 개수를 판별하는 b²-4ac.", "D=b²-4ac", ["이차방정식", "근의 공식"], "대수", "고등"),
    ("고차방정식", "higher-degree equation", "미지수의 최고 차수가 3 이상인 다항방정식.", "P(x)=0", ["다항식", "인수정리"], "대수", "고등"),
    ("절댓값 방정식", "absolute value equation", "절댓값을 포함하며 경우를 나누어 해결하는 방정식.", "|f(x)|=a", ["절댓값", "방정식"], "대수", "고등"),
    ("유리식", "rational expression", "두 다항식의 몫으로 나타낸 식.", "P(x)/Q(x), Q(x)≠0", ["유리함수", "부분분수"], "대수", "고등"),
    ("무리식", "radical expression", "문자를 포함한 근호가 들어 있는 식.", "√f(x)", ["무리함수", "유리화"], "대수", "고등"),
    ("집합", "set", "분명한 기준으로 구별할 수 있는 대상들을 모은 것.", "A={…}", ["원소", "부분집합", "합집합", "교집합"], "집합·논리", "고등"),
    ("부분집합", "subset", "집합 A의 모든 원소가 집합 B에도 포함될 때 A를 B의 부분집합이라 한다.", "A⊆B", ["집합", "진부분집합"], "집합·논리", "고등"),
    ("합집합", "union", "두 집합 중 적어도 하나에 속하는 원소들의 집합.", "A∪B", ["교집합", "여집합"], "집합·논리", "고등"),
    ("교집합", "intersection", "두 집합에 동시에 속하는 원소들의 집합.", "A∩B", ["합집합", "여집합"], "집합·논리", "고등"),
    ("명제", "proposition", "참 또는 거짓이 분명하게 결정되는 문장이나 수학적 주장.", "p, q", ["조건", "역", "이", "대우"], "집합·논리", "고등"),
    ("필요조건", "necessary condition", "명제 p⇒q가 참일 때 q가 p에 대해 가지는 조건.", "p⇒q", ["충분조건", "필요충분조건"], "집합·논리", "고등"),
    ("충분조건", "sufficient condition", "명제 p⇒q가 참일 때 p가 q에 대해 가지는 조건.", "p⇒q", ["필요조건", "필요충분조건"], "집합·논리", "고등"),
    ("합성함수", "composite function", "한 함수의 출력을 다른 함수의 입력으로 넣어 만든 함수.", "(f∘g)(x)=f(g(x))", ["함수", "역함수"], "함수", "고등"),
    ("역함수", "inverse function", "함수의 입력과 출력을 서로 뒤바꾸는 대응을 나타내는 함수.", "f⁻¹(f(x))=x", ["일대일함수", "합성함수"], "함수", "고등"),
    ("유리함수", "rational function", "두 다항식의 몫으로 표현되는 함수.", "f(x)=P(x)/Q(x)", ["점근선", "유리식"], "함수", "고등"),
    ("무리함수", "radical function", "독립변수가 근호 안에 포함되는 함수.", "f(x)=√g(x)", ["제곱근", "정의역"], "함수", "고등"),
    ("지수함수", "exponential function", "변수가 지수에 들어가는 함수.", "f(x)=a^x, a>0, a≠1", ["로그함수", "자연상수"], "함수", "고등"),
    ("로그", "logarithm", "a^y=x를 y=log_a x로 바꾸어 나타내는 지수의 역연산.", "y=log_a x ⇔ a^y=x", ["지수", "로그함수", "상용로그"], "함수", "고등"),
    ("로그함수", "logarithmic function", "지수함수의 역함수인 로그를 이용한 함수.", "f(x)=log_a x", ["지수함수", "역함수"], "함수", "고등"),
    ("삼각비", "trigonometric ratio", "직각삼각형에서 한 예각에 대해 두 변의 길이 비로 정의되는 sin, cos, tan.", "sinθ=대변/빗변", ["사인", "코사인", "탄젠트"], "기하", "고등"),
    ("사인", "sine", "단위원에서 각 θ에 대응하는 점의 y좌표와 연결되는 삼각함수.", "sinθ", ["코사인", "탄젠트", "단위원"], "삼각함수", "고등"),
    ("코사인", "cosine", "단위원에서 각 θ에 대응하는 점의 x좌표와 연결되는 삼각함수.", "cosθ", ["사인", "탄젠트", "단위원"], "삼각함수", "고등"),
    ("탄젠트", "tangent", "사인과 코사인의 비로 나타낼 수 있는 삼각함수.", "tanθ=sinθ/cosθ", ["사인", "코사인"], "삼각함수", "고등"),
    ("삼각함수", "trigonometric function", "각을 입력으로 하여 사인, 코사인, 탄젠트 등의 값을 출력하는 주기함수.", "sin x, cos x, tan x", ["단위원", "주기함수", "삼각방정식"], "삼각함수", "고등"),
    ("사인법칙", "law of sines", "삼각형에서 각 변 길이와 그 대각의 사인 사이의 비가 일정하다는 법칙.", "a/sinA=b/sinB=c/sinC=2R", ["코사인법칙", "삼각형"], "기하", "고등"),
    ("코사인법칙", "law of cosines", "삼각형의 세 변과 한 각 사이의 관계를 나타내는 법칙.", "c²=a²+b²-2ab cosC", ["사인법칙", "피타고라스 정리"], "기하", "고등"),
    ("수열", "sequence", "자연수와 같은 순서 있는 지표에 따라 수를 나열한 것.", "{aₙ}", ["등차수열", "등비수열", "점화식"], "수열", "고등"),
    ("등차수열", "arithmetic sequence", "이웃한 두 항의 차가 항상 일정한 수열.", "aₙ=a₁+(n-1)d", ["등비수열", "등차중항"], "수열", "고등"),
    ("등비수열", "geometric sequence", "이웃한 두 항의 비가 항상 일정한 수열.", "aₙ=a₁r^(n-1)", ["등차수열", "등비중항"], "수열", "고등"),
    ("시그마 기호", "summation notation", "여러 항의 합을 간결하게 나타내는 Σ 표기.", "Σ aₖ", ["수열", "급수"], "수열", "고등"),
    ("수학적 귀납법", "mathematical induction", "자연수에 관한 명제가 모든 자연수에서 참임을 기초 단계와 귀납 단계로 증명하는 방법.", "P(1), P(k)⇒P(k+1)", ["증명", "수열"], "집합·논리", "고등"),
    ("순열", "permutation", "서로 다른 대상을 순서를 고려하여 배열하는 경우의 수.", "nP_r=n!/(n-r)!", ["조합", "팩토리얼"], "확률·통계", "고등"),
    ("조합", "combination", "서로 다른 대상 중 일부를 순서를 고려하지 않고 고르는 경우의 수.", "nC_r=n!/(r!(n-r)!)", ["순열", "이항정리"], "확률·통계", "고등"),
    ("이항정리", "binomial theorem", "(a+b)^n의 전개 계수가 이항계수로 주어진다는 정리.", "(a+b)^n=Σ nC_k a^(n-k)b^k", ["조합", "파스칼 삼각형"], "대수", "고등"),
    ("조건부확률", "conditional probability", "사건 B가 일어났다는 조건 아래 사건 A가 일어날 확률.", "P(A|B)=P(A∩B)/P(B)", ["독립사건", "베이즈 정리"], "확률·통계", "고등"),
    ("독립사건", "independent events", "한 사건의 발생 여부가 다른 사건의 확률에 영향을 주지 않는 두 사건.", "P(A∩B)=P(A)P(B)", ["조건부확률", "종속사건"], "확률·통계", "고등"),
    ("확률변수", "random variable", "표본공간의 각 결과에 수를 대응시키는 함수.", "X:Ω→R", ["확률분포", "기댓값"], "확률·통계", "고등"),
    ("이항분포", "binomial distribution", "서로 독립인 베르누이 시행을 n번 반복했을 때 성공 횟수의 분포.", "P(X=k)=nC_k p^k(1-p)^(n-k)", ["베르누이 시행", "정규분포"], "확률·통계", "고등"),
    ("정규분포", "normal distribution", "평균을 중심으로 좌우대칭인 종 모양의 연속확률분포.", "N(μ,σ²)", ["표준정규분포", "표준편차"], "확률·통계", "고등"),
    ("모평균", "population mean", "모집단 전체의 평균.", "μ", ["표본평균", "추정"], "확률·통계", "고등"),
    ("표본평균", "sample mean", "표본 관측값들의 산술평균.", "x̄=(Σxᵢ)/n", ["모평균", "표본분산"], "확률·통계", "고등"),
    ("극한", "limit", "입력값이 특정 값에 가까워질 때 함수값이 가까워지는 값을 다루는 개념.", "lim_{x→a} f(x)=L", ["연속", "미분", "수열의 극한"], "미적분", "고등"),
    ("연속", "continuity", "함수값과 극한값이 일치하여 그래프가 해당 점에서 끊어지지 않는 성질.", "lim_{x→a}f(x)=f(a)", ["극한", "불연속"], "미적분", "고등"),
    ("미분계수", "derivative at a point", "한 점에서 함수의 순간변화율 또는 접선의 기울기.", "f'(a)=lim_{h→0}[f(a+h)-f(a)]/h", ["도함수", "기울기"], "미적분", "고등"),
    ("도함수", "derivative function", "각 입력에 그 점의 미분계수를 대응시킨 함수.", "f'(x)=df/dx", ["미분계수", "미분법"], "미적분", "고등"),
    ("접선", "tangent line", "곡선의 한 점에서 그 점 근처의 변화 방향을 가장 잘 나타내는 직선.", "y-f(a)=f'(a)(x-a)", ["미분계수", "법선"], "미적분", "고등"),
    ("부정적분", "indefinite integral", "주어진 함수의 모든 원시함수를 적분상수와 함께 나타낸 것.", "∫f(x)dx=F(x)+C", ["정적분", "원시함수"], "미적분", "고등"),
    ("정적분", "definite integral", "구간에서 함수값을 누적한 값으로 넓이와 총변화량을 나타내는 데 쓰인다.", "∫_a^b f(x)dx", ["리만합", "미적분학의 기본정리"], "미적분", "고등"),
    ("미적분학의 기본정리", "fundamental theorem of calculus", "미분과 적분이 서로 역연산 관계임을 연결하는 핵심 정리.", "∫_a^b f(x)dx=F(b)-F(a)", ["정적분", "도함수"], "미적분", "고등"),
    ("벡터", "vector", "크기와 방향을 함께 가지는 양 또는 좌표 성분으로 표현되는 수학적 대상.", "v=(v₁,v₂,…)", ["스칼라", "내적", "위치벡터"], "기하", "고등"),
    ("벡터의 내적", "dot product", "두 벡터의 대응 성분 곱의 합으로 각도와 투영을 연결하는 연산.", "a·b=|a||b|cosθ", ["벡터", "정사영", "직교"], "기하", "고등"),
    ("공간좌표", "spatial coordinates", "3차원 공간에서 점을 세 좌표 (x,y,z)로 나타내는 방법.", "(x,y,z)", ["좌표평면", "벡터", "공간도형"], "기하", "고등"),
    ("직선의 방정식", "equation of a line", "평면 또는 공간에서 한 직선을 만족하는 점들의 좌표 관계.", "y=mx+b", ["기울기", "평면의 방정식"], "기하", "고등"),
    ("원의 방정식", "equation of a circle", "중심과 반지름이 주어진 원 위의 점들이 만족하는 방정식.", "(x-a)²+(y-b)²=r²", ["원", "좌표기하"], "기하", "고등"),
    ("포물선", "parabola", "한 초점과 한 준선까지의 거리가 같은 점들의 자취.", "y²=4px", ["이차함수", "원뿔곡선"], "기하", "고등"),
    ("타원", "ellipse", "두 초점까지 거리의 합이 일정한 점들의 자취.", "x²/a²+y²/b²=1", ["초점", "원뿔곡선", "쌍곡선"], "기하", "고등"),
    ("쌍곡선", "hyperbola", "두 초점까지 거리 차의 절댓값이 일정한 점들의 자취.", "x²/a²-y²/b²=1", ["타원", "점근선", "원뿔곡선"], "기하", "고등"),

    # University calculus / linear algebra / DE / discrete / analysis / algebra / probability
    ("리만합", "Riemann sum", "구간을 작은 조각으로 나누고 각 조각의 함수값과 폭을 곱해 더한 합.", "Σ f(xᵢ*)Δxᵢ", ["정적분", "리만적분"], "미적분", "대학"),
    ("리만적분", "Riemann integral", "리만합의 분할 크기를 0으로 보낼 때 존재하는 극한으로 정의한 적분.", "∫_a^b f(x)dx", ["리만합", "적분가능"], "해석학", "대학"),
    ("편미분", "partial derivative", "다변수 함수에서 한 변수만 변화시키고 나머지는 고정하여 구하는 미분.", "∂f/∂x", ["전미분", "그래디언트"], "다변수미적분", "대학"),
    ("그래디언트", "gradient", "스칼라장의 각 좌표방향 편미분을 성분으로 갖는 벡터.", "∇f=(∂f/∂x₁,…)", ["편미분", "방향도함수"], "다변수미적분", "대학"),
    ("방향도함수", "directional derivative", "주어진 방향으로 함수가 얼마나 빠르게 변하는지 나타내는 미분.", "D_u f=∇f·u", ["그래디언트", "편미분"], "다변수미적분", "대학"),
    ("야코비안", "Jacobian", "다변수 변환의 편미분들을 모은 행렬 또는 그 행렬식.", "J=[∂fᵢ/∂xⱼ]", ["변수변환", "다중적분"], "다변수미적분", "대학"),
    ("이중적분", "double integral", "2차원 영역에서 함수값을 누적하는 적분.", "∬_D f(x,y)dA", ["다중적분", "야코비안"], "다변수미적분", "대학"),
    ("삼중적분", "triple integral", "3차원 영역에서 함수값을 누적하는 적분.", "∭_V f dV", ["이중적분", "체적"], "다변수미적분", "대학"),
    ("선적분", "line integral", "곡선을 따라 스칼라장 또는 벡터장을 누적하는 적분.", "∫_C f ds 또는 ∫_C F·dr", ["벡터장", "그린 정리"], "벡터해석", "대학"),
    ("면적분", "surface integral", "곡면 위에서 함수나 벡터장의 플럭스를 누적하는 적분.", "∬_S F·n dS", ["발산정리", "스토크스 정리"], "벡터해석", "대학"),
    ("발산", "divergence", "벡터장이 한 점에서 퍼져나가는 정도를 나타내는 스칼라.", "∇·F", ["회전", "발산정리"], "벡터해석", "대학"),
    ("회전", "curl", "벡터장의 국소적인 회전 성향을 나타내는 벡터.", "∇×F", ["발산", "스토크스 정리"], "벡터해석", "대학"),
    ("그린 정리", "Green's theorem", "평면 영역의 이중적분과 그 경계의 선적분을 연결하는 정리.", "∮(Pdx+Qdy)=∬(∂Q/∂x-∂P/∂y)dA", ["선적분", "스토크스 정리"], "벡터해석", "대학"),
    ("스토크스 정리", "Stokes' theorem", "곡면 위 회전의 플럭스와 경계곡선의 선적분을 연결하는 정리.", "∮_∂S F·dr=∬_S (∇×F)·n dS", ["회전", "그린 정리"], "벡터해석", "대학"),
    ("발산정리", "divergence theorem", "부피 내부의 발산 적분과 경계면을 통과하는 플럭스를 연결하는 정리.", "∭_V ∇·F dV=∯_∂V F·n dS", ["발산", "면적분"], "벡터해석", "대학"),
    ("행렬", "matrix", "수를 직사각형 배열로 정리한 수학적 대상.", "A=[aᵢⱼ]", ["행렬식", "역행렬", "선형변환"], "선형대수", "대학"),
    ("행렬식", "determinant", "정사각행렬에 대응하는 스칼라로 선형변환의 부피 배율과 가역성을 나타낸다.", "det(A)", ["행렬", "역행렬", "고유값"], "선형대수", "대학"),
    ("역행렬", "inverse matrix", "곱했을 때 단위행렬이 되는 정사각행렬의 역원.", "AA⁻¹=I", ["행렬", "행렬식"], "선형대수", "대학"),
    ("가우스 소거법", "Gaussian elimination", "행 기본변환으로 연립일차방정식이나 행렬을 사다리꼴로 바꾸어 푸는 방법.", "", ["행렬", "연립일차방정식", "랭크"], "선형대수", "대학"),
    ("벡터공간", "vector space", "벡터 덧셈과 스칼라곱이 정의되고 공리를 만족하는 집합.", "V", ["부분공간", "기저", "차원"], "선형대수", "대학"),
    ("부분공간", "subspace", "벡터공간의 연산에 대해 닫혀 있어 그 자체로 벡터공간이 되는 부분집합.", "W≤V", ["벡터공간", "생성공간"], "선형대수", "대학"),
    ("선형결합", "linear combination", "벡터들에 스칼라를 곱해 더한 표현.", "c₁v₁+…+cₙvₙ", ["생성", "선형독립"], "선형대수", "대학"),
    ("선형독립", "linear independence", "벡터들의 선형결합이 0이 되는 경우가 모든 계수 0뿐인 성질.", "Σcᵢvᵢ=0 ⇒ cᵢ=0", ["기저", "선형종속"], "선형대수", "대학"),
    ("기저", "basis", "벡터공간을 생성하면서 선형독립인 벡터들의 집합.", "B={v₁,…,vₙ}", ["차원", "선형독립"], "선형대수", "대학"),
    ("차원", "dimension", "벡터공간의 한 기저가 갖는 벡터의 개수.", "dim V", ["기저", "벡터공간"], "선형대수", "대학"),
    ("선형변환", "linear transformation", "벡터 덧셈과 스칼라곱을 보존하는 함수.", "T(av+bw)=aT(v)+bT(w)", ["행렬", "핵", "상"], "선형대수", "대학"),
    ("고유값", "eigenvalue", "선형변환이 어떤 영이 아닌 벡터의 방향은 유지하고 크기만 λ배 할 때의 λ.", "Av=λv", ["고유벡터", "대각화"], "선형대수", "대학"),
    ("고유벡터", "eigenvector", "행렬 A에 의해 방향이 바뀌지 않고 스칼라배만 되는 영이 아닌 벡터.", "Av=λv", ["고유값", "고유공간"], "선형대수", "대학"),
    ("대각화", "diagonalization", "행렬을 적절한 기저에서 대각행렬과 닮음인 형태로 나타내는 과정.", "A=PDP⁻¹", ["고유값", "고유벡터"], "선형대수", "대학"),
    ("직교", "orthogonality", "내적이 0인 두 벡터 사이의 관계.", "u·v=0", ["내적", "정규직교기저"], "선형대수", "대학"),
    ("그람-슈미트 과정", "Gram-Schmidt process", "선형독립 벡터들로부터 같은 생성공간을 갖는 직교정규 벡터들을 만드는 절차.", "", ["직교", "정규직교기저"], "선형대수", "대학"),
    ("최소제곱법", "least squares", "잔차 제곱합을 최소화하여 과잉결정 선형시스템의 근사해를 구하는 방법.", "min ||Ax-b||²", ["정사영", "회귀"], "선형대수", "대학"),
    ("미분방정식", "differential equation", "미지함수와 그 도함수 사이의 관계를 나타내는 방정식.", "F(x,y,y',…)=0", ["상미분방정식", "편미분방정식"], "미분방정식", "대학"),
    ("상미분방정식", "ordinary differential equation", "하나의 독립변수에 대한 미지함수의 도함수를 포함하는 미분방정식.", "y'=f(x,y)", ["초기값문제", "선형미분방정식"], "미분방정식", "대학"),
    ("편미분방정식", "partial differential equation", "둘 이상의 독립변수를 가진 미지함수의 편도함수를 포함하는 방정식.", "F(x,y,u,u_x,…)=0", ["열방정식", "파동방정식", "라플라스 방정식"], "미분방정식", "대학"),
    ("변수분리법", "separation of variables", "미분방정식을 서로 다른 변수의 항들로 분리하여 적분하는 풀이법.", "dy/g(y)=f(x)dx", ["상미분방정식", "적분"], "미분방정식", "대학"),
    ("1계 선형미분방정식", "first-order linear ODE", "y와 y'가 1차로 나타나는 1계 미분방정식.", "y'+p(x)y=q(x)", ["적분인자", "상미분방정식"], "미분방정식", "대학"),
    ("적분인자", "integrating factor", "선형미분방정식을 완전미분 형태로 바꾸기 위해 곱하는 함수.", "μ=e^{∫p(x)dx}", ["1계 선형미분방정식"], "미분방정식", "대학"),
    ("2계 선형미분방정식", "second-order linear ODE", "최고 도함수가 2계이고 미지함수와 도함수들이 선형으로 나타나는 방정식.", "ay''+by'+cy=g(x)", ["특성방정식", "중첩원리"], "미분방정식", "대학"),
    ("라플라스 변환", "Laplace transform", "시간 함수 f(t)를 복소 주파수 변수 s의 함수로 바꾸는 적분변환.", "L{f}=∫₀∞e^{-st}f(t)dt", ["역라플라스 변환", "미분방정식"], "미분방정식", "대학"),
    ("푸리에 급수", "Fourier series", "주기함수를 사인과 코사인의 무한합으로 표현하는 전개.", "f(x)~a₀/2+Σ(aₙcos nx+bₙsin nx)", ["푸리에 변환", "직교함수"], "해석학", "대학"),
    ("푸리에 변환", "Fourier transform", "함수를 주파수 성분으로 분해하는 적분변환.", "F(ω)=∫f(t)e^{-iωt}dt", ["푸리에 급수", "스펙트럼"], "해석학", "대학"),
    ("수렴", "convergence", "수열·급수·함수열 등이 어떤 극한값이나 대상에 가까워지는 성질.", "aₙ→L", ["발산", "극한"], "해석학", "대학"),
    ("코시 수열", "Cauchy sequence", "뒤쪽 항들끼리의 거리를 원하는 만큼 작게 만들 수 있는 수열.", "∀ε>0, ∃N: m,n>N⇒|a_m-a_n|<ε", ["완비성", "수렴"], "해석학", "대학"),
    ("엡실론-델타 논법", "epsilon-delta definition", "극한과 연속을 거리의 정량적 조건으로 엄밀하게 정의하는 방식.", "∀ε>0 ∃δ>0: |x-a|<δ⇒|f(x)-L|<ε", ["극한", "연속"], "해석학", "대학"),
    ("균등연속", "uniform continuity", "δ를 점의 위치와 무관하게 하나로 선택할 수 있는 연속성.", "", ["연속", "콤팩트성"], "해석학", "대학"),
    ("점별수렴", "pointwise convergence", "함수열이 각 점을 고정했을 때 그 점에서 수렴하는 것.", "fₙ(x)→f(x)", ["균등수렴", "함수열"], "해석학", "대학"),
    ("균등수렴", "uniform convergence", "함수열의 오차를 모든 점에서 동시에 같은 기준으로 작게 만들 수 있는 수렴.", "sup|fₙ-f|→0", ["점별수렴", "함수열"], "해석학", "대학"),
    ("멱급수", "power series", "한 점을 중심으로 (x-a)^n의 계수합으로 표현되는 무한급수.", "Σcₙ(x-a)^n", ["테일러 급수", "수렴반경"], "해석학", "대학"),
    ("테일러 급수", "Taylor series", "함수의 한 점에서의 모든 도함수를 이용해 만든 멱급수 전개.", "Σ f^(n)(a)(x-a)^n/n!", ["맥클로린 급수", "멱급수"], "해석학", "대학"),
    ("맥클로린 급수", "Maclaurin series", "중심이 0인 테일러 급수.", "Σ f^(n)(0)x^n/n!", ["테일러 급수", "멱급수"], "해석학", "대학"),
    ("복소평면", "complex plane", "복소수의 실수부를 x축, 허수부를 y축에 대응시키는 평면.", "z=x+iy", ["복소수", "극형식"], "복소해석", "대학"),
    ("오일러 공식", "Euler's formula", "복소지수와 삼각함수를 연결하는 공식.", "e^{iθ}=cosθ+i sinθ", ["복소지수", "오일러 항등식"], "복소해석", "대학"),
    ("복소미분", "complex derivative", "복소평면의 모든 방향에서 같은 극한을 가져야 하는 미분.", "f'(z)=lim_{h→0}[f(z+h)-f(z)]/h", ["해석함수", "코시-리만 방정식"], "복소해석", "대학"),
    ("코시-리만 방정식", "Cauchy-Riemann equations", "복소함수의 실수부와 허수부 편미분이 만족하는 해석성의 핵심 조건.", "u_x=v_y, u_y=-v_x", ["복소미분", "해석함수"], "복소해석", "대학"),
    ("군", "group", "결합법칙, 항등원, 역원을 갖는 하나의 이항연산이 정의된 집합.", "(G,*)", ["부분군", "군준동형"], "추상대수", "대학"),
    ("환", "ring", "덧셈에 대해 아벨군이고 곱셈이 결합적인 대수구조.", "(R,+,·)", ["군", "체", "아이디얼"], "추상대수", "대학"),
    ("체", "field", "0이 아닌 원소가 곱셈 역원을 가지는 가환환.", "(F,+,·)", ["환", "벡터공간"], "추상대수", "대학"),
    ("군준동형", "group homomorphism", "군 연산을 보존하는 함수.", "φ(ab)=φ(a)φ(b)", ["군", "핵", "상"], "추상대수", "대학"),
    ("동형사상", "isomorphism", "구조를 보존하면서 일대일 대응인 사상.", "A≅B", ["준동형", "역함수"], "추상대수", "대학"),
    ("그래프 이론", "graph theory", "꼭짓점과 그 사이의 연결인 변으로 이루어진 구조를 연구하는 분야.", "G=(V,E)", ["정점", "간선", "경로"], "이산수학", "대학"),
    ("정점", "vertex", "그래프에서 대상 하나를 나타내는 점.", "v∈V", ["간선", "그래프 이론"], "이산수학", "대학"),
    ("간선", "edge", "그래프에서 두 정점 사이의 연결을 나타내는 선.", "e∈E", ["정점", "경로"], "이산수학", "대학"),
    ("트리", "tree", "연결되어 있고 사이클이 없는 그래프.", "|E|=|V|-1", ["그래프", "스패닝 트리"], "이산수학", "대학"),
    ("귀류법", "proof by contradiction", "명제의 부정을 가정한 뒤 모순을 이끌어 원래 명제가 참임을 보이는 증명법.", "", ["증명", "대우증명"], "이산수학", "대학"),
    ("비둘기집 원리", "pigeonhole principle", "n개 상자에 n+1개 이상의 대상을 넣으면 적어도 한 상자에는 둘 이상이 들어간다는 원리.", "", ["조합론", "경우의 수"], "이산수학", "대학"),
    ("포아송분포", "Poisson distribution", "일정한 평균 발생률로 독립적으로 일어나는 사건 횟수를 모델링하는 이산분포.", "P(X=k)=e^{-λ}λ^k/k!", ["이항분포", "지수분포"], "확률·통계", "대학"),
    ("기댓값", "expected value", "확률변수가 장기적으로 가지는 평균적인 값을 나타내는 확률가중 평균.", "E[X]=ΣxP(X=x)", ["분산", "확률변수"], "확률·통계", "대학"),
    ("공분산", "covariance", "두 확률변수가 함께 변하는 방향과 정도를 나타내는 값.", "Cov(X,Y)=E[(X-μ_X)(Y-μ_Y)]", ["상관계수", "분산"], "확률·통계", "대학"),
    ("상관계수", "correlation coefficient", "두 변수의 선형 관계 정도를 -1과 1 사이로 표준화한 값.", "ρ=Cov(X,Y)/(σ_Xσ_Y)", ["공분산", "회귀"], "확률·통계", "대학"),
    ("중심극한정리", "central limit theorem", "조건이 맞으면 많은 독립 확률변수의 합이나 평균의 분포가 정규분포에 가까워진다는 정리.", "", ["정규분포", "표본평균"], "확률·통계", "대학"),
    ("베이즈 정리", "Bayes' theorem", "조건부확률의 방향을 뒤집어 사후확률을 계산하는 정리.", "P(A|B)=P(B|A)P(A)/P(B)", ["조건부확률", "사전확률", "사후확률"], "확률·통계", "대학"),
    ("수치해석", "numerical analysis", "수학 문제를 컴퓨터로 근사 계산하기 위한 알고리즘과 오차를 연구하는 분야.", "", ["절단오차", "반올림오차", "수치적분"], "수치해석", "대학"),
    ("뉴턴 방법", "Newton's method", "함수의 접선을 반복 사용하여 방정식 f(x)=0의 근을 근사하는 방법.", "x_{n+1}=x_n-f(x_n)/f'(x_n)", ["근 찾기", "수치해석"], "수치해석", "대학"),
    ("오일러 방법", "Euler method", "미분방정식의 해를 작은 시간 간격의 접선 근사로 계산하는 가장 기본적인 수치 방법.", "y_{n+1}=y_n+h f(t_n,y_n)", ["룬게-쿠타 방법", "수치미분방정식"], "수치해석", "대학"),
]

# Additional concise glossary terms. These substantially widen coverage while
# keeping each definition original and useful for search/navigation.
BANKS: Dict[Tuple[str, str], List[Tuple[str, str]]] = {
    ("수와 연산", "중등"): [
        ("약수", "divisor"), ("배수", "multiple"), ("공약수", "common divisor"), ("공배수", "common multiple"),
        ("서로소", "coprime"), ("유한소수", "terminating decimal"), ("순환소수", "repeating decimal"), ("근삿값", "approximation"),
        ("유효숫자", "significant figures"), ("오차", "error"), ("상대오차", "relative error"), ("비", "ratio"), ("비율", "rate"),
        ("백분율", "percentage"), ("연비례", "proportion"), ("분수", "fraction"), ("대분수", "mixed number"), ("가분수", "improper fraction")
    ],
    ("대수", "중등"): [
        ("상수", "constant"), ("변수", "variable"), ("미지수", "unknown"), ("상수항", "constant term"), ("식의 값", "value of expression"),
        ("분배법칙", "distributive law"), ("교환법칙", "commutative law"), ("결합법칙", "associative law"), ("이항", "transposition"),
        ("등식", "equality"), ("항등식", "identity"), ("방정식의 해", "solution of equation"), ("등식의 성질", "properties of equality"),
        ("연립방정식의 해", "solution of a system"), ("대입법", "substitution method"), ("가감법", "elimination method"),
        ("인수", "factor"), ("인수분해", "factorization"), ("완전제곱식", "perfect square expression"), ("곱셈공식", "algebraic identities")
    ],
    ("함수", "중등"): [
        ("순서쌍", "ordered pair"), ("좌표", "coordinate"), ("원점", "origin"), ("사분면", "quadrant"), ("그래프", "graph"),
        ("x절편", "x-intercept"), ("y절편", "y-intercept"), ("변화율", "rate of change"), ("함숫값", "function value"),
        ("독립변수", "independent variable"), ("종속변수", "dependent variable"), ("대응", "mapping"), ("일차함수의 그래프", "graph of linear function")
    ],
    ("기하", "중등"): [
        ("점", "point"), ("직선", "line"), ("반직선", "ray"), ("선분", "line segment"), ("각", "angle"), ("맞꼭지각", "vertical angles"),
        ("동위각", "corresponding angles"), ("엇각", "alternate angles"), ("평행선", "parallel lines"), ("수직", "perpendicular"),
        ("다각형", "polygon"), ("정다각형", "regular polygon"), ("내각", "interior angle"), ("외각", "exterior angle"),
        ("사각형", "quadrilateral"), ("평행사변형", "parallelogram"), ("직사각형", "rectangle"), ("마름모", "rhombus"),
        ("정사각형", "square"), ("사다리꼴", "trapezoid"), ("대각선", "diagonal"), ("원", "circle"), ("반지름", "radius"),
        ("지름", "diameter"), ("현", "chord"), ("호", "arc"), ("접선", "tangent to circle"), ("부채꼴", "sector"),
        ("원주", "circumference"), ("원주율", "pi"), ("입체도형", "solid figure"), ("각기둥", "prism"), ("각뿔", "pyramid"),
        ("원기둥", "cylinder"), ("원뿔", "cone"), ("구", "sphere"), ("겉넓이", "surface area"), ("부피", "volume"),
        ("도형의 이동", "geometric transformation"), ("평행이동", "translation"), ("대칭이동", "reflection"), ("회전이동", "rotation")
    ],
    ("확률·통계", "중등"): [
        ("자료", "data"), ("도수", "frequency"), ("도수분포표", "frequency table"), ("히스토그램", "histogram"), ("도수분포다각형", "frequency polygon"),
        ("상대도수", "relative frequency"), ("산점도", "scatter plot"), ("상관관계", "correlation"), ("양의 상관관계", "positive correlation"),
        ("음의 상관관계", "negative correlation"), ("표본공간", "sample space"), ("사건", "event"), ("경우의 수", "counting")
    ],
    ("대수", "고등"): [
        ("단항식", "monomial"), ("이항식", "binomial"), ("삼항식", "trinomial"), ("차수", "degree"), ("다항식의 차수", "degree of polynomial"),
        ("조립제법", "synthetic division"), ("대칭식", "symmetric polynomial"), ("교대식", "alternating polynomial"),
        ("삼차방정식", "cubic equation"), ("사차방정식", "quartic equation"), ("연립이차방정식", "system of quadratic equations"),
        ("부등식의 영역", "region of inequality"), ("절대부등식", "absolute inequality"), ("산술평균-기하평균 부등식", "AM-GM inequality"),
        ("코시-슈바르츠 부등식", "Cauchy-Schwarz inequality"), ("유리화", "rationalization"), ("부분분수", "partial fractions")
    ],
    ("집합·논리", "고등"): [
        ("원소", "element"), ("공집합", "empty set"), ("전체집합", "universal set"), ("여집합", "complement"), ("차집합", "set difference"),
        ("드모르간 법칙", "De Morgan's laws"), ("조건", "condition"), ("역", "converse"), ("이", "inverse proposition"), ("대우", "contrapositive"),
        ("필요충분조건", "necessary and sufficient condition"), ("증명", "proof"), ("직접증명", "direct proof"), ("반례", "counterexample")
    ],
    ("함수", "고등"): [
        ("일대일함수", "injective function"), ("일대일대응", "bijective function"), ("항등함수", "identity function"), ("상수함수", "constant function"),
        ("짝함수", "even function"), ("홀함수", "odd function"), ("주기함수", "periodic function"), ("다항함수", "polynomial function"),
        ("절댓값 함수", "absolute value function"), ("계단함수", "step function"), ("점근선", "asymptote"), ("수평점근선", "horizontal asymptote"),
        ("수직점근선", "vertical asymptote"), ("지수방정식", "exponential equation"), ("로그방정식", "logarithmic equation"),
        ("지수부등식", "exponential inequality"), ("로그부등식", "logarithmic inequality"), ("상용로그", "common logarithm"), ("자연로그", "natural logarithm")
    ],
    ("삼각함수", "고등"): [
        ("호도법", "radian measure"), ("라디안", "radian"), ("단위원", "unit circle"), ("삼각함수의 주기", "period of trigonometric function"),
        ("삼각함수의 그래프", "graphs of trigonometric functions"), ("삼각방정식", "trigonometric equation"), ("삼각부등식", "trigonometric inequality"),
        ("삼각함수 덧셈정리", "angle addition formulas"), ("배각공식", "double-angle formula"), ("반각공식", "half-angle formula"),
        ("곱을 합으로 바꾸는 공식", "product-to-sum formulas"), ("합을 곱으로 바꾸는 공식", "sum-to-product formulas")
    ],
    ("수열", "고등"): [
        ("일반항", "general term"), ("첫째항", "first term"), ("공차", "common difference"), ("공비", "common ratio"), ("등차중항", "arithmetic mean"),
        ("등비중항", "geometric mean"), ("등차수열의 합", "sum of arithmetic sequence"), ("등비수열의 합", "sum of geometric sequence"),
        ("점화식", "recurrence relation"), ("계차수열", "difference sequence"), ("수열의 귀납적 정의", "recursive definition of sequence"),
        ("수열의 극한", "limit of a sequence"), ("무한수열", "infinite sequence"), ("무한급수", "infinite series"), ("등비급수", "geometric series")
    ],
    ("확률·통계", "고등"): [
        ("팩토리얼", "factorial"), ("중복순열", "permutations with repetition"), ("원순열", "circular permutation"), ("중복조합", "combination with repetition"),
        ("분할", "partition counting"), ("덧셈정리", "addition rule of probability"), ("곱셈정리", "multiplication rule of probability"),
        ("여사건", "complementary event"), ("배반사건", "mutually exclusive events"), ("종속사건", "dependent events"),
        ("베르누이 시행", "Bernoulli trial"), ("확률분포", "probability distribution"), ("이산확률변수", "discrete random variable"),
        ("연속확률변수", "continuous random variable"), ("확률질량함수", "probability mass function"), ("확률밀도함수", "probability density function"),
        ("누적분포함수", "cumulative distribution function"), ("표준정규분포", "standard normal distribution"), ("표준화", "standardization"),
        ("모집단", "population"), ("표본", "sample"), ("임의추출", "random sampling"), ("추정", "estimation"), ("신뢰구간", "confidence interval")
    ],
    ("미적분", "고등"): [
        ("좌극한", "left-hand limit"), ("우극한", "right-hand limit"), ("무한대의 극한", "limit at infinity"), ("무한극한", "infinite limit"),
        ("불연속", "discontinuity"), ("미분가능", "differentiability"), ("평균변화율", "average rate of change"), ("순간변화율", "instantaneous rate of change"),
        ("미분법", "differentiation"), ("합의 미분법", "sum rule"), ("곱의 미분법", "product rule"), ("몫의 미분법", "quotient rule"),
        ("합성함수의 미분법", "chain rule"), ("음함수 미분법", "implicit differentiation"), ("역함수 미분법", "derivative of inverse function"),
        ("고계도함수", "higher derivative"), ("증가함수", "increasing function"), ("감소함수", "decreasing function"),
        ("극대", "local maximum"), ("극소", "local minimum"), ("극값", "extremum"), ("변곡점", "inflection point"),
        ("원시함수", "antiderivative"), ("적분상수", "constant of integration"), ("치환적분", "substitution integration"),
        ("부분적분", "integration by parts"), ("넓이의 적분", "area by integration"), ("속도와 거리의 적분", "motion by integration")
    ],
    ("기하", "고등"): [
        ("좌표기하", "analytic geometry"), ("두 점 사이의 거리", "distance between two points"), ("선분의 내분점", "internal division point"),
        ("선분의 외분점", "external division point"), ("두 직선의 평행 조건", "condition for parallel lines"), ("두 직선의 수직 조건", "condition for perpendicular lines"),
        ("점과 직선 사이의 거리", "distance from point to line"), ("원과 직선의 위치관계", "circle-line intersection"),
        ("두 원의 위치관계", "circle-circle intersection"), ("평면벡터", "plane vector"), ("위치벡터", "position vector"),
        ("단위벡터", "unit vector"), ("벡터의 성분", "vector components"), ("벡터의 크기", "vector magnitude"),
        ("벡터의 덧셈", "vector addition"), ("벡터의 실수배", "scalar multiplication"), ("정사영", "orthogonal projection"),
        ("평면의 방정식", "equation of a plane"), ("구의 방정식", "equation of a sphere"), ("원뿔곡선", "conic section"),
        ("초점", "focus of conic"), ("준선", "directrix"), ("이심률", "eccentricity")
    ],
    ("선형대수", "대학"): [
        ("단위행렬", "identity matrix"), ("영행렬", "zero matrix"), ("전치행렬", "transpose matrix"), ("대칭행렬", "symmetric matrix"),
        ("반대칭행렬", "skew-symmetric matrix"), ("삼각행렬", "triangular matrix"), ("대각행렬", "diagonal matrix"),
        ("행 기본변환", "elementary row operation"), ("행 사다리꼴", "row echelon form"), ("기약 행 사다리꼴", "reduced row echelon form"),
        ("랭크", "rank"), ("영공간", "null space"), ("열공간", "column space"), ("행공간", "row space"),
        ("핵", "kernel"), ("상", "image"), ("차원정리", "rank-nullity theorem"), ("좌표벡터", "coordinate vector"),
        ("기저변환", "change of basis"), ("유사행렬", "similar matrices"), ("고유공간", "eigenspace"), ("특성다항식", "characteristic polynomial"),
        ("특성방정식", "characteristic equation"), ("스펙트럴 정리", "spectral theorem"), ("직교행렬", "orthogonal matrix"),
        ("정규행렬", "normal matrix"), ("내적공간", "inner product space"), ("노름", "norm"), ("거리", "metric distance"),
        ("정규직교기저", "orthonormal basis"), ("QR 분해", "QR decomposition"), ("LU 분해", "LU decomposition"),
        ("특잇값 분해", "singular value decomposition"), ("양의 정부호 행렬", "positive definite matrix"), ("이차형식", "quadratic form")
    ],
    ("미적분", "대학"): [
        ("평균값 정리", "mean value theorem"), ("롤의 정리", "Rolle's theorem"), ("로피탈 정리", "L'Hopital's rule"),
        ("뉴턴-라이프니츠 공식", "Newton-Leibniz formula"), ("이상적분", "improper integral"), ("호의 길이", "arc length"),
        ("회전체의 부피", "volume of revolution"), ("회전체의 겉넓이", "surface area of revolution"), ("극좌표", "polar coordinates"),
        ("매개변수곡선", "parametric curve"), ("곡률", "curvature"), ("쌍곡함수", "hyperbolic function"), ("역삼각함수", "inverse trigonometric function")
    ],
    ("해석학", "대학"): [
        ("상한", "supremum"), ("하한", "infimum"), ("최대원", "maximum element"), ("최소원", "minimum element"),
        ("완비성", "completeness"), ("볼차노-바이어슈트라스 정리", "Bolzano-Weierstrass theorem"), ("중간값 정리", "intermediate value theorem"),
        ("최대최소 정리", "extreme value theorem"), ("콤팩트 집합", "compact set"), ("열린집합", "open set"), ("닫힌집합", "closed set"),
        ("근방", "neighborhood"), ("집적점", "limit point"), ("함수열", "sequence of functions"), ("급수의 절대수렴", "absolute convergence"),
        ("조건수렴", "conditional convergence"), ("비교판정법", "comparison test"), ("비율판정법", "ratio test"), ("근판정법", "root test"),
        ("적분판정법", "integral test"), ("교대급수판정법", "alternating series test"), ("수렴반경", "radius of convergence")
    ],
    ("미분방정식", "대학"): [
        ("초기값문제", "initial value problem"), ("경계값문제", "boundary value problem"), ("자율미분방정식", "autonomous differential equation"),
        ("평형해", "equilibrium solution"), ("방향장", "slope field"), ("정확미분방정식", "exact differential equation"),
        ("베르누이 방정식", "Bernoulli differential equation"), ("중첩원리", "superposition principle"), ("특수해", "particular solution"),
        ("일반해", "general solution"), ("상수계수 선형미분방정식", "constant-coefficient linear ODE"), ("비제차 미분방정식", "nonhomogeneous ODE"),
        ("연립미분방정식", "system of differential equations"), ("위상평면", "phase plane"), ("안정성", "stability"),
        ("열방정식", "heat equation"), ("파동방정식", "wave equation"), ("라플라스 방정식", "Laplace equation")
    ],
    ("이산수학", "대학"): [
        ("관계", "relation"), ("동치관계", "equivalence relation"), ("동치류", "equivalence class"), ("부분순서", "partial order"),
        ("하세도", "Hasse diagram"), ("불 대수", "Boolean algebra"), ("논리곱", "conjunction"), ("논리합", "disjunction"),
        ("부정", "negation"), ("진리표", "truth table"), ("술어", "predicate"), ("전칭기호", "universal quantifier"), ("존재기호", "existential quantifier"),
        ("재귀", "recursion"), ("생성함수", "generating function"), ("포함배제 원리", "inclusion-exclusion principle"),
        ("그래프의 차수", "degree of vertex"), ("경로", "path"), ("사이클", "cycle"), ("연결그래프", "connected graph"),
        ("완전그래프", "complete graph"), ("이분그래프", "bipartite graph"), ("오일러 경로", "Euler path"), ("해밀턴 경로", "Hamiltonian path"),
        ("평면그래프", "planar graph"), ("스패닝 트리", "spanning tree"), ("최단경로", "shortest path")
    ],
    ("확률·통계", "대학"): [
        ("표본분포", "sampling distribution"), ("대수의 법칙", "law of large numbers"), ("모멘트", "moment"), ("적률생성함수", "moment-generating function"),
        ("결합분포", "joint distribution"), ("주변분포", "marginal distribution"), ("조건부분포", "conditional distribution"),
        ("독립확률변수", "independent random variables"), ("다항분포", "multinomial distribution"), ("기하분포", "geometric distribution"),
        ("음이항분포", "negative binomial distribution"), ("초기하분포", "hypergeometric distribution"), ("지수분포", "exponential distribution"),
        ("감마분포", "gamma distribution"), ("카이제곱분포", "chi-square distribution"), ("t분포", "Student's t-distribution"), ("F분포", "F-distribution"),
        ("점추정", "point estimation"), ("최대가능도추정", "maximum likelihood estimation"), ("불편추정량", "unbiased estimator"),
        ("가설검정", "hypothesis testing"), ("귀무가설", "null hypothesis"), ("대립가설", "alternative hypothesis"), ("유의수준", "significance level"),
        ("p값", "p-value"), ("1종 오류", "type I error"), ("2종 오류", "type II error"), ("검정력", "statistical power"),
        ("단순선형회귀", "simple linear regression"), ("최소제곱추정", "least squares estimation"), ("결정계수", "coefficient of determination")
    ],
    ("추상대수", "대학"): [
        ("아벨군", "abelian group"), ("순환군", "cyclic group"), ("부분군", "subgroup"), ("잉여류", "coset"), ("정규부분군", "normal subgroup"),
        ("몫군", "quotient group"), ("라그랑주 정리", "Lagrange's theorem"), ("군의 작용", "group action"), ("치환군", "permutation group"),
        ("아이디얼", "ideal"), ("주아이디얼", "principal ideal"), ("몫환", "quotient ring"), ("정역", "integral domain"),
        ("유클리드 정역", "Euclidean domain"), ("주아이디얼 정역", "principal ideal domain"), ("유일인수분해정역", "unique factorization domain"),
        ("다항식환", "polynomial ring"), ("체의 확대", "field extension"), ("갈루아 군", "Galois group")
    ],
    ("수치해석", "대학"): [
        ("절단오차", "truncation error"), ("반올림오차", "round-off error"), ("조건수", "condition number"), ("이분법", "bisection method"),
        ("할선법", "secant method"), ("고정점 반복법", "fixed-point iteration"), ("보간", "interpolation"), ("라그랑주 보간", "Lagrange interpolation"),
        ("뉴턴 보간", "Newton interpolation"), ("스플라인", "spline"), ("수치미분", "numerical differentiation"), ("수치적분", "numerical integration"),
        ("사다리꼴 공식", "trapezoidal rule"), ("심프슨 공식", "Simpson's rule"), ("룬게-쿠타 방법", "Runge-Kutta method"),
        ("거듭제곱법", "power method"), ("수치선형대수", "numerical linear algebra")
    ],
    ("위상수학", "대학"): [
        ("위상공간", "topological space"), ("위상", "topology"), ("기저 위상", "basis for a topology"), ("연속사상", "continuous map"),
        ("위상동형", "homeomorphism"), ("연결성", "connectedness"), ("경로연결", "path connectedness"), ("콤팩트성", "compactness"),
        ("곱위상", "product topology"), ("몫위상", "quotient topology"), ("하우스도르프 공간", "Hausdorff space")
    ],
}

CATEGORY_EXPLANATIONS = {
    "수와 연산": "수의 성질과 연산 규칙을 다루는 기본 개념이다.",
    "대수": "문자와 식, 방정식, 다항식의 구조와 연산을 다루는 개념이다.",
    "함수": "입력과 출력 사이의 대응과 그래프의 성질을 다루는 개념이다.",
    "삼각함수": "각과 주기적 현상을 사인·코사인 등의 함수로 표현하는 개념이다.",
    "수열": "순서에 따라 나열된 수와 그 합, 극한을 다루는 개념이다.",
    "기하": "점·선·도형·공간의 위치와 크기, 관계를 다루는 개념이다.",
    "확률·통계": "불확실성과 자료의 분포, 추정과 검정을 수학적으로 다루는 개념이다.",
    "집합·논리": "수학적 대상을 집합으로 묶고 명제와 논리 관계를 엄밀하게 다루는 개념이다.",
    "미적분": "변화율과 누적량을 극한, 미분, 적분으로 연구하는 개념이다.",
    "다변수미적분": "둘 이상의 변수를 가진 함수의 변화와 누적량을 다루는 개념이다.",
    "벡터해석": "벡터장과 미분·적분을 결합해 공간의 흐름과 회전을 다루는 개념이다.",
    "선형대수": "벡터공간, 행렬, 선형변환의 구조를 연구하는 개념이다.",
    "미분방정식": "함수와 그 변화율 사이의 관계로 자연·공학 현상을 모델링하는 개념이다.",
    "해석학": "극한, 연속, 수렴, 미분과 적분을 엄밀한 논리로 연구하는 분야의 개념이다.",
    "복소해석": "복소변수 함수의 미분과 적분, 해석성을 연구하는 개념이다.",
    "이산수학": "유한하거나 셀 수 있는 구조와 논리, 조합, 그래프를 다루는 개념이다.",
    "추상대수": "군·환·체처럼 연산이 가진 공통 구조를 추상적으로 연구하는 개념이다.",
    "수치해석": "정확한 해 대신 계산 가능한 근사값을 안정적으로 얻는 알고리즘을 연구하는 개념이다.",
    "위상수학": "길이와 각도보다 연속적인 변형에서 보존되는 공간의 구조를 연구하는 개념이다.",
}

SIM_MAP = {
    "일차함수": "linear_function", "기울기": "linear_function", "이차함수": "quadratic", "포물선": "quadratic",
    "삼각함수": "unit_circle", "사인": "unit_circle", "코사인": "unit_circle", "탄젠트": "unit_circle", "단위원": "unit_circle",
    "벡터": "vectors", "벡터의 내적": "vectors", "평면벡터": "vectors", "벡터의 덧셈": "vectors",
    "미분계수": "derivative", "도함수": "derivative", "접선": "derivative", "미분법": "derivative",
    "정적분": "integral", "리만합": "integral", "리만적분": "integral", "부정적분": "integral",
    "행렬": "matrix", "선형변환": "matrix", "고유값": "matrix", "고유벡터": "matrix",
    "수열": "sequence", "등차수열": "sequence", "등비수열": "sequence", "수열의 극한": "sequence",
}


def _slug(text: str) -> str:
    import hashlib
    return "math-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:14]


def _sources(level: str) -> List[str]:
    return SOURCE_UNIV[:] if level == "대학" else SOURCE_SCHOOL[:]


def _build_entry(ko: str, en: str, summary: str, formula: str, related: List[str], category: str, level: str) -> dict:
    detail = summary + " " + CATEGORY_EXPLANATIONS.get(category, "수학에서 중요한 개념이다.")
    if level == "중등":
        detail += " 중학교 단계에서는 구체적인 수나 도형, 그래프 예시와 연결해 이해하는 것이 좋다."
    elif level == "고등":
        detail += " 고등학교 단계에서는 식의 변형뿐 아니라 그래프·조건·적용 범위를 함께 확인해야 한다."
    else:
        detail += " 대학 단계에서는 정의의 가정과 정리의 조건, 다른 구조와의 연결을 함께 살피는 것이 중요하다."
    return {
        "id": _slug(ko + "|" + en),
        "name_ko": ko,
        "name_en": en,
        "aliases": [],
        "subject": "수학",
        "category": category,
        "level": level,
        "summary": summary,
        "detail": detail,
        "formula": formula,
        "unit": "",
        "example": "",
        "caution": "정의와 정리의 적용 조건을 확인하고, 기호가 어떤 대상을 뜻하는지 먼저 확인한다.",
        "related": related,
        "sources": _sources(level),
        "simulator": SIM_MAP.get(ko, ""),
        "search_text": " ".join([ko, en, category, level, summary, formula] + related),
    }


def generate_math_terms() -> List[dict]:
    result: List[dict] = []
    seen = set()
    for ko, en, summary, formula, related, category, level in CORE:
        if ko in seen:
            continue
        seen.add(ko)
        result.append(_build_entry(ko, en, summary, formula, related, category, level))

    for (category, level), pairs in BANKS.items():
        for ko, en in pairs:
            if ko in seen:
                continue
            seen.add(ko)
            summary = f"{ko}({en})는 {CATEGORY_EXPLANATIONS.get(category, '수학에서 사용되는 개념이다.')}"
            # Remove the duplicated '개념이다.' cadence in generated text.
            summary = summary.replace("개념이다.는", "개념은")
            related = []
            result.append(_build_entry(ko, en, summary, "", related, category, level))

    return result


if __name__ == "__main__":
    terms = generate_math_terms()
    print(len(terms))
    for level in ("중등", "고등", "대학"):
        print(level, sum(1 for t in terms if t["level"] == level))
