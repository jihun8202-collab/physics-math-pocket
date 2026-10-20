# -*- coding: utf-8 -*-
"""Every supplied concept gets five mechanically verifiable reading drills.

A structured card-reading drill is not a peer-reviewed science quiz. The two
inventories must be kept separate and preserved through updates.
"""
import json
import tempfile
import unittest
from pathlib import Path

from core import load_terms
from concept_drills_359 import ConceptDrillIndex, _clean
from quiz_engine import PER_CONCEPT, QuizProgress, get_bank, recommend_questions


class ConceptDrills359Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms = load_terms()
        cls.index = ConceptDrillIndex(cls.terms)

    def test_all_existing_cards_produce_exactly_five(self):
        # This is a functional/structural check, not scientific fact checking.
        counts = set()
        for term in self.terms:
            if term.get("subject") not in self.index.subjects:
                continue
            with self.subTest(term=term.get("id")):
                exercises = self.index.for_term(term)
                self.assertEqual(len(exercises), 5)
                self.assertEqual(len({q["id"] for q in exercises}), 5)
                for exercise in exercises:
                    self.assertEqual(exercise["subject"], term["subject"])
                    self.assertEqual(exercise["concept_id"], term["id"])
                    self.assertEqual(exercise["review_status"], "mechanically_derived")
                    self.assertFalse(exercise["count_as_reviewed"])
                    self.assertEqual(len(exercise["choices"]), 4)
                    self.assertEqual(len(set(exercise["choices"])), 4)
                    self.assertIn(exercise["answer_index"], range(4))
                    self.assertGreater(len(exercise["explanation"]), 10)
                    self.assertEqual(exercise["match"], "현재 개념 · 카드 읽기")
                self.assertEqual(exercises[0]["choices"][exercises[0]["answer_index"]],
                                 _clean(term.get("summary", "")) or
                                 _clean(term.get("detail", "")) or _clean(term.get("name_ko")))
                self.assertEqual(exercises[1]["choices"][exercises[1]["answer_index"]],
                                 _clean(term.get("name_ko")))
                self.assertEqual(exercises[2]["choices"][exercises[2]["answer_index"]],
                                 term["subject"])
                if term.get("category"):
                    self.assertEqual(exercises[3]["choices"][exercises[3]["answer_index"]],
                                     _clean(term["category"]))
                counts.add(len(exercises))
        self.assertEqual(counts, {5})

    def test_ids_stable_across_visits_and_offline_progress(self):
        term = self.terms[15]
        first = self.index.for_term(term)
        self.assertEqual(first, self.index.for_term(term))
        with tempfile.TemporaryDirectory() as temp:
            progress = QuizProgress(Path(temp) / "progress.json")
            self.assertEqual(len(recommend_questions(first, progress)), PER_CONCEPT)
            q = first[0]
            progress.record(q["id"], True)
            self.assertEqual(QuizProgress(Path(temp) / "progress.json").stats[q["id"]]["correct"], 1)

    def test_verified_and_reading_drills_are_separate(self):
        bank = get_bank()
        before = bank.inventory()["actual"]
        self.assertEqual(before, 76)
        term = {"id": "no-authored", "name_ko": "새로운 카드", "subject": "물리",
                "summary": "새 항목을 테스트하는 가상의 샘플", "category": "", "level": "", "related": []}
        drills = self.index.for_term(term)
        self.assertEqual(len(drills), 5)
        self.assertEqual(bank.inventory()["actual"], before)
        self.assertFalse(any(q["review_status"] in ("curated", "source_checked") for q in drills))


if __name__ == "__main__":
    unittest.main()
