# -*- coding: utf-8 -*-
"""Offline, source-attributed quiz bank and explainable adaptive recommender.

50,000 UNIQUE verified questions per subject is the 3.5.5 acceptance target,
not a claim about current inventory. Packaged SQLite shards are optional;
missing questions must never be fabricated to reach five items on a card.
"""
from __future__ import annotations

import json
import math
import sqlite3
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from core import normalize, resource_path, user_data_dir

SUBJECTS = ("수학", "물리", "화학", "생명과학", "지구과학", "천문학", "국어")
DIFFICULTIES = ("기초", "중급", "심화", "최상위")
KINDS = ("개념 확인", "계산", "적용", "자료 해석", "추론")
PER_SUBJECT_TARGET = 50000
TOTAL_TARGET = len(SUBJECTS) * PER_SUBJECT_TARGET
PER_CONCEPT = 5


def validate_question(item: dict) -> dict:
    """Canonical schema; review/source is required, no generated placeholders."""
    if not isinstance(item, dict):
        raise ValueError("Question must be an object")
    q = dict(item)
    if not isinstance(q.get("id"), str) or not q["id"] or len(q["id"]) > 140:
        raise ValueError("Question id required")
    if q.get("subject") not in SUBJECTS:
        raise ValueError("Unknown subject: " + str(q.get("subject")))
    if q.get("difficulty") not in DIFFICULTIES or q.get("kind") not in KINDS:
        raise ValueError("Unknown difficulty or question type")
    if not (q.get("concept_id") or q.get("concept_name")):
        raise ValueError("Every question must belong to a concept")
    if not isinstance(q.get("question"), str) or not q["question"].strip():
        raise ValueError("Missing question")
    choices = q.get("choices")
    if not isinstance(choices, list) or not 2 <= len(choices) <= 5:
        raise ValueError("Expected 2 to 5 options")
    if any(not isinstance(choice, str) or not choice.strip() for choice in choices):
        raise ValueError("Empty answer choice")
    if len({" ".join(unicodedata.normalize("NFKC", choice).casefold().split()) for choice in choices}) != len(choices):
        raise ValueError("Duplicate answer choice")
    idx = q.get("answer_index")
    if type(idx) is not int or idx not in range(len(choices)):
        raise ValueError("Invalid correct answer index")
    if not isinstance(q.get("explanation"), str) or len(q["explanation"].strip()) < 10:
        raise ValueError("A substantive answer explanation is required")
    if not isinstance(q.get("source"), str) or not q["source"].strip():
        raise ValueError("Source provenance is required")
    if q.get("review_status") not in ("curated", "source_checked"):
        raise ValueError("Only reviewed questions are installable")
    q["concept_id"] = str(q.get("concept_id", "") or "")
    q["concept_name"] = str(q.get("concept_name", "") or "")
    return q


def _legacy_korean_questions(path: Path) -> List[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in payload.get("items", []):
        records.append(validate_question({
            "id": "legacy-korean-" + item["term_id"],
            "subject": "국어",
            "concept_id": item["term_id"],
            "concept_name": "",
            "difficulty": "기초",
            "kind": "개념 확인",
            "question": item["question"],
            "choices": item["choices"],
            "answer_index": item["answer_index"],
            "explanation": item["feedback"],
            "source": "기존 앱에서 자체 작성한 국어 3.1.6 문제",
            "review_status": "curated",
        }))
    return records


class QuizBank:
    def __init__(self, questions: Iterable[dict], sqlite_path: Optional[Path] = None) -> None:
        self.questions: List[dict] = []
        self.by_concept_id: Dict[str, List[dict]] = {}
        self.by_concept_name: Dict[tuple, List[dict]] = {}
        self.by_subject: Dict[str, List[dict]] = {name: [] for name in SUBJECTS}
        seen = set()
        for item in questions:
            q = validate_question(item)
            if q["id"] in seen:
                raise ValueError("Duplicate quiz id: " + q["id"])
            seen.add(q["id"])
            self.questions.append(q)
            self.by_subject[q["subject"]].append(q)
            if q["concept_id"]:
                self.by_concept_id.setdefault(q["concept_id"], []).append(q)
            if q["concept_name"]:
                key = (q["subject"], normalize(q["concept_name"]))
                self.by_concept_name.setdefault(key, []).append(q)
        self.sqlite_path = sqlite_path if sqlite_path and sqlite_path.is_file() else None

    @classmethod
    def from_resources(cls) -> "QuizBank":
        base = resource_path("data")
        path = base / "quiz_bank_355.json"
        native = json.loads(path.read_text(encoding="utf-8"))["questions"] if path.exists() else []
        return cls([*_legacy_korean_questions(base / "korean_quizzes.json"), *native],
                   sqlite_path=base / "quiz_bank_355.sqlite3")

    def _sqlite_lookup(self, term: dict, related: bool) -> List[dict]:
        if not self.sqlite_path:
            return []
        name = normalize(term.get("name_ko", ""))
        terms = [name]
        if related:
            terms.extend(normalize(x) for x in term.get("related", [])[:15])
        placeholders = ",".join("?" for _ in terms)
        uri = self.sqlite_path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        try:
            rows = connection.execute(
                "SELECT payload_json FROM questions WHERE subject=? "
                "AND (concept_id=? OR concept_norm IN (" + placeholders + ")) "
                "LIMIT 150",
                [term.get("subject", ""), term.get("id", ""), *terms]
            ).fetchall()
            return [validate_question(json.loads(row[0])) for row in rows]
        finally:
            connection.close()

    def for_term(self, term: dict, *, related: bool = True) -> List[dict]:
        """Return exact-concept questions first, then authored related-concept items."""
        tid, subject = term.get("id", ""), term.get("subject", "")
        name = normalize(term.get("name_ko", ""))
        exact = [q for q in self.by_concept_id.get(tid, []) if q["subject"] == subject]
        exact.extend(self.by_concept_name.get((subject, name), []))
        candidates = list(exact)
        if related:
            for alias in term.get("related", [])[:15]:
                candidates.extend(self.by_concept_name.get((subject, normalize(alias)), []))
        candidates.extend(self._sqlite_lookup(term, related))
        unique = {}
        for q in candidates:
            if q["id"] not in unique:
                unique[q["id"]] = dict(q, match=("개념 확인" if
                    q["concept_id"] == tid or normalize(q["concept_name"]) == name else "연관 개념"))
        return list(unique.values())

    def catalog(self, *, subject: str = "전체", difficulty: str = "전체",
                kind: str = "전체", limit: int = 80) -> List[dict]:
        """Browse by three explicit filters, with bounded SQLite queries."""
        if limit < 1 or limit > 500:
            raise ValueError("Catalog limit must be between 1 and 500")
        if subject != "전체" and subject not in SUBJECTS:
            raise ValueError("Unknown subject filter")
        if difficulty != "전체" and difficulty not in DIFFICULTIES:
            raise ValueError("Unknown difficulty filter")
        if kind != "전체" and kind not in KINDS:
            raise ValueError("Unknown kind filter")
        records = [q for q in self.questions if
                   (subject == "전체" or q["subject"] == subject) and
                   (difficulty == "전체" or q["difficulty"] == difficulty) and
                   (kind == "전체" or q["kind"] == kind)]
        if self.sqlite_path:
            conditions = []
            params = []
            for column, value in (("subject", subject), ("difficulty", difficulty), ("kind", kind)):
                if value != "전체":
                    conditions.append(column + "=?")
                    params.append(value)
            query = "SELECT payload_json FROM questions"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY subject, difficulty, kind, id LIMIT ?"
            uri = self.sqlite_path.resolve().as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
            try:
                records.extend(validate_question(json.loads(r[0])) for r in
                               connection.execute(query, [*params, limit]).fetchall())
            finally:
                connection.close()
        by_id = {q["id"]: q for q in records}
        return sorted(by_id.values(), key=lambda q:
                      (SUBJECTS.index(q["subject"]), DIFFICULTIES.index(q["difficulty"]),
                       KINDS.index(q["kind"]), q["id"]))[:limit]

    def inventory(self) -> dict:
        counts = Counter(q["subject"] for q in self.questions)
        if self.sqlite_path:
            connection = sqlite3.connect(self.sqlite_path.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                for subject, count in connection.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject"):
                    counts[subject] += count
            finally:
                connection.close()
        result = {subject: counts[subject] for subject in SUBJECTS}
        return {"per_subject": result, "actual": sum(result.values()),
                "target": TOTAL_TARGET, "remaining": max(0, TOTAL_TARGET - sum(result.values()))}


class QuizProgress:
    """Private local progress: no account, telemetry, or remote AI required."""
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (user_data_dir() / "quiz_progress_v355.json")
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.stats = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            self.stats = {}

    def record(self, question_id: str, correct: bool) -> None:
        if not question_id or type(correct) is not bool:
            raise ValueError("Invalid question result")
        row = self.stats.get(question_id, {})
        if not isinstance(row, dict):
            row = {}
        row = {"attempts": int(row.get("attempts", 0)) + 1,
               "correct": int(row.get("correct", 0)) + int(correct),
               "last_correct": correct}
        self.stats[question_id] = row
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.stats, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def accuracy(self, questions: Iterable[dict]) -> Optional[float]:
        total = success = 0
        for q in questions:
            row = self.stats.get(q["id"], {})
            total += int(row.get("attempts", 0))
            success += int(row.get("correct", 0))
        return success / total if total else None


def recommend_questions(questions: Iterable[dict], progress: QuizProgress,
                        *, limit: int = PER_CONCEPT, difficulty: str = "전체",
                        kind: str = "전체") -> List[dict]:
    """Explainable rule-based personalization, not an ML-generated answer.

    Prefer current-concept, unattempted and previously missed problems.
    When overall accuracy rises, gently introduce harder questions. Diversity
    of question type matters after the strongest concept matches.
    """
    items = [q for q in questions if (difficulty == "전체" or q["difficulty"] == difficulty)
             and (kind == "전체" or q["kind"] == kind)]
    if limit < 1:
        raise ValueError("Invalid recommendation limit")
    accuracy = progress.accuracy(items)
    target_difficulty = 0 if accuracy is None or accuracy < .6 else (1 if accuracy < .85 else 2)
    ordered = []
    for q in items:
        row = progress.stats.get(q["id"], {})
        attempts = max(0, int(row.get("attempts", 0)))
        missed = attempts and row.get("last_correct") is False
        score = (100 if q.get("match") == "개념 확인" else 60)
        score += (12 if missed else 9 if not attempts else 0)
        score += max(0, 5 - abs(DIFFICULTIES.index(q["difficulty"]) - target_difficulty) * 3)
        ordered.append((score, q["id"], q))
    ordered.sort(key=lambda item: (-item[0], item[1]))
    picked = []
    used_types = set()
    # Select high-priority questions without filling a quota with fabricated content.
    pool = [item[2] for item in ordered]
    while pool and len(picked) < limit:
        choice = next((q for q in pool if q["kind"] not in used_types), pool[0])
        pool.remove(choice)
        picked.append(choice)
        used_types.add(choice["kind"])
    return picked


@lru_cache(maxsize=1)
def get_bank() -> QuizBank:
    return QuizBank.from_resources()
