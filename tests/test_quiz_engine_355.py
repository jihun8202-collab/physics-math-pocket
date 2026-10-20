# -*- coding: utf-8 -*-
"""v3.5.5 quiz bank regression and data integrity tests."""
import json
import tempfile
import unittest
from pathlib import Path

from quiz_engine import (
    SUBJECTS, TOTAL_TARGET, PER_CONCEPT, QuizBank, QuizProgress,
    validate_question, recommend_questions
)
from tools.build_quiz_db_355 import build


class Quiz355Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = QuizBank.from_resources()

    def test_target_and_actual_inventory_are_distinct(self):
        self.assertEqual(TOTAL_TARGET, 350000)
        self.assertEqual(PER_CONCEPT, 5)
        inv = self.bank.inventory()
        self.assertEqual(inv["actual"], 76)
        self.assertEqual(inv["target"], 350000)
        self.assertEqual(inv["remaining"], 349924)
        self.assertEqual(inv["per_subject"]["국어"], 46)
        for subject in SUBJECTS:
            self.assertGreater(inv["per_subject"][subject], 0)

    def test_five_questions_for_sample_concepts(self):
        samples = [
            ("수학", "일차함수", ""),
            ("물리", "뉴턴 제2법칙", ""),
            ("화학", "원자", ""),
            ("생명과학", "세포", ""),
            ("지구과학", "지진파", ""),
            ("천문학", "태양", ""),
            ("국어", "품사", "korean-316-word-class")
        ]
        for subject, name, concept_id in samples:
            with self.subTest(subject=subject):
                term = {"id": concept_id, "subject": subject,
                        "name_ko": name, "related": []}
                q = self.bank.for_term(term)
                self.assertEqual(len(q), 5)
                self.assertEqual(len(recommend_questions(q, QuizProgress(Path("/nonexistent")))), 5)
                self.assertTrue(all(item["match"] == "개념 확인" for item in q))

    def test_missing_concepts_never_get_fabricated_questions(self):
        q = self.bank.for_term({
            "id": "imaginary", "subject": "수학",
            "name_ko": "없는 임의 개념", "related": []
        })
        self.assertEqual(q, [])

    def test_duplicate_options_and_no_source_rejected(self):
        question = dict(self.bank.questions[0])
        question["choices"] = ["같음", "같음"]
        with self.assertRaises(ValueError):
            validate_question(question)
        question = dict(self.bank.questions[0])
        question["source"] = ""
        with self.assertRaises(ValueError):
            validate_question(question)
        with self.assertRaises(ValueError):
            QuizBank([self.bank.questions[0], self.bank.questions[0]])

    def test_options_correct_indices_and_unique_stems(self):
        seen = set()
        for q in self.bank.questions:
            with self.subTest(id=q["id"]):
                self.assertIn(q["answer_index"], range(len(q["choices"])))
                self.assertGreaterEqual(len(q["explanation"]), 10)
                self.assertTrue(q["source"])
                signature = (q["subject"], q.get("concept_id") or q.get("concept_name"),
                             q["question"])
                self.assertNotIn(signature, seen)
                seen.add(signature)

    def test_offline_attempts_and_difficulty_filters(self):
        with tempfile.TemporaryDirectory() as folder:
            progress_path = Path(folder) / "stats.json"
            progress = QuizProgress(progress_path)
            term = {"id": "", "subject": "수학",
                    "name_ko": "일차함수", "related": []}
            questions = self.bank.for_term(term)
            first = recommend_questions(questions, progress, difficulty="기초")
            self.assertTrue(first)
            self.assertTrue(all(item["difficulty"] == "기초" for item in first))
            progress.record(first[0]["id"], False)
            self.assertEqual(QuizProgress(progress_path).stats[first[0]["id"]]["attempts"], 1)
            self.assertEqual(progress.accuracy(first), 0.0)
            progress.record(first[0]["id"], True)
            self.assertEqual(progress.accuracy(first), 0.5)
            self.assertTrue(recommend_questions(questions, progress, kind="계산"))
            with self.assertRaises(ValueError):
                recommend_questions(questions, progress, limit=0)

    def test_sqlite_bulk_import_has_same_query_api(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "reviewed.jsonl"
            output = Path(folder) / "quiz.sqlite3"
            items = [self.bank.by_subject["물리"][0], self.bank.by_subject["수학"][0]]
            file.write_text("\n".join(json.dumps(q, ensure_ascii=False) for q in items), encoding="utf-8")
            report = build(file, output)
            self.assertEqual(report["actual"], 2)
            self.assertEqual(report["remaining"], 349998)
            loaded = QuizBank([], sqlite_path=output)
            self.assertEqual(loaded.inventory()["actual"], 2)
            result = loaded.for_term({"id": "", "subject": "수학", "name_ko": "일차함수", "related": []})
            self.assertEqual(len(result), 1)
            with self.assertRaises(FileExistsError):
                build(file, output)

    def test_corrupt_jsonl_refuses_output(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "bad.jsonl"
            output = Path(folder) / "quiz.sqlite3"
            file.write_text('{"id":"empty"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                build(file, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
