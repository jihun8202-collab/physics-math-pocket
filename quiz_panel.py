# -*- coding: utf-8 -*-
"""Embedded five-slot concept quiz panel for the existing Tkinter detail view.

Every rendered answer comes from a validated bank record. Missing slots are
truthfully identified rather than auto-filled with unverified trivia.
"""
from __future__ import annotations

import tkinter as tk

from quiz_engine import PER_CONCEPT, QuizProgress, get_bank, recommend_questions


def build_concept_quiz_panel(app, parent, term):
    t = app.theme
    bank = get_bank()
    progress = getattr(app, "_quiz_progress_355", None)
    if progress is None:
        progress = QuizProgress()
        app._quiz_progress_355 = progress

    questions = recommend_questions(bank.for_term(term), progress)
    wrapper = app._card(parent, padx=22, pady=18)
    wrapper.pack(fill="x", pady=6)
    body = app._put_card_content(wrapper)
    title = tk.Frame(body, bg=t["surface"])
    title.pack(fill="x", pady=(0, 8))
    tk.Label(title, text="개념 확인문제", bg=t["surface"], fg=t["text"],
             font=("Malgun Gothic", app._font(13), "bold")).pack(side="left")
    tk.Label(title, text=f"{len(questions)}/{PER_CONCEPT}개 준비됨", bg=t["surface"],
             fg=t["accent2"], font=("Malgun Gothic", app._font(9), "bold")).pack(side="right")

    tk.Label(body,
        text="문제 추천: 이 개념·연관 개념을 먼저 선택하며, 정답률과 오답 기록에 따라 난이도와 유형을 조정합니다. 로컬 규칙 기반으로 동작합니다.",
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

    if len(questions) < PER_CONCEPT:
        tk.Label(body, text="부족한 문항은 실제로 검증된 문제가 등록될 때 채워집니다. 같은 내용을 반복해서 문제 개수를 부풀리지 않습니다.",
                 bg=t["surface"], fg=t["muted"], justify="left", anchor="w", wraplength=780,
                 font=("Malgun Gothic", app._font(8))).pack(fill="x", pady=(9, 0))
    return wrapper
