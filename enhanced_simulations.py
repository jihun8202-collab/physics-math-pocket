"""Animated experiments added beside every preserved legacy simulator."""
from __future__ import annotations

from collections import deque
import math
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional
import webbrowser

from physics_engine import FIXED_DT, PhysicsEngine, Settings
from simulations import build_simulator as legacy_build_simulator
from simulations import simulator_for_term as legacy_simulator_for_term

ENHANCED_TITLES = {
    "enhanced_collision": "실험 · 여러 물체의 2차원 충돌",
    "enhanced_force": "실험 · 일정한 힘과 실제 가속 운동",
    "enhanced_projectile": "실험 · 공기 저항과 포물선 운동",
    "enhanced_pendulum": "실험 · 큰 각도와 감쇠 진자",
    "enhanced_spring": "실험 · 마찰이 있는 용수철",
}
ENHANCED_SUBJECTS = {sid: "물리" for sid in ENHANCED_TITLES}

SPECS = {
    "force": {
        "formula": "a = F/m     x = v₀t + ½at²     v = v₀ + at     ΔK = Fx",
        "parameters": [
            ("applied_force", "일정한 수평 힘 F", "N", -50, 50, 8),
            ("mass", "물체 질량", "kg", 0.1, 10, 2),
            ("initial_velocity", "처음 수평 속도 v₀", "m/s", -60, 60, 0),
        ],
        "notes": "마찰 없는 수평면에서 일정한 외력을 받는 점질량을 계산합니다. x = 0에서 출발합니다. 벽을 두지 않으므로 화면 끝에서 속도가 바뀌지 않습니다. 눈금과 관찰 화면이 물체를 따라 이동합니다. 가속도와 처음 속도가 반대라면 실제로 정지한 뒤 방향을 바꿀 수 있습니다. 조건을 바꾸면 새 실험으로 초기화됩니다.",
        "source": "https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law",
    },
    "projectile": {
        "formula": "F저항 = −D |v| v     ax = −D |v| vx / m     ay = −g − D |v| vy / m",
        "parameters": [
            ("launch_speed", "발사 속력", "m/s", 2, 60, 20),
            ("angle_degrees", "발사 각도", "°", 5, 80, 45),
            ("mass", "질량", "kg", 0.1, 10, 1),
            ("quadratic_drag", "제곱 저항 계수 D", "kg/m", 0, 0.05, 0.008),
            ("initial_height", "출발 높이", "m", 0, 20, 0),
            ("gravity", "중력 가속도", "m/s²", 1, 15, 9.80665),
        ],
        "notes": "정지한 공기에서 속력의 제곱에 비례하는 저항을 적용합니다. D = ½ρCdA이며 D = 0이면 진공입니다. 중력은 일정하고 바람·회전·양력은 생략합니다. 지면에 닿으면 계산을 끝내고 착지 직전의 속도와 에너지를 표시합니다. 충돌 이후의 운동은 계산하지 않습니다. 역학적 에너지의 위치 기준은 지면입니다.",
        "source": "https://openstax.org/books/college-physics-2e/pages/5-2-drag-forces",
    },
    "pendulum": {
        "formula": "θ″ = −(g/L) sin θ − βθ′     E = ½mL²ω² + mgL(1 − cos θ)",
        "parameters": [
            ("angle_degrees", "처음 각도 · 수직 기준", "°", 0, 120, 45),
            ("length", "진자 길이", "m", 0.2, 5, 1.5),
            ("angular_damping", "각속도 감쇠율 β", "s⁻¹", 0, 2, 0.08),
            ("mass", "추의 질량", "kg", 0.1, 10, 1),
            ("gravity", "중력 가속도", "m/s²", 1, 15, 9.80665),
        ],
        "notes": "sin θ를 그대로 계산하여 큰 각도에서 주기가 길어지는 현상을 표현합니다. 늘어나지 않는 질량 없는 줄, 점질량 추, 일정한 중력, 각속도에 비례하는 감쇠를 가정합니다. 추의 크기는 보기 쉽게 표현했습니다. 에너지는 가장 낮은 위치를 기준으로 합니다. 참고 주기 T₀는 작은 각도·감쇠 없음에만 해당합니다.",
        "source": "https://openstax.org/books/college-physics-2e/pages/16-4-the-simple-pendulum",
    },
    "spring": {
        "formula": "mx″ + cx′ + kx = 0     E = ½mv² + ½kx²     감쇠비 ζ = c/(2√km)",
        "parameters": [
            ("amplitude", "처음 변위", "m", 0, 2, 0.6),
            ("stiffness", "용수철 상수 k", "N/m", 1, 100, 20),
            ("mass", "물체 질량", "kg", 0.1, 10, 1),
            ("spring_damping", "점성 감쇠 계수 c", "N·s/m", 0, 5, 0.6),
        ],
        "notes": "수평면에서 훅의 법칙과 속도에 비례하는 저항을 계산합니다. 물체는 처음 변위에서 정지한 채 출발합니다. 용수철의 질량·변형 한계·건조 마찰은 생략합니다. ζ < 1은 진동하며 감쇠, ζ = 1은 임계 감쇠, ζ > 1은 진동 없이 감쇠합니다. 그림의 용수철 길이는 이해를 돕는 표현이며 변위는 눈금과 수치로 확인합니다.",
        "source": "https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations",
    },
}

LEGACY_PHYSICAL_ALIASES = {
    "newton2": "enhanced_force", "projectile": "enhanced_projectile",
    "spring": "enhanced_spring", "elastic_collision": "enhanced_collision",
}


def simulator_for_term(term: dict) -> str:
    explicit = str(term.get("simulator", "")).strip()
    return LEGACY_PHYSICAL_ALIASES.get(explicit, explicit) if explicit in ENHANCED_TITLES or explicit in LEGACY_PHYSICAL_ALIASES else legacy_simulator_for_term(term)


def build_simulator(master: tk.Misc, term: dict, theme: dict, fps: int = 30):
    sid = str(term.get("simulator", "")).strip()
    model = LEGACY_PHYSICAL_ALIASES.get(sid, sid)
    if model == "enhanced_collision":
        from collision_simulation import CollisionSimulator
        return CollisionSimulator(master, theme, fps)
    if model in ENHANCED_TITLES:
        sim = EnhancedSimulator(master, model, theme, fps)
        if sid == "projectile":
            sim._vars["quadratic_drag"].set(0)
        elif sid == "spring":
            sim._vars["spring_damping"].set(0)
        return sim
    return legacy_build_simulator(master, term, theme, fps=fps)


class EnhancedSimulator(tk.Frame):
    """MiniSimulator-compatible lifecycle with deterministic physical steps."""
    def __init__(self, master: tk.Misc, sim_id: str, theme: dict, fps: int = 30) -> None:
        super().__init__(master, bg=theme["surface"])
        self.sim_id, self.kind, self.theme = sim_id, sim_id.removeprefix("enhanced_"), theme
        self.fps = 60 if fps >= 60 else 30
        self.running = False
        self.t = 0.0
        self._job: Optional[str] = None
        self._vars = {}
        self._controls = []
        self._setting_up = True
        self._last_clock = 0.0
        self._accumulator = 0.0
        self._parameter_job: Optional[str] = None
        self._columns = 0
        self.trail = deque(maxlen=3000)
        self.history = deque(maxlen=3600)
        self._build()
        self._setting_up = False
        self.reset()
        self.bind("<Configure>", self._layout)

    def _button(self, master, text, command, primary=False):
        t = self.theme
        return tk.Button(master, text=text, command=command, relief="flat", bd=0,
                         bg=t["accent"] if primary else t["accent_soft"],
                         fg="#FFFFFF" if primary else t["accent2"],
                         activebackground=t["accent_soft"], activeforeground=t["accent2"],
                         font=("Malgun Gothic", 9, "bold"), padx=12, pady=7, cursor="hand2")

    def _build(self):
        t, spec = self.theme, SPECS[self.kind]
        self.title_label = tk.Label(self, text=ENHANCED_TITLES[self.sim_id], anchor="w", justify="left",
                                    bg=t["surface"], fg=t["text"], font=("Malgun Gothic", 12, "bold"))
        self.title_label.pack(fill="x", pady=(0, 7))
        self.formula_label = tk.Label(self, text=spec["formula"], anchor="w", justify="left",
                                      bg=t["surface"], fg=t["accent2"], font=("Malgun Gothic", 10))
        self.formula_label.pack(fill="x", pady=(0, 12))
        self.controls = tk.Frame(self, bg=t["surface"])
        self.controls.pack(fill="x")
        for name, label, unit, lo, hi, default in spec["parameters"]:
            cell = tk.Frame(self.controls, bg=t["surface2"], padx=10, pady=6)
            row = tk.Frame(cell, bg=t["surface2"])
            row.pack(fill="x")
            tk.Label(row, text=label, bg=t["surface2"], fg=t["text"], font=("Malgun Gothic", 9), anchor="w").pack(side="left")
            value = tk.DoubleVar(value=default)
            self._vars[name] = value
            output = tk.Label(row, bg=t["surface2"], fg=t["accent2"], font=("Consolas", 9), anchor="e")
            output.pack(side="right")
            def show(*_, value=value, output=output, unit=unit):
                output.configure(text=f"{value.get():.3g} {unit}")
            value.trace_add("write", show)
            value.trace_add("write", self._conditions_changed)
            show()
            ttk.Scale(cell, from_=lo, to=hi, variable=value, orient="horizontal").pack(fill="x", pady=(3, 0))
            self._controls.append(cell)
        self.parameter_hint = tk.Label(self, text="조건을 바꾸면 실험을 처음으로 되돌립니다. 모든 수치는 SI 단위를 사용합니다.",
                                       anchor="w", justify="left", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 8))
        self.parameter_hint.pack(fill="x", pady=(7, 8))
        bar = tk.Frame(self, bg=t["surface"])
        bar.pack(fill="x", pady=(0, 9))
        self.play_btn = self._button(bar, "▶ 시작", self.toggle, primary=True)
        self.play_btn.pack(side="left", padx=(0, 6))
        self.reset_btn = self._button(bar, "처음으로", self.reset)
        self.reset_btn.pack(side="left", padx=(0, 6))
        self.step_btn = self._button(bar, "한 단계", self.step_once)
        self.step_btn.pack(side="left", padx=(0, 9))
        self.speed_var = tk.StringVar(value="1배")
        speed = ttk.Combobox(bar, textvariable=self.speed_var, values=("0.25배", "0.5배", "1배", "2배", "4배"),
                             state="readonly", width=7)
        speed.pack(side="left")
        self.status = tk.Label(self, text="", bg=t["surface"], fg=t["muted"], anchor="w", justify="left", font=("Malgun Gothic", 8))
        self.status.pack(fill="x", pady=(0, 8))
        self.canvas = tk.Canvas(self, width=650, height=330, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda _: self.redraw())
        self.legend = tk.Label(self, anchor="w", justify="left", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 8))
        self.legend.pack(fill="x", pady=(6, 8))
        self.info = tk.Label(self, anchor="w", justify="left", bg=t["surface2"], fg=t["text"], font=("Malgun Gothic", 10), padx=12, pady=10)
        self.info.pack(fill="x")
        self.history_canvas = tk.Canvas(self, width=650, height=135, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
        self.history_canvas.pack(fill="x", pady=(9, 10))
        self.history_canvas.bind("<Configure>", lambda _: self._draw_history())
        self.notes_label = tk.Label(self, text="모델과 가정 · " + spec["notes"], anchor="w", justify="left",
                                    bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 9))
        self.notes_label.pack(fill="x")
        source = tk.Label(self, text="모델 참고: OpenStax ↗", anchor="w", bg=t["surface"], fg=t["blue"],
                          font=("Malgun Gothic", 9, "underline"), cursor="hand2")
        source.pack(fill="x", pady=(7, 0))
        source.bind("<Button-1>", lambda _: webbrowser.open(spec["source"]))

    def _layout(self, event):
        if event.widget is not self:
            return
        width = max(240, event.width)
        columns = 2 if width >= 650 else 1
        if columns != self._columns:
            for i, cell in enumerate(self._controls):
                cell.grid(row=i // columns, column=i % columns, sticky="ew", padx=(0 if i % columns == 0 else 8, 0), pady=3)
            for column in range(2):
                self.controls.columnconfigure(column, weight=1 if column < columns else 0)
            self._columns = columns
        for label in (self.title_label, self.formula_label, self.parameter_hint, self.status, self.legend, self.info, self.notes_label):
            label.configure(wraplength=max(220, width - 24))

    def _conditions_changed(self, *_):
        if self._setting_up:
            return
        self.stop()
        if self._parameter_job:
            self.after_cancel(self._parameter_job)
        self._parameter_job = self.after_idle(self._reset_after_change)

    def _reset_after_change(self):
        self._parameter_job = None
        self.reset()

    def reset(self):
        self.stop()
        self.engine = PhysicsEngine(Settings(kind=self.kind, **{name: var.get() for name, var in self._vars.items()}))
        self.t, self._accumulator = 0.0, 0.0
        self.apex = self.engine.reading.y
        self.trail.clear(); self.history.clear()
        self.trail.append(self.engine.reading); self.history.append(self.engine.reading)
        self.initial_energy = self.engine.reading.energy
        self._set_bounds()
        self.play_btn.configure(text="▶ 시작")
        self.status.configure(text="준비됨 · 조건을 정한 뒤 시작하세요. 한 단계는 1/60초입니다.")
        self.redraw()

    def _set_bounds(self):
        p = self.engine.settings
        self.vacuum = []
        if self.kind == "projectile":
            angle = math.radians(p.angle_degrees)
            vx, vy = p.launch_speed * math.cos(angle), p.launch_speed * math.sin(angle)
            duration = (vy + math.sqrt(vy * vy + 2 * p.gravity * p.initial_height)) / p.gravity
            for i in range(161):
                t = duration * i / 160
                self.vacuum.append((vx * t, max(0, p.initial_height + vy * t - p.gravity * t * t / 2)))
            self.bounds = (0, max(2, vx * duration * 1.08), 0, max(1, (p.initial_height + vy * vy / (2 * p.gravity)) * 1.16))
        elif self.kind == "pendulum":
            self.bounds = (-p.length * 1.3, p.length * 1.3, -p.length * 1.2, p.length * 0.65)
        elif self.kind == "force":
            self.bounds = (-2, 8, -0.8, 0.8)
        else:
            limit = max(0.3, p.amplitude * 1.5)
            self.bounds = (-limit, limit, -0.5, 0.5)

    def start(self):
        if self.running:
            return
        if self.engine.reading.landed or self.t >= 120:
            self.reset()
        self.running = True
        self.play_btn.configure(text="Ⅱ 일시정지")
        self.status.configure(text="재생 중 · 재생 속도를 바꿔도 실험의 물리 조건은 같습니다.")
        self._last_clock = time.perf_counter()
        self._job = self.after(max(10, round(1000 / self.fps)), self._tick)

    def stop(self):
        self.running = False
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        self.play_btn.configure(text="▶ 계속")

    def toggle(self):
        if self.running:
            self.stop()
            self.status.configure(text="일시정지 · 계속 버튼으로 현재 상태에서 이어갈 수 있습니다.")
        else:
            self.start()

    def step_once(self):
        self.stop()
        self._advance(4)
        if not self.engine.reading.landed and self.t < 120:
            self.status.configure(text="한 단계 이동 · 1/60초의 물리 시간을 진행했습니다.")
        self.redraw()

    def _tick(self):
        self._job = None
        if not self.running or not self.winfo_exists():
            return
        now = time.perf_counter()
        elapsed = now - self._last_clock
        self._last_clock = now
        if elapsed > 2:
            self.stop()
            self.status.configure(text="화면이 오래 멈춰 실험을 일시정지했습니다. 계속 버튼으로 이어가세요.")
            return
        self._accumulator += elapsed * float(self.speed_var.get().replace("배", ""))
        steps = int(self._accumulator / FIXED_DT)
        self._accumulator -= steps * FIXED_DT
        self._advance(steps)
        self.redraw()
        if self.running:
            self._job = self.after(max(10, round(1000 / self.fps)), self._tick)

    def _advance(self, steps):
        for _ in range(steps):
            q = self.engine.step()
            self.t = q.time
            if self.kind == "force":
                xmin, xmax, ymin, ymax = self.bounds
                span = xmax - xmin
                if q.x > xmin + 0.8 * span or q.x < xmin + 0.2 * span:
                    self.bounds = (q.x - span / 2, q.x + span / 2, ymin, ymax)
            self.apex = max(self.apex, q.y)
            if round(q.time / FIXED_DT) % 12 == 0 or q.landed:
                self.trail.append(q); self.history.append(q)
            if q.landed or q.time >= 120:
                self.stop()
                self.status.configure(text="착지 완료 · 시작을 누르면 새로 발사합니다." if q.landed else "120초 관찰 완료 · 시작을 누르면 새 실험을 시작합니다.")
                break

    def _map(self, x, y):
        xmin, xmax, ymin, ymax = self.bounds
        w, h = max(220, self.canvas.winfo_width()), self.canvas.winfo_height()
        sx, sy = (w - 72) / (xmax - xmin), (h - 58) / (ymax - ymin)
        if self.kind not in ("spring", "force"):
            sx = sy = min(sx, sy)
        left = 53 + (w - 72 - sx * (xmax - xmin)) / 2
        bottom = h - 34 - (h - 58 - sy * (ymax - ymin)) / 2
        return (left + (x - xmin) * sx, bottom - (y - ymin) * sy)

    def _grid(self):
        c, t = self.canvas, self.theme
        xmin, xmax, ymin, ymax = self.bounds
        for i in range(5):
            x, y = xmin + (xmax - xmin) * i / 4, ymin + (ymax - ymin) * i / 4
            a, b = self._map(x, ymin), self._map(x, ymax)
            c.create_line(*a, *b, fill=t["line"])
            c.create_text(a[0], a[1] + 15, text=f"{x:.2g}", fill=t["muted"], font=("Consolas", 8))
            if self.kind != "spring":
                a, b = self._map(xmin, y), self._map(xmax, y)
                c.create_line(*a, *b, fill=t["line"])
                c.create_text(a[0] - 6, a[1], text=f"{y:.2g}", anchor="e", fill=t["muted"], font=("Consolas", 8))
        if ymin <= 0 <= ymax:
            c.create_line(*self._map(xmin, 0), *self._map(xmax, 0), fill=t["muted"], width=1.5)
        if xmin <= 0 <= xmax:
            c.create_line(*self._map(0, ymin), *self._map(0, ymax), fill=t["muted"], width=1.5)

    def _ball(self, x, y, radius, color):
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline=self.theme["surface"], width=2)
        self.canvas.create_oval(x - radius * 0.45, y - radius * 0.55, x - radius * 0.05, y - radius * 0.15, fill=self.theme["surface"], outline="")

    def _velocity_arrow(self, x, y, vx, vy):
        magnitude = math.hypot(vx, vy)
        if magnitude < 1e-6:
            return
        scale = min(5, 65 / magnitude)
        endx, endy = x + vx * scale, y - vy * scale
        self.canvas.create_line(x, y, endx, endy, arrow="last", arrowshape=(9, 11, 4), fill=self.theme["blue"], width=2)
        self.canvas.create_text(endx + 6, endy - 7, text="v", fill=self.theme["blue"], font=("Consolas", 10, "bold"))

    def redraw(self):
        if not hasattr(self, "engine") or self.canvas.winfo_width() < 10:
            return
        c, t, q, p = self.canvas, self.theme, self.engine.reading, self.engine.settings
        c.delete("all")
        self._grid()
        lost = max(0.0, self.initial_energy - q.energy)
        if self.kind == "projectile":
            vacuum = [coordinate for point in self.vacuum for coordinate in self._map(*point)]
            c.create_line(*vacuum, fill=t["muted"], width=1.5, dash=(5, 5))
            path = [coordinate for r in self.trail for coordinate in self._map(r.x, r.y)]
            if len(path) >= 4:
                c.create_line(*path, fill=t["accent"], width=2.5)
            x, y = self._map(q.x, q.y)
            self._velocity_arrow(x, y, q.vx, q.vy)
            self._ball(x, y, 8, t["accent"])
            self.legend.configure(text="x: 수평 거리 (m) · y: 높이 (m) · 같은 축척 · 점선: 진공의 전체 궤적 · 파란 화살표: 속도 방향")
            speed_label = "착지 직전 속력" if q.landed else "속력"
            text = f"시간 {q.time:.3f} s   |   x {q.x:.3f} m   |   높이 {q.y:.3f} m\n{speed_label} {q.speed:.3f} m/s   |   역학적 에너지 {q.energy:.3f} J   |   저항으로 잃은 에너지 {lost:.3f} J\n관측 최고 높이 {self.apex:.3f} m"
            if q.landed:
                text += f"   |   비행 시간 {q.time:.3f} s   |   도달 거리 {q.x:.3f} m"
        elif self.kind == "pendulum":
            arc = [coordinate for a in range(-120, 121, 3) for coordinate in self._map(p.length * math.sin(math.radians(a)), -p.length * math.cos(math.radians(a)))]
            c.create_line(*arc, fill=t["line"], width=2, dash=(3, 4))
            pivot, bob = self._map(0, 0), self._map(q.x, q.y)
            c.create_line(*pivot, *bob, fill=t["accent"], width=3)
            c.create_line(pivot[0] - 24, pivot[1] - 5, pivot[0] + 24, pivot[1] - 5, fill=t["muted"], width=5)
            self._velocity_arrow(*bob, q.vx, q.vy)
            self._ball(*pivot, 4, t["muted"]); self._ball(*bob, 13, t["accent"])
            reference = 2 * math.pi * math.sqrt(p.length / p.gravity)
            self.legend.configure(text="고정점이 원점 · x, y (m) · 같은 축척 · θ: 수직 아래부터 잰 각도 · 파란 화살표: 속도 방향")
            text = f"시간 {q.time:.3f} s   |   각도 {math.degrees(q.angle):.2f}°   |   각속도 {q.angular_velocity:.3f} rad/s\n속력 {q.speed:.3f} m/s   |   역학적 에너지 {q.energy:.3f} J   |   감쇠로 잃은 에너지 {lost:.3f} J\n작은 각도 참고 주기 T₀ {reference:.3f} s · 큰 각도의 실제 주기는 이 값보다 길어집니다."
        elif self.kind == "force":
            position = self._map(q.x, 0)
            c.create_rectangle(position[0]-19,position[1]-19,position[0]+19,position[1]+19,fill=t["accent"],outline=t["surface"],width=2)
            self._velocity_arrow(*position, q.vx, 0)
            if abs(p.applied_force) > 1e-12:
                direction = 1 if p.applied_force > 0 else -1
                c.create_line(position[0],position[1]+36,position[0]+direction*65,position[1]+36,arrow="last",fill=t["danger"],width=3)
                c.create_text(position[0]+direction*72,position[1]+36,text="F",fill=t["danger"],font=("Consolas",-12,"bold"))
            work = p.applied_force * q.x
            error = q.energy-self.initial_energy-work
            self.legend.configure(text="x: 실제 위치 (m) · 물체를 따라 이동하는 눈금 · 벽 없음 · 파랑: 속도 · 빨강: 일정한 힘")
            text = f"시간 {q.time:.6f} s  |  실제 위치 x {q.x:.6f} m  |  속도 v {q.vx:.6f} m/s\n가속도 {p.applied_force/p.mass:.6f} m/s²  |  운동에너지 {q.energy:.6f} J  |  외력이 한 일 {work:.6f} J\n일-에너지 검산 ΔK−W {error:.3e} J · 화면 이동은 물리 좌표를 바꾸지 않습니다."
        else:
            anchor, mass = self._map(self.bounds[0], 0), self._map(q.x, 0)
            c.create_line(anchor[0], anchor[1] - 37, anchor[0], anchor[1] + 37, fill=t["muted"], width=5)
            coil = [*anchor]
            for i in range(1, 25):
                coil.extend((anchor[0] + (mass[0] - anchor[0]) * i / 25, anchor[1] + (9 if i % 2 else -9)))
            coil.extend(mass)
            c.create_line(*coil, fill=t["accent"], width=2.5)
            c.create_rectangle(mass[0] - 17, mass[1] - 17, mass[0] + 17, mass[1] + 17, fill=t["accent"], outline=t["surface"], width=2)
            self._velocity_arrow(*mass, q.vx, 0)
            damping = p.spring_damping / (2 * math.sqrt(p.stiffness * p.mass))
            regime = "진동하며 감쇠" if damping < 1 - 1e-6 else "과감쇠" if damping > 1 + 1e-6 else "임계 감쇠"
            self.legend.configure(text="x: 평형 위치에서 잰 수평 변위 (m) · 용수철 모양은 이해를 돕는 표현 · 파란 화살표: 속도 방향")
            text = f"시간 {q.time:.3f} s   |   변위 {q.x:.3f} m   |   속도 {q.vx:.3f} m/s\n역학적 에너지 {q.energy:.3f} J   |   저항으로 잃은 에너지 {lost:.3f} J\n감쇠비 ζ {damping:.3f} · {regime}"
        if self.kind != "force":
            lossless = (self.kind == "projectile" and p.quadratic_drag == 0) or (self.kind == "pendulum" and p.angular_damping == 0) or (self.kind == "spring" and p.spring_damping == 0)
            if lossless:
                text += f"\n에너지 보존 검산 ΔE = {q.energy-self.initial_energy:+.3e} J"
        self.info.configure(text=text)
        self._draw_history()

    def _draw_history(self):
        if not hasattr(self, "engine"):
            return
        c, t = self.history_canvas, self.theme
        c.delete("all")
        w, h = max(220, c.winfo_width()), max(100, c.winfo_height())
        now = self.engine.reading.time
        start, end = max(0, now - 12), max(12, now)
        data = [q for q in self.history if q.time >= start]
        if self.kind == "pendulum":
            value = lambda q: math.degrees(q.angle)
            minimum, maximum = -max(5, self.engine.settings.angle_degrees * 1.1), max(5, self.engine.settings.angle_degrees * 1.1)
            title = "시간에 따른 각도 θ (°) · 최근 12초"
        elif self.kind == "spring":
            value = lambda q: q.x
            minimum, maximum = -max(0.1, self.engine.settings.amplitude * 1.1), max(0.1, self.engine.settings.amplitude * 1.1)
            title = "시간에 따른 변위 x (m) · 최근 12초"
        elif self.kind == "force":
            value = lambda q: q.vx
            speeds = [q.vx for q in data] + [self.engine.reading.vx]
            minimum, maximum = min(0,min(speeds)), max(0,max(speeds))
            pad = max(1, (maximum-minimum)*0.1)
            minimum -= pad; maximum += pad
            title = "시간에 따른 실제 속도 v (m/s) · 최근 12초"
        else:
            value = lambda q: q.energy
            minimum, maximum = 0, max(1, self.initial_energy * 1.08)
            title = "시간에 따른 역학적 에너지 E (J) · 최근 12초"
        c.create_text(12, 12, text=title, anchor="w", fill=t["muted"], font=("Malgun Gothic", 8))
        left, right, top, bottom = 53, w - 18, 31, h - 25
        def point(q):
            return (left + (q.time - start) / (end - start) * (right - left), bottom - (value(q) - minimum) / (maximum - minimum) * (bottom - top))
        for i in range(3):
            y = top + (bottom - top) * i / 2
            number = maximum - (maximum - minimum) * i / 2
            c.create_line(left, y, right, y, fill=t["line"])
            c.create_text(left - 6, y, text=f"{number:.2g}", anchor="e", fill=t["muted"], font=("Consolas", 8))
        c.create_text(left, bottom + 14, text=f"{start:.1f} s", fill=t["muted"], font=("Consolas", 8))
        c.create_text(right, bottom + 14, text=f"{end:.1f} s", fill=t["muted"], font=("Consolas", 8))
        points = [coordinate for q in data for coordinate in point(q)]
        if len(points) >= 4:
            c.create_line(*points, fill=t["green"], width=2)
        x, y = point(self.engine.reading)
        c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=t["green"], outline="")

    def destroy(self):
        self.stop()
        if self._parameter_job:
            self.after_cancel(self._parameter_job)
            self._parameter_job = None
        super().destroy()
