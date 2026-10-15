"""Real widget controls, model routing and stop/destroy behavior for 3.5."""
import tkinter as tk
import unittest
from enhanced_simulations import build_simulator, EnhancedSimulator
from scientific_catalog import SCENARIOS
from scientific_simulation import ScientificGraphSimulator
from test_enhanced_simulations import THEME

class NewLaboratoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root=tk.Tk(); cls.root.withdraw(); cls.root.overrideredirect(True)
            cls.root.attributes('-alpha',0); cls.root.geometry('1000x1000+0+0'); cls.root.deiconify(); cls.root.update()
        except tk.TclError as error:raise unittest.SkipTest(str(error))
    @classmethod
    def tearDownClass(cls):cls.root.destroy()
    def tearDown(self):
        for child in self.root.winfo_children():child.destroy()
        self.root.update()

    def test_analytic_comparison_and_exact_controls(self):
        sid=next(sid for sid,s in SCENARIOS.items() if not s.get('dynamic'))
        widget=build_simulator(self.root,{'simulator':sid},THEME)
        self.assertIsInstance(widget,ScientificGraphSimulator)
        widget.pack(fill='x'); self.root.update()
        original=list(widget._baseline)
        label,name,lo,hi,_=widget.spec['sliders'][0]
        widget._vars[name].set(hi); self.root.update()
        self.assertEqual(widget._baseline,original)
        self.assertNotEqual(widget._data,original)
        widget._entries[name].delete(0,'end'); widget._entries[name].insert(0,'nan'); widget._set_entry(name)
        self.assertEqual(widget._vars[name].get(),hi)
        widget.pin(); self.assertEqual(widget._baseline,widget._data)
        widget.start(); job=widget._job; widget.stop()
        self.assertNotIn(job,self.root.tk.call('after','info'))
        self.root.geometry('540x1000+0+0'); self.root.update()
        self.assertGreater(len(widget.canvas.find_all()),20)
        self.assertEqual(widget._buttons[2].grid_info()['row'],1)
        widget.destroy(); self.root.geometry('1000x1000+0+0')

    def test_dynamic_presets_reach_the_real_physics_engine(self):
        checked=set()
        for sid,spec in SCENARIOS.items():
            dynamic=spec.get('dynamic')
            if not dynamic or dynamic['kind'] in checked:continue
            checked.add(dynamic['kind'])
            widget=build_simulator(self.root,{'simulator':sid},THEME)
            self.assertIsInstance(widget,EnhancedSimulator)
            for name,value in dynamic['settings'].items():
                self.assertAlmostEqual(getattr(widget.engine.settings,name),value)
            widget.step_once(); self.assertGreater(widget.engine.reading.time,0)
            widget.destroy()
        self.assertEqual(checked,{'force','projectile','pendulum','spring'})

    def test_biology_route_and_pause_cleanup(self):
        from biology_simulation import BiologySimulator
        widget=build_simulator(self.root,{'simulator':'biology_body'},THEME)
        self.assertIsInstance(widget,BiologySimulator)
        widget.pack(fill='x'); self.root.update(); widget.redraw()
        self.assertGreater(len(widget.canvas.find_all()),10)
        widget.step_once(); self.assertGreater(widget.engine.time,0)
        widget.start(); self.assertTrue(widget.running)
        widget.stop(); self.assertFalse(widget.running)
        before=list(widget.engine.state); self.root.update(); self.assertEqual(widget.engine.state,before)
        widget.reset(); self.assertEqual(widget.engine.time,0)
        widget.destroy()

    def test_integer_controls_show_the_value_used_by_calculation(self):
        sid=next(sid for sid,s in SCENARIOS.items() if s['family']=='taylor_exp')
        widget=build_simulator(self.root,{'simulator':sid},THEME)
        widget._vars['order'].set(4.6)
        self.assertEqual(widget.parameters()['order'],5)
        self.assertEqual(float(widget._entries['order'].get()),5)
        widget.pin(); self.assertEqual(widget._baseline_params['order'],5)

    def test_sample_and_hold_uses_vertical_jumps(self):
        sid=next(sid for sid,s in SCENARIOS.items() if s['family']=='sampling')
        widget=build_simulator(self.root,{'simulator':sid},THEME)
        # 50 Hz sampled at 100 Hz happens to yield all zeros. Choose a
        # nondegenerate signal to verify held levels and vertical jumps.
        widget._vars['frequency'].set(125)
        widget._vars['sample_rate'].set(1000)
        curve=widget._curve(widget._data,widget.parameters()); jumps=0
        for (x1,y1),(x2,y2) in zip(curve,curve[1:]):
            if x1!=x2:self.assertAlmostEqual(y1,y2,places=6)
            elif abs(y1-y2)>1e-6:jumps+=1
        self.assertGreater(jumps,1)
