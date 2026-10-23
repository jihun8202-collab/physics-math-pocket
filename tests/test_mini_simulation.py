"""Concept matching, shared model state, rendering and callback lifecycle."""
from pathlib import Path
import math
import sys
import tkinter as tk
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mini_simulation import build_mini_simulator, mini_kind_for_term, mini_initial_conditions
from physics_engine import PhysicsEngine, Settings
from scientific_catalog import SCENARIOS

THEME = {
    "surface": "#FFFFFF", "surface2": "#F7F8FC", "text": "#17191F", "muted": "#737987",
    "accent": "#5B54F6", "accent2": "#3F45C8", "accent_soft": "#ECEBFF", "blue": "#356EE8",
    "line": "#E2E6EF", "green": "#248A64", "orange": "#C97728", "danger": "#D94B54",
}


class ConceptMatchTests(unittest.TestCase):
    def test_exact_concepts_match_but_broad_categories_and_descriptions_do_not(self):
        self.assertEqual(mini_kind_for_term({"name_ko": "뉴턴의 제2법칙"}), "force")
        self.assertEqual(mini_kind_for_term({"name_ko": "단진자"}), "pendulum")
        self.assertEqual(mini_kind_for_term({"name_en": "Hooke’s law"}), "spring")
        self.assertEqual(mini_kind_for_term({"aliases": ["Projectile motion"]}), "projectile")
        for term in [
            {"category": "운동학", "subject": "물리"},
            {"name_ko": "광전 효과", "detail": "뉴턴의 제2법칙과 구분한다."},
            {"name_ko": "포물선 운동의 역사"},
            {"name_ko": "포물선 운동", "simulator": "unknown"},
            {"simulator": "biology_body"},
        ]:
            self.assertEqual(mini_kind_for_term(term), "", term)

    def test_all_400_dynamic_scenarios_preserve_their_starting_settings(self):
        matched = 0
        for sid, spec in SCENARIOS.items():
            kind = mini_kind_for_term({"simulator": sid})
            if not spec["dynamic"]:
                self.assertEqual(kind, "")
                continue
            matched += 1
            self.assertEqual(kind, spec["dynamic"]["kind"])
            params = mini_initial_conditions({"simulator": sid}, kind)
            self.assertEqual(params, spec["dynamic"]["settings"])
            PhysicsEngine(Settings(kind=kind, **params))
        self.assertEqual(matched, 400)


class MiniSimulationLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.window = tk.Tk()
            cls.window.withdraw()
            cls.window.overrideredirect(True)
            cls.window.attributes("-alpha", 0)
            cls.window.geometry("1000x1000+0+0")
            cls.window.deiconify()
            cls.window.update()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display unavailable: {error}")

    @classmethod
    def tearDownClass(cls):
        cls.window.destroy()

    def tearDown(self):
        for child in self.window.winfo_children():
            child.destroy()
        self.window.update()

    def test_each_compact_experiment_matches_full_engine_and_draws_small_and_large(self):
        for sid in ("newton2", "projectile", "pendulum", "spring"):
            with self.subTest(sid=sid):
                widget = build_mini_simulator(self.window, {"simulator": sid}, THEME, 60)
                widget.pack(fill="x")
                self.window.update()
                reference = PhysicsEngine(widget.engine.settings)
                widget._advance(120)
                reference.advance_steps(120)
                self.assertEqual(widget.engine.reading, reference.reading)
                self.assertGreater(len(widget.history), 5)
                for width, columns in ((360, 1), (720, 2), (1000, 3)):
                    self.window.geometry(f"{width}x1000+0+0")
                    self.window.update()
                    widget.redraw()
                    self.assertEqual(widget._columns, columns)
                    self.assertGreater(len(widget.canvas.find_all()), 8)
                    self.assertGreater(len(widget.history_canvas.find_all()), 6)
                    for control in widget._controls + widget._toolbar_items:
                        self.assertLessEqual(control.winfo_x() + control.winfo_width(),
                                             control.master.winfo_width() + 1)
                widget.destroy()

    def test_parameter_change_resets_state_and_destroy_cancels_every_callback(self):
        widget = build_mini_simulator(self.window, {"name_ko": "가속도"}, THEME)
        widget.pack(fill="x")
        self.window.update()
        widget._advance(240)
        self.assertAlmostEqual(widget.engine.reading.time, 1)
        widget._vars["applied_force"].set(-12)
        self.window.update()
        self.assertEqual(widget.engine.reading.time, 0)
        self.assertEqual(widget.engine.settings.applied_force, -12)
        widget.step_once()
        self.assertLess(widget.engine.reading.x, 0)
        widget.start()
        timer = widget._job
        self.assertIsNotNone(timer)
        widget._vars["mass"].set(3)
        deferred = widget._parameter_job
        self.assertIsNotNone(deferred)
        widget.destroy()
        callbacks = self.window.tk.call("after", "info")
        self.assertNotIn(timer, callbacks)
        self.assertNotIn(deferred, callbacks)

    def test_unknown_concept_does_not_create_empty_widget(self):
        before = self.window.winfo_children()
        self.assertIsNone(build_mini_simulator(self.window, {"name_ko": "비유법"}, THEME))
        self.assertEqual(self.window.winfo_children(), before)

    def test_undamped_concept_defaults_and_linked_scenario_settings(self):
        for sid, parameter in (("spring", "spring_damping"), ("projectile", "quadratic_drag"),
                               ("pendulum", "angular_damping")):
            widget = build_mini_simulator(self.window, {"simulator": sid}, THEME)
            self.assertEqual(getattr(widget.engine.settings, parameter), 0)
            widget.destroy()
        sid = "sci_spring_099"
        widget = build_mini_simulator(self.window, {"simulator": sid}, THEME)
        for parameter, value in SCENARIOS[sid]["dynamic"]["settings"].items():
            self.assertEqual(getattr(widget.engine.settings, parameter), value)
        widget.destroy()

    def test_slider_extremes_stay_finite_and_render_measured_geometry(self):
        extremes = {
            "force": {"applied_force": -50, "mass": 0.1, "initial_velocity": 60},
            "projectile": {"launch_speed": 60, "angle_degrees": 80, "quadratic_drag": 0.05, "mass": 0.1},
            "pendulum": {"angle_degrees": 120, "length": 0.2, "angular_damping": 2},
            "spring": {"stiffness": 100, "mass": 0.1, "spring_damping": 5, "amplitude": 2},
        }
        for kind, settings in extremes.items():
            with self.subTest(kind=kind):
                widget = build_mini_simulator(self.window, {"simulator": "enhanced_" + kind}, THEME)
                widget.pack(fill="x")
                widget._setting_up = True
                for name, value in settings.items():
                    widget._vars[name].set(value)
                widget._setting_up = False
                widget.reset()
                self.window.update()
                widget._advance(1200)
                widget.redraw()
                reading = widget.engine.reading
                self.assertTrue(all(math.isfinite(value) for value in
                                    (reading.x, reading.y, reading.vx, reading.vy, reading.energy)))
                self.assertGreaterEqual(reading.energy, 0)
                for canvas in (widget.canvas, widget.history_canvas):
                    self.assertGreater(len(canvas.find_all()), 6)
                    for item in canvas.find_all():
                        self.assertTrue(all(math.isfinite(value) for value in canvas.coords(item)))
                widget.destroy()


if __name__ == "__main__":
    unittest.main()
