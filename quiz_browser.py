# -*- coding: utf-8 -*-
"""Filterable, offline quiz library with optional rule-based recommendations."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from quiz_engine import (SUBJECTS, DIFFICULTIES, KINDS, get_bank,
                         QuizProgress, recommend_questions)


def build_quiz_browser(app):
    app.current_page = "quizzes"
    app.current_term = None
    app._refresh_nav_state()
    host = app._clear_center()
    t = app.theme
    bank = get_bank()
    progress = getattr(app, "_quiz_progress_355", None)
    if progress is None:
        progress = QuizProgress()
        app._quiz_progress_355 = progress

    app._page_title(host, "문제은행", "난이도·유형별 탐색과 오답 복습 · 오프라인 기초 추천")
    inventory = bank.inventory()
    tk.Label(host, text=f"현재 검증 문항 {inventory['actual']:,}개  /  3.5.5 목표 {inventory['target']:,}개 · 과목당 목표 50,000개",
             fg=t["muted"], bg=t["bg"], font=("Malgun Gothic", app._font(9))).pack(anchor="w", pady=(0, 12))

    filters = tk.Frame(host, bg=t["surface"], highlightbackground=t["line"], highlightthickness=1)
    filters.pack(fill="x", pady=(0, 12), ipady=10)
    subject = tk.StringVar(value="전체")
    difficulty = tk.StringVar(value="전체")
    kind = tk.StringVar(value="전체")
    adaptive = tk.BooleanVar(value=True)
    for title, variable, choices in (
        ("과목", subject, ("전체", *SUBJECTS)),
        ("난이도", difficulty, ("전체", *DIFFICULTIES)),
        ("문제 유형", kind, ("전체", *KINDS)),
    ):
        group = tk.Frame(filters, bg=t["surface"])
        group.pack(side="left", padx=(15, 2))
        tk.Label(group, text=title, bg=t["surface"], fg=t["muted"],
                 font=("Malgun Gothic", app._font(8))).pack(anchor="w")
        box = ttk.Combobox(group, values=choices, textvariable=variable,
                           state="readonly", width=13)
        box.pack()
        box.bind("<<ComboboxSelected>>", lambda _e: refresh())
    tk.Checkbutton(filters, text="학습 기록으로 추천", variable=adaptive,
                   command=lambda: refresh(), bg=t["surface"], fg=t["text"],
                   selectcolor=t["surface"], activebackground=t["surface"],
                   font=("Malgun Gothic", app._font(9))).pack(side="left", padx=14)

    content = tk.Frame(host, bg=t["bg"])
    content.pack(fill="both", expand=True)
    content.grid_columnconfigure(0, weight=2)
    content.grid_columnconfigure(1, weight=3)
    content.grid_rowconfigure(0, weight=1)

    left = app._card(content, padx=12, pady=12)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    list_host = app._put_card_content(left)
    count = tk.StringVar(value="")
    tk.Label(list_host, textvariable=count, bg=t["surface"], fg=t["accent2"],
             font=("Malgun Gothic", app._font(9), "bold")).pack(anchor="w", pady=(0, 7))
    scroll = ttk.Scrollbar(list_host, orient="vertical")
    scroll.pack(side="right", fill="y")
    choices = tk.Listbox(list_host, bg=t["surface2"], fg=t["text"], relief="flat",
                         highlightthickness=0, selectbackground=t["accent_soft"],
                         selectforeground=t["accent2"], font=("Malgun Gothic", app._font(9)),
                         yscrollcommand=scroll.set)
    choices.pack(side="left", fill="both", expand=True)
    scroll.configure(command=choices.yview)

    right = app._card(content, padx=18, pady=15)
    right.grid(row=0, column=1, sticky="nsew")
    detail = app._put_card_content(right)
    visible = []

    def selected(_event=None):
        for child in detail.winfo_children():
            child.destroy()
        row = choices.curselection()
        if not row or row[0] >= len(visible):
            return
        q = visible[row[0]]
        tk.Label(detail, text=q["question"], bg=t["surface"], fg=t["text"],
                 font=("Malgun Gothic", app._font(12), "bold"), wraplength=540,
                 justify="left", anchor="w").pack(fill="x", pady=(0, 10))
        tk.Label(detail, text=f"{q['subject']} · {q['difficulty']} · {q['kind']} · {q.get('concept_name', '')}",
                 bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", app._font(9))).pack(anchor="w")
        feedback = tk.StringVar(value="보기를 골라 정답과 해설을 확인하세요.")
        option_buttons = []

        def answer(idx):
            progress.record(q["id"], idx == q["answer_index"])
            feedback.set(("정답! " if idx == q["answer_index"] else
                          "정답: " + q["choices"][q["answer_index"]] + "\n") + q["explanation"])
            for i,button in enumerate(option_buttons):
                button.configure(state="disabled",
                                 bg=t["accent_soft"] if i == q["answer_index"] else t["surface3"])

        for i,text in enumerate(q["choices"]):
            button = app._button(detail, f"{i+1}. {text}", lambda i=i: answer(i),
                                 kind="normal", padx=12, pady=8)
            button.configure(anchor="w", justify="left")
            button.pack(fill="x", pady=3)
            option_buttons.append(button)
        tk.Label(detail, textvariable=feedback, bg=t["surface"], fg=t["accent2"],
                 wraplength=540, justify="left", anchor="w",
                 font=("Malgun Gothic", app._font(9))).pack(fill="x", pady=(12, 8))
        source = q["source"]
        if source.startswith("https://"):
            app._link_button(detail, "출처 확인 ↗", lambda url=source: app.open_url(url)).pack(anchor="w")
        else:
            tk.Label(detail, text=source, bg=t["surface"], fg=t["muted"],
                     font=("Malgun Gothic", app._font(8))).pack(anchor="w")

    def refresh():
        records = bank.catalog(subject=subject.get(), difficulty=difficulty.get(),
                               kind=kind.get(), limit=80)
        if adaptive.get():
            records = recommend_questions(records, progress, limit=max(1, len(records)),
                                          difficulty=difficulty.get(), kind=kind.get())
        visible[:] = records
        choices.delete(0, "end")
        for q in records:
            choices.insert("end", f"[{q['difficulty']} / {q['kind']}] {q['question'][:58]}")
        count.set(f"조건에 맞는 문제 {len(records)}개 표시 (최대 80개)")
        if records:
            choices.selection_set(0)
            selected()
        else:
            for child in detail.winfo_children():
                child.destroy()
            tk.Label(detail, text="등록·검증된 문제가 아직 없습니다.", bg=t["surface"],
                     fg=t["muted"]).pack(anchor="w")

    choices.bind("<<ListboxSelect>>", selected)
    refresh()
    app.status_var.set("문제은행 · 오프라인 추천과 학습 기록")
    return host
