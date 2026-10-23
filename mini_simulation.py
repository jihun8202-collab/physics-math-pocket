"""Compact concept experiments using the same SI engine as the full laboratory.

Public integration:
    widget = build_mini_simulator(parent, concept, theme, fps=30)
    if widget is not None:
        widget.pack(fill="x")

The caller owns the widget and calls stop()/destroy() on page changes. No timer
starts automatically. Matching is deliberately narrow; a concept's subject or
description alone never attaches an unrelated experiment.
"""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from enhanced_simulations import EnhancedSimulator, SPECS
from scientific_catalog import SCENARIOS

_EXPLICIT = {
    "newton2": "force",
    "enhanced_force": "force",
    "projectile": "projectile",
    "enhanced_projectile": "projectile",
    "pendulum": "pendulum",
    "enhanced_pendulum": "pendulum",
    "spring": "spring",
    "enhanced_spring": "spring",
    "damping": "spring",
}
_NAMES = {
    "force": (
        "뉴턴의 제2법칙", "뉴턴 제2법칙", "뉴턴의 운동 제2법칙",
        "가속도", "등가속도 운동", "힘과 가속도",
        "Newton's second law", "uniformly accelerated motion",
    ),
    "projectile": ("포물선 운동", "포사체 운동", "투사체 운동", "projectile motion"),
    "pendulum": ("단진자", "진자 운동", "simple pendulum", "pendulum"),
    "spring": ("훅의 법칙", "용수철 진동", "감쇠 진동", "감쇠진동", "Hooke's law", "damped oscillation"),
}
_CONTROL_NAMES = {
    "force": ("applied_force", "mass", "initial_velocity"),
    "projectile": ("launch_speed", "angle_degrees", "quadratic_drag"),
    "pendulum": ("angle_degrees", "length", "angular_damping"),
    "spring": ("stiffness", "mass", "spring_damping"),
}
_TITLES = {
    "force": "힘을 바꾸면 속도가 어떻게 달라질까?",
    "projectile": "발사 조건과 공기 저항을 비교해 보세요",
    "pendulum": "진자의 길이·각도·감쇠를 비교해 보세요",
    "spring": "용수철의 강성과 감쇠를 비교해 보세요",
}
_ASSUMPTIONS = {
    "force": "마찰 없는 수평면·일정한 외력. 화면은 물체를 따라가며, 화면 끝에서 튕기지 않습니다.",
    "projectile": "일정한 중력·정지한 공기·제곱 저항. 점선은 진공 궤적이며 착지에서 계산을 끝냅니다.",
    "pendulum": "질량 없는 강체 막대·점질량 추. 큰 각도도 sin θ 그대로 계산합니다. 느슨해지는 줄은 포함하지 않습니다.",
    "spring": "수평 용수철·선형 탄성·속도에 비례하는 감쇠. 건조 마찰은 포함하지 않습니다.",
}


def _normalize(value: str) -> str:
    return "".join(value.casefold().split()).replace("’", "'")


def mini_kind_for_term(term: dict) -> str:
    """Return a supported physical model, or '' when the concept does not match."""
    explicit = str(term.get("simulator") or "").strip()
    if explicit in SCENARIOS:
        dynamic = SCENARIOS[explicit].get("dynamic")
        return dynamic["kind"] if dynamic else ""
    if explicit in _EXPLICIT:
        return _EXPLICIT[explicit]
    if explicit:
        return ""
    names = [term.get("name_ko"), term.get("name_en"), term.get("title")]
    aliases = term.get("aliases", [])
    if isinstance(aliases, (list, tuple)):
        names.extend(aliases)
    normalized = {_normalize(name) for name in names if isinstance(name, str)}
    for kind, accepted in _NAMES.items():
        if any(_normalize(name) in normalized for name in accepted):
            return kind
    return ""


def mini_initial_conditions(term: dict, kind: str) -> dict:
    """Preserve a linked scenario's actual starting values; never relabel it."""
    sid = str(term.get("simulator") or "").strip()
    if sid in SCENARIOS and SCENARIOS[sid].get("dynamic"):
        return dict(SCENARIOS[sid]["dynamic"]["settings"])
    if kind == "projectile" and sid != "enhanced_projectile":
        return {"quadratic_drag": 0.0}
    if kind == "spring" and sid != "damping" and sid != "enhanced_spring":
        return {"spring_damping": 0.0}
    if kind == "pendulum" and sid != "enhanced_pendulum":
        return {"angular_damping": 0.0}
    return {}


def build_mini_simulator(master, term: dict, theme: dict, fps: int = 30):
    kind = mini_kind_for_term(term)
    if not kind:
        return None
    widget = ConceptMiniSimulator(master, kind, theme, fps=fps)
    widget._setting_up = True
    for name, value in mini_initial_conditions(term, kind).items():
        if name in widget._vars:
            widget._vars[name].set(value)
    widget._setting_up = False
    widget.reset()
    return widget


class ConceptMiniSimulator(EnhancedSimulator):
    """Four compact experiments, sharing fixed 1/240 s integration and graphs."""

    def __init__(self, master, kind, theme, fps=30):
        super().__init__(master, "enhanced_" + kind, theme, fps=fps)

    def _label(self, text="", **options):
        return tk.Label(self, text=text, bg=self.theme["surface"],
                        fg=self.theme["muted"], anchor="w", justify="left",
                        font=("Malgun Gothic", 9), **options)

    def _build(self):
        t, spec = self.theme, SPECS[self.kind]
        self.title_label = self._label("미니 실험 · " + _TITLES[self.kind])
        self.title_label.configure(fg=t["text"], font=("Malgun Gothic", 11, "bold"))
        self.title_label.pack(fill="x", pady=(0, 5))
        self.formula_label = self._label(spec["formula"])
        self.formula_label.configure(fg=t["accent2"])
        self.formula_label.pack(fill="x", pady=(0, 6))
        self.controls = tk.Frame(self, bg=t["surface"])
        self.controls.pack(fill="x")
        self._control_labels = []
        for name, label, unit, low, high, default in spec["parameters"]:
            variable = tk.DoubleVar(value=default)
            self._vars[name] = variable
            variable.trace_add("write", self._conditions_changed)
            if name not in _CONTROL_NAMES[self.kind]:
                continue
            cell = tk.Frame(self.controls, bg=t["surface2"], padx=9, pady=6)
            output = tk.Label(cell, anchor="w", justify="left", bg=t["surface2"],
                              fg=t["text"], font=("Malgun Gothic", 9))
            output.pack(fill="x")
            self._control_labels.append(output)

            def show(*_, variable=variable, output=output, label=label, unit=unit):
                output.configure(text=f"{label} · {variable.get():.3g} {unit}")

            variable.trace_add("write", show)
            show()
            ttk.Scale(cell, from_=low, to=high, variable=variable).pack(fill="x", pady=(3, 0))
            self._controls.append(cell)
        self.parameter_hint = self._label("조건을 바꾸면 초기화됩니다. 시작 또는 한 단계를 눌러 움직임과 그래프를 확인하세요.")
        self.parameter_hint.pack(fill="x", pady=6)
        self._toolbar = tk.Frame(self, bg=t["surface"])
        self._toolbar.pack(fill="x", pady=(0, 6))
        self.play_btn = self._button(self._toolbar, "▶ 시작", self.toggle, primary=True)
        self.reset_btn = self._button(self._toolbar, "처음으로", self.reset)
        self.step_btn = self._button(self._toolbar, "한 단계", self.step_once)
        self.speed_var = tk.StringVar(value="1배")
        self.speed_control = ttk.Combobox(self._toolbar, textvariable=self.speed_var,
                                         values=("0.25배", "0.5배", "1배", "2배", "4배"),
                                         state="readonly", width=7)
        self._toolbar_items = [self.play_btn, self.reset_btn, self.step_btn, self.speed_control]
        self.status = self._label()
        self.status.pack(fill="x", pady=(0, 5))
        self.canvas = tk.Canvas(self, width=480, height=225, bg=t["surface2"],
                                highlightthickness=1, highlightbackground=t["line"])
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda _: self.redraw())
        self.legend = self._label()
        self.legend.pack(fill="x", pady=4)
        self.info = self._label()
        self.info.configure(fg=t["text"], bg=t["surface2"], padx=9, pady=7)
        self.info.pack(fill="x")
        self.history_canvas = tk.Canvas(self, width=480, height=115, bg=t["surface2"],
                                        highlightthickness=1, highlightbackground=t["line"])
        self.history_canvas.pack(fill="x", pady=(6, 6))
        self.history_canvas.bind("<Configure>", lambda _: self._draw_history())
        self.notes_label = self._label("모델의 범위 · " + _ASSUMPTIONS[self.kind])
        self.notes_label.pack(fill="x")

    def _layout(self, event):
        if event.widget is not self:
            return
        width = max(220, event.width)
        columns = 3 if width >= 870 else 2 if width >= 550 else 1
        if columns != self._columns:
            for i, cell in enumerate(self._controls):
                cell.grid(row=i // columns, column=i % columns, sticky="ew", padx=3, pady=3)
            for column in range(3):
                self.controls.columnconfigure(column, weight=1 if column < columns else 0,
                                              uniform="mini" if column < columns else "")
            self._columns = columns
        for label in self._control_labels:
            label.configure(wraplength=max(180, width // columns - 28))
        toolbar_columns = 4 if width >= 480 else 2
        for i, item in enumerate(self._toolbar_items):
            item.grid(row=i // toolbar_columns, column=i % toolbar_columns, sticky="ew", padx=3, pady=3)
        for column in range(4):
            self._toolbar.columnconfigure(column, weight=1 if column < toolbar_columns else 0)
        for label in (self.title_label, self.formula_label, self.parameter_hint, self.status,
                      self.legend, self.info, self.notes_label):
            label.configure(wraplength=width - 24)

    def redraw(self):
        super().redraw()
        if not hasattr(self, "engine"):
            return
        p, q = self.engine.settings, self.engine.reading
        if self.kind == "pendulum":
            measurement = f"각도 {math.degrees(q.angle):.2f}° · 각속도 {q.angular_velocity:.3f} rad/s"
        else:
            measurement = f"x {q.x:.3f} m · " + (f"높이 {q.y:.3f} m" if self.kind == "projectile" else f"속도 {q.vx:.3f} m/s")
        self.info.configure(text=f"시간 {q.time:.3f} s · {measurement}\n"
                                 f"{'운동' if self.kind == 'force' else '역학적 '}에너지 {q.energy:.3f} J · "
                                 + (f"가속도 {p.applied_force / p.mass:.3f} m/s²" if self.kind == "force"
                                    else "파란 화살표: 속도 방향"))
