# -*- coding: utf-8 -*-
"""Embedded five-slot concept quiz panel for the existing Tkinter detail view.

Every rendered answer comes from a validated bank record. Missing slots are
truthfully identified rather than auto-filled with unverified trivia.
"""
from __future__ import annotations

import tkinter as tk

from quiz_engine import PER_CONCEPT, QuizProgress, get_bank, recommend_questions
from concept_drills_359 import ConceptDrillIndex


def build_concept_quiz_panel(app, parent, term):
    t = app.theme
    bank = get_bank()
    progress = getattr(app, "_quiz_progress_355", None)
    if progress is None:
        progress = QuizProgress()
        app._quiz_progress_355 = progress

    curated = recommend_questions(bank.for_term(term), progress)
    if not hasattr(app, "_concept_drills_359"):
        app._concept_drills_359 = ConceptDrillIndex(app.terms)
    missing = max(0, PER_CONCEPT - len(curated))
    # Only fill absent slots with deterministic metadata reading exercises.
    # These are visibly distinct and NEVER counted as reviewed question-bank entries.
    reading = recommend_questions(app._concept_drills_359.for_term(term), progress,
                                  limit=PER_CONCEPT)[:missing] if missing else []
    questions = curated + reading
    wrapper = app._card(parent, padx=22, pady=18)
    wrapper.pack(fill="x", pady=6)
    body = app._put_card_content(wrapper)
    title = tk.Frame(body, bg=t["surface"])
    title.pack(fill="x", pady=(0, 8))
    tk.Label(title, text="개념 확인문제", bg=t["surface"], fg=t["text"],
             font=("Malgun Gothic", app._font(13), "bold")).pack(side="left")
    tk.Label(title, text=f"검수 문제 {len(curated)} · 카드 연습 {len(reading)}", bg=t["surface"],
             fg=t["accent2"], font=("Malgun Gothic", app._font(9), "bold")).pack(side="right")

    tk.Label(body,
        text="정식 검수 문항이 부족하면 해당 카드의 설명·분류를 묻는 자동 독해 연습으로 채웁니다. 카드 연습은 독립 검증된 문제은행 문항이 아니며, 정답률 기반 추천은 로컬에서만 동작합니다.",
        bg=t["surface"], fg=t["muted"], justify="left", anchor="w", wraplength=780,
        font=("Malgun Gothic", app._font(9))).pack(fill="x", pady=(0, 11))

    for index in range(PER_CONCEPT):
        card = tk.Frame(body, bg=t["surface2"], highlightbackground=t["line"], highlightthickness=1)
        card.pack(fill="x", pady=4, ipadx=12, ipady=8)
        if index >= len(questions):
            tk.Label(card, text=f"{index + 1}. 검증된 문제 준비 중",
                     bg=t["surface2"], fg=t["muted"],
                     font=("Malgun Gothic", app._font(9))).pack(anchor="w", padx=10, pady=6)
            continue

        q = questions[index]
        tk.Label(card, text=f"{index+1}. {q['question']}",
                 bg=t["surface2"], fg=t["text"],
                 font=("Malgun Gothic", app._font(10), "bold"),
                 justify="left", anchor="w", wraplength=770).pack(fill="x", padx=10, pady=(7, 3))
        tk.Label(card, text=f"{q['subject']} · {q['difficulty']} · {q['kind']} · {q['match']}",
                 bg=t["surface2"], fg=t["muted"],
                 font=("Malgun Gothic", app._font(8))).pack(anchor="w", padx=10, pady=(0, 5))
        feedback = tk.StringVar(value="보기를 선택하면 정답과 해설을 확인할 수 있습니다.")
        buttons = []

        def select(answer_index, question=q, message=feedback, options=buttons):
            correct = answer_index == question["answer_index"]
            progress.record(question["id"], correct)
            message.set(("정답입니다. " if correct else
                         "오답입니다. 정답: " + question["choices"][question["answer_index"]] + "\n")
                        + question["explanation"])
            for n, button in enumerate(options):
                button.configure(state="disabled",
                    bg=t["accent_soft"] if n == question["answer_index"] else t["surface3"],
                    fg=t["accent2"] if n == question["answer_index"] else t["muted"])

        for j, text in enumerate(q["choices"]):
            button = tk.Button(card, text=f"{j+1}. {text}", command=lambda j=j: select(j),
                relief="flat", bd=0, bg=t["surface"], fg=t["text"],
                activebackground=t["accent_soft"], activeforeground=t["accent2"],
                font=("Malgun Gothic", app._font(9)), anchor="w",
                justify="left", padx=12, pady=6, cursor="hand2")
            button.pack(fill="x", padx=10, pady=2)
            buttons.append(button)
        tk.Label(card, textvariable=feedback, bg=t["surface2"], fg=t["muted"],
            font=("Malgun Gothic", app._font(9)), justify="left", anchor="w",
            wraplength=765).pack(fill="x", padx=10, pady=(6, 8))

    if len(reading):
        tk.Label(body,
            text="카드 연습은 저장된 문구와 분류의 일치 여부를 확인하는 기초 독해 활동입니다. 새로운 물리·과학 법칙의 참거짓을 검증하지 않으며 고유 검수 문제 수에 포함되지 않습니다.",
            bg=t["surface"], fg=t["muted"], justify="left", anchor="w", wraplength=780,
            font=("Malgun Gothic", app._font(8))).pack(fill="x", pady=(9, 0))
    if len(questions) < PER_CONCEPT:
        tk.Label(body, text="일부 학습 카드에는 자료가 부족해 5문항을 완성할 수 없습니다.",
                 bg=t["surface"], fg=t["muted"], justify="left", anchor="w",
                 font=("Malgun Gothic", app._font(8))).pack(fill="x", pady=(6, 0))
    return wrapper
