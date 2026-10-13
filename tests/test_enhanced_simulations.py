"""Tk lifecycle smoke checks; use an invisible real window when a display exists."""
from pathlib import Path
import sys
import tkinter as tk
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from enhanced_simulations import ENHANCED_TITLES, EnhancedSimulator, build_simulator, simulator_for_term
from simulations import SIM_TITLES, MiniSimulator

THEME = {
    "surface": "#FFFFFF", "surface2": "#F7F8FC", "text": "#17191F", "muted": "#737987",
    "accent": "#5B54F6", "accent2": "#3F45C8", "accent_soft": "#ECEBFF", "blue": "#356EE8",
    "line": "#E2E6EF", "green": "#248A64", "orange": "#C97728", "danger": "#D94B54",
}


class EnhancedSimulationLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.window = tk.Tk()
            cls.window.withdraw()
            cls.window.overrideredirect(True)
            cls.window.attributes("-alpha", 0)
            cls.window.geometry("1000x900+0+0")
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

    def test_enhanced_models_render_and_reset_at_both_layout_widths(self):
        for sid in ENHANCED_TITLES:
            with self.subTest(sid=sid):
                widget = build_simulator(self.window, {"simulator": sid}, THEME, fps=60)
                self.assertIsInstance(widget, EnhancedSimulator)
                self.assertEqual(simulator_for_term({"simulator": sid}), sid)
                widget.pack(fill="x")
                self.window.update()
                self.assertGreater(len(widget.canvas.find_all()), 10)
                self.assertEqual(widget._columns, 2)
                widget.step_once()
                self.assertAlmostEqual(widget.engine.reading.time, 1 / 60, places=12)
                widget._vars["mass"].set(2)
                self.window.update()
                self.assertEqual(widget.engine.reading.time, 0)
                self.assertEqual(widget.engine.settings.mass, 2)
                self.window.geometry("600x900+0+0")
                self.window.update()
                widget.redraw()
                self.assertEqual(widget._columns, 1)
                self.assertGreater(len(widget.canvas.find_all()), 10)
                self.assertGreater(len(widget.history_canvas.find_all()), 6)
                widget.destroy()
                self.window.geometry("1000x900+0+0")
                self.window.update()

    def test_pause_and_destroy_cancel_animation_callbacks(self):
        widget = build_simulator(self.window, {"simulator": "enhanced_projectile"}, THEME)
        widget.pack(fill="x")
        self.window.update()
        widget.start()
        self.assertTrue(widget.running)
        job = widget._job
        self.assertIsNotNone(job)
        widget.stop()
        self.assertFalse(widget.running)
        self.assertIsNone(widget._job)
        self.assertNotIn(job, self.window.tk.call("after", "info"))
        widget.start()
        job = widget._job
        widget.destroy()
        self.assertNotIn(job, self.window.tk.call("after", "info"))

    def test_real_timer_advances_and_pause_keeps_the_same_state(self):
        widget = build_simulator(self.window, {"simulator": "enhanced_pendulum"}, THEME, fps=60)
        widget.pack(fill="x")
        self.window.update()
        widget.start()
        self.window.after(120, self.window.quit)
        self.window.mainloop()
        widget.stop()
        self.assertGreater(widget.engine.reading.time, 0)
        self.assertLessEqual(widget.engine.reading.time, 1)
        paused = widget.engine.reading
        self.window.after(60, self.window.quit)
        self.window.mainloop()
        self.assertEqual(widget.engine.reading, paused)
        widget.reset()
        self.assertEqual(widget.engine.reading.time, 0)
        self.assertFalse(widget.running)

    def test_every_legacy_registry_entry_remains_available(self):
        self.assertEqual(len(SIM_TITLES), 100)
        for sid in SIM_TITLES:
            self.assertEqual(simulator_for_term({"simulator": sid}), sid)
        widget = build_simulator(self.window, {"simulator": "projectile"}, THEME)
        self.assertIsInstance(widget, MiniSimulator)
        self.assertIsNone(build_simulator(self.window, {"simulator": "unknown"}, THEME))


if __name__ == "__main__":
    unittest.main()
