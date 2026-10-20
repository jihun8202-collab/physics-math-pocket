# -*- coding: utf-8 -*-
"""Korean curriculum study cards sharing the existing dictionary and user data."""
from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import Iterable, Optional

from core import load_json, normalize, hangul_initials, is_initial_query

CATEGORIES = ("전체", "문법", "문학", "읽기", "쓰기", "듣기·말하기", "매체", "어휘", "관용구", "속담", "사자성어", "맞춤법", "방언", "고어", "기타")


def filter_korean_terms(terms: Iterable[dict], query: str = "", category: str = "전체", limit: int | None = 300) -> list:
    """Search full explanations, examples, cautions, names and Korean initials."""
    q = normalize(query)
    initials = is_initial_query(query) if q else False
    results = []
    for term in terms:
        if term.get("subject") != "국어":
            continue
        short_category = term.get("category", "").removeprefix("국어 · ")
        if category != "전체" and short_category != category:
            continue
        blob = term.get("_search_blob") or normalize(" ".join(str(term.get(key, "")) for key in
                                  ("name_ko", "summary", "detail", "example", "caution", "category")))
        title = normalize(term.get("name_ko", ""))
        if q and q not in blob and not (initials and q in hangul_initials(term.get("name_ko", ""))):
            continue
        rank = 0 if q and title == q else 1 if q and title.startswith(q) else 2
        results.append((rank, CATEGORIES.index(short_category) if short_category in CATEGORIES else 99,
                        term.get("name_ko", ""), term))
    results.sort(key=lambda row: row[:3])
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        results = results[:limit]
    return [row[3] for row in results]


def evaluate_answer(quiz: dict, answer_index: int) -> tuple:
    choices = quiz.get("choices", [])
    if not isinstance(answer_index, int) or answer_index < 0 or answer_index >= len(choices):
        raise ValueError("보기 중 하나를 선택해 주세요.")
    right = quiz["answer_index"]
    correct = answer_index == right
    message = ("정답이에요. " if correct else "다시 생각해 보세요. ") + quiz.get("feedback", "")
    if not correct:
        message += "\n정답: " + choices[right]
    return correct, message


def source_label(url: str) -> str:
    if "kornorms" in url:
        return "국립국어원 어문 규정"
    if "stdict.korean.go.kr" in url:
        return "국립국어원 표준국어대사전"
    if "opendict.korean.go.kr" in url or "data.go.kr/data/15019347" in url:
        return "국립국어원 우리말샘"
    if "korean.go.kr" in url:
        return "국립국어원 설명"
    if "ncic.re.kr" in url:
        return "국가교육과정정보센터"
    return "참고 자료"


class _ScrollArea(tk.Frame):
    def __init__(self, master, bg):
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        self.canvas.bind("<MouseWheel>", self.scroll)

    def scroll(self, event):
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


def build_korean_page(app):
    """Build the app's Korean route. All 42 cards remain normal dictionary terms."""
    payload = load_json("data/korean_quizzes.json")
    quiz_by_id = {item["term_id"]: item for item in payload["items"]}
    terms = [term for term in app.terms if term.get("subject") == "국어"]
    session = getattr(app, "_korean_completed", None)
    if session is None:
        session = set()
        app._korean_completed = session
    t = app.theme
    frame = app._clear_center()
    app._page_title(frame, "국어 학습", "개념을 읽고, 예문을 살펴보고, 확인 문제로 이해를 점검하세요.")
    top = tk.Frame(frame, bg=t["bg"])
    top.pack(fill="x", pady=(0, 12))
    progress = tk.StringVar()
    def update_progress():
        progress.set(f"{len(terms)}개 개념 · 확인 완료 {len(session & set(quiz_by_id))}/{len(quiz_by_id)} · 이번 실행 기준")
    update_progress()
    tk.Label(top, textvariable=progress, bg=t["bg"], fg=t["accent2"],
             font=("Malgun Gothic", app._font(9), "bold")).pack(side="left")

    body = tk.Frame(frame, bg=t["bg"])
    body.pack(fill="both", expand=True)
    body.grid_columnconfigure(0, minsize=265)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=1)
    rail = app._card(body, padx=15, pady=15)
    rail.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    rail_content = app._put_card_content(rail)
    query = tk.StringVar()
    category = tk.StringVar(value="전체")
    tk.Label(rail_content, text="개념·예문 검색", bg=t["surface"], fg=t["text"],
             font=("Malgun Gothic", app._font(10), "bold")).pack(anchor="w", pady=(0, 8))
    entry = tk.Entry(rail_content, textvariable=query, relief="flat", bg=t["surface2"], fg=t["text"],
                     insertbackground=t["text"], font=("Malgun Gothic", app._font(10)))
    entry.pack(fill="x", ipady=8)
    combo = ttk.Combobox(rail_content, textvariable=category, values=CATEGORIES, state="readonly", width=20)
    combo.pack(fill="x", pady=10)
    count = tk.StringVar()
    tk.Label(rail_content, textvariable=count, bg=t["surface"], fg=t["muted"],
             font=("Malgun Gothic", app._font(8))).pack(anchor="w", pady=(0, 6))
    list_box_frame = tk.Frame(rail_content, bg=t["surface"])
    list_box_frame.pack(fill="both", expand=True)
    list_box = tk.Listbox(list_box_frame, exportselection=False, activestyle="none", relief="flat", bd=0,
                          bg=t["surface"], fg=t["text"], selectbackground=t["accent_soft"],
                          selectforeground=t["accent2"], font=("Malgun Gothic", app._font(10)),
                          height=16, width=24)
    scrollbar = ttk.Scrollbar(list_box_frame, command=list_box.yview)
    list_box.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    list_box.pack(side="left", fill="both", expand=True)
    detail = _ScrollArea(body, t["bg"])
    detail.grid(row=0, column=1, sticky="nsew")
    visible = []
    selected = {"id": None}
    pending = {"job": None}

    def label(master, text, size=10, color=None, bold=False):
        widget = tk.Label(master, text=text, bg=master.cget("bg"), fg=color or t["text"],
                          font=("Malgun Gothic", app._font(size), "bold" if bold else "normal"),
                          justify="left", anchor="w", wraplength=620)
        widget.pack(fill="x", anchor="w", pady=4)
        widget.bind("<Configure>", lambda e: widget.configure(wraplength=max(200, e.width-6)))
        widget.bind("<MouseWheel>", detail.scroll)
        return widget

    def card(title, text):
        outer = app._card(detail.inner, padx=20, pady=14)
        outer.pack(fill="x", pady=(0, 10))
        content = app._put_card_content(outer)
        label(content, title, 11, t["accent2"], True)
        label(content, text)
        return content

    def show(term):
        selected["id"] = term["id"]
        for child in detail.inner.winfo_children():
            child.destroy()
        detail.canvas.yview_moveto(0)
        header = card(term["name_ko"], term.get("summary", ""))
        label(header, term.get("category", "") + " · " + term.get("level", ""), 8, t["muted"])
        actions = tk.Frame(header, bg=t["surface"])
        actions.pack(fill="x", pady=(10, 0))
        app._button(actions, "사전 상세·메모", lambda: app.show_term(term, add_history=True), kind="subtle").pack(side="left")
        favorite = app._button(actions, "★ 즐겨찾기" if term["id"] in app.favorite_ids else "☆ 즐겨찾기", lambda: None, kind="ghost")
        def toggle():
            app.toggle_favorite(term)
            favorite.configure(text="★ 즐겨찾기" if term["id"] in app.favorite_ids else "☆ 즐겨찾기")
        favorite.configure(command=toggle)
        favorite.pack(side="left", padx=6)
        card("개념 이해", term.get("detail", ""))
        card("예문으로 확인", term.get("example", ""))
        card("헷갈리기 쉬운 점", term.get("caution", ""))
        quiz = quiz_by_id.get(term["id"])
        if quiz:
            content = card("확인 문제", quiz["question"])
            feedback = tk.StringVar(value="보기 하나를 선택하면 이유를 바로 확인할 수 있어요.")
            choices = []
            def answer(index):
                correct, text = evaluate_answer(quiz, index)
                feedback.set(text)
                feedback_label.configure(fg=t["green"] if correct else t["danger"])
                for i, button in enumerate(choices):
                    button.configure(bg=t["accent_soft"] if i==quiz["answer_index"] else t["surface2"],
                                     fg=t["accent2"] if i==quiz["answer_index"] else t["text"])
                if correct:
                    session.add(term["id"])
                    update_progress()
            for i, text in enumerate(quiz["choices"]):
                button = app._button(content, f"{i+1}. {text}", lambda i=i: answer(i), padx=12, pady=9)
                button.configure(anchor="w", justify="left", wraplength=560)
                button.pack(fill="x", pady=3)
                button.bind("<Configure>", lambda e,b=button: b.configure(wraplength=max(200,e.width-30)))
                button.bind("<MouseWheel>", detail.scroll)
                choices.append(button)
            feedback_label = label(content, "", 9, t["muted"])
            feedback_label.configure(textvariable=feedback)
        references = card("참고 자료", "예문과 문제는 앱에서 자체 작성했습니다. 사전·규정·교육과정 자료에서 더 확인할 수 있어요.")
        for source in term.get("sources", []):
            url = source if source.startswith("https://") else app.sources.get(source, {}).get("url", "")
            if url.startswith("https://"):
                app._link_button(references, source_label(url) + " ↗", lambda u=url: webbrowser.open(u)).pack(anchor="w")
        label(detail.inner, payload.get("scope_note", ""), 8, t["muted"])

    def choose(_event=None):
        selection = list_box.curselection()
        if selection and selection[0] < len(visible):
            show(visible[selection[0]])

    def refresh():
        pending["job"] = None
        if not frame.winfo_exists():
            return
        visible[:] = filter_korean_terms(terms, query.get(), category.get())
        list_box.delete(0, "end")
        for term in visible:
            list_box.insert("end", term["name_ko"])
        count.set(f"검색 결과 {len(visible)}개 표시" + (" · 더 구체적으로 검색해 보세요" if len(visible) >= 300 else ""))
        if visible:
            current = next((i for i,term in enumerate(visible) if term["id"]==selected["id"]), 0)
            list_box.selection_set(current)
            list_box.see(current)
            choose()
        else:
            for child in detail.inner.winfo_children():
                child.destroy()
            card("검색 결과가 없어요", "다른 낱말이나 예문 일부로 검색하거나 영역을 전체로 바꾸어 보세요.")

    def schedule(*_args):
        if pending["job"] is not None:
            frame.after_cancel(pending["job"])
        pending["job"] = frame.after(120, refresh)

    def on_destroy(event):
        if event.widget is frame and pending["job"] is not None:
            frame.after_cancel(pending["job"])
            pending["job"] = None
    frame.bind("<Destroy>", on_destroy)
    query.trace_add("write", schedule)
    combo.bind("<<ComboboxSelected>>", schedule)
    list_box.bind("<<ListboxSelect>>", choose)
    refresh()
    app.status_var.set("국어 학습 · 개념, 예문, 확인 문제")
    return frame
