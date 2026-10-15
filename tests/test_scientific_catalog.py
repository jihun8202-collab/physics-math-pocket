"""Scientific contracts and independently derived known values, no UI mocks."""
import math
import unittest
from collections import Counter

from scientific_catalog import MODELS, SCENARIOS, evaluate, samples
from physics_engine import PhysicsEngine, Settings


class ScientificCatalogTests(unittest.TestCase):
    def test_counts_and_each_condition_is_unique_within_family(self):
        self.assertEqual(len(MODELS),50)
        self.assertEqual(len(SCENARIOS),5000)
        self.assertEqual(Counter(s['family'] for s in SCENARIOS.values()),Counter({k:100 for k in MODELS}))
        self.assertEqual(len({s['title'] for s in SCENARIOS.values()}),5000)
        for family in MODELS:
            members=[s for s in SCENARIOS.values() if s['family']==family]
            self.assertEqual(len({tuple(sorted(s['condition'].items())) for s in members}),100)

    def test_all_5000_have_finite_domain_boundaries_and_midpoint(self):
        for sid,spec in SCENARIOS.items():
            self.assertEqual(len(spec['sliders']),2,sid)
            self.assertTrue(spec['source'].startswith('https://'),sid)
            self.assertTrue(spec['notes'],sid)
            for label,name,lo,hi,default in spec['sliders']:
                self.assertTrue(lo<=default<=hi,(sid,name))
                self.assertIn('(',label)
            for x in (spec['xmin'],(spec['xmin']+spec['xmax'])/2,spec['xmax']):
                self.assertTrue(math.isfinite(evaluate(spec,x)),(sid,x))

    def test_every_parameter_corner_has_finite_complete_curve(self):
        for family,model in MODELS.items():
            one,two=model['parameters']
            for a in (one['minimum'],one['maximum']):
                for b in (two['minimum'],two['maximum']):
                    points=samples(model,{one['name']:a,two['name']:b},count=65)
                    self.assertEqual(points[0][0],model['xmin'])
                    self.assertAlmostEqual(points[-1][0],model['xmax'])
                    self.assertTrue(all(math.isfinite(y) for _,y in points),family)

    def test_dynamic_settings_fit_engine_and_preserve_initial_conditions(self):
        count=0
        for spec in SCENARIOS.values():
            dynamic=spec['dynamic']
            if dynamic is None:
                continue
            settings=Settings(kind=dynamic['kind'],**dynamic['settings'])
            settings.validate()
            engine=PhysicsEngine(settings)
            count+=1
            if dynamic['kind']=='pendulum':
                self.assertAlmostEqual(math.degrees(engine.reading.angle),evaluate(spec,0),places=10)
            elif dynamic['kind']=='spring':
                self.assertAlmostEqual(engine.reading.x,evaluate(spec,0),places=10)
        self.assertEqual(count,400)

    def test_force_reference_and_scaling(self):
        m=MODELS['force']
        self.assertEqual(evaluate(m,2,{'applied_force':8,'mass':2}),8)
        self.assertEqual(evaluate(m,2,{'applied_force':-8,'mass':2}),-8)

    def test_projectile_closed_form_apex_and_landing(self):
        p={'launch_speed':20,'angle_degrees':45}; g=9.80665
        vy=20/math.sqrt(2)
        self.assertAlmostEqual(evaluate(MODELS['projectile'],vy/g,p),vy*vy/(2*g),places=10)
        self.assertAlmostEqual(evaluate(MODELS['projectile'],2*vy/g,p),0,places=10)
        self.assertEqual(evaluate(MODELS['projectile'],10,p),0)

    def test_nonlinear_pendulum_and_spring_agree_with_independent_engine_path(self):
        for kind,params in [('pendulum',{'angle_degrees':100,'length':1.5}),('spring',{'stiffness':20,'spring_damping':0.6})]:
            settings={'gravity':9.80665,'angular_damping':0,'mass':1} if kind=='pendulum' else {'amplitude':0.6,'mass':1}
            engine=PhysicsEngine(Settings(kind=kind,**params,**settings))
            engine.advance_steps(240)
            expected=math.degrees(engine.reading.angle) if kind=='pendulum' else engine.reading.x
            self.assertAlmostEqual(evaluate(MODELS[kind],1,params),expected,places=7)

    def test_units_and_chemical_reference_values(self):
        self.assertAlmostEqual(evaluate(MODELS['hydrostatic'],10,{'density':1000,'gravity':9.80665}),199391.5)
        # One RC time constant must charge to 1-exp(-1) of5V.
        self.assertAlmostEqual(evaluate(MODELS['rc_charge'],1,{'resistance':10000,'capacitance':100}),5*(1-math.exp(-1)))
        self.assertAlmostEqual(evaluate(MODELS['first_order'],math.log(2)/0.1,{'initial':1,'rate':0.1}),0.5)
        self.assertAlmostEqual(evaluate(MODELS['second_order'],10,{'initial':1,'rate':0.1}),0.5)
        self.assertEqual(evaluate(MODELS['buffer'],0.005,{'pka':4.5,'acid':0.005}),4.5)
        self.assertAlmostEqual(evaluate(MODELS['beer_lambert'],0.002,{'absorptivity':500,'path':1}),1)

    def test_biology_limits_are_actual_equation_limits(self):
        self.assertEqual(evaluate(MODELS['enzyme'],0,{'vmax':5,'km':1}),0)
        self.assertAlmostEqual(evaluate(MODELS['enzyme'],1,{'vmax':5,'km':1}),2.5)
        self.assertAlmostEqual(evaluate(MODELS['logistic'],0,{'capacity':1000,'growth':0.5}),10)
        self.assertEqual(evaluate(MODELS['oxygen_binding'],26,{'p50':26,'hill':2.8}),0.5)
        self.assertEqual(evaluate(MODELS['q10'],30,{'baseline':5,'q10':2}),10)

    def test_transit_overlap_and_time_reversal(self):
        m=MODELS['transit']; p={'radius_ratio':0.1,'duration':4}
        self.assertAlmostEqual(evaluate(m,0,p),0.99)
        self.assertEqual(evaluate(m,2,p),1)
        self.assertAlmostEqual(evaluate(m,1.8,p),evaluate(m,-1.8,p),places=13)
        points=samples(m,p,401)
        self.assertTrue(all(0.99-1e-12<=y<=1 for _,y in points))

    def test_actual_midpoint_error_and_bayes_known_value(self):
        a,b,n=0,1,10
        actual=abs(sum(math.sin(a+(j+0.5)*(b-a)/n)*(b-a)/n for j in range(n))-(math.cos(a)-math.cos(b)))
        self.assertAlmostEqual(evaluate(MODELS['midpoint_error'],n,{'start':a,'end':b}),actual,places=14)
        self.assertAlmostEqual(evaluate(MODELS['bayes'],0.01,{'sensitivity':0.9,'specificity':0.99}),0.009/(0.009+0.0099))

    def test_queue_amdahl_and_repetition_reference(self):
        self.assertAlmostEqual(evaluate(MODELS['queue_latency'],5,{'service':10,'latency':0.1}),0.3)
        self.assertEqual(evaluate(MODELS['amdahl'],1,{'parallel':0.9,'overhead':0.009}),1)
        self.assertAlmostEqual(evaluate(MODELS['repetition_code'],0.01,{'bits':8,'repeat_index':1}),1-0.99**8)
        protected=evaluate(MODELS['repetition_code'],0.01,{'bits':8,'repeat_index':2})
        self.assertLess(protected,1-0.99**8)

    def test_reject_invalid_values_and_never_execute_expr(self):
        m=MODELS['enzyme']
        for value in (float('nan'),float('inf'),True,-1,20):
            with self.assertRaises(ValueError): evaluate(m,value)
        with self.assertRaises(ValueError): evaluate(m,1,{'vmax':0})
        with self.assertRaises(ValueError): evaluate(m,1,{'unknown':1})
        with self.assertRaises(ValueError): samples(m,count=1)
        # A spec's textual expression has no influence on trusted dispatch.
        altered={**m,'expr':"__import__('os').getcwd()"}
        self.assertEqual(evaluate(altered,1),evaluate(m,1))


if __name__=='__main__': unittest.main()
