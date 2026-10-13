from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator_specs import CALCULATOR_SPECS
from core import APP_VERSION, load_terms
from formula_catalog import build_formula_catalog, search_formulas
from simulations import SIM_TITLES, SIM_SUBJECTS


class FinalReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.terms = load_terms()
        cls.formulas = build_formula_catalog(cls.terms)

    def test_final_version(self) -> None:
        self.assertEqual(APP_VERSION, "3.1.6")

    def test_final_content_targets(self) -> None:
        self.assertGreaterEqual(len(self.terms), 2000)
        self.assertGreaterEqual(len(self.formulas), 500)
        self.assertEqual(len(SIM_TITLES), 100)
        self.assertGreaterEqual(len(CALCULATOR_SPECS), 50)

    def test_formula_ids_unique_and_searchable(self) -> None:
        ids = [row["id"] for row in self.formulas]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(search_formulas(self.formulas, "패러데이"))
        self.assertTrue(search_formulas(self.formulas, "derivative") or search_formulas(self.formulas, "미분"))
        self.assertTrue(search_formulas(self.formulas, "삼각형"))

    def test_all_calculator_defaults_evaluate(self) -> None:
        for title, _category, _formula, fields, func, _note in CALCULATOR_SPECS:
            values = [float(default) for _label, _unit, default in fields]
            result, unit = func(values)
            self.assertTrue(math.isfinite(float(result)), title)
            self.assertIsInstance(unit, str)

    def test_simulator_metadata_complete(self) -> None:
        self.assertEqual(set(SIM_TITLES), set(SIM_SUBJECTS))
        self.assertEqual(len(set(SIM_TITLES.values())), len(SIM_TITLES))


if __name__ == "__main__":
    unittest.main()
