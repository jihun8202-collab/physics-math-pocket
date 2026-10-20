# -*- coding: utf-8 -*-
"""Five exact-source *reading exercises* for every concept card (v3.5.9).

These are NOT 350k editor-reviewed, subject-specific quiz questions. They
test information explicitly present on the app's stored concept card. This
separate fallback offers interactive exercises even when a curated question
bank has not yet reached a term. It does not contribute to verified inventory.
No LLM is used and no external scientific claims are invented.
"""
from __future__ import annotations

import hashlib
import unicodedata
from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Sequence

from quiz_engine import SUBJECTS, PER_CONCEPT


def _clean(value: object, length: int = 180) -> str:
    if not isinstance(value, str):
        return ""
    value = " ".join(value.split())
    return value if len(value) <= length else value[:length - 1].rstrip() + "…"


def _distinct(values: Iterable[str]) -> List[str]:
    output = []
    seen = set()
    for value in values:
        value = _clean(value)
        key = unicodedata.normalize("NFKC", value).casefold()
        if value and key not in seen:
            output.append(value)
            seen.add(key)
    return output


def _digest(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:18]


class ConceptDrillIndex:
    """Read-only lookup built once; lazily create up to five drills per term."""

    def __init__(self, terms: Iterable[dict]):
        self.by_subject: Dict[str, List[dict]] = defaultdict(list)
        self.all_terms: List[dict] = []
        self.subjects = tuple(SUBJECTS)
        for term in terms:
            if not isinstance(term, dict) or not term.get("id"):
                continue
            if term.get("subject") not in SUBJECTS:
                continue
            self.by_subject[term["subject"]].append(term)
            self.all_terms.append(term)
        self.category_pool = _distinct(t.get("category", "") for t in self.all_terms)
        self.level_pool = _distinct(t.get("level", "") for t in self.all_terms)

    @staticmethod
    def _rotated(items: Sequence[dict], tid: str):
        if not items:
            return
        index = int(_digest(tid), 16) % len(items)
        for offset in range(len(items)):
            yield items[(index + offset) % len(items)]

    def _peer_texts(self, term: dict, field: str, *, pool_size: int = 3) -> List[str]:
        """Prefer the same subject; fall back to other subjects when sparse."""
        seen = set()
        output = []
        tid = term.get("id", "")
        for candidates in (self.by_subject.get(term.get("subject"), []), self.all_terms):
            for peer in self._rotated(candidates, tid):
                if peer.get("id") == tid:
                    continue
                value = _clean(peer.get(field, ""))
                canonical = unicodedata.normalize("NFKC", value).casefold()
                if not value or canonical in seen:
                    continue
                seen.add(canonical)
                output.append(value)
                if len(output) >= pool_size + 8:
                    return output
        return output

    @staticmethod
    def _item(term: dict, slot: int, question: str, correct: str,
              other_options: Iterable[str], explanation: str,
              *, kind: str = "개념 확인", difficulty: str = "기초") -> dict:
        vals = _distinct([correct, *other_options])
        if len(vals) < 4:
            raise ValueError("A concept card lacks enough distinct options")
        correct = _clean(correct)
        options = vals[:4]
        # Deterministically shift option order without disturbing the correct value.
        rotation = int(_digest(term["id"] + "|" + str(slot)), 16) % 4
        options = options[rotation:] + options[:rotation]
        answer_index = options.index(correct)
        return {
            "id": "drill-359-" + _digest(term["id"]) + "-" + str(slot + 1),
            "subject": term["subject"],
            "concept_id": term["id"],
            "concept_name": term.get("name_ko", ""),
            "difficulty": difficulty, "kind": kind,
            "question": question, "choices": options,
            "answer_index": answer_index,
            "explanation": explanation,
            "source": "앱 개념 카드: " + term["id"],
            "review_status": "mechanically_derived",
            "match": "현재 개념 · 카드 읽기",
            "count_as_reviewed": False,
        }

    def for_term(self, term: dict) -> List[dict]:
        """Always five mechanically checkable items for supported built-in cards.

        If the source fields themselves are wrong, metadata drills cannot
        establish factual correctness. The UI must label them separately.
        """
        tid = term.get("id", "")
        subject = term.get("subject", "")
        title = _clean(term.get("name_ko", ""))
        if not tid or subject not in SUBJECTS or not title:
            return []
        summary = _clean(term.get("summary", ""))
        category = _clean(term.get("category", ""))
        level = _clean(term.get("level", ""))
        definition = summary or _clean(term.get("detail", "")) or title

        # 1. Recall which summary belongs to the current concept.
        summaries = self._peer_texts(term, "summary")
        if definition in summaries:
            summaries.remove(definition)
        first = self._item(
            term, 0, f"'{title}' 카드의 '한눈에 보기' 설명으로 기록된 내용은?",
            definition, summaries,
            "이 앱의 해당 개념 카드에는 다음 설명이 등록돼 있습니다: " + definition)

        # 2. Read a supplied description and identify the corresponding card.
        other_titles = [name for name in self._peer_texts(term, "name_ko") if name != title]
        second = self._item(
            term, 1, "다음은 어떤 학습 카드의 설명인가?\n" + definition,
            title, other_titles,
            f"이 설명은 앱에서 '{title}'라는 표제어 아래에 등록되어 있습니다.")

        # 3. Classify the course in which the card is filed.
        third = self._item(
            term, 2, f"앱에서 '{title}'가 속한 학습 과목은?",
            subject, (s for s in SUBJECTS if s != subject),
            f"앱 데이터에 기록된 과목 분류는 '{subject}'입니다.",
            kind="자료 해석")

        # 4. Distinguish the more specific category.
        if category:
            fourth = self._item(
                term, 3, f"'{title}' 카드의 세부 분류로 등록된 것은?",
                category, (v for v in self.category_pool if v != category),
                f"해당 개념의 분류 필드는 '{category}'입니다.",
                kind="자료 해석")
        else:
            # User-added records sometimes omit category: derive a numerical
            # spelling exercise directly from the title with an exact key.
            count = len(title.replace(" ", ""))
            fourth = self._item(
                term, 3, f"표제어 '{title}'의 공백을 제외한 글자 수는?",
                str(count) + "글자",
                (str(n) + "글자" for n in (count + 1, count + 2, count + 3)),
                f"표제어에서 공백을 제외하고 세면 {count}글자입니다.",
                kind="계산")

        # 5. Prefer an independent documented formula; otherwise level.
        formula = _clean(term.get("formula", ""))
        if formula and len(self._peer_texts(term, "formula")) >= 3:
            fifth = self._item(
                term, 4, f"'{title}' 카드에 기록된 대표 공식은?",
                formula, (v for v in self._peer_texts(term, "formula") if v != formula),
                "이 카드의 공식 필드에 다음 식이 등록돼 있습니다: " + formula,
                kind="자료 해석")
        elif level and len(_distinct([level, *self.level_pool])) >= 4:
            fifth = self._item(
                term, 4, f"'{title}' 카드에 기록된 학습 수준은?",
                level, (v for v in self.level_pool if v != level),
                f"앱 데이터에 등록된 학습 수준은 '{level}'입니다.",
                kind="자료 해석")
        else:
            length = len(title.replace(" ", ""))
            fifth = self._item(
                term, 4, f"표제어 '{title}'에서 공백을 제외하고 첫 글자 뒤에 남는 글자 수는?",
                str(max(0, length - 1)) + "글자",
                (str(n) + "글자" for n in (length, length + 1, length + 2)),
                f"공백 없는 표제어 {length}글자에서 첫 글자 하나를 빼면 {max(0, length-1)}글자입니다.",
                kind="계산")
        return [first, second, third, fourth, fifth]
