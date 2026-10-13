"""Known-value regressions for the existing generator-based graph expressions."""
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulations import GENERIC_SIM_SPECS, MiniSimulator


class LegacySeriesGraphTests(unittest.TestCase):
    @staticmethod
    def evaluate(sid, x):
        # _generic_eval needs only the public value-variable interface; no display.
        variables = {
            name: SimpleNamespace(get=lambda value=default: float(value))
            for _, name, _, _, default in GENERIC_SIM_SPECS[sid]["sliders"]
        }
        context = SimpleNamespace(sim_id=sid, _vars=variables)
        return MiniSimulator._generic_eval(context, x)

    def test_taylor_graph_reports_the_known_exponential_approximation_error(self):
        # This existing graph plots the error, rather than the polynomial itself.
        self.assertEqual(self.evaluate("taylor_series", 0), 0)
        self.assertAlmostEqual(self.evaluate("taylor_series", 1), math.e - 65 / 24, places=13)
        self.assertTrue(math.isfinite(self.evaluate("taylor_series", -1.5)))

    def test_fourier_graph_evaluates_named_functions_inside_the_series(self):
        self.assertEqual(self.evaluate("fourier_series", 0), 0)
        self.assertAlmostEqual(self.evaluate("fourier_series", math.pi / 2), 1 - 1 / 3 + 1 / 5 - 1 / 7 + 1 / 9, places=13)
        self.assertAlmostEqual(self.evaluate("fourier_series", -math.pi / 2), -(1 - 1 / 3 + 1 / 5 - 1 / 7 + 1 / 9), places=13)


if __name__ == "__main__":
    unittest.main()
