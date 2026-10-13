"""Physical direction and pause regressions behind the 3.1.7 motion repair."""
from pathlib import Path
import math
import sys
import tkinter as tk
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physics_engine import FIXED_DT, PhysicsEngine, Settings, constant_force_motion
from simulations import MiniSimulator

THEME = {
    "surface": "#FFFFFF", "surface2": "#F7F8FC", "text": "#17191F", "muted": "#737987",
    "accent": "#5B54F6", "accent2": "#3F45C8", "accent_soft": "#ECEBFF", "blue": "#356EE8",
    "line": "#E2E6EF", "green": "#248A64", "orange": "#C97728", "danger": "#D94B54",
}


class ConstantForceDirectionTests(unittest.TestCase):
    def test_positive_force_from_rest_never_reverses(self):
        positions = []
        for seconds in (0, 0.5, 1, 2, 3, 4, 5, 10):
            position, velocity = constant_force_motion(8, 2, seconds)
            self.assertAlmostEqual(position, 2 * seconds ** 2, places=11)
            self.assertAlmostEqual(velocity, 4 * seconds, places=11)
            positions.append(position)
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(constant_force_motion(8, 2, 5), (50, 20))

    def test_opposing_force_turns_only_when_velocity_reaches_zero(self):
        self.assertEqual(constant_force_motion(-8, 2, 2, v0=12), (16, 4))
        self.assertEqual(constant_force_motion(-8, 2, 3, v0=12), (18, 0))
        self.assertEqual(constant_force_motion(-8, 2, 4, v0=12), (16, -4))

    def test_zero_force_preserves_inertial_motion(self):
        self.assertEqual(constant_force_motion(0, 2, 5, x0=3, v0=-2), (-7, -2))

    def test_force_engine_matches_si_position_and_work(self):
        engine = PhysicsEngine(Settings(kind="force", applied_force=8, mass=2, initial_velocity=0))
        reading = engine.advance_steps(round(5 / FIXED_DT))
        self.assertAlmostEqual(reading.time, 5, places=11)
        self.assertAlmostEqual(reading.x, 50, places=9)
        self.assertAlmostEqual(reading.vx, 20, places=9)
        self.assertAlmostEqual(reading.energy, 8 * reading.x, places=8)

    def test_force_timestep_batching_cannot_change_direction_or_state(self):
        first = PhysicsEngine(Settings(kind="force", applied_force=8, mass=2))
        second = PhysicsEngine(Settings(kind="force", applied_force=8, mass=2))
        first.advance_steps(1200)
        for count in (17, 200, 1, 982):
            second.advance_steps(count)
        self.assertEqual(first.reading, second.reading)


class MotionDisplayRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.window = tk.Tk()
            cls.window.withdraw()
            cls.window.overrideredirect(True)
            cls.window.attributes("-alpha", 0)
            cls.window.geometry("1000x700+0+0")
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

    def widget(self, sid):
        widget = MiniSimulator(self.window, sid, THEME)
        widget.pack(fill="x")
        self.window.update()
        return widget

    @staticmethod
    def geometry(widget):
        return [(widget.canvas.type(item), widget.canvas.coords(item)) for item in widget.canvas.find_all()]

    def test_pausing_does_not_teleport_or_hide_any_animated_legacy_object(self):
        for sid in ("newton2", "projectile", "spring", "wave", "unit_circle", "uniform_motion"):
            with self.subTest(sid=sid):
                widget = self.widget(sid)
                widget.t, widget.running = 0.37, True
                widget.redraw()
                playing_geometry = self.geometry(widget)
                widget.running = False
                widget.redraw()
                self.assertEqual(self.geometry(widget), playing_geometry)
                if sid == "projectile":
                    self.assertIn("oval", [kind for kind, _ in playing_geometry])
                widget.destroy()

    def test_legacy_projectile_does_not_relaunch_after_contact(self):
        widget = self.widget("projectile")
        duration = 2 * widget._vars["v"].get() * math.sin(math.radians(widget._vars["ang"].get())) / widget._vars["g"].get()
        widget.running = True
        widget.t = duration + 0.2
        widget.redraw()
        landed = self.geometry(widget)
        widget.t = duration + 1.2
        widget.redraw()
        self.assertEqual(self.geometry(widget), landed)
        self.assertIn("oval", [kind for kind, _ in landed])

    def test_time_axis_probe_moves_forward_and_stays_at_end(self):
        widget = self.widget("uniform_motion")
        positions = []
        for seconds in (0, 0.5, 1, 2, 5, 9, 10, 11, 20):
            widget.t = seconds
            positions.append(widget._probe_x())
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(positions[4], 5)
        self.assertEqual(positions[-1], 10)

    def test_non_time_relation_probe_has_no_automatic_reverse(self):
        widget = self.widget("gravity_inverse_square")
        positions = []
        for seconds in (0, 1, 2, 3, 4, 5, 6, 10, 20):
            widget.t = seconds
            positions.append(widget._probe_x())
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(positions[0], 0.2)
        self.assertEqual(positions[-1], 8)

    def test_fast_pause_resume_leaves_one_callback_chain(self):
        widget = self.widget("wave")
        widget.toggle()
        first = widget._job
        self.assertIsNotNone(first)
        widget.toggle()
        self.assertFalse(widget.running)
        self.assertIsNone(widget._job)
        self.assertNotIn(first, self.window.tk.call("after", "info"))
        widget.toggle()
        resumed = widget._job
        self.assertIsNotNone(resumed)
        self.assertIn(resumed, self.window.tk.call("after", "info"))
        widget.destroy()
        self.assertNotIn(resumed, self.window.tk.call("after", "info"))

    def test_relationship_graph_does_not_join_across_physical_or_math_poles(self):
        for sid, parameter, pole in (("thin_lens", "f", 2.0), ("rational_function", "h", 0.0),
                                     ("newton_method", None, 0.0)):
            with self.subTest(sid=sid):
                widget = self.widget(sid)
                if parameter:
                    widget._vars[parameter].set(pole)
                segments = widget._plot_segments()
                self.assertGreaterEqual(len(segments), 2)
                for segment in segments:
                    x_values = [point[0] for point in segment]
                    self.assertFalse(min(x_values) < pole < max(x_values), (sid, x_values))
                    self.assertTrue(all(math.isfinite(x) and math.isfinite(y) for x, y in segment))
                widget.destroy()

    def test_wall_time_advancement_does_not_depend_on_frame_count(self):
        slow = self.widget("newton2")
        fast = self.widget("newton2")
        slow._advance(1.0)
        for _ in range(60):
            fast._advance(1 / 60)
        self.assertAlmostEqual(slow.t, 1.0, places=11)
        self.assertAlmostEqual(fast.t, slow.t, places=11)
        expected = constant_force_motion(8, 2, 1.0)
        self.assertEqual(expected, (2.0, 4.0))
        for first, second in zip(constant_force_motion(8, 2, slow.t), constant_force_motion(8, 2, fast.t)):
            self.assertAlmostEqual(first, second, places=10)


if __name__ == "__main__":
    unittest.main()
