"""Mathematical invariants and stated causal behavior, not clinical validation."""
from dataclasses import replace
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from biology_engine import (
    BiologyEngine, Conditions, Profile, CELL_INDEX, CELLS, DT, N,
    CYTOKINE_INDEX, FEVER_INDEX, STATE_SIZE,
    ORGAN_INDEX, ORGAN_PARAMETERS, ORGANS, TRANSPORT_EDGES,
)


class BiologyEngineTests(unittest.TestCase):
    def test_finite_input_validation(self):
        for name in ('growth_b', 'growth_v', 'spread', 'resistance', 'immune',
                     'allergy', 'antibiotic', 'antiviral', 'support', 'oxygen',
                     'anti_inflammatory', 'cytokine_feedback'):
            for invalid in (math.nan, math.inf, -math.inf, -1, '1', True, None):
                with self.subTest(name=name, value=invalid), self.assertRaises(ValueError):
                    BiologyEngine(replace(Conditions(), **{name: invalid}))
        for bad in (None, {}, {'not_a_cell': 1}, dict.fromkeys(CELL_INDEX, math.nan)):
            with self.assertRaises(ValueError):
                Conditions(cell_levels=bad).validate()

    def test_invalid_exposure_is_atomic(self):
        engine = BiologyEngine()
        old = engine.state[:], engine.events[:]
        for organ, b, v in (('unknown', 0, 0), ([], 0, 0), ('lung', -1, 0),
                            ('lung', .2, math.nan), ('lung', True, 0)):
            with self.assertRaises(ValueError):
                engine.expose(organ, b, v)
            self.assertEqual(old, (engine.state, engine.events))

    def test_exposure_saturates_and_records_actual_input(self):
        engine = BiologyEngine(bacteria=.9)
        engine.expose('lung', .3, .25)
        q = engine.organ_reading('lung')
        self.assertEqual(q['bacteria'], 1)
        self.assertEqual(q['virus'], .25)
        self.assertIn('0.10', engine.events[-1][1])

    def test_invalid_step_state_or_timestep_rejected_before_progress(self):
        engine = BiologyEngine()
        for value in (True, 1.5, -1, 120001):
            with self.assertRaises(ValueError):
                engine.advance_steps(value)
        for value in (0, DT*2, math.nan, True):
            with self.assertRaises(ValueError):
                BiologyEngine(dt=value)
        engine.state[0] = math.nan
        with self.assertRaises(ValueError):
            engine.advance_steps(1)
        self.assertEqual(engine.steps, 0)

    def test_mutated_controls_validated(self):
        engine = BiologyEngine()
        engine.conditions.antibiotic = 10
        with self.assertRaises(ValueError):
            engine.advance_steps(10)
        self.assertEqual(engine.steps, 0)

    def test_disease_free_zero_state_is_an_equilibrium(self):
        engine = BiologyEngine(bacteria=0, virus=0)
        engine.advance_steps(120)
        self.assertEqual(engine.state, [0.0]*len(engine.state))
        self.assertEqual(engine.reserve, 1)

    def test_deterministic_independent_of_ui_batching(self):
        a = BiologyEngine(bacteria=.35, virus=.2)
        b = BiologyEngine(bacteria=.35, virus=.2)
        a.advance_steps(480)
        for _ in range(12):
            b.advance_steps(40)
        self.assertEqual(a.state, b.state)
        self.assertEqual(a.snapshot(), b.snapshot())

    def test_exact_single_compartment_logistic_with_clearance(self):
        engine = BiologyEngine(Conditions(immune=0, spread=0), bacteria=.23)
        engine.advance_steps(240)
        p = ORGAN_PARAMETERS['lung']
        r = engine.conditions.growth_b*p.bacterial_growth
        a = r-.16*p.local_clearance
        e = math.exp(a*engine.time)
        exact = a*.23*e/(a+r*.23*(e-1))
        self.assertAlmostEqual(engine.organ_reading('lung')['bacteria'], exact, delta=2e-11)

    def test_rk4_fourth_order_against_independent_exponential(self):
        errors = []
        for dt in (DT, DT/2):
            engine = BiologyEngine(Conditions(immune=0), bacteria=0, dt=dt)
            engine.state[CELL_INDEX['neutrophil']] = 1
            engine.advance_steps(round(1/dt))
            errors.append(abs(engine.state[CELL_INDEX['neutrophil']]-math.exp(-1.2)))
        self.assertLess(errors[1], 1e-11)
        self.assertGreater(errors[0]/errors[1], 14)
        self.assertLess(errors[0]/errors[1], 18)

    def test_transport_conserves_each_pathogen_and_preserves_other_states(self):
        rng = random.Random(35000)
        engine = BiologyEngine()
        y = [rng.random() for _ in engine.state]
        dy = engine.transport_derivative(y)
        self.assertAlmostEqual(math.fsum(dy[0:4*N:4]), 0, places=14)
        self.assertAlmostEqual(math.fsum(dy[1:4*N:4]), 0, places=14)
        self.assertTrue(all(dy[i] == 0 for i in range(len(y)) if i >= 4*N or i % 4 in (2, 3)))
        # Integrate this isolated production component through the same RK4 path.
        engine.state = y
        engine.state[2:4*N:4] = [0]*N
        before = [math.fsum(engine.state[offset:4*N:4]) for offset in (0, 1)]
        engine._derivative = engine.transport_derivative
        engine.advance_steps(120)
        after = [math.fsum(engine.state[offset:4*N:4]) for offset in (0, 1)]
        for left, right in zip(before, after):
            self.assertAlmostEqual(left, right, places=13)

    def test_transport_network_connected_and_no_duplicate_edges(self):
        edges = {tuple(sorted((i, j))) for i, j, _ in TRANSPORT_EDGES}
        self.assertEqual(len(edges), len(TRANSPORT_EDGES))
        reached = {0}
        while True:
            more = {j if i in reached else i for i, j in edges if i in reached or j in reached}
            if more <= reached:
                break
            reached |= more
        self.assertEqual(reached, set(range(N)))

    def test_vector_field_points_into_unit_domain_at_all_boundaries(self):
        rng = random.Random(35001)
        controls = Conditions(growth_b=2, growth_v=2, spread=.3, immune=2,
                              allergy=1, antibiotic=1, antiviral=1, support=1,
                              oxygen=1, anti_inflammatory=1,
                              cell_levels=dict.fromkeys(CELL_INDEX, 3))
        engine = BiologyEngine(controls)
        for _ in range(3):
            base = [rng.random() for _ in engine.state]
            for i in range(len(base)):
                for boundary in (0, 1):
                    y = base[:]
                    y[i] = boundary
                    derivative = engine._derivative(y)[i]
                    with self.subTest(index=i, boundary=boundary):
                        self.assertGreaterEqual(derivative if boundary == 0 else -derivative, -1e-12)

    def test_extreme_controls_stay_bounded(self):
        for immune in (0, 2):
            engine = BiologyEngine(Conditions(growth_b=2, growth_v=2, spread=.3,
                immune=immune, allergy=1, cell_levels=dict.fromkeys(CELL_INDEX, 3)), bacteria=1, virus=1)
            engine.advance_steps(2400)
            self.assertTrue(all(math.isfinite(x) and 0 <= x <= 1 for x in engine.state))

    def test_antibiotic_only_changes_bacteria_not_virus_only_case(self):
        a = BiologyEngine(Conditions(antibiotic=0), bacteria=0, virus=.4)
        b = BiologyEngine(Conditions(antibiotic=1), bacteria=0, virus=.4)
        a.advance_steps(360); b.advance_steps(360)
        self.assertEqual(a.state, b.state)
        x = BiologyEngine(Conditions(antibiotic=0, immune=0), bacteria=.4)
        y = BiologyEngine(Conditions(antibiotic=1, immune=0), bacteria=.4)
        x.advance_steps(120); y.advance_steps(120)
        self.assertLess(y.snapshot()['bacteria'], x.snapshot()['bacteria'])

    def test_full_resistance_removes_model_antibiotic_effect(self):
        a = BiologyEngine(Conditions(antibiotic=0), bacteria=.4)
        b = BiologyEngine(Conditions(antibiotic=1, resistance=1), bacteria=.4)
        a.advance_steps(240); b.advance_steps(240)
        self.assertEqual(a.state, b.state)

    def test_antiviral_has_no_direct_bacterial_effect(self):
        a = BiologyEngine(Conditions(antiviral=0), bacteria=.4)
        b = BiologyEngine(Conditions(antiviral=1), bacteria=.4)
        a.advance_steps(240); b.advance_steps(240)
        self.assertEqual(a.state, b.state)

    def test_support_changes_injury_not_pure_bacterial_growth(self):
        a = BiologyEngine(Conditions(immune=0, support=0), bacteria=.5)
        b = BiologyEngine(Conditions(immune=0, support=1), bacteria=.5)
        a.advance_steps(360); b.advance_steps(360)
        self.assertEqual(a.snapshot()['bacteria'], b.snapshot()['bacteria'])
        self.assertLess(b.organ_reading('lung')['damage'], a.organ_reading('lung')['damage'])

    def test_adaptive_path_has_sequential_lag_and_separate_cell_states(self):
        engine = BiologyEngine(bacteria=.5)
        engine.advance_steps(12)
        q = engine.cell_readings()
        self.assertGreater(q['dendritic']['activation'], q['helper']['activation'])
        self.assertGreater(q['helper']['activation'], q['bcell']['activation'])
        self.assertGreater(q['bcell']['activation'], q['plasma']['activation'])
        self.assertNotEqual(CELL_INDEX['bcell'], CELL_INDEX['plasma'])
        self.assertNotEqual(CELL_INDEX['basophil'], CELL_INDEX['mast'])

    def test_dendritic_activity_causally_drives_helper_response(self):
        a = BiologyEngine(bacteria=.5)
        c = Conditions(); c.cell_levels['dendritic'] = 0
        b = BiologyEngine(c, bacteria=.5)
        a.advance_steps(240); b.advance_steps(240)
        self.assertGreater(a.cell_readings()['helper']['activity'], 0)
        self.assertEqual(b.cell_readings()['helper']['activity'], 0)

    def test_allergy_controls_are_separate_and_increase_inflammation(self):
        a = BiologyEngine(Conditions(allergy=0), bacteria=0)
        b = BiologyEngine(Conditions(allergy=1), bacteria=0)
        a.advance_steps(240); b.advance_steps(240)
        self.assertEqual(a.snapshot()['inflammation'], 0)
        self.assertGreater(b.snapshot()['inflammation'], 0)
        self.assertEqual(b.snapshot()['bacteria'], 0)
        self.assertEqual(b.snapshot()['virus'], 0)

    def test_organs_have_distinct_parameters_and_responses(self):
        self.assertEqual(set(ORGAN_PARAMETERS), set(ORGAN_INDEX))
        self.assertEqual(len(set(ORGAN_PARAMETERS.values())), N)
        engine = BiologyEngine(Conditions(spread=0, immune=0), bacteria=0)
        for organ in ORGANS:
            engine.expose(organ.key, .2)
        engine.advance_steps(120)
        self.assertNotEqual(engine.organ_reading('lung'), engine.organ_reading('skin'))

    def test_end_is_model_threshold_and_freezes_integrator(self):
        engine = BiologyEngine()
        engine.state[4*ORGAN_INDEX['heart']+2] = .9
        engine.advance_steps(1)
        self.assertTrue(engine.ended)
        state, steps = engine.state[:], engine.steps
        engine.advance_steps(100)
        self.assertEqual(state, engine.state)
        self.assertEqual(steps, engine.steps)
        self.assertIn('실제 사망 예측 아님', engine.events[-1][1])
        with self.assertRaises(ValueError):
            engine.expose('heart', .1)

    def test_profile_validation_and_metadata_do_not_invent_age_or_sex_risks(self):
        for invalid in (Profile(age_years=-1), Profile(age_years=121),
                        Profile(age_years=math.nan), Profile(sex='unknown'),
                        Profile(diabetes=1), Profile(chronic_lung='yes')):
            with self.assertRaises(ValueError):
                BiologyEngine(profile=invalid)
        a = BiologyEngine(profile=Profile(age_years=8, sex='female'))
        b = BiologyEngine(profile=Profile(age_years=85, sex='male'))
        a.advance_steps(120); b.advance_steps(120)
        self.assertEqual(a.state, b.state)
        self.assertEqual(a.snapshot()['profile']['age_years'], 8)
        self.assertEqual(b.snapshot()['profile']['sex'], 'male')

    def test_state_extension_preserves_organ_and_cell_offsets(self):
        self.assertEqual(CYTOKINE_INDEX, 4*N+len(CELLS))
        self.assertEqual(FEVER_INDEX, CYTOKINE_INDEX+1)
        self.assertEqual(len(BiologyEngine().state), STATE_SIZE)
        self.assertTrue(all(index < CYTOKINE_INDEX for index in CELL_INDEX.values()))

    def test_infection_drives_cytokine_and_delayed_fever_response(self):
        engine = BiologyEngine(bacteria=.7, virus=.2)
        engine.advance_steps(120)
        q = engine.snapshot()
        self.assertGreater(q['cytokine'], 0)
        self.assertGreater(q['fever'], 0)
        self.assertGreater(q['cytokine'], q['fever'])
        self.assertNotIn('temperature', q)
        self.assertNotIn('minutes_to_death', q)

    def test_positive_feedback_changes_signal_and_systemic_damage(self):
        a = BiologyEngine(Conditions(cytokine_feedback=0), bacteria=0)
        b = BiologyEngine(Conditions(cytokine_feedback=1), bacteria=0)
        a.state[CYTOKINE_INDEX] = b.state[CYTOKINE_INDEX] = .5
        self.assertLess(a._derivative(a.state)[CYTOKINE_INDEX], 0)
        self.assertGreater(b._derivative(b.state)[CYTOKINE_INDEX], 0)
        a.advance_steps(240); b.advance_steps(240)
        self.assertGreater(b.snapshot()['cytokine'], a.snapshot()['cytokine'])
        self.assertGreater(b.organ_reading('liver')['damage'], a.organ_reading('liver')['damage'])

    def test_support_and_inflammation_control_promote_signal_resolution(self):
        a = BiologyEngine(Conditions(cytokine_feedback=1), bacteria=0)
        b = BiologyEngine(Conditions(cytokine_feedback=1, support=1, anti_inflammatory=1), bacteria=0)
        a.state[CYTOKINE_INDEX] = b.state[CYTOKINE_INDEX] = .6
        a.advance_steps(240); b.advance_steps(240)
        self.assertLess(b.snapshot()['cytokine'], a.snapshot()['cytokine'])
        self.assertLess(b.snapshot()['fever'], a.snapshot()['fever'])

    def test_fever_response_matches_independent_exact_solution(self):
        # Hold only the signal fixed to isolate the actual fever state equation.
        engine = BiologyEngine(bacteria=0)
        engine.state[CYTOKINE_INDEX] = .7
        original = engine._derivative
        def signal_clamped(y):
            dy = original(y)
            dy[CYTOKINE_INDEX] = 0
            return dy
        engine._derivative = signal_clamped
        engine.advance_steps(120)
        exact = .7*(1-math.exp(-.6))
        self.assertAlmostEqual(engine.snapshot()['fever'], exact, delta=1e-11)

    def test_background_conditions_have_explicit_teaching_effects(self):
        base = BiologyEngine(bacteria=0)
        diabetes = BiologyEngine(bacteria=0, profile=Profile(diabetes=True))
        immune = BiologyEngine(bacteria=0, profile=Profile(immunosuppression=True))
        i = 4*ORGAN_INDEX['skin']
        for e in (base, diabetes, immune):
            e.state[i+2] = .4
            e.state[CELL_INDEX['neutrophil']] = .5
        self.assertAlmostEqual(diabetes._derivative(diabetes.state)[i+2], .75*base._derivative(base.state)[i+2])
        self.assertAlmostEqual(immune.cell_readings()['neutrophil']['activity'], .55*base.cell_readings()['neutrophil']['activity'])

    def test_chronic_organ_function_floor_persists_in_uninfected_model(self):
        engine = BiologyEngine(bacteria=0, profile=Profile(chronic_lung=True, chronic_kidney=True))
        self.assertEqual(engine.reserve, .75)
        before = engine.state[:]
        engine.advance_steps(1200)
        self.assertEqual(engine.state, before)
        self.assertEqual(engine.organ_reading('lung')['damage'], .25)
        self.assertEqual(engine.organ_reading('kidney')['damage'], .25)

    def test_combined_profile_and_cytokine_extremes_are_bounded(self):
        engine = BiologyEngine(Conditions(growth_b=2, growth_v=2, spread=.3,
            allergy=1, cytokine_feedback=1, immune=2,
            cell_levels=dict.fromkeys(CELL_INDEX, 3)), bacteria=1, virus=1,
            profile=Profile(diabetes=True, immunosuppression=True,
                            chronic_lung=True, chronic_kidney=True))
        engine.state[CYTOKINE_INDEX] = 1
        engine.state[FEVER_INDEX] = 1
        engine.advance_steps(2400)
        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1 for v in engine.state))
        self.assertGreaterEqual(engine.organ_reading('lung')['damage'], .25)
        self.assertGreaterEqual(engine.organ_reading('kidney')['damage'], .25)


if __name__ == '__main__':
    unittest.main()
