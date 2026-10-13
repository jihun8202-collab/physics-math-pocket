# -*- coding: utf-8 -*-
"""Inspectable two-dimensional collisions using an independent physical engine."""
from __future__ import annotations

from collections import deque
from dataclasses import replace
import math
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional

from collision_engine import Disc, CollisionEngine, CollisionSettings

FIXED_DT = 1 / 240
WORLD_WIDTH, WORLD_HEIGHT = 10.0, 6.0
COLORS = ("#5B69EC", "#E58B43", "#29A785", "#D7678B", "#9274DA", "#24A8C2")
BOUNDARIES = {"반사 벽 · 외부 충격량 있음": "reflect",
              "열린 경계 · 바깥에서도 계속 이동": "open",
              "주기 경계 · 반대편으로 연결": "periodic"}
PRESETS = ("정면 탄성 충돌", "서로 다른 질량", "비스듬한 충돌", "공 여러 개 · 당구 모형")


def preset_bodies(name: str) -> tuple:
    if name == PRESETS[1]:
        return (Disc("A", 2, 3, 2, 0, 1, .3), Disc("B", 7, 3, -1, 0, 3, .3))
    if name == PRESETS[2]:
        return (Disc("A", 2, 2, 2, .5, 1, .3), Disc("B", 6, 3, -1, 0, 1, .3))
    if name == PRESETS[3]:
        return (Disc("A", 1.5, 3, 3, 0, 1, .25), Disc("B", 6, 3, 0, 0, 1, .25),
                Disc("C", 6.75, 3.38, 0, 0, 1, .25), Disc("D", 6.85, 2.55, 0, 0, 1, .25))
    return (Disc("A", 2, 3, 2, 0, 1, .3), Disc("B", 7, 3, -1, 0, 1, .3))


def evenly_spaced_bodies(count: int) -> tuple:
    if not 2 <= count <= 6:
        raise ValueError("물체 수는 2~6개로 정하세요.")
    return tuple(Disc(chr(65+i), 1.25+1.5*i, 3, 1.5 if i==0 else 0, 0, 1, .28)
                 for i in range(count))


def finite_number(text: str, label: str, lo: float, hi: float) -> float:
    try:
        value = float(text)
    except (ValueError, TypeError):
        raise ValueError(f"{label}: 숫자를 입력하세요.") from None
    if not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"{label}: {lo:g}~{hi:g} 범위의 유한한 수를 입력하세요.")
    return value


class CollisionSimulator(tk.Frame):
    """MiniSimulator-compatible lifecycle. Conditions are separate from live readings."""
    sim_id = "enhanced_collision"

    def __init__(self, master: tk.Misc, theme: dict, fps: int = 30):
        super().__init__(master, bg=theme["surface"])
        self.theme = theme
        self.fps = 60 if fps >= 60 else 30
        self.running = False
        self.t = 0.0
        self._job: Optional[str] = None
        self._last_clock = 0.0
        self._accumulator = 0.0
        self._selected_id = "A"
        self._drag_id = None
        self._ghost = None
        self._columns = 0
        self._populating = False
        self.initial_bodies = preset_bodies(PRESETS[0])
        self.settings = CollisionSettings(width=WORLD_WIDTH, height=WORLD_HEIGHT,
                                          boundary="reflect", restitution=1.0)
        self.trails = {}
        self.event_log = deque(maxlen=8)
        self._last_trail_time = 0.0
        self._build()
        self.reset()
        self.bind("<Configure>", self._layout)

    def _button(self, master, text, command, primary=False):
        t = self.theme
        return tk.Button(master, text=text, command=command, relief="flat", bd=0,
                         bg=t["accent"] if primary else t["accent_soft"],
                         fg="white" if primary else t["accent2"],
                         activebackground=t["surface2"], activeforeground=t["accent2"],
                         font=("Malgun Gothic", 9, "bold"), padx=11, pady=7, cursor="hand2")

    def _build(self):
        t = self.theme
        self.title_label = tk.Label(self, text="충돌 실험실 · 여러 물체의 2차원 운동", bg=t["surface"],
                                    fg=t["text"], anchor="w", justify="left", font=("Malgun Gothic", 13, "bold"))
        self.title_label.pack(fill="x", pady=(0, 5))
        self.intro_label = tk.Label(self, text="초기 위치를 끌어 옮기고 질량·반지름·속도를 숫자로 조절하세요. 충돌 전후 운동량과 에너지를 비교할 수 있어요.",
                                    bg=t["surface"], fg=t["muted"], anchor="w", justify="left", font=("Malgun Gothic", 9))
        self.intro_label.pack(fill="x", pady=(0, 12))

        setup = tk.Frame(self, bg=t["surface"])
        setup.pack(fill="x", pady=(0, 8))
        self.preset_var = tk.StringVar(value=PRESETS[0])
        preset = ttk.Combobox(setup, textvariable=self.preset_var, values=PRESETS, state="readonly", width=24)
        preset.pack(side="left", padx=(0, 6))
        preset.bind("<<ComboboxSelected>>", self.load_preset)
        tk.Label(setup, text="물체 수", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 4))
        self.count_var = tk.StringVar(value="2")
        count = ttk.Combobox(setup, textvariable=self.count_var, values=("2","3","4","5","6"), state="readonly", width=3)
        count.pack(side="left")
        count.bind("<<ComboboxSelected>>", self.change_count)

        self.environment = tk.Frame(self, bg=t["surface2"], padx=10, pady=8)
        self.environment.pack(fill="x", pady=(0, 9))
        boundary_row = tk.Frame(self.environment, bg=t["surface2"])
        boundary_row.pack(fill="x")
        self.boundary_var = tk.StringVar(value=next(iter(BOUNDARIES)))
        boundary = ttk.Combobox(boundary_row, textvariable=self.boundary_var, values=tuple(BOUNDARIES), state="readonly", width=35)
        boundary.pack(side="left", padx=(0, 10))
        boundary.bind("<<ComboboxSelected>>", lambda _: self.apply_conditions())
        tk.Label(boundary_row, text="반발계수 e", bg=t["surface2"], fg=t["text"], font=("Malgun Gothic", 9)).pack(side="left")
        self.restitution_var = tk.StringVar(value="1")
        self.restitution_entry = tk.Entry(boundary_row, textvariable=self.restitution_var, width=6,
                                           bg=t["surface"], fg=t["text"], insertbackground=t["text"], relief="flat",
                                           font=("Consolas", 10))
        self.restitution_entry.pack(side="left", ipady=4, padx=(6, 0))
        self.restitution_entry.bind("<Return>", lambda _: self.apply_conditions())

        editor_header = tk.Frame(self, bg=t["surface"])
        editor_header.pack(fill="x")
        tk.Label(editor_header, text="초기 조건 편집", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", 10, "bold")).pack(side="left")
        self.body_var = tk.StringVar(value="A")
        self.body_combo = ttk.Combobox(editor_header, textvariable=self.body_var, state="readonly", width=4)
        self.body_combo.pack(side="left", padx=8)
        self.body_combo.bind("<<ComboboxSelected>>", self.select_body)
        self.apply_btn = self._button(editor_header, "조건 적용 · 처음으로", self.apply_conditions)
        self.apply_btn.pack(side="right")
        self.editor = tk.Frame(self, bg=t["surface"])
        self.editor.pack(fill="x", pady=(7, 8))
        specs = (("mass","질량","kg",1), ("radius","반지름","m",.3),
                 ("x","처음 x","m",2), ("y","처음 y","m",3),
                 ("vx","처음 vx","m/s",2), ("vy","처음 vy","m/s",0))
        self._vars = {}
        self._controls = []
        for key, caption, unit, value in specs:
            cell = tk.Frame(self.editor, bg=t["surface2"], padx=9, pady=6)
            tk.Label(cell, text=f"{caption} ({unit})", bg=t["surface2"], fg=t["muted"], anchor="w",
                     font=("Malgun Gothic", 8)).pack(fill="x")
            var = tk.StringVar(value=str(value))
            self._vars[key] = var
            entry = tk.Entry(cell, textvariable=var, bg=t["surface"], fg=t["text"], insertbackground=t["text"],
                             relief="flat", font=("Consolas", 10), width=9)
            entry.pack(fill="x", ipady=4, pady=(4,0))
            entry.bind("<Return>", lambda _: self.apply_conditions())
            self._controls.append(cell)

        self.edit_hint = tk.Label(self, text="숫자를 수정한 뒤 조건 적용을 누르세요. 물체를 바꾸면 아직 적용하지 않은 입력은 취소됩니다. 일시정지 중 드래그하면 초기 위치를 바꾸고 시간을 0으로 되돌립니다.",
                                   bg=t["surface"], fg=t["muted"], anchor="w", justify="left", font=("Malgun Gothic", 8))
        self.edit_hint.pack(fill="x", pady=(0, 10))
        bar = tk.Frame(self, bg=t["surface"])
        bar.pack(fill="x", pady=(0, 7))
        self.play_btn = self._button(bar, "▶ 시작", self.toggle, True)
        self.play_btn.pack(side="left", padx=(0,6))
        self.reset_btn = self._button(bar, "처음으로", self.reset)
        self.reset_btn.pack(side="left", padx=(0,6))
        self.step_btn = self._button(bar, "한 단계 · 1/60 s", self.step_once)
        self.step_btn.pack(side="left", padx=(0,8))
        self.speed_var = tk.StringVar(value="1배")
        ttk.Combobox(bar, textvariable=self.speed_var, values=("0.1배","0.25배","0.5배","1배","2배"),
                     state="readonly", width=7).pack(side="left")

        view = tk.Frame(self, bg=t["surface"])
        view.pack(fill="x", pady=(0,8))
        self.velocity_var = tk.BooleanVar(value=True)
        self.momentum_var = tk.BooleanVar(value=False)
        self.trail_var = tk.BooleanVar(value=True)
        for text, var in (("속도 벡터",self.velocity_var),("운동량 벡터",self.momentum_var),("이동 자취",self.trail_var)):
            tk.Checkbutton(view, text=text, variable=var, command=self.redraw, bg=t["surface"], fg=t["text"],
                           selectcolor=t["surface2"], activebackground=t["surface"], font=("Malgun Gothic",9)).pack(side="left",padx=(0,10))
        self.status = tk.Label(self, text="", bg=t["surface"], fg=t["muted"], anchor="w", justify="left", font=("Malgun Gothic",9))
        self.status.pack(fill="x", pady=(0,8))
        self.canvas = tk.Canvas(self, width=650, height=355, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda _: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)
        self.legend = tk.Label(self, text="", bg=t["surface"], fg=t["muted"], anchor="w", justify="left", font=("Malgun Gothic",8))
        self.legend.pack(fill="x", pady=(5,8))
        self.info = tk.Label(self, text="", bg=t["surface2"], fg=t["text"], anchor="w", justify="left",
                             font=("Consolas",10), padx=12, pady=10)
        self.info.pack(fill="x", pady=(0,10))
        self.event_label = tk.Label(self,text="",bg=t["surface"],fg=t["accent2"],anchor="w",justify="left",font=("Malgun Gothic",8))
        self.event_label.pack(fill="x",pady=(0,8))

        tk.Label(self, text="현재 상태 · 행 선택: 초기 조건 편집 · 좁은 화면에서는 표 아래 가로 스크롤", bg=t["surface"], fg=t["text"], anchor="w",
                 font=("Malgun Gothic",9,"bold")).pack(fill="x", pady=(0,5))
        table_wrap = tk.Frame(self, bg=t["surface"])
        table_wrap.pack(fill="x")
        columns=("mass","radius","x","y","vx","vy","px","py","energy")
        self.table = ttk.Treeview(table_wrap, columns=columns, show="tree headings", height=4, selectmode="browse")
        self.table.heading("#0",text="물체")
        self.table.column("#0",width=42,minwidth=36,stretch=False,anchor="center")
        names=("m / kg","r / m","x / m","y / m","vx / m/s","vy / m/s","px / kg·m/s","py / kg·m/s","K / J")
        for column, name in zip(columns,names):
            self.table.heading(column,text=name)
            self.table.column(column,width=76,minwidth=68,anchor="e")
        hscroll = ttk.Scrollbar(table_wrap,orient="horizontal",command=self.table.xview)
        self.table.configure(xscrollcommand=hscroll.set)
        self.table.pack(fill="x")
        hscroll.pack(fill="x")
        self.table.bind("<<TreeviewSelect>>", self._table_selected)
        self.notes_label = tk.Label(self, text="모델과 가정 · 질량과 반지름이 있는 원판이 마찰 없이 직선 운동합니다. 접촉 순간의 법선 충격량만 계산하며, 회전·중력·변형 시간·접선 마찰은 생략합니다. e=1은 탄성, 0≤e<1은 운동 에너지 일부가 열·변형 등으로 바뀌는 모형입니다. 반사 벽에서는 벽의 충격량을 포함해야 운동량 수지가 맞습니다. 열린 경계에서는 화면 밖에서도 좌표 계산이 계속됩니다. 주기 경계에서는 양 끝이 이어져 있습니다. 동시 접촉은 질량과 접촉 방향을 함께 고려하는 강체 충격량 모형이며 실제 접촉의 변형 과정을 재현하지 않습니다.",
                                    bg=t["surface"],fg=t["muted"],anchor="w",justify="left",font=("Malgun Gothic",9))
        self.notes_label.pack(fill="x",pady=(10,0))

    def _layout(self,event):
        if event.widget is not self:
            return
        width=max(260,event.width)
        columns=3 if width>=720 else 2
        if self._columns!=columns:
            for i,cell in enumerate(self._controls):
                cell.grid(row=i//columns,column=i%columns,sticky="ew",padx=(0,6),pady=3)
            for i in range(3):
                self.editor.columnconfigure(i,weight=1 if i<columns else 0)
            self._columns=columns
        for label in (self.title_label,self.intro_label,self.edit_hint,self.status,self.legend,self.info,self.event_label,self.notes_label):
            label.configure(wraplength=max(220,width-24))

    def _set_status(self,text,error=False):
        self.status.configure(text=text,fg=self.theme["danger"] if error else self.theme["muted"])

    def _fill_editor(self):
        body=next((b for b in self.initial_bodies if b.id==self._selected_id),self.initial_bodies[0])
        self._selected_id=body.id
        self.body_var.set(body.id)
        self.body_combo.configure(values=tuple(b.id for b in self.initial_bodies))
        for key,var in self._vars.items():
            var.set(f"{getattr(body,key):.8g}")

    def select_body(self,_event=None):
        self._selected_id=self.body_var.get()
        self._fill_editor()
        self.redraw()

    def _table_selected(self,_event=None):
        if self._populating:
            return
        selection=self.table.selection()
        if selection:
            self._selected_id=selection[0]
            self._fill_editor()
            self.redraw()

    def apply_conditions(self):
        self.stop()
        try:
            values={key:finite_number(var.get(),key,
                      .05 if key in ("mass","radius") else -20 if key in ("vx","vy") else 0,
                      100 if key=="mass" else 1 if key=="radius" else 20 if key in ("vx","vy") else WORLD_WIDTH if key=="x" else WORLD_HEIGHT)
                    for key,var in self._vars.items()}
            bodies=tuple(replace(body,**values) if body.id==self._selected_id else body for body in self.initial_bodies)
            restitution=finite_number(self.restitution_var.get(),"반발계수 e",0,1)
            settings=CollisionSettings(width=WORLD_WIDTH,height=WORLD_HEIGHT,boundary=BOUNDARIES[self.boundary_var.get()],restitution=restitution)
            CollisionEngine(bodies,settings)
        except (ValueError,KeyError) as error:
            message=str(error)
            if "overlap" in message:
                message="물체가 겹칩니다. 초기 위치를 옮기거나 반지름을 줄이세요."
            elif "whole disc inside" in message:
                message="반사 벽에서는 물체 전체가 공간 안에 있어야 합니다. 초기 위치와 반지름을 확인하세요."
            elif "Periodic pairs" in message:
                message="주기 경계에서는 두 물체의 반지름 합이 1.5 m보다 작아야 합니다."
            self._set_status(message,True)
            return False
        self.initial_bodies,self.settings=bodies,settings
        self.reset()
        self._set_status("초기 조건을 적용했습니다. 시간이 0으로 되돌아갔어요.")
        return True

    def load_preset(self,_event=None):
        self.stop()
        self.initial_bodies=preset_bodies(self.preset_var.get())
        self._selected_id=self.initial_bodies[0].id
        self.count_var.set(str(len(self.initial_bodies)))
        self.boundary_var.set(next(iter(BOUNDARIES)))
        self.restitution_var.set("1")
        self.settings=CollisionSettings(width=WORLD_WIDTH,height=WORLD_HEIGHT,boundary="reflect",restitution=1)
        self.reset()

    def change_count(self,_event=None):
        self.stop()
        self.initial_bodies=evenly_spaced_bodies(int(self.count_var.get()))
        self._selected_id="A"
        self.reset()
        self._set_status("물체 수를 바꾸어 겹치지 않는 초기 배치를 만들었습니다. 각 물체의 값을 편집할 수 있어요.")

    def reset(self):
        self.stop()
        self.engine=CollisionEngine(self.initial_bodies,self.settings)
        self.initial_momentum=self.engine.momentum
        self.initial_energy=self.engine.kinetic_energy
        self.t=0.0
        self._accumulator=0.0
        self._ghost=None
        self.trails={body.id:deque([(body.x,body.y)],maxlen=900) for body in self.initial_bodies}
        self._last_trail_time=0.0
        self.event_log.clear()
        self._fill_editor()
        self.table.configure(height=min(6,len(self.initial_bodies)))
        self.play_btn.configure(text="▶ 시작")
        self._set_status("준비됨 · 일시정지 중 공을 끌어 초기 위치를 정할 수 있어요. 공간은 10 m × 6 m입니다.")
        self.redraw()

    def start(self):
        if self.running:
            return
        # Editing alone never changes a live experiment: the apply button does.
        self.running=True
        self._last_clock=time.perf_counter()
        self.play_btn.configure(text="Ⅱ 일시정지")
        self._set_status("재생 중 · 계산은 1/240초 간격으로 진행하며 화면 재생률과 분리되어 있습니다.")
        self._job=self.after(max(10,round(1000/self.fps)),self._tick)

    def stop(self):
        self.running=False
        if self._job:
            self.after_cancel(self._job)
            self._job=None
        if hasattr(self,"play_btn"):
            self.play_btn.configure(text="▶ 계속")

    def toggle(self):
        if self.running:
            self.stop()
            self._set_status("일시정지 · 계속하면 현재 상태에서 이어집니다. 공을 끌면 새 초기 배치로 되돌아갑니다.")
        else:
            self.start()

    def step_once(self):
        self.stop()
        if self._advance(4):
            self._set_status("한 단계 · 1/60초의 물리 시간을 진행했습니다.")
        self.redraw()

    def _tick(self):
        self._job=None
        if not self.running or not self.winfo_exists():
            return
        now=time.perf_counter()
        elapsed=now-self._last_clock
        self._last_clock=now
        if elapsed>2:
            self.stop()
            self._set_status("화면이 오래 멈춰 실험을 일시정지했습니다. 계속 버튼으로 이어가세요.")
            return
        self._accumulator+=elapsed*float(self.speed_var.get().replace("배",""))
        steps=int(self._accumulator/FIXED_DT)
        self._accumulator-=steps*FIXED_DT
        self._advance(steps)
        self.redraw()
        if self.running:
            self._job=self.after(max(10,round(1000/self.fps)),self._tick)

    def _advance(self,steps):
        for _ in range(steps):
            try:
                self.engine.advance(FIXED_DT)
            except (ValueError,RuntimeError) as error:
                self.stop()
                self._set_status("충돌 계산을 일시정지했습니다. 초기 배치를 바꾸어 다시 시도하세요. " + str(error),True)
                return False
            self.t=self.engine.time
            self.event_log.extend(event for event in self.engine.events if event.kind in ("wall","pair"))
            if self.t-self._last_trail_time>=1/30-1e-10:
                for body in self.engine.bodies:
                    self.trails[body.id].append((body.x,body.y))
                self._last_trail_time=self.t
        return True

    def _geometry(self):
        w,h=max(260,self.canvas.winfo_width()),max(200,self.canvas.winfo_height())
        scale=min((w-80)/WORLD_WIDTH,(h-65)/WORLD_HEIGHT)
        return (w-WORLD_WIDTH*scale)/2, (h+WORLD_HEIGHT*scale)/2-9, scale

    def _map(self,x,y):
        left,bottom,scale=self._geometry()
        return left+x*scale,bottom-y*scale

    def _unmap(self,x,y):
        left,bottom,scale=self._geometry()
        return (x-left)/scale,(bottom-y)/scale

    def _body_images(self,body):
        xs,ys=[body.x],[body.y]
        if self.settings.boundary=="periodic":
            if body.x<body.radius: xs.append(body.x+WORLD_WIDTH)
            if body.x>WORLD_WIDTH-body.radius: xs.append(body.x-WORLD_WIDTH)
            if body.y<body.radius: ys.append(body.y+WORLD_HEIGHT)
            if body.y>WORLD_HEIGHT-body.radius: ys.append(body.y-WORLD_HEIGHT)
        return [(x,y) for x in xs for y in ys]

    def _drag_start(self,event):
        if self.running:
            self._set_status("초기 위치를 편집하려면 먼저 일시정지하세요.")
            return
        x,y=self._unmap(event.x,event.y)
        def hit(body):
            dx,dy=body.x-x,body.y-y
            if self.settings.boundary=="periodic":
                dx-=WORLD_WIDTH*math.floor(dx/WORLD_WIDTH+.5)
                dy-=WORLD_HEIGHT*math.floor(dy/WORLD_HEIGHT+.5)
            return math.hypot(dx,dy)<=body.radius+.08
        body=next((b for b in reversed(self.engine.bodies) if hit(b)),None)
        if body:
            self._drag_id=body.id
            self._selected_id=body.id
            self._fill_editor()
            self.redraw()

    def _drag_motion(self,event):
        if not self._drag_id or self.running:
            return
        x,y=self._unmap(event.x,event.y)
        body=next(b for b in self.initial_bodies if b.id==self._drag_id)
        if self.settings.boundary=="reflect":
            x=max(body.radius,min(WORLD_WIDTH-body.radius,x))
            y=max(body.radius,min(WORLD_HEIGHT-body.radius,y))
        else:
            x=max(0,min(WORLD_WIDTH,x))
            y=max(0,min(WORLD_HEIGHT,y))
        bodies=tuple(replace(b,x=x,y=y) if b.id==body.id else b for b in self.initial_bodies)
        try:
            CollisionEngine(bodies,self.settings)
        except ValueError:
            self._ghost=(x,y,body.radius)
            self._set_status("이 위치에서는 물체가 겹칩니다. 서로 떨어진 위치에 놓으세요.",True)
            self.redraw()
            return
        self.initial_bodies=bodies
        self.reset()
        self._set_status("초기 위치를 바꾸어 시간을 0으로 되돌렸습니다.")

    def _drag_end(self,event):
        self._drag_id=None
        self._ghost=None
        self.redraw()

    def redraw(self):
        if not hasattr(self,"engine") or not self.winfo_exists():
            return
        c,t=self.canvas,self.theme
        c.delete("all")
        left,bottom,scale=self._geometry()
        def map_xy(point):
            return left+point[0]*scale,bottom-point[1]*scale
        for x in range(11):
            a,b=self._map(x,0),self._map(x,WORLD_HEIGHT)
            c.create_line(*a,*b,fill=t["line"])
            c.create_text(a[0],a[1]+15,text=str(x),fill=t["muted"],font=("Consolas",-11))
        for y in range(7):
            a,b=self._map(0,y),self._map(WORLD_WIDTH,y)
            c.create_line(*a,*b,fill=t["line"])
            c.create_text(a[0]-8,a[1],text=str(y),anchor="e",fill=t["muted"],font=("Consolas",-11))
        x0,y0=self._map(0,WORLD_HEIGHT)
        x1,y1=self._map(WORLD_WIDTH,0)
        c.create_rectangle(x0,y0,x1,y1,outline=t["accent2"] if self.settings.boundary=="reflect" else t["muted"],
                           width=2,dash=() if self.settings.boundary=="reflect" else (4,4))
        c.create_text(x1+10,y1+15,text="x / m",anchor="w",fill=t["muted"],font=("Consolas",-11))
        c.create_text(x0-10,y0-13,text="y / m",anchor="w",fill=t["muted"],font=("Consolas",-11))
        for i,body in enumerate(self.engine.bodies):
            color=COLORS[i]
            if self.trail_var.get():
                points=list(self.trails[body.id])
                segment=[]
                for point in points:
                    if segment and self.settings.boundary=="periodic" and (abs(point[0]-segment[-1][0])>WORLD_WIDTH/2 or abs(point[1]-segment[-1][1])>WORLD_HEIGHT/2):
                        if len(segment)>1:
                            c.create_line(*[v for point in segment for v in map_xy(point)],fill=color,width=1,tags=("trajectory",f"trail-{body.id}"))
                        segment=[]
                    segment.append(point)
                if len(segment)>1:
                    c.create_line(*[v for point in segment for v in map_xy(point)],fill=color,width=1,tags=("trajectory",f"trail-{body.id}"))
            r=body.radius*scale
            for image_i,(image_x,image_y) in enumerate(self._body_images(body)):
                x,y=self._map(image_x,image_y)
                c.create_oval(x-r,y-r,x+r,y+r,fill=color,outline=t["text"] if body.id==self._selected_id else t["surface"],
                              width=3 if body.id==self._selected_id else 1,tags=("disc" if image_i==0 else "periodic-image",body.id))
                c.create_text(x,y,text=body.id,fill="white",font=("Segoe UI",-12,"bold"))
                if self.velocity_var.get() and math.hypot(body.vx,body.vy)>1e-12:
                    endpoint=self._map(image_x+.35*body.vx,image_y+.35*body.vy)
                    c.create_line(x,y,*endpoint,fill=t["danger"],width=2,arrow="last",arrowshape=(8,10,4))
                if self.momentum_var.get() and math.hypot(body.vx,body.vy)>1e-12:
                    endpoint=self._map(image_x+.15*body.mass*body.vx,image_y+.15*body.mass*body.vy)
                    c.create_line(x,y,*endpoint,fill=t["green"],width=2,arrow="last",arrowshape=(8,10,4),dash=(4,2))
        if self._ghost:
            x,y,r=self._ghost
            x,y=self._map(x,y)
            c.create_oval(x-r*scale,y-r*scale,x+r*scale,y+r*scale,outline=t["danger"],width=2,dash=(4,3))
        if self.settings.boundary=="periodic":
            # Clip periodic images to the world; each edge shows the visible
            # part of the same disc, with its unchanged physical velocity.
            w,h=max(260,c.winfo_width()),max(200,c.winfo_height())
            for coords in ((0,0,w,y0),(0,y1,w,h),(0,y0,x0,y1),(x1,y0,w,y1)):
                c.create_rectangle(*coords,fill=t["surface2"],outline="")
            for x in range(11):
                a=self._map(x,0)
                c.create_text(a[0],a[1]+15,text=str(x),fill=t["muted"],font=("Consolas",-11))
            for y in range(7):
                a=self._map(0,y)
                c.create_text(a[0]-8,a[1],text=str(y),anchor="e",fill=t["muted"],font=("Consolas",-11))
            c.create_rectangle(x0,y0,x1,y1,outline=t["muted"],width=2,dash=(4,4))
            c.create_text(x1+10,y1+15,text="x / m",anchor="w",fill=t["muted"],font=("Consolas",-11))
            c.create_text(x0-10,y0-13,text="y / m",anchor="w",fill=t["muted"],font=("Consolas",-11))
        self.legend.configure(text="1칸 = 1 m · 빨간 실선: 속도, 1 m/s → 눈금 0.35 m · 초록 점선: 운동량, 1 kg·m/s → 눈금 0.15 m · 원의 크기는 실제 반지름 비율입니다. 주기 경계의 양쪽 조각은 같은 물체입니다.")
        px,py=self.engine.momentum
        jx,jy=self.engine.wall_impulse
        balance=math.hypot(px-self.initial_momentum[0]-jx,py-self.initial_momentum[1]-jy)
        self.info.configure(text=(f"t = {self.t:.3f} s   |   충돌 {self.engine.collision_count}회   |   총 운동량 p = ({px:.5g}, {py:.5g}) kg·m/s\n"
                                  f"운동 에너지 K = {self.engine.kinetic_energy:.6g} J   |   처음 K = {self.initial_energy:.6g} J   |   비탄성 손실 = {self.engine.dissipated_energy:.6g} J\n"
                                  f"누적 벽 충격량 J = ({jx:.5g}, {jy:.5g}) N·s   |   운동량 수지 오차 = {balance:.3g} kg·m/s"))
        if self.event_log:
            last=self.event_log[-1]
            target=" ↔ ".join(last.body_ids)+(" ↔ 벽" if last.kind=="wall" else "")
            self.event_label.configure(text=f"마지막 접촉 · {last.time:.4f} s · {target} · 법선 충격량 {last.impulse:.5g} N·s")
        else:
            self.event_label.configure(text="아직 접촉이 없습니다. 반발계수와 질량을 바꾸어 결과를 비교해 보세요.")
        self._populating=True
        try:
            existing=set(self.table.get_children())
            for body in self.engine.bodies:
                values=tuple(f"{value:.5g}" for value in (body.mass,body.radius,body.x,body.y,body.vx,body.vy,
                                                         body.mass*body.vx,body.mass*body.vy,.5*body.mass*(body.vx**2+body.vy**2)))
                if body.id in existing:
                    self.table.item(body.id,text=body.id,values=values)
                else:
                    self.table.insert("","end",iid=body.id,text=body.id,values=values)
                existing.discard(body.id)
            for item in existing:
                self.table.delete(item)
        finally:
            self._populating=False

    def destroy(self):
        self.stop()
        super().destroy()
