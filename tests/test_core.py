from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import convert_unit, load_constants, load_sources, load_terms, search_terms
from simulations import SIM_TITLES, simulator_for_term


class PhysicsMathPocketDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.terms = load_terms()
        cls.sources = load_sources()
        cls.source_ids = {s["id"] for s in cls.sources}

    def test_term_count_is_expanded(self) -> None:
        self.assertGreaterEqual(len(self.terms), 1100)
        self.assertGreaterEqual(sum(t.get("subject") == "물리" for t in self.terms), 500)
        self.assertGreaterEqual(sum(t.get("subject") == "수학" for t in self.terms), 600)

    def test_ids_are_unique(self) -> None:
        ids = [t["id"] for t in self.terms]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields_exist(self) -> None:
        required = {"id", "name_ko", "name_en", "subject", "category", "level", "summary", "detail", "sources"}
        for term in self.terms:
            self.assertTrue(required.issubset(term), term.get("name_ko"))
            self.assertTrue(term["name_ko"].strip())
            self.assertTrue(term["name_en"].strip())
            self.assertTrue(term["summary"].strip())

    def test_all_sources_resolve(self) -> None:
        for term in self.terms:
            for source_id in term["sources"]:
                self.assertIn(source_id, self.source_ids, term["name_ko"])

    def test_physics_searches(self) -> None:
        self.assertEqual(search_terms(self.terms, "속도", limit=3)[0]["name_ko"], "속도")
        self.assertEqual(search_terms(self.terms, "velocity", limit=3)[0]["name_ko"], "속도")
        self.assertEqual(search_terms(self.terms, "ㅈㅈㄱㅇㄷ", limit=5)[0]["name_ko"], "전자기 유도")

    def test_math_searches(self) -> None:
        for query, expected in [("이차함수", "이차함수"), ("derivative", "미분계수"), ("행렬", "행렬")]:
            result = search_terms(self.terms, query, limit=10)
            self.assertTrue(result, query)
            self.assertIn(expected, {x["name_ko"] for x in result}, query)

    def test_math_breadth(self) -> None:
        cats = {t["category"] for t in self.terms if t.get("subject") == "수학"}
        for category in ("대수", "기하", "함수", "삼각함수", "미적분", "선형대수", "미분방정식", "해석학", "복소해석", "추상대수"):
            self.assertIn(category, cats)
        levels = " ".join(t.get("level", "") for t in self.terms if t.get("subject") == "수학")
        for level in ("중등", "고등", "대학"):
            self.assertIn(level, levels)

    def test_simulators_are_wired(self) -> None:
        self.assertGreaterEqual(len(SIM_TITLES), 15)
        by_name = {t["name_ko"]: t for t in self.terms}
        for name in ("뉴턴 운동 제2법칙", "이차함수", "미분계수", "행렬"):
            self.assertTrue(simulator_for_term(by_name[name]), name)

    def test_formula_search(self) -> None:
        names = {t["name_ko"] for t in search_terms(self.terms, "E=mc2", limit=10)}
        self.assertTrue("질량-에너지 등가" in names or "질량결손" in names)

    def test_constants_present(self) -> None:
        symbols = {c["symbol"] for c in load_constants()}
        self.assertTrue({"c", "h", "G"}.issubset(symbols))


class UnitConversionTests(unittest.TestCase):
    def test_speed(self) -> None:
        self.assertAlmostEqual(convert_unit(72, "속력", "km/h", "m/s"), 20.0)

    def test_temperature(self) -> None:
        self.assertAlmostEqual(convert_unit(0, "온도", "°C", "K"), 273.15)
        self.assertAlmostEqual(convert_unit(32, "온도", "°F", "°C"), 0.0)

    def test_force_frequency_energy(self) -> None:
        self.assertAlmostEqual(convert_unit(1, "힘", "kN", "N"), 1000.0)
        self.assertAlmostEqual(convert_unit(60, "주파수", "rpm", "Hz"), 1.0)
        self.assertTrue(math.isclose(convert_unit(1, "에너지", "eV", "J"), 1.602176634e-19, rel_tol=1e-15))


class UserDatabaseTests(unittest.TestCase):
    def test_crud_and_dynamic_quota(self) -> None:
        old = os.environ.get("PHYSICSMATHPOCKET_DATA_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = td
                # Import only after environment is redirected. This prevents
                # Windows build tests from ever touching the real user database.
                import importlib
                import knowledge_db
                importlib.reload(knowledge_db)
                db = knowledge_db.KnowledgeDatabase(limit_gb=5)
                self.assertEqual(db.limit_gb, 5)
                self.assertLess(db.size_bytes(), 20 * 1024 * 1024)  # no blank 5 GB preallocation
                tid = db.upsert_term({
                    "name_ko": "내 테스트 개념", "name_en": "My test concept", "subject": "수학",
                    "category": "사용자 추가", "level": "사용자", "summary": "테스트 항목", "detail": "직접 추가한 데이터"
                })
                self.assertEqual(db.count(), 1)
                self.assertTrue(any(t["id"] == tid and t.get("user_added") for t in db.all_user_terms()))
                self.assertTrue(db.delete_term(tid))
                self.assertEqual(db.count(), 0)
                db.close()
        finally:
            if old is None:
                os.environ.pop("PHYSICSMATHPOCKET_DATA_DIR", None)
            else:
                os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = old


if __name__ == "__main__":
    unittest.main()
