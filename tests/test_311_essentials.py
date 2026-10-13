from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import APP_VERSION, load_terms, search_terms


class EssentialsPatch311Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.terms = load_terms()
        cls.by_name = {t["name_ko"]: t for t in cls.terms}

    def test_version(self) -> None:
        self.assertEqual(APP_VERSION, "3.2.0")

    def test_foundational_math_is_present(self) -> None:
        required = {
            "수열", "일반항", "점화식", "등차수열", "공차", "등차급수",
            "등비수열", "공비", "등비급수", "부분합", "사인", "코사인",
            "탄젠트", "사인 법칙", "코사인 법칙", "순열", "조합",
        }
        self.assertTrue(required.issubset(self.by_name), required - set(self.by_name))

    def test_common_misspelling_alias(self) -> None:
        results = search_terms(self.terms, "등차곱수", limit=5)
        self.assertTrue(results)
        self.assertEqual(results[0]["name_ko"], "등차급수")

    def test_foundational_science_is_present(self) -> None:
        required = {
            "밀도", "압력", "부력", "토크", "로렌츠 변환",
            "몰", "아보가드로 상수", "공유결합", "pH", "산화", "환원",
            "DNA", "효소", "세포호흡", "광합성", "항원", "항체",
            "암석 순환", "엘니뇨", "온실효과", "해류",
            "광년", "파섹", "H-R도", "은하", "적색편이",
        }
        self.assertTrue(required.issubset(self.by_name), required - set(self.by_name))

    def test_no_sparse_core_categories(self) -> None:
        subjects = {"수학", "물리", "화학", "생명과학", "지구과학", "천문학"}
        for subject in subjects:
            counts = Counter(
                t.get("category") for t in self.terms
                if t.get("subject") == subject and t.get("category") != "시뮬레이션 개념"
            )
            self.assertTrue(counts, subject)
            self.assertGreaterEqual(min(counts.values()), 30, (subject, counts))

    def test_visible_back_navigation_is_implemented(self) -> None:
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('self.back_button = self._button(left, "←", self.go_back', source)
        self.assertIn('self.bind_all("<Alt-Left>", self.go_back)', source)
        self.assertIn('def go_back(self, _event=None)', source)
        self.assertIn('self.nav_history', source)


if __name__ == "__main__":
    unittest.main()



