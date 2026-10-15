"""Inspectable, qualitative immune/organ laboratory; no clinical predictions.

The animation is a schematic illustration of aggregate engine states. Displayed
particles are representative marks, never an inferred cell count or a microscopy
image. All time is model time with no validated conversion to disease duration.
"""
from __future__ import annotations

from collections import deque
import csv
import math
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from biology_engine import BiologyEngine, CELLS, Conditions, DT, N, ORGANS, Profile, SOURCES, TRANSPORT_EDGES

BACTERIA = "#F4B766"
VIRUS = "#E887BC"
IMMUNE = "#70C7E8"
FUNCTION = "#71D6AA"
INFLAMMATION = "#F18A7E"
ORGAN_NAMES = {organ.key: organ.name for organ in ORGANS}
ORGAN_KEYS = {organ.name: organ.key for organ in ORGANS}
PRESETS = {
    "세균 · 피부 유입": ("skin", .3, 0, 1, 0),
    "바이러스 · 호흡기 유입": ("lung", 0, .3, 1, 0),
    "혼합 감염 부담": ("lung", .3, .3, 1, 0),
    "낮은 면역 활동": ("lung", .2, .1, .35, 0),
    "알레르기 신호": ("skin", 0, 0, 1, .85),
    "초기 무감염": ("lung", 0, 0, 1, 0),
}


def _mix(a, b, fraction):
    fraction = max(0, min(1, fraction))
    rgb = tuple(round(int(a[i:i+2], 16)*(1-fraction)+int(b[i:i+2], 16)*fraction)
                for i in (1, 3, 5))
    return "#%02x%02x%02x" % rgb


class _ScrollPage(tk.Frame):
    """An independently scrollable notebook page, with no global wheel binds."""
    def __init__(self, master, theme):
        super().__init__(master, bg=theme["surface"])
        self.canvas = tk.Canvas(self, bg=theme["surface"], highlightthickness=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=theme["surface"])
        self.window = self.canvas.create_window(0, 0, anchor="nw", window=self.inner)
        self.inner.bind("<Configure>", self._bounds)
        self.canvas.bind("<Configure>", self._width)
        self.canvas.bind("<MouseWheel>", self._wheel)

    def _bounds(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _width(self, event):
        self.canvas.itemconfigure(self.window, width=max(1, event.width))

    def _wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120), "units")
        return "break"


class BiologySimulator(tk.Frame):
    """MiniSimulator-compatible educational infection/immune laboratory."""
    sim_id = "biology_body"

    def __init__(self, master, theme, fps=30):
        super().__init__(master, bg=theme["surface"])
        self.theme = dict(theme)
        self.theme.setdefault("line", "#384152")
        self.theme.setdefault("accent2", self.theme.get("accent", "#8C9EFF"))
        self.theme.setdefault("muted", "#AAB5C9")
        self.theme.setdefault("accent_soft", self.theme["surface2"])
        self.colors = {"bacteria":theme.get("orange",BACTERIA), "virus":theme.get("pink",VIRUS),
                       "immune":theme.get("cyan",IMMUNE), "function":theme.get("green",FUNCTION),
                       "inflammation":theme.get("danger",INFLAMMATION),
                       "cytokine":theme.get("accent2","#B8B6FF"), "fever":theme.get("orange",BACTERIA)}
        self.fps = 60 if fps >= 60 else 30
        self.running = False
        self.t = 0.0
        self._job = None
        self._last_clock = 0.0
        self._accumulator = 0.0
        self._layout_job = None
        self._columns = -1
        self._selected = "lung"
        self._selected_cell = "neutrophil"
        self._setting_up = True
        self._vars = {}
        self._cell_vars = {}
        self._control_cards = []
        self._cell_cards = []
        self._labels_to_wrap = []
        self._history = deque(maxlen=2400)
        self._last_record = -1.0
        self._events = deque(maxlen=500)
        self._engine_events = 0
        self.engine = BiologyEngine()
        self._build()
        self._setting_up = False
        self.reset()
        self.bind("<Configure>", self._configure)

    def _label(self, master, text="", muted=False, bold=False, size=9, **kwargs):
        bg = kwargs.pop("bg", master.cget("bg"))
        return tk.Label(master, text=text, bg=bg,
                        fg=self.theme["muted"] if muted else self.theme["text"],
                        font=("Malgun Gothic", size, "bold" if bold else "normal"),
                        anchor="w", justify="left", **kwargs)

    def _wrapped(self, master, text, **kwargs):
        label = self._label(master, text, wraplength=700, **kwargs)
        self._labels_to_wrap.append(label)
        return label

    def _button(self, master, text, command, primary=False):
        t = self.theme
        return tk.Button(master, text=text, command=command, relief="flat", bd=0,
                         bg=t["accent"] if primary else t["accent_soft"],
                         fg="white" if primary else t["accent2"],
                         activebackground=t["surface2"], activeforeground=t["accent2"],
                         font=("Malgun Gothic", 9, "bold"), padx=12, pady=7,
                         cursor="hand2", takefocus=True)

    def _build(self):
        t = self.theme
        self._wrapped(self, "생명과학 실험실  ·  면역과 장기 네트워크", bold=True, size=14).pack(fill="x", pady=(0, 6))
        self._wrapped(self, "장기를 선택하고, 감염 부담·면역 활동·지원 개입을 바꾸며 시간에 따른 연결을 관찰하세요.", muted=True).pack(fill="x", pady=(0, 7))
        banner = tk.Frame(self, bg=t["accent_soft"], padx=12, pady=9)
        banner.pack(fill="x", pady=(0, 10))
        self._wrapped(banner, "교육용 가상 모형 · 수치는 상대 지표입니다. 실제 환자의 병세·고통·사망 시각을 계산하지 않습니다. 모형 시간은 임상 시간으로 환산할 수 없습니다.", size=9).pack(fill="x")

        toolbar = tk.Frame(self, bg=t["surface"])
        toolbar.pack(fill="x", pady=(0, 9))
        self.play_btn = self._button(toolbar, "▶ 시작", self.toggle, True)
        self.play_btn.pack(side="left", padx=(0, 5))
        self._button(toolbar, "+ 0.5 모형 h", self.step).pack(side="left", padx=3)
        self._button(toolbar, "↺ 초기화", self.reset).pack(side="left", padx=3)
        self._button(toolbar, "CSV 저장", self.export_csv).pack(side="left", padx=3)
        speed_row = tk.Frame(self, bg=t["surface"])
        speed_row.pack(fill="x", pady=(0, 10))
        self._label(speed_row, "진행 속도").pack(side="left")
        self.speed_var = tk.StringVar(value="4 모형 h / 실제 초")
        self.speed_box = ttk.Combobox(speed_row, state="readonly", width=22,
                                     textvariable=self.speed_var,
                                     values=["0.25 모형 h / 실제 초", "1 모형 h / 실제 초",
                                             "4 모형 h / 실제 초", "12 모형 h / 실제 초"])
        self.speed_box.pack(side="left", padx=9)
        self.time_label = self._label(speed_row, "", bold=True)
        self.time_label.pack(side="left", padx=5)

        self.kpis = tk.Frame(self, bg=t["surface"])
        self.kpis.pack(fill="x", pady=(0, 10))
        self._kpi_cards = []
        self._kpi_values = {}
        for key, title, color in (("reserve", "가상 기능 예비력", self.colors["function"]),
                                  ("bacteria", "평균 세균 부담", self.colors["bacteria"]),
                                  ("virus", "평균 바이러스 부담", self.colors["virus"]),
                                  ("inflammation", "평균 염증 활동", self.colors["inflammation"]),
                                  ("cytokine", "사이토카인 신호", self.colors["cytokine"]),
                                  ("fever", "발열 반응 지표 · ℃ 아님", self.colors["fever"])):
            card = tk.Frame(self.kpis, bg=t["surface2"], padx=12, pady=9)
            self._label(card, title, muted=True, size=8).pack(fill="x")
            value = self._label(card, "0.0 / 100", bold=True, size=14)
            value.configure(fg=color)
            value.pack(fill="x", pady=(3, 0))
            self._kpi_cards.append(card)
            self._kpi_values[key] = value

        self.visuals = tk.Frame(self, bg=t["surface"])
        self.visuals.pack(fill="x")
        self.map_panel = tk.Frame(self.visuals, bg=t["surface2"])
        self._label(self.map_panel, "인체 지도  ·  장기를 눌러 관찰", bold=True).pack(fill="x", padx=12, pady=(10, 0))
        self.canvas = tk.Canvas(self.map_panel, width=340, height=390,
                                bg=t["surface2"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self.redraw())
        self.canvas.bind("<Button-1>", self._map_click)

        self.detail_panel = tk.Frame(self.visuals, bg=t["surface2"])
        detail_header = tk.Frame(self.detail_panel, bg=t["surface2"])
        detail_header.pack(fill="x", padx=12, pady=(10, 2))
        self.organ_var = tk.StringVar(value="폐")
        self.organ_box = ttk.Combobox(detail_header, state="readonly", width=15,
                                     textvariable=self.organ_var, values=list(ORGAN_KEYS))
        self.organ_box.pack(side="left")
        self.organ_box.bind("<<ComboboxSelected>>", self._organ_changed)
        self.organ_label = self._label(detail_header, "", bold=True)
        self.organ_label.pack(side="left", padx=9)
        self.tissue_canvas = tk.Canvas(self.detail_panel, width=560, height=260,
                                       bg=t["surface2"], highlightthickness=0)
        self.tissue_canvas.pack(fill="both", expand=True)
        self.tissue_canvas.bind("<Configure>", lambda _: self.redraw())
        self.organ_metrics = self._wrapped(self.detail_panel, "", size=9)
        self.organ_metrics.pack(fill="x", padx=12, pady=(3, 5))
        self._wrapped(self.detail_panel, "● 세균    ✳ 바이러스    ◉ 면역세포  |  입자는 상태를 설명하는 대표 그림이며 실제 개수·배율이 아닙니다.", muted=True, size=8).pack(fill="x", padx=12, pady=(0, 10))
        self._cell_name_to_key={name:key for key,name,_ in CELLS}
        cell_row=tk.Frame(self.detail_panel,bg=t["surface2"])
        cell_row.pack(fill="x",padx=12,pady=(0,4))
        self._label(cell_row,"세포 도식").pack(side="left",padx=(0,7))
        self.cell_var=tk.StringVar(value=CELLS[0][1])
        self.cell_box=ttk.Combobox(cell_row,textvariable=self.cell_var,state="readonly",width=18,values=list(self._cell_name_to_key))
        self.cell_box.pack(side="left")
        self.cell_box.bind("<<ComboboxSelected>>",self._cell_changed)
        self.cell_focus_label=self._wrapped(self.detail_panel,"",size=8,muted=True)
        self.cell_focus_label.pack(fill="x",padx=12,pady=(0,10))

        self.status_label = self._wrapped(self, "", bold=True, size=10)
        self.status_label.pack(fill="x", pady=(10, 3))
        self.cytokine_label = self._wrapped(self,"",size=9)
        self.cytokine_label.pack(fill="x",pady=(0,3))
        self.profile_summary = self._wrapped(self,"",size=8,muted=True)
        self.profile_summary.pack(fill="x",pady=(0,3))
        self._wrapped(self, "통증: 실제 산출 불가  ·  사망까지 남은 시간: 실제 산출 불가  ·  조직 손상·염증 지표로 모형의 변화를 관찰합니다.", muted=True, size=8).pack(fill="x", pady=(0, 10))

        style = ttk.Style(self)
        prefix = f"Bio{id(self)}"
        style.configure(prefix+".TNotebook", background=t["surface"], borderwidth=0)
        style.configure(prefix+".TNotebook.Tab", padding=(8, 8))
        self.notebook = ttk.Notebook(self, height=330, style=prefix+".TNotebook")
        self.notebook.pack(fill="both", expand=True)
        self.conditions_page = _ScrollPage(self.notebook, t)
        self.profile_page = _ScrollPage(self.notebook,t)
        self.cells_page = _ScrollPage(self.notebook, t)
        self.organs_page = _ScrollPage(self.notebook, t)
        self.graph_page = tk.Frame(self.notebook, bg=t["surface"])
        self.notes_page = _ScrollPage(self.notebook, t)
        for frame, name in ((self.conditions_page, "조건 · 개입"), (self.profile_page,"숙주 조건"),
                            (self.cells_page, "면역세포"), (self.organs_page, "장기 상태"),
                            (self.graph_page, "그래프"), (self.notes_page, "해석 · 출처")):
            self.notebook.add(frame, text=name)
        self._build_conditions()
        self._build_profile()
        self._build_cells()
        self._build_organs()
        self._build_graph()
        self._build_notes()

    def _slider(self, master, key, title, lo, hi, default, note, collection, live=True):
        t = self.theme
        card = tk.Frame(master, bg=t["surface2"], padx=11, pady=8)
        self._wrapped(card, title, bold=True).pack(fill="x")
        var = tk.DoubleVar(value=default)
        self._vars[key] = var
        out = self._label(card, "", size=9)
        out.configure(fg=t["accent2"])
        out.pack(fill="x", pady=(2, 0))
        scale=ttk.Scale(card, variable=var, from_=lo, to=hi, orient="horizontal")
        scale.pack(fill="x", pady=4)
        scale.bind("<ButtonRelease-1>",lambda _:self._add_event(f"조건 변경: {title} = {var.get():.2f}"))
        self._wrapped(card, note, muted=True, size=8).pack(fill="x")
        def changed(*_):
            out.configure(text=f"{var.get():.2f}  상대 계수")
            if live and not self._setting_up:
                self._sync_conditions()
        var.trace_add("write", changed)
        changed()
        collection.append(card)
        return card

    def _build_conditions(self):
        p, t = self.conditions_page.inner, self.theme
        self._wrapped(p, "초기 감염 설정은 ‘초기화’에 적용됩니다. 아래 개입과 면역 활동은 실행 중에도 적용됩니다. 수치는 용량·개수·검사 수치가 아닙니다.", muted=True, size=8).pack(fill="x", padx=8, pady=9)
        presets = tk.Frame(p, bg=t["surface"])
        presets.pack(fill="x", padx=8, pady=(0, 8))
        self.preset_var = tk.StringVar(value=next(iter(PRESETS)))
        ttk.Combobox(presets, state="readonly", width=24, values=list(PRESETS),
                     textvariable=self.preset_var).pack(side="left", padx=(0, 8))
        self._button(presets, "새 실험 적용", lambda:self.apply_preset(self.preset_var.get())).pack(side="left")
        support = tk.Frame(p, bg=t["surface"])
        support.pack(fill="x", padx=8, pady=(0, 8))
        self.support_btn = self._button(support, "지원 개입 묶음 적용", self.toggle_support)
        self.support_btn.pack(side="left")
        self._wrapped(support, "지원 0.75 · 산소 0.50의 가상 계수 묶음", muted=True, size=8).pack(side="left", padx=8)
        entry = tk.Frame(p, bg=t["surface"])
        entry.pack(fill="x", padx=8, pady=(0, 7))
        self._label(entry, "유입 장기").pack(side="left")
        self.entry_organ_var = tk.StringVar(value="폐")
        ttk.Combobox(entry, state="readonly", width=16, textvariable=self.entry_organ_var,
                     values=list(ORGAN_KEYS)).pack(side="left", padx=8)
        self._button(entry, "현재 장기에 추가 유입", self.expose).pack(side="left", padx=4)
        self.controls_grid = tk.Frame(p, bg=t["surface"])
        self.controls_grid.pack(fill="x", padx=5)
        fields = (
            ("initial_bacteria", "초기 / 추가 세균 부담", 0, 1, .18, "활성 부담의 상대 크기 · 0~1", False),
            ("initial_virus", "초기 / 추가 바이러스 부담", 0, 1, 0, "감염 부담의 상대 크기 · 0~1", False),
            ("growth_b", "세균 증식 계수", 0, 2, .8, "정해진 로지스틱 증식식의 계수", True),
            ("growth_v", "바이러스 증식 계수", 0, 2, .7, "건강한 조직 비율에 따라 제한됨", True),
            ("spread", "구획 사이 전달", 0, .3, .08, "혈관·림프절에 연결한 가상 혼합 그래프", True),
            ("immune", "전체 면역 활동 배율", 0, 2, 1, "면역능 검사 수치와 대응하지 않음", True),
            ("antibiotic", "항생제 효과 모형", 0, 1, 0, "세균 제거 항에만 작용 · 처방·용량 아님", True),
            ("resistance", "세균 내성 계수", 0, 1, 0, "1이면 모형의 항생제 효과가 사라짐", True),
            ("antiviral", "항바이러스 효과 모형", 0, 1, 0, "바이러스 제거 항의 추상적인 효과", True),
            ("support", "병원 지원 개입 모형", 0, 1, 0, "조직 손상 감소와 회복 항에 작용", True),
            ("oxygen", "산소 지원 모형", 0, 1, 0, "폐 구획의 손상 항 감소에 더 크게 작용", True),
            ("anti_inflammatory", "항염증 효과 모형", 0, 1, 0, "염증 신호 감소 항 · 실제 약물 재현 아님", True),
            ("allergy", "알레르기 신호", 0, 1, 0, "호산구·호염기구 활동 구획에 연결", True),
            ("cytokine_feedback", "염증 신호 되먹임", 0, 1, .4, "사이토카인·발열 반응 연결의 가상 계수", True),
        )
        for key, title, lo, hi, default, note, live in fields:
            self._slider(self.controls_grid, key, title, lo, hi, default, note, self._control_cards, live)

    def _build_profile(self):
        p,t=self.profile_page.inner,self.theme
        self._wrapped(p,"숙주 조건 · 초기화 또는 ‘새 실험’에 적용",bold=True,size=11).pack(fill="x",padx=12,pady=(12,5))
        self._wrapped(p,"연령·성별은 기록용입니다. 기저질환 표시는 교육용 가상 계수만 바꾸며 실제 환자 위험도·치료·예후를 예측하지 않습니다.",muted=True,size=9).pack(fill="x",padx=12,pady=(0,10))
        row=tk.Frame(p,bg=t["surface2"],padx=12,pady=10)
        row.pack(fill="x",padx=8,pady=4)
        self._label(row,"나이 · 기록용").pack(side="left")
        self.age_var=tk.StringVar(value="30")
        ttk.Spinbox(row,from_=0,to=120,increment=1,textvariable=self.age_var,width=7).pack(side="left",padx=8)
        self._label(row,"성별 · 기록용").pack(side="left",padx=(8,0))
        self.sex_var=tk.StringVar(value="미지정")
        ttk.Combobox(row,textvariable=self.sex_var,state="readonly",width=8,values=("미지정","여성","남성")).pack(side="left",padx=8)
        self.profile_flags={}
        for key,name,description in (("diabetes","당뇨병 조건","모형의 조직 회복 계수 변경"),
                                      ("immunosuppression","면역 억제 조건","모형의 면역 활동 예비 계수 변경"),
                                      ("chronic_lung","만성 폐질환 조건","폐 구획의 가상 손상·회복 계수 변경"),
                                      ("chronic_kidney","만성 신장질환 조건","신장 구획의 가상 손상·회복 계수 변경")):
            card=tk.Frame(p,bg=t["surface2"],padx=12,pady=8)
            card.pack(fill="x",padx=8,pady=4)
            var=tk.BooleanVar(value=False)
            self.profile_flags[key]=var
            tk.Checkbutton(card,text=name,variable=var,bg=t["surface2"],fg=t["text"],
                           activebackground=t["surface2"],activeforeground=t["text"],selectcolor=t["surface"],
                           font=("Malgun Gothic",10,"bold"),anchor="w").pack(fill="x")
            self._wrapped(card,description+" · 실제 질병의 정량 재현 아님",size=8,muted=True).pack(fill="x")
        self._button(p,"이 조건으로 새 실험",self.reset,True).pack(anchor="w",padx=12,pady=10)
        self._wrapped(p,"사이토카인·발열: 면역과 조직 염증에서 유도되는 가상 신호입니다. ‘모형 과염증 상태’는 실제 사이토카인 폭풍 진단이 아니며 발열 지표를 체온 ℃로 환산하지 않습니다.",size=9,muted=True).pack(fill="x",padx=12,pady=(0,12))

    def _make_profile(self):
        try:
            age=float(self.age_var.get())
            if not math.isfinite(age) or not 0<=age<=120:
                raise ValueError
        except ValueError:
            raise ValueError("나이는 0~120 범위의 숫자로 입력하세요.") from None
        return Profile(age_years=age,sex={"미지정":"unspecified","여성":"female","남성":"male"}[self.sex_var.get()],
                       **{key:var.get() for key,var in self.profile_flags.items()})

    def _build_cells(self):
        p = self.cells_page.inner
        self._wrapped(p, f"{len(CELLS)}개의 면역 활동 구획 · 배율 0~3. 성숙·신호 전달을 단순화했습니다. 백혈구 아형 전체나 실제 세포 수를 재현한 모형은 아닙니다.", muted=True, size=8).pack(fill="x", padx=8, pady=9)
        self.cell_grid = tk.Frame(p, bg=self.theme["surface"])
        self.cell_grid.pack(fill="x", padx=5)
        self.cell_activity_labels = {}
        for key, name, role in CELLS:
            card = self._slider(self.cell_grid, "cell_"+key, name, 0, 3, 1, role,
                                self._cell_cards, live=False)
            var = self._vars["cell_"+key]
            self._cell_vars[key] = var
            var.trace_add("write", lambda *_: self._sync_conditions())
            active = self._label(card, "활성 신호 0.0 / 100", size=8)
            active.configure(fg=self.colors["immune"])
            active.pack(fill="x", pady=(4, 0))
            self.cell_activity_labels[key] = active

    def _build_organs(self):
        p, t = self.organs_page.inner, self.theme
        self._wrapped(p, "18개 대표 구획의 상태 · 모든 장기·세부 조직을 포함하지 않습니다. 장기별로 가상 증식·손상·회복 계수가 다르며 실제 해부 생리를 재현하지 않습니다. 행을 선택하면 확대 화면이 바뀝니다.", muted=True, size=8).pack(fill="x", padx=8, pady=9)
        columns = ("organ", "function", "bacteria", "virus", "damage", "inflammation")
        self.organ_table = ttk.Treeview(p, columns=columns, show="headings", height=18, selectmode="browse")
        for col, title in zip(columns, ("장기", "기능 지표", "세균 부담", "바이러스 부담", "조직 손상", "염증 활동")):
            self.organ_table.heading(col, text=title)
            self.organ_table.column(col, width=112 if col=="organ" else 92, minwidth=75, anchor="w" if col=="organ" else "center")
        for organ in ORGANS:
            self.organ_table.insert("", "end", iid=organ.key, values=(organ.name, "", "", "", "", ""))
        self.organ_table.pack(fill="x", padx=8, pady=(0, 8))
        hbar = ttk.Scrollbar(p, orient="horizontal", command=self.organ_table.xview)
        self.organ_table.configure(xscrollcommand=hbar.set)
        hbar.pack(fill="x", padx=8)
        self.organ_table.bind("<<TreeviewSelect>>", self._table_selected)

    def _build_graph(self):
        t = self.theme
        self._wrapped(self.graph_page, "상대 지표 / 100 · 녹색 기능 · 주황 세균 · 분홍 바이러스 · 붉은 염증 · 보라 사이토카인 · 점선 발열 (℃ 아님)", size=8, muted=True).pack(fill="x", padx=8, pady=(8, 0))
        self.history_canvas = tk.Canvas(self.graph_page, height=145, bg=t["surface2"], highlightthickness=0)
        self.history_canvas.pack(fill="x", padx=8, pady=6)
        self.history_canvas.bind("<Configure>", lambda _: self._draw_history())
        self.log = tk.Text(self.graph_page, height=5, bg=t["surface2"], fg=t["text"],
                           relief="flat", wrap="word", font=("Malgun Gothic", 8),
                           state="disabled", padx=8, pady=5)
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _build_notes(self):
        p = self.notes_page.inner
        notes = (
            ("모형의 범위", f"세균·바이러스의 상대 부담, 조직 손상, 염증 활동을 {N}개 구획에서 계산합니다. {'·'.join(name for _,name,_ in CELLS)}를 {len(CELLS)}개 활동 구획으로 표현합니다. 아형 전체, 분자 신호와 모든 장기의 해부 생리를 포함하지 않습니다."),
            ("해부학 그림을 읽는 방법", "지도는 장기 선택을 돕는 도식입니다. 기관의 모양·위치·크기를 단순화했고 피부·골수·근육·혈관은 대표 위치로 나타냅니다. 확대 화면은 공간적인 감염 확산을 계산하는 현미경 영상이 아닙니다."),
            ("시간과 수치 정확도", "고정 간격 RK4 적분으로 명시된 미분방정식을 풉니다. 계산 간격은 1/120 모형 시간입니다. 수치 적분의 정확도와 생물학적 정확도는 다릅니다. 계수는 환자·병원체·의약품 자료에 맞춰 검증되지 않았습니다. 배속은 모형 시간을 빨리 진행하며 실제 질병 기간을 뜻하지 않습니다."),
            ("상태와 종료 기준", "가상 기능 예비력은 뇌·폐·심장·간·신장 구획 중 가장 큰 손상의 보수입니다. 예비력 20 미만이면 가상 기능 소실로 계산을 멈춥니다. 이 경계는 교육용 가정이며 실제 사망·중환자 기준이 아닙니다. 통증, 실제 심각도, 남은 생존 시간은 이 모형에서 산출할 수 없습니다."),
            ("외부 개입", "항생제는 세균 제거 항에만, 항바이러스는 바이러스 제거 항에 작용합니다. 병원 지원·산소 지원·항염증은 추상적인 계수를 바꿉니다. 특정 약물, 용량, 부작용, 투여 경로, 진료 결과를 재현하지 않습니다."),
            ("숙주와 과염증 신호", "연령·성별은 실험 기록에만 사용하며 임상 위험도 차이를 적용하지 않습니다. 당뇨병·면역 억제·만성 폐질환·만성 신장질환은 정량 자료에 맞추지 않은 가상 계수 변경입니다. 사이토카인·발열 지표는 상대적인 신호이며 실제 사이토카인 농도, 체온, 사이토카인 폭풍 진단과 대응하지 않습니다."),
            ("재현 가능한 관찰", "같은 초기 조건과 개입 순서를 사용하면 같은 결과를 얻습니다. 초기화하면 현재 그래프와 기록이 지워지고 새 실험이 시작됩니다. CSV에는 모형 시간과 상대 지표, 구획별 상태, 개입 계수를 기록합니다. 출처는 일반 면역 개념의 근거이며 이 계산식의 임상 검증 근거가 아닙니다."),
        )
        for title, body in notes:
            self._wrapped(p, title, bold=True, size=10).pack(fill="x", padx=12, pady=(12, 4))
            self._wrapped(p, body, muted=True, size=9).pack(fill="x", padx=12)
        for title, url in SOURCES:
            button = self._button(p, title+" ↗", lambda url=url: webbrowser.open(url))
            button.pack(anchor="w", padx=12, pady=7)

    def _configure(self, event):
        if event.widget is not self or self._layout_job is not None:
            return
        self._layout_job = self.after_idle(self._layout)

    def _layout(self):
        self._layout_job = None
        width = max(1, self.winfo_width())
        cols = 3 if width >= 1000 else 2 if width >= 580 else 1
        if cols != self._columns:
            self._columns = cols
            for parent, cards in ((self.controls_grid, self._control_cards), (self.cell_grid, self._cell_cards)):
                for i in range(3):
                    parent.grid_columnconfigure(i, weight=1 if i < cols else 0, uniform="bio" if i<cols else "", minsize=0)
                for i, card in enumerate(cards):
                    card.grid(row=i//cols, column=i%cols, sticky="nsew", padx=4, pady=4)
        kcols = 3 if width >= 820 else 2
        for i in range(6):
            self.kpis.grid_columnconfigure(i, weight=1 if i<kcols else 0, uniform="kpi" if i<kcols else "", minsize=0)
        for i, card in enumerate(self._kpi_cards):
            card.grid(row=i//kcols, column=i%kcols, sticky="nsew", padx=3, pady=3)
        self.visuals.grid_columnconfigure(0, weight=3, uniform="visual")
        self.visuals.grid_columnconfigure(1, weight=5 if width>=760 else 0, uniform="visual")
        if width >= 760:
            self.map_panel.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=(0, 5), pady=0)
            self.detail_panel.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=(5, 0), pady=0)
        else:
            self.map_panel.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 7))
            self.detail_panel.grid(row=1, column=0, columnspan=2, sticky="nsew")
        for label in self._labels_to_wrap:
            if label.winfo_exists():
                label.configure(wraplength=max(120, label.master.winfo_width()-26))
        self.redraw()

    def _sync_conditions(self):
        if self._setting_up or not hasattr(self, "engine"):
            return
        c = self.engine.conditions
        for name in Conditions.__dataclass_fields__:
            if name != "cell_levels" and name in self._vars:
                setattr(c, name, float(self._vars[name].get()))
        c.cell_levels = {key: var.get() for key, var in self._cell_vars.items()}
        c.validate()

    def _add_event(self, text):
        self._events.append((self.engine.time, text))
        self._show_events()

    def _show_events(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", "\n".join(f"[{stamp:7.2f} 모형 h] {text}" for stamp, text in self._events))
        self.log.see("end")
        self.log.configure(state="disabled")

    def reset(self):
        self.stop()
        try:
            profile=self._make_profile()
        except ValueError as exc:
            messagebox.showerror("숙주 조건",str(exc),parent=self)
            return
        self.engine = BiologyEngine(organ=ORGAN_KEYS[self.entry_organ_var.get()],
                                    bacteria=self._vars["initial_bacteria"].get(),
                                    virus=self._vars["initial_virus"].get(),profile=profile)
        self._sync_conditions()
        self.t = 0.0
        self._accumulator = 0.0
        self._history.clear()
        self._events.clear()
        self._engine_events = 0
        self._last_record = -1.0
        self._selected = ORGAN_KEYS[self.entry_organ_var.get()]
        self.organ_var.set(ORGAN_NAMES[self._selected])
        self._record(force=True)
        self._add_event("새 실험 · 상대 지표, 모형 시간 기준")
        self.redraw()

    def apply_preset(self, name):
        self.stop()
        aliases = {"bacteria":"세균 · 피부 유입", "virus":"바이러스 · 호흡기 유입", "mixed":"혼합 감염 부담"}
        name=aliases.get(name,name)
        organ,bacteria,virus,immune,allergy=PRESETS[name]
        self.entry_organ_var.set(ORGAN_NAMES[organ])
        self._vars["initial_bacteria"].set(bacteria)
        self._vars["initial_virus"].set(virus)
        for key in ("antibiotic", "antiviral", "support", "oxygen", "anti_inflammatory", "resistance", "allergy"):
            self._vars[key].set(0)
        self._vars["immune"].set(immune)
        self._vars["allergy"].set(allergy)
        self._vars["growth_b"].set(.8)
        self._vars["growth_v"].set(.7)
        self._vars["spread"].set(.08)
        self._vars["cytokine_feedback"].set(.4)
        for var in self._cell_vars.values():
            var.set(1)
        self.preset_var.set(name)
        self.reset()
        self._add_event("실험 조건: "+name)

    def toggle_support(self):
        enabled = self._vars["support"].get() >= .7 and self._vars["oxygen"].get() >= .45
        self._vars["support"].set(0 if enabled else .75)
        self._vars["oxygen"].set(0 if enabled else .5)
        self._add_event("지원 개입 묶음 해제" if enabled else "지원 개입 묶음 적용 · 가상 계수, 실제 치료 조건 아님")
        self._record(force=True)
        self.redraw()

    def expose(self):
        if self.engine.ended:
            self._add_event("종료된 모형은 초기화한 뒤 추가 유입을 적용하세요")
            return
        organ = self._selected
        self.engine.expose(organ, self._vars["initial_bacteria"].get(), self._vars["initial_virus"].get())
        self._record(force=True)
        self.redraw()

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if not self.running and not self.engine.ended:
            self.running = True
            self.play_btn.configure(text="Ⅱ 일시정지")
            self._last_clock = time.perf_counter()
            self._tick()

    def stop(self):
        self.running = False
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        if hasattr(self, "play_btn"):
            self.play_btn.configure(text="▶ 시작")

    def step(self):
        self.stop()
        self._advance(60)
        self.redraw()

    def step_once(self):
        self.step()

    def _advance(self, steps):
        self._sync_conditions()
        self.engine.advance_steps(steps)
        self.t = self.engine.time
        self._record()
        if self.engine.ended:
            self.stop()

    def _tick(self):
        self._job = None
        if not self.running or not self.winfo_exists():
            return
        now = time.perf_counter()
        elapsed = min(.15, max(0, now-self._last_clock))
        self._last_clock = now
        speed = float(self.speed_var.get().split()[0])
        self._accumulator += elapsed*speed
        steps = min(80, int(self._accumulator/DT))
        if steps:
            self._advance(steps)
            self._accumulator -= steps*DT
        self.redraw()
        if self.running:
            self._job = self.after(round(1000/self.fps), self._tick)

    def _record(self, force=False):
        if force or self.engine.time-self._last_record >= .15:
            snap = self.engine.snapshot()
            snap["organs"] = {organ.key: self.engine.organ_reading(organ.key) for organ in ORGANS}
            snap["conditions"] = {key: getattr(self.engine.conditions, key) for key in Conditions.__dataclass_fields__ if key!="cell_levels"}
            snap["cells"] = dict(self.engine.conditions.cell_levels)
            snap["cell_signals"]=self.engine.cell_readings()
            snap["profile"]={key:getattr(self.engine.profile,key) for key in Profile.__dataclass_fields__}
            self._history.append(snap)
            self._last_record = self.engine.time
        new = self.engine.events[self._engine_events:]
        if new:
            self._events.extend(new)
            self._engine_events = len(self.engine.events)
            self._show_events()

    def _organ_changed(self, _=None):
        self._selected = ORGAN_KEYS[self.organ_var.get()]
        self.redraw()

    def _cell_changed(self,_=None):
        self._selected_cell=self._cell_name_to_key[self.cell_var.get()]
        self.redraw()

    def _table_selected(self, _=None):
        selection = self.organ_table.selection()
        if selection:
            self._selected = selection[0]
            self.organ_var.set(ORGAN_NAMES[self._selected])
            self.redraw()

    def _map_click(self, event):
        near = None
        distance = float("inf")
        for key, (x, y, radius) in getattr(self, "_organ_positions", {}).items():
            d = math.hypot(event.x-x, event.y-y)
            if d < max(22, radius+8) and d < distance:
                near, distance = key, d
        if near:
            self._selected = near
            self.organ_var.set(ORGAN_NAMES[near])
            self.redraw()

    def redraw(self):
        if not self.winfo_exists() or not hasattr(self, "organ_table"):
            return
        snap = self.engine.snapshot()
        self.time_label.configure(text=f"가상 시간 {snap['time']:.2f} 모형 h")
        for key, output in self._kpi_values.items():
            output.configure(text=f"{100*snap[key]:.1f} / 100")
        self.status_label.configure(text="상태: "+snap["status"]+"  ·  가상 구획과 설정된 방정식의 결과")
        self.cytokine_label.configure(text="염증 신호: "+snap["cytokine_status"]+" · 발열 반응은 상대 지표이며 실제 체온·진단이 아닙니다.")
        profile=self.engine.profile
        selected=[name for key,name in (("diabetes","당뇨병"),("immunosuppression","면역 억제"),("chronic_lung","만성 폐질환"),("chronic_kidney","만성 신장질환")) if getattr(profile,key)]
        self.profile_summary.configure(text=f"숙주 기록: {profile.age_years:g}세 · "+{"unspecified":"성별 미지정","female":"여성","male":"남성"}[profile.sex]+" (연령·성별은 기록용) · 가상 기저 조건: "+(" / ".join(selected) if selected else "없음"))
        if self.engine.ended:
            self.status_label.configure(text="상태: 가상 기능 소실로 모형 종료 · 실제 사망 판단 아님 · 초기화로 새 실험을 시작하세요")
        enabled = self._vars["support"].get() >= .7 and self._vars["oxygen"].get() >= .45
        self.support_btn.configure(text="지원 개입 묶음 해제" if enabled else "지원 개입 묶음 적용")
        organ = next(o for o in ORGANS if o.key==self._selected)
        reading = self.engine.organ_reading(self._selected)
        self.organ_label.configure(text=organ.name+" · 확대 도식")
        self.organ_metrics.configure(text=f"기능 {reading['function']*100:.1f}  ·  조직 손상 {reading['damage']*100:.1f}  ·  염증 {reading['inflammation']*100:.1f} / 100\n{organ.role}")
        for o in ORGANS:
            r = self.engine.organ_reading(o.key)
            self.organ_table.item(o.key, values=(o.name, *(f"{r[k]*100:.1f}" for k in ("function", "bacteria", "virus", "damage", "inflammation"))))
        for j, (key, _, _) in enumerate(CELLS):
            signal = self.engine.state[4*N+j]
            self.cell_activity_labels[key].configure(text=f"활성 신호 {signal*100:.1f} / 100 · 배율 {self._cell_vars[key].get():.2f}")
        selected_index=next(j for j,(key,_,_) in enumerate(CELLS) if key==self._selected_cell)
        _,cell_name,role=CELLS[selected_index]
        signal=self.engine.state[4*N+selected_index]
        self.cell_focus_label.configure(text=f"{cell_name}: {role}\n활성 신호 {signal*100:.1f} / 100 · 형태는 학습용 도식이며 실제 현미경 모양·크기·개수를 재현하지 않습니다.")
        self._draw_body()
        self._draw_tissue()
        self._draw_history()

    def _draw_body(self):
        c, t = self.canvas, self.theme
        immune,function,inflammation=(self.colors[k] for k in ("immune","function","inflammation"))
        c.delete("all")
        w, h = max(200, c.winfo_width()), max(250, c.winfo_height())
        scale = min(w/340, h/390)
        cx = w*.49
        ox, oy = cx-170*scale, 9
        def xy(x, y): return (ox+x*scale, oy+y*scale)
        bodyfill = _mix(t["surface2"], immune, .09)
        outline = _mix(t["surface2"], immune, .35)
        head = (*xy(140, 7), *xy(200, 68))
        c.create_oval(*head, fill=bodyfill, outline=outline, width=2)
        points = (153,69,140,80,104,90,82,147,63,213,77,222,107,167,121,126,
                  121,214,131,253,124,325,124,362,147,362,157,289,170,252,
                  183,289,193,362,216,362,216,325,209,253,219,214,219,126,
                  233,167,263,222,277,213,258,147,236,90,200,80,187,69)
        flat = [v for point in zip(points[::2], points[1::2]) for v in xy(*point)]
        c.create_polygon(flat, fill=bodyfill, outline=outline, width=2, smooth=True)
        # Diagrammatic vascular connections; they are not anatomical flow routes.
        for first,last,_ in TRANSPORT_EDGES:
            a,b=ORGANS[first],ORGANS[last]
            selected=self._selected in (a.key,b.key)
            c.create_line(*xy(a.x*340,a.y*385), *xy(b.x*340,b.y*385),
                          fill=_mix(t["surface2"], inflammation, .28 if selected else .08), width=1)
        self._organ_positions = {}
        # Label two columns with fixed baselines so even nearby organs do not overlap.
        left = [o for i,o in enumerate(ORGANS) if i%2==0]
        right = [o for i,o in enumerate(ORGANS) if i%2]
        labels = {o.key: (15, 28+i*36, "w") for i,o in enumerate(left)}
        labels.update({o.key:(325, 28+i*36, "e") for i,o in enumerate(right)})
        for organ in ORGANS:
            x, y = xy(organ.x*340, organ.y*385)
            r = 8*scale if organ.key not in ("lung", "brain", "liver", "intestine") else 11*scale
            self._organ_positions[organ.key] = (x,y,r)
            damage = self.engine.organ_reading(organ.key)["damage"]
            color = _mix(function, inflammation, min(1, damage*2))
            lx, ly, anchor = labels[organ.key]
            tx, ty = xy(lx, ly)
            elbow = tx+(62*scale if anchor=="w" else -62*scale)
            label_edge=tx+(53*scale if anchor=="w" else -53*scale)
            c.create_line(x,y,elbow,ty,label_edge,ty, fill=_mix(t["surface2"], color, .45), width=1)
            if organ.key==self._selected:
                c.create_oval(x-r-5,y-r-5,x+r+5,y+r+5,outline=t["accent2"],width=2)
            self._organ_shape(c,organ.key,x,y,r,color,t["surface2"])
            c.create_text(tx,ty,anchor=anchor,text=organ.name,fill=t["accent2"] if organ.key==self._selected else t["text"],font=("Malgun Gothic", max(7,round(8*scale)), "bold" if organ.key==self._selected else "normal"),tags=("organ_"+organ.key,))
            c.tag_bind("organ_"+organ.key, "<Button-1>", lambda _,key=organ.key:self._select_organ(key))
        c.create_text(w/2,h-10,text="대표 구획 · 해부학적 크기와 혈류를 단순화",fill=t["muted"],font=("Malgun Gothic",8))

    @staticmethod
    def _organ_shape(c,key,x,y,r,color,bg):
        fill=_mix(bg,color,.48)
        if key=="lung":
            c.create_oval(x-r*1.2,y-r*1.6,x-r*.1,y+r*1.4,fill=fill,outline=color)
            c.create_oval(x+r*.1,y-r*1.6,x+r*1.2,y+r*1.4,fill=fill,outline=color)
            c.create_line(x,y-r*2,x,y,x-r*.5,y+r*.4,x,y,x+r*.5,y+r*.4,fill=color,width=2)
        elif key=="brain":
            c.create_oval(x-r,y-r*.9,x+r,y+r*.9,fill=fill,outline=color)
            c.create_line(x,y-r*.75,x,y+r*.75,fill=color)
            for offset in (-.45,.2):
                c.create_arc(x-r*.8,y+r*offset,x+r*.8,y+r*(offset+.55),start=15,extent=145,style="arc",outline=color)
        elif key=="heart":
            c.create_polygon(x,y+r*1.25,x-r,y-r*.2,x-r*.75,y-r,x,y-r*.55,x+r*.75,y-r,x+r,y-r*.2,fill=fill,outline=color,smooth=True)
        elif key=="liver":
            c.create_polygon(x-r*1.5,y-r*.7,x+r*1.4,y-r*.4,x+r*.5,y+r*.55,x-r*1.2,y+r*.8,fill=fill,outline=color,smooth=True)
        elif key=="intestine":
            c.create_rectangle(x-r,y-r,x+r,y+r,fill=fill,outline=color)
            c.create_line(x-r*.65,y-r*.5,x+r*.55,y-r*.5,x+r*.55,y,x-r*.55,y,x-r*.55,y+r*.5,x+r*.65,y+r*.5,fill=color,width=2,smooth=True)
        elif key in ("kidney","stomach","spleen"):
            c.create_polygon(x-r*.8,y-r,x+r*.7,y-r*.7,x+r,y+r*.4,x+r*.15,y+r,x-r*.7,y+r*.55,x-r*.25,y,fill=fill,outline=color,smooth=True)
        else:
            c.create_oval(x-r,y-r,x+r,y+r,fill=fill,outline=color,width=1)

    def _select_organ(self,key):
        self._selected=key
        self.organ_var.set(ORGAN_NAMES[key])
        self.redraw()

    def _draw_tissue(self):
        c, t = self.tissue_canvas, self.theme
        bacteria,virus,immune,inflammation=(self.colors[k] for k in ("bacteria","virus","immune","inflammation"))
        c.delete("all")
        w, h = max(240,c.winfo_width()), max(180,c.winfo_height())
        r = self.engine.organ_reading(self._selected)
        # Fixed seed geometry gives reproducible, flicker-free schematic tissue.
        base = _mix(t["surface2"], virus, .065)
        for row in range(5):
            for col in range(9):
                x = (col+.6+(row%2)*.4)*w/9
                y = (row+.5)*h/5
                radius = min(w/9,h/5)*.47
                injured = ((row*13+col*7)%43)/43 < r["damage"]
                fill = _mix(base, inflammation if injured else immune,.16 if injured else .06)
                c.create_oval(x-radius,y-radius,x+radius,y+radius,fill=fill,outline=_mix(t["surface2"],inflammation if injured else immune,.16),width=1)
                c.create_oval(x-3,y-3,x+3,y+3,fill=_mix(fill,virus,.35),outline="")
        # A vessel is a visual guide only; no unmodelled spatial flow is inferred.
        c.create_line(-20,h*.77,w*.25,h*.62,w*.56,h*.74,w+20,h*.56,
                      smooth=True,width=24,fill=_mix(t["surface2"],inflammation,.12))
        phase=self.engine.time*.55
        bcount=min(35,round(r["bacteria"]*35))
        vcount=min(35,round(r["virus"]*35))
        for kind,count,color in ((0,bcount,bacteria),(1,vcount,virus)):
            for j in range(count):
                x=12+((j*.618033+kind*.23+phase*.08+math.sin(j+phase)*.015)%1)*(w-24)
                y=18+((j*.414214+kind*.38+phase*.035+math.cos(j*.7+phase)*.03)%1)*(h-36)
                if kind==0:
                    angle=j*1.3+phase*.4
                    dx,dy=5*math.cos(angle),5*math.sin(angle)
                    c.create_line(x-dx,y-dy,x+dx,y+dy,fill=color,width=5,capstyle="round")
                    c.create_line(x+dx,y+dy,x+dx+5,y+dy-4,fill=_mix(t["surface2"],color,.6))
                else:
                    for k in range(7):
                        a=2*math.pi*k/7+phase*.2
                        c.create_line(x+4*math.cos(a),y+4*math.sin(a),x+7*math.cos(a),y+7*math.sin(a),fill=color,width=1)
                    c.create_oval(x-4,y-4,x+4,y+4,fill=_mix(t["surface2"],color,.7),outline=color)
        for j,(key,_,_) in enumerate(CELLS):
            activity=self.engine.state[4*N+j]*self._cell_vars[key].get()
            if activity < .015:
                continue
            for k in range(min(3,1+int(activity))):
                index=j*3+k
                x=16+((index*.381966+phase*.018+math.sin(phase+index)*.04)%1)*(w-32)
                y=17+((index*.732051+phase*.013+math.cos(phase*.8+index)*.04)%1)*(h-34)
                radius=7+min(4,activity*2)
                color=_mix(immune,self.theme["accent2"],j/max(1,len(CELLS)-1)*.5)
                self._immune_cell(c,key,x,y,radius,color,phase)
                if key==self._selected_cell:
                    c.create_oval(x-radius-4,y-radius-4,x+radius+4,y+radius+4,outline=t["accent2"],dash=(2,3))
        if not bcount and not vcount:
            c.create_text(w-10,17,anchor="e",text="병원체 부담이 작음",fill=t["muted"],font=("Malgun Gothic",8))
        c.create_rectangle(8,7,min(w-8,220),63,fill=t["surface2"],outline=t["line"])
        self._immune_cell(c,self._selected_cell,36,35,16,immune,0)
        c.create_text(63,27,anchor="w",text=self.cell_var.get(),fill=t["text"],font=("Malgun Gothic",9,"bold"))
        c.create_text(63,46,anchor="w",text="세포 형태 · 학습용 도식",fill=t["muted"],font=("Malgun Gothic",8))
        c.create_rectangle(8,h-27,w-8,h-6,fill=t["surface2"],outline="")
        c.create_text(15,h-16,anchor="w",text=f"{ORGAN_NAMES[self._selected]}  |  세균 {r['bacteria']*100:.1f}  바이러스 {r['virus']*100:.1f} / 100",fill=t["text"],font=("Malgun Gothic",8))

    def _immune_cell(self,c,key,x,y,r,color,phase):
        """Recognizable morphology cues, explicitly schematic, never microscopy."""
        bg=self.theme["surface2"]
        color={"bcell":self.colors["function"],"plasma":self.colors["virus"],
               "helper":self.theme["accent2"],"killer":self.colors["immune"],
               "eosinophil":self.colors["bacteria"],"mast":self.colors["virus"]}.get(key,color)
        fill=_mix(bg,color,.35)
        nucleus=_mix(color,bg,.15)
        c.create_oval(x-r-2,y-r-2,x+r+2,y+r+2,outline=_mix(bg,color,.15))
        if key=="macrophage":
            points=[]
            for k in range(16):
                a=k*math.pi/8
                radius=r*(1.1 if k%2 else .83)
                points.extend((x+radius*math.cos(a),y+radius*math.sin(a)))
            c.create_polygon(*points,fill=fill,outline=color,smooth=True)
        else:
            c.create_oval(x-r,y-r,x+r,y+r,fill=fill,outline=color,width=1)
        def oval(dx,dy,rx,ry,fill=nucleus):
            c.create_oval(x+r*(dx-rx),y+r*(dy-ry),x+r*(dx+rx),y+r*(dy+ry),fill=fill,outline="")
        if key=="neutrophil":
            c.create_line(x-r*.4,y+r*.15,x,y-r*.2,x+r*.4,y+r*.15,fill=nucleus,width=max(1,r*.1))
            for dx,dy in ((-.4,.15),(0,-.2),(.4,.15)):
                oval(dx,dy,.23,.26)
        elif key in ("monocyte","macrophage"):
            c.create_polygon(x-r*.45,y-r*.55,x+r*.2,y-r*.55,x+r*.45,y-r*.1,x+r*.2,y+r*.5,
                             x-r*.45,y+r*.45,x-r*.12,y,x-r*.45,y-r*.2,
                             smooth=True,fill=nucleus,outline="")
            if key=="macrophage":
                for dx,dy in ((.5,.5),(-.6,.45),(.5,-.5)):
                    oval(dx,dy,.12,.12,_mix(color,bg,.3))
        elif key=="dendritic":
            for arm in range(6):
                a=arm*math.pi/3+phase*.1
                ex,ey=x+r*1.45*math.cos(a),y+r*1.45*math.sin(a)
                c.create_line(x+r*.7*math.cos(a),y+r*.7*math.sin(a),ex,ey,fill=color,width=max(1,r*.1))
                c.create_line(ex,ey,ex+r*.27*math.cos(a+.5),ey+r*.27*math.sin(a+.5),fill=color)
            oval(0,0,.33,.4)
        elif key=="plasma":
            oval(-.35,0,.38,.45)
            for k in range(3):
                c.create_arc(x-r*.1,y-r*(.65-k*.16),x+r*.75,y+r*(.65-k*.16),start=-75,extent=150,style="arc",outline=color,width=1)
        elif key=="eosinophil":
            oval(-.28,0,.25,.4); oval(.28,0,.25,.4)
        elif key in ("helper","killer","bcell","nk"):
            oval(-.1,-.05,.61 if key!="nk" else .49,.61 if key!="nk" else .52)
        else:
            oval(0,0,.38,.48)
        if key in ("eosinophil","basophil","mast","nk","killer"):
            count=12 if key in ("basophil","mast") else 7
            for k in range(count):
                a=k*2.4
                radius=.68 if k%2 else .48
                dx,dy=radius*math.cos(a),radius*math.sin(a)
                oval(dx,dy,.075,.075,nucleus if key in ("basophil","mast") else color)

    def _draw_history(self):
        if not hasattr(self,"history_canvas"):
            return
        c,t=self.history_canvas,self.theme
        c.delete("all")
        w,h=max(200,c.winfo_width()),max(100,c.winfo_height())
        left,right,top,bottom=38,w-12,12,h-25
        for value in (0,.5,1):
            y=bottom-value*(bottom-top)
            c.create_line(left,y,right,y,fill=t["line"])
            c.create_text(left-7,y,text=f"{100*value:g}",anchor="e",fill=t["muted"],font=("Consolas",8))
        if not self._history:
            return
        data=list(self._history)
        first,last=data[0]["time"],max(data[0]["time"]+1,data[-1]["time"])
        for key,color in (("reserve",self.colors["function"]),("bacteria",self.colors["bacteria"]),("virus",self.colors["virus"]),("inflammation",self.colors["inflammation"]),("cytokine",self.colors["cytokine"]),("fever",self.colors["fever"])):
            points=[]
            for sample in data:
                points.extend((left+(sample["time"]-first)/(last-first)*(right-left),bottom-sample[key]*(bottom-top)))
            if len(points)>=4:
                c.create_line(*points,fill=color,width=2,dash=(4,3) if key=="fever" else ())
        for value,x,anchor in ((first,left,"w"),(last,right,"e")):
            c.create_text(x,bottom+14,text=f"{value:.1f} 모형 h",anchor=anchor,fill=t["muted"],font=("Malgun Gothic",8))

    def export_csv(self, path=None):
        """Optional explicit path makes exports testable without a file dialog."""
        if path is None:
            path=filedialog.asksaveasfilename(parent=self, title="모형 실험 기록 저장", defaultextension=".csv",
                                              initialfile="biology-model-observations.csv",
                                              filetypes=[("CSV 파일","*.csv")])
        if not path:
            return
        self._record(force=True)
        fields=["model_hours","mean_bacteria_relative","mean_virus_relative","functional_reserve_relative","mean_inflammation_relative","cytokine_signal_relative","fever_response_relative_not_Celsius","model_status","cytokine_model_status"]
        fields += [f"{organ.key}_{metric}_relative" for organ in ORGANS for metric in ("bacteria","virus","damage","inflammation","function")]
        condition_names=[name for name in Conditions.__dataclass_fields__ if name!="cell_levels"]
        fields += ["setting_"+name for name in condition_names]+["cell_multiplier_"+key for key,_,_ in CELLS]
        fields += ["cell_"+key+"_"+metric for key,_,_ in CELLS for metric in ("activation","activity")]
        profile_fields=list(Profile.__dataclass_fields__)
        fields += ["profile_"+name for name in profile_fields]
        try:
            with open(path,"w",encoding="utf-8-sig",newline="") as stream:
                writer=csv.writer(stream)
                writer.writerow(["EDUCATIONAL FICTIONAL MODEL. Model hours are not clinical hours. Relative indices are not patient measurements."])
                writer.writerow(fields)
                for s in self._history:
                    row=[s["time"],s["bacteria"],s["virus"],s["reserve"],s["inflammation"],s["cytokine"],s["fever"],s["status"],s["cytokine_status"]]
                    row += [s["organs"][organ.key][metric] for organ in ORGANS for metric in ("bacteria","virus","damage","inflammation","function")]
                    row += [s["conditions"][name] for name in condition_names]+[s["cells"][key] for key,_,_ in CELLS]
                    row += [s["cell_signals"][key][metric] for key,_,_ in CELLS for metric in ("activation","activity")]
                    row += [s["profile"][name] for name in profile_fields]
                    writer.writerow(row)
                writer.writerow([])
                writer.writerow(["event_model_hours","event"])
                writer.writerows(self._events)
            self._add_event("CSV 실험 기록 저장")
            return path
        except OSError as exc:
            messagebox.showerror("기록 저장", f"저장하지 못했습니다.\n{exc}",parent=self)
            return None

    def destroy(self):
        self.stop()
        if self._layout_job is not None:
            self.after_cancel(self._layout_job)
            self._layout_job=None
        super().destroy()
