# -*- coding: utf-8 -*-
"""Real Tk interactions and lifecycle checks for the multi-body collision lab."""
from pathlib import Path
import sys
import tkinter as tk
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from collision_simulation import CollisionSimulator,PRESETS,BOUNDARIES
from test_enhanced_simulations import THEME


class CollisionUILifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.window=tk.Tk()
            cls.window.withdraw()
            cls.window.overrideredirect(True)
            cls.window.attributes('-alpha',0)
            cls.window.geometry('1000x1250+0+0')
            cls.window.deiconify()
            cls.window.update()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error))
        cls.errors=[]
        cls.window.report_callback_exception=lambda kind,value,tb: cls.errors.append(str(value))

    @classmethod
    def tearDownClass(cls):
        cls.window.destroy()

    def setUp(self):
        self.errors.clear()
        self.lab=CollisionSimulator(self.window,THEME,fps=60)
        self.lab.pack(fill='x')
        self.window.update()

    def tearDown(self):
        self.lab.destroy()
        self.window.update()
        self.assertFalse(self.errors,self.errors)

    def test_exact_numeric_conditions_apply_and_reset_retains_them(self):
        self.lab._vars['mass'].set('2.75')
        self.lab._vars['vx'].set('3.125')
        self.lab.restitution_var.set('0.65')
        self.lab.apply_btn.invoke()
        body=self.lab.engine.bodies[0]
        self.assertEqual(body.mass,2.75)
        self.assertEqual(body.vx,3.125)
        self.assertEqual(self.lab.engine.settings.restitution,.65)
        self.lab.step_btn.invoke()
        self.assertAlmostEqual(self.lab.t,1/60,places=10)
        self.lab.reset_btn.invoke()
        self.assertEqual(self.lab.t,0)
        self.assertEqual(self.lab.engine.bodies[0],body)

    def test_invalid_number_or_overlap_cannot_replace_valid_conditions(self):
        initial=self.lab.initial_bodies
        self.lab._vars['mass'].set('nan')
        self.assertFalse(self.lab.apply_conditions())
        self.assertEqual(self.lab.initial_bodies,initial)
        self.lab._vars['mass'].set('1')
        self.lab._vars['x'].set('7')
        self.assertFalse(self.lab.apply_conditions())
        self.assertEqual(self.lab.initial_bodies,initial)
        self.assertEqual(self.lab.engine.bodies,initial)

    def test_paused_canvas_drag_changes_initial_position_and_resets_time(self):
        self.lab.step_btn.invoke()
        old=self.lab.engine.bodies[0]
        x,y=self.lab._map(old.x,old.y)
        end_x,end_y=self.lab._map(3.2,2.4)
        self.lab.canvas.event_generate('<ButtonPress-1>',x=round(x),y=round(y))
        self.lab.canvas.event_generate('<B1-Motion>',x=round(end_x),y=round(end_y))
        self.lab.canvas.event_generate('<ButtonRelease-1>',x=round(end_x),y=round(end_y))
        self.window.update()
        new=self.lab.engine.bodies[0]
        self.assertAlmostEqual(new.x,3.2,delta=.04)
        self.assertAlmostEqual(new.y,2.4,delta=.04)
        self.assertEqual(self.lab.t,0)
        self.assertEqual(self.lab.engine.bodies,self.lab.initial_bodies)
        self.assertEqual(new.vx,old.vx)

    def test_all_presets_and_all_boundaries_have_valid_inspectable_state(self):
        for preset in PRESETS:
            self.lab.preset_var.set(preset)
            self.lab.load_preset()
            self.assertEqual(self.lab.t,0)
            self.assertGreaterEqual(len(self.lab.engine.bodies),2)
            self.assertEqual(len(self.lab.table.get_children()),len(self.lab.engine.bodies))
            self.assertGreater(len(self.lab.canvas.find_all()),25)
            self.lab._advance(240)
            self.assertAlmostEqual(self.lab.t,1,places=10)
        for label,mode in BOUNDARIES.items():
            self.lab.boundary_var.set(label)
            self.assertTrue(self.lab.apply_conditions())
            self.assertEqual(self.lab.engine.settings.boundary,mode)

    def test_six_bodies_and_numeric_editor_fit_at_narrow_width(self):
        self.lab.count_var.set('6')
        self.lab.change_count()
        self.assertEqual(len(self.lab.engine.bodies),6)
        self.assertEqual(len(self.lab.table.get_children()),6)
        self.window.geometry('540x1350+0+0')
        self.window.update()
        for cell in self.lab._controls:
            self.assertLessEqual(cell.winfo_x()+cell.winfo_width(),self.lab.editor.winfo_width()+1)
            self.assertGreater(cell.winfo_width(),100)
        self.assertGreater(len(self.lab.canvas.find_all()),30)
        self.window.geometry('1000x1250+0+0')
        self.window.update()

    def test_periodic_edge_shows_same_disc_and_trajectory_breaks_at_seam(self):
        self.lab.boundary_var.set(next(label for label,mode in BOUNDARIES.items() if mode=='periodic'))
        self.lab._vars['x'].set('9.85')
        self.lab._vars['vx'].set('2')
        self.assertTrue(self.lab.apply_conditions())
        self.assertTrue(self.lab.canvas.find_withtag('periodic-image'))
        self.lab._advance(240)
        self.lab.redraw()
        trails=self.lab.canvas.find_withtag('trail-A')
        self.assertGreaterEqual(len(trails),2)
        world_pixel_width=self.lab._map(10,0)[0]-self.lab._map(0,0)[0]
        for item in trails:
            xs=self.lab.canvas.coords(item)[::2]
            self.assertTrue(all(abs(b-a)<world_pixel_width/2 for a,b in zip(xs,xs[1:])))
        self.assertEqual(self.lab.engine.bodies[0].vx,2)

    def test_real_timer_pause_and_destroy_release_callback(self):
        self.lab.play_btn.invoke()
        self.window.after(120,self.window.quit)
        self.window.mainloop()
        self.lab.play_btn.invoke()
        self.assertFalse(self.lab.running)
        self.assertGreater(self.lab.t,0)
        snapshot=self.lab.engine.bodies
        self.window.after(50,self.window.quit)
        self.window.mainloop()
        self.assertEqual(self.lab.engine.bodies,snapshot)
        self.lab.start()
        pending=self.lab._job
        self.lab.destroy()
        self.assertNotIn(pending,self.window.tk.call('after','info'))
        # Avoid destroying the same widget again in tearDown.
        self.lab=CollisionSimulator(self.window,THEME)
        self.lab.pack(fill='x')


if __name__=='__main__':
    unittest.main()
