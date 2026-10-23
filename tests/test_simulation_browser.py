"""Real Tk navigation checks without loading the unrelated application database."""
import tkinter as tk
import unittest
from unittest.mock import patch

from simulation_browser import build_simulation_browser, LEGACY_TOOL_COUNT
from scientific_simulation import ScientificGraphSimulator
from test_enhanced_simulations import THEME


class _Holder(tk.Frame):
    def __init__(self, parent, background):
        super().__init__(parent, bg=background)
        self.inner = tk.Frame(self, bg=background)
        self.inner.pack(fill="both", expand=True)

    def to_top(self):
        pass


class _AppHarness:
    def __init__(self, root):
        self.root = root
        self.theme = {**THEME, "bg": "#F7F8FC"}
        self.settings = {"animations": False, "simulation_fps": 60}
        self._active_simulators = []
        self.status_var = tk.StringVar()

    def _refresh_nav_state(self):
        pass

    def _clear_center(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)
        return self.frame

    def _page_title(self, frame, title, description):
        self.title, self.description = title, description

    def _card(self, parent, **options):
        return tk.Frame(parent, bg=self.theme["surface"], **options)

    def _put_card_content(self, outer):
        return outer

    def _button(self, parent, text, command, kind=None, **options):
        return tk.Button(parent, text=text, command=command, **options)


class SimulationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
            cls.root.overrideredirect(True)
            cls.root.attributes("-alpha", 0)
            cls.root.geometry("1200x1100+0+0")
            cls.root.deiconify()
            cls.root.update()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error))

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.app = _AppHarness(self.root)
        build_simulation_browser(self.app, _Holder)
        self.root.update()

    def tearDown(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.update()

    def test_lazy_catalog_preserves_counts_and_wraps_after_narrow_resize(self):
        self.assertEqual(LEGACY_TOOL_COUNT, 105)
        self.assertIn("5,000", self.app.description)
        self.assertEqual(self.app._active_simulators, [])
        self.assertEqual(len(self.app._simulation_browser_state["cards"]), 24)
        for width, columns in ((1200, 3), (760, 2), (460, 1)):
            self.root.geometry(f"{width}x1100+0+0")
            self.root.update()
            self.assertEqual(self.app._simulation_browser_state["columns"], columns)
            for card, _ in self.app._simulation_browser_state["cards"]:
                self.assertLessEqual(card.winfo_x() + card.winfo_width(), card.master.winfo_width())
        self.app._open_simulation_family("force")
        self.root.update()
        self.assertEqual(len(self.app._simulation_browser_state["cards"]), 24)
        self.assertIn("100", self.app.status_var.get())
        self.assertEqual(self.app._active_simulators, [])

    def test_disabled_animations_and_selected_fps_reach_actual_widgets(self):
        for sid in ("sci_hydrostatic_001", "sci_force_001", "enhanced_collision"):
            with self.subTest(sid=sid):
                self.app._open_simulation_card(sid)
                self.root.update()
                widget = self.app._active_simulators[0]
                self.assertEqual(widget.fps, 60)
                self.assertEqual(str(widget.play_btn.cget("state")), "disabled")
                widget.play_btn.invoke()
                self.assertFalse(widget.running)
                self.assertGreater(len(widget.canvas.find_all()), 2)
        self.app._open_simulation_family("force")
        self.assertEqual(self.app._active_simulators, [])

    def test_graph_fps_changes_schedule_without_changing_elapsed_time_progress(self):
        readings = []
        for fps in (30, 60):
            widget = ScientificGraphSimulator(self.root, "sci_hydrostatic_001", THEME, fps=fps)
            with patch("scientific_simulation.time.perf_counter", side_effect=(10.0, 10.25)):
                with patch.object(widget, "after", wraps=widget.after) as schedule:
                    widget.start()
                    self.assertEqual(schedule.call_args.args[0], round(1000 / fps))
                    # Perform one physical UI callback at the same elapsed time.
                    widget.after_cancel(widget._job)
                    widget._tick()
                    readings.append(widget.probe.get())
                    self.assertEqual(schedule.call_args.args[0], round(1000 / fps))
            widget.destroy()
        self.assertEqual(readings, [0.025, 0.025])


if __name__ == "__main__":
    unittest.main()
