"""Deterministic educational immune network, NOT a calibrated patient model.

Burdens, activities and impairments are dimensionless. All coefficients are
invented teaching values. A model hour has no validated clinical conversion.
RK4 accuracy concerns only these equations; see BIOLOGY_MODEL.md.
"""
from dataclasses import dataclass, field
from numbers import Real
import math

@dataclass(frozen=True)
class Organ:
    key: str
    name: str
    x: float
    y: float
    role: str

ORGANS = (
    Organ('brain','뇌',.50,.10,'신경 조절 · 기능 손상 지표'),
    Organ('skin','피부',.24,.46,'외부 장벽 · 감염 유입'),
    Organ('lung','폐',.44,.29,'호흡 · 산소 공급 지원'),
    Organ('heart','심장',.56,.33,'혈액 순환'),
    Organ('liver','간',.43,.42,'대사 · 혈중 물질 처리'),
    Organ('stomach','위',.57,.43,'소화'),
    Organ('kidney','신장',.61,.50,'노폐물 · 수분 균형'),
    Organ('intestine','장',.50,.56,'흡수 · 점막 장벽'),
    Organ('nodes','림프절',.64,.23,'항원 전달 · 적응 면역 활성'),
    Organ('spleen','비장',.64,.40,'혈액 내 면역 감시'),
    Organ('marrow','골수',.36,.70,'면역세포 공급'),
    Organ('thymus','흉선',.50,.25,'T세포 성숙 기관 · 모형에서는 면역 예비력'),
    Organ('pancreas','췌장',.50,.47,'소화 · 대사 조절'),
    Organ('gallbladder','담낭',.39,.46,'담즙 저장'),
    Organ('bladder','방광',.50,.65,'소변 저장'),
    Organ('muscle','근육',.65,.76,'운동 · 대사 예비력'),
    Organ('vessels','혈관',.70,.51,'모형 내 감염 전달 연결'),
    Organ('reproductive','생식기관',.50,.72,'생식기 조직 구획'),
)
CELLS = (
    ('neutrophil','호중구','빠른 선천 면역 · 세균 제거'),
    ('monocyte','단핵구','조직 대식세포 반응의 공급'),
    ('macrophage','대식세포','포식 · 염증 신호 · 잔해 처리'),
    ('dendritic','수지상세포','항원 제시 · 적응 면역 연결'),
    ('nk','NK세포','바이러스 감염세포에 대한 선천 반응'),
    ('helper','보조 T세포','B세포와 세포독성 반응 지원'),
    ('killer','세포독성 T세포','바이러스 감염세포 제거'),
    ('bcell','B세포','항원 반응 · 형질세포 활동 유도'),
    ('eosinophil','호산구','기생충·알레르기 관련 · 여기서는 알레르기 신호만'),
    ('basophil','호염기구','혈중 알레르기 신호 활동'),
    ('plasma','형질세포','항체 분비를 대표하는 별도 활동 구획'),
    ('mast','비만세포','조직의 알레르기 신호 활동'),
)
N = len(ORGANS)
ORGAN_INDEX = {o.key:i for i,o in enumerate(ORGANS)}
CELL_INDEX = {key:4*N+j for j,(key,_,_) in enumerate(CELLS)}
CYTOKINE_INDEX = 4*N+len(CELLS)
FEVER_INDEX = CYTOKINE_INDEX+1
STATE_SIZE = FEVER_INDEX+1
DT = 1/120
SOURCES = (
    ('면역세포 개요 · NIAID', 'https://www.niaid.nih.gov/research/immune-system-overview'),
    ('전신 면역 반응과 장기 손상 · NIGMS', 'https://www.nigms.nih.gov/education/fact-sheets/Pages/sepsis'),
    ('항생제는 바이러스에 작용하지 않음 · CDC', 'https://www.cdc.gov/antibiotic-use/about/'),
    ('사이토카인 폭풍의 개념 · NCI', 'https://www.cancer.gov/publications/dictionaries/cancer-terms/def/cytokine-storm'),
)

@dataclass(frozen=True)
class OrganParameters:
    """Invented differences between equal-volume teaching compartments."""
    bacterial_growth: float
    viral_growth: float
    local_clearance: float
    injury: float
    repair: float
    exchange: float

# NOT estimates of actual organ rates or clinical susceptibility rankings.
_PARAMETER_ROWS = (
    ('brain',.65,.75,.85,1.25,.65,.30),
    ('skin',1.00,.75,1.15,.80,1.30,.45),
    ('lung',1.10,1.20,1.00,1.10,1.00,1.20),
    ('heart',.75,.80,1.00,1.20,.75,1.35),
    ('liver',.90,1.00,1.35,.90,1.30,1.25),
    ('stomach',.80,.65,1.15,.75,1.20,.55),
    ('kidney',.95,.80,1.00,1.15,.90,1.20),
    ('intestine',1.15,1.00,1.10,.90,1.25,.85),
    ('nodes',.70,.70,1.35,.85,1.10,.65),
    ('spleen',.75,.75,1.45,.90,1.10,1.10),
    ('marrow',.80,.80,.90,1.00,.90,.75),
    ('thymus',.70,.75,1.00,.85,.85,.45),
    ('pancreas',.85,.85,1.00,1.05,.85,.75),
    ('gallbladder',.95,.65,1.05,.80,1.00,.45),
    ('bladder',1.10,.60,.90,.85,1.10,.50),
    ('muscle',.80,.70,1.00,.70,1.15,.75),
    ('vessels',.70,.70,1.15,1.00,1.00,1.00),
    ('reproductive',.90,.90,1.00,.90,1.00,.65),
)
ORGAN_PARAMETERS = {key:OrganParameters(*v) for key,*v in _PARAMETER_ROWS}
# Mixing abstraction: equal volumes, undirected edges, no anatomical flow claim.
TRANSPORT_EDGES = tuple((ORGAN_INDEX[o.key],ORGAN_INDEX['vessels'],ORGAN_PARAMETERS[o.key].exchange)
                        for o in ORGANS if o.key!='vessels') + tuple(
    (ORGAN_INDEX[key],ORGAN_INDEX['nodes'],.35) for key in ('skin','lung','intestine'))

def _bounded(value,lo,hi,label):
    if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError(f'{label} must be a finite number in [{lo}, {hi}]')

@dataclass(frozen=True)
class Profile:
    """Scenario metadata and explicitly fictional background condition switches.

    Age/sex are recorded only. They do not determine a medical risk multiplier.
    Disease flags select invented teaching variants, not patient predictions.
    """
    age_years: float = 30
    sex: str = 'unspecified'
    diabetes: bool = False
    immunosuppression: bool = False
    chronic_lung: bool = False
    chronic_kidney: bool = False

    def validate(self):
        _bounded(self.age_years,0,120,'age_years')
        if self.sex not in ('unspecified','female','male'):
            raise ValueError('Unknown sex metadata')
        for name in ('diabetes','immunosuppression','chronic_lung','chronic_kidney'):
            if not isinstance(getattr(self,name),bool):
                raise ValueError(f'{name} must be boolean')

    def modifiers(self):
        """Full transparent coefficient mapping, all deliberately uncalibrated."""
        return {'immune_activity':.55 if self.immunosuppression else 1.0,
                'all_repair':.75 if self.diabetes else 1.0,
                'lung_repair':.8 if self.chronic_lung else 1.0,
                'kidney_repair':.8 if self.chronic_kidney else 1.0,
                'lung_baseline_damage':.25 if self.chronic_lung else 0.0,
                'kidney_baseline_damage':.25 if self.chronic_kidney else 0.0}

@dataclass
class Conditions:
    growth_b: float = .8
    growth_v: float = .7
    spread: float = .08
    resistance: float = 0
    immune: float = 1
    allergy: float = 0
    antibiotic: float = 0
    antiviral: float = 0
    support: float = 0
    oxygen: float = 0
    anti_inflammatory: float = 0
    cytokine_feedback: float = .4
    cell_levels: dict = field(default_factory=lambda:{key:1.0 for key,_,_ in CELLS})

    def validate(self):
        bounds={'growth_b':(0,2),'growth_v':(0,2),'spread':(0,.3),'resistance':(0,1),
                'immune':(0,2),'allergy':(0,1),'antibiotic':(0,1),'antiviral':(0,1),
                'support':(0,1),'oxygen':(0,1),'anti_inflammatory':(0,1),
                'cytokine_feedback':(0,1)}
        for name,(lo,hi) in bounds.items(): _bounded(getattr(self,name),lo,hi,name)
        if not isinstance(self.cell_levels,dict) or set(self.cell_levels)!=set(CELL_INDEX):
            raise ValueError('Immune cell groups must be complete')
        for key,value in self.cell_levels.items(): _bounded(value,0,3,key)

class BiologyEngine:
    def __init__(self,conditions=None,organ='lung',bacteria=.18,virus=0,*,dt=DT,profile=None):
        if conditions is not None and not isinstance(conditions,Conditions): raise ValueError('conditions must be Conditions')
        if profile is not None and not isinstance(profile,Profile): raise ValueError('profile must be Profile')
        _bounded(dt,DT/64,DT,'dt')
        self.conditions=conditions if conditions is not None else Conditions()
        self.conditions.validate()
        self.profile=profile if profile is not None else Profile()
        self.profile.validate()
        self.profile_modifiers=self.profile.modifiers()
        self._baseline_damage=[0.0]*N
        self._baseline_damage[ORGAN_INDEX['lung']]=self.profile_modifiers['lung_baseline_damage']
        self._baseline_damage[ORGAN_INDEX['kidney']]=self.profile_modifiers['kidney_baseline_damage']
        self.dt=float(dt)
        self.state=[0.0]*STATE_SIZE
        for i,damage in enumerate(self._baseline_damage): self.state[4*i+2]=damage
        self.steps=0
        self.events=[]
        self.ended=False
        self.expose(organ,bacteria,virus)

    @property
    def time(self): return self.steps*self.dt

    def expose(self,organ,bacteria=0,virus=0):
        if not isinstance(organ,str) or organ not in ORGAN_INDEX: raise ValueError('Unknown organ')
        _bounded(bacteria,0,1,'bacteria'); _bounded(virus,0,1,'virus')
        if self.ended: raise ValueError('Reset the ended model before exposure')
        i=ORGAN_INDEX[organ]
        added_b=min(1-self.state[4*i],bacteria)
        added_v=min(1-self.state[4*i+1],virus)
        self.state[4*i]+=added_b
        self.state[4*i+1]+=added_v
        if added_b or added_v:
            self.events.append((self.time,f'{ORGANS[i].name}: 세균 {added_b:.2f}, 바이러스 {added_v:.2f} 모형 부담 유입'))

    def transport_derivative(self,y):
        """Conservative transfer only: each pathogen sum is zero to roundoff."""
        dy=[0.0]*len(y)
        for i,j,weight in TRANSPORT_EDGES:
            for offset in (0,1):
                flux=self.conditions.spread*weight*(y[4*j+offset]-y[4*i+offset])
                dy[4*i+offset]+=flux
                dy[4*j+offset]-=flux
        return dy

    def _derivative(self,y):
        c=self.conditions
        dy=self.transport_derivative(y)
        B=sum(y[0:4*N:4])/N; V=sum(y[1:4*N:4])/N
        cytokine,fever=y[CYTOKINE_INDEX],y[FEVER_INDEX]
        antigen=min(1,(B+V)*5)
        node_damage=y[4*ORGAN_INDEX['nodes']+2]
        marrow_damage=y[4*ORGAN_INDEX['marrow']+2]
        thymus_damage=y[4*ORGAN_INDEX['thymus']+2]
        W={key:y[index]*c.cell_levels[key]*c.immune*self.profile_modifiers['immune_activity']
           for key,index in CELL_INDEX.items()}
        signals={'neutrophil':min(1,6*B),'monocyte':antigen,
                 'macrophage':min(1,antigen+.3*W['monocyte']),
                 'dendritic':antigen,'nk':min(1,6*V),
                 'helper':min(1,W['dendritic'])*(1-node_damage)*(1-.5*thymus_damage),
                 'killer':min(1,6*V)*min(1,W['helper']),
                 'bcell':antigen*min(1,W['helper']),'plasma':min(1,W['bcell']),
                 'eosinophil':c.allergy,'basophil':c.allergy,'mast':c.allergy}
        for key,index in CELL_INDEX.items():
            speed=.25 if key in ('helper','killer','bcell','plasma') else 1.2
            dy[index]=speed*(signals[key]*(1-.8*marrow_damage)-y[index])
        # Relative systemic signalling, NOT a measured cytokine concentration.
        mean_f=sum(y[3:4*N:4])/N
        peak_f=max(y[3:4*N:4])
        drive=min(1,.7*mean_f+.3*peak_f+.08*min(1,W['macrophage'])*antigen)
        resolution=.25+.20*c.support+.10*c.anti_inflammatory
        dy[CYTOKINE_INDEX]=.8*drive*(1-cytokine)+1.8*c.cytokine_feedback*cytokine**2*(1-cytokine)-resolution*cytokine
        # Fever response index lags the signalling state; it is never degrees C.
        dy[FEVER_INDEX]=.6*(cytokine-fever)
        antib=c.antibiotic*(1-c.resistance)
        for i,o in enumerate(ORGANS):
            b,v,d,f=y[4*i:4*i+4]; p=ORGAN_PARAMETERS[o.key]
            kb=p.local_clearance*(.16+.9*W['neutrophil']+.5*W['macrophage']+.6*W['plasma'])+2*antib
            kv=p.local_clearance*(.1+.6*W['nk']+.9*W['killer']+.4*W['plasma'])+1.8*c.antiviral
            dy[4*i]+=c.growth_b*p.bacterial_growth*b*(1-b)-kb*b
            # Effective viral pressure, not resolved infected-cell kinetics.
            dy[4*i+1]+=c.growth_v*p.viral_growth*v*(1-v)*(1-d)-kv*v
            allergy_signal=.06*W['eosinophil']+.05*W['basophil']+.09*W['mast']
            stimulus=min(1,1.2*(b+v)+allergy_signal+.35*c.cytokine_feedback*cytokine)
            dy[4*i+3]=.8*(stimulus-f)-.7*c.anti_inflammatory*f
            protective=c.support+(.7*c.oxygen if o.key=='lung' else .1*c.oxygen)
            injury=p.injury*(.16*(b+v)+.1*f*f+.08*cytokine**2)*(1-.25*protective)
            organ_repair=self.profile_modifiers.get(o.key+'_repair',1.0)
            repair=p.repair*self.profile_modifiers['all_repair']*organ_repair*(.025+.08*c.support+.035*W['macrophage'])
            dy[4*i+2]=injury*(1-d)-repair*(d-self._baseline_damage[i])
        return dy

    def _validate_state(self):
        if len(self.state)!=STATE_SIZE: raise ValueError('Invalid model state length')
        for value in self.state: _bounded(value,0,1,'model state')

    def advance_steps(self,count):
        if isinstance(count,bool) or not isinstance(count,int) or not 0<=count<=120000: raise ValueError('Step count')
        self.conditions.validate(); self._validate_state()
        dt=self.dt
        for _ in range(count):
            if self.ended: break
            y=self.state
            k1=self._derivative(y)
            k2=self._derivative([a+dt*b/2 for a,b in zip(y,k1)])
            k3=self._derivative([a+dt*b/2 for a,b in zip(y,k2)])
            k4=self._derivative([a+dt*b for a,b in zip(y,k3)])
            result=[a+dt*(b+2*c+2*d+e)/6 for a,b,c,d,e in zip(y,k1,k2,k3,k4)]
            if any(not math.isfinite(v) or v < -1e-10 or v > 1+1e-10 for v in result):
                raise ArithmeticError('Integrator left invariant domain')
            # Roundoff removal only; substantive domain violations raise above.
            self.state=[min(1,max(0,v)) for v in result]
            self.steps+=1
            if self.reserve<.2:
                self.ended=True
                self.events.append((self.time,'가상 기능 예비력 소실: 모형 종료 (실제 사망 예측 아님)'))

    @property
    def reserve(self):
        return 1-max(self.state[4*ORGAN_INDEX[key]+2] for key in ('brain','lung','heart','liver','kidney'))

    def organ_reading(self,key):
        if not isinstance(key,str) or key not in ORGAN_INDEX: raise ValueError('Unknown organ')
        i=ORGAN_INDEX[key]
        b,v,d,f=self.state[4*i:4*i+4]
        return dict(bacteria=b,virus=v,damage=d,inflammation=f,function=1-d)

    def cell_readings(self):
        """Activation [0,1], effective activity [0,6]; never cell counts."""
        c=self.conditions
        return {key:{'activation':self.state[index],'activity':self.state[index]*c.cell_levels[key]*c.immune*self.profile_modifiers['immune_activity']}
                for key,index in CELL_INDEX.items()}

    def snapshot(self):
        r=self.reserve
        cytokine=self.state[CYTOKINE_INDEX]
        return {'time':self.time,'bacteria':sum(self.state[0:4*N:4])/N,
                'virus':sum(self.state[1:4*N:4])/N,'reserve':r,
                'inflammation':sum(self.state[3:4*N:4])/N,
                'cytokine':cytokine,'fever':self.state[FEVER_INDEX],
                'cytokine_status':'모형 과염증 상태' if cytokine>=.6 else '모형 신호 증가' if cytokine>=.25 else '낮은 신호',
                'profile':{'age_years':self.profile.age_years,'sex':self.profile.sex,
                           'modifiers':dict(self.profile_modifiers)},
                'status':'가상 기능 소실' if self.ended else ('높은 모형 부담' if r<.5 else '모형 부담 증가' if r<.8 else '모형 기능 유지')}
