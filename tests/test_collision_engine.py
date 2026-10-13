"""Analytic and conservation checks for continuous 2-D disc collisions."""
import math
import random
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collision_engine import CollisionEngine, CollisionSettings, Disc


class CollisionEngineTests(unittest.TestCase):
    def engine(self, bodies, boundary="open", restitution=1, width=10, height=6):
        return CollisionEngine(bodies, CollisionSettings(width, height, boundary, restitution))

    def assert_conserved(self, engine, momentum, energy, places=9):
        self.assertAlmostEqual(engine.momentum[0], momentum[0], places=places)
        self.assertAlmostEqual(engine.momentum[1], momentum[1], places=places)
        self.assertAlmostEqual(engine.kinetic_energy, energy, places=places)

    def test_equal_mass_head_on_matches_analytic_velocities_and_contact_time(self):
        engine = self.engine([Disc("a", 2, 3, 2, 0, radius=0.5), Disc("b", 5, 3, -1, 0, radius=0.5)])
        momentum, energy = engine.momentum, engine.kinetic_energy
        a, b = engine.advance(1)
        self.assertAlmostEqual(a.vx, -1, places=12)
        self.assertAlmostEqual(b.vx, 2, places=12)
        self.assertAlmostEqual(a.x, 3, places=12)
        self.assertAlmostEqual(b.x, 5, places=12)
        self.assertAlmostEqual(engine.events[0].time, 2 / 3, places=12)
        self.assert_conserved(engine, momentum, energy)

    def test_unequal_masses_match_closed_form_elastic_solution(self):
        engine = self.engine([Disc("a", 2, 3, 2, 0, mass=1, radius=0.5), Disc("b", 5, 3, -1, 0, mass=3, radius=0.5)])
        momentum, energy = engine.momentum, engine.kinetic_energy
        a, b = engine.advance(1)
        self.assertAlmostEqual(a.vx, -2.5, places=12)
        self.assertAlmostEqual(b.vx, 0.5, places=12)
        self.assert_conserved(engine, momentum, energy)

    def test_oblique_collision_preserves_tangential_velocity(self):
        engine = self.engine([Disc("a", 2, 2, 2, 1, mass=2, radius=0.5), Disc("b", 5, 3, 0, 0, mass=3, radius=0.5)])
        momentum, energy = engine.momentum, engine.kinetic_energy
        a, b = engine.advance(1.2)
        self.assertAlmostEqual(engine.events[0].time, 1, places=12)
        self.assertAlmostEqual(a.vx, -0.4, places=12)
        self.assertAlmostEqual(b.vx, 1.6, places=12)
        self.assertAlmostEqual(a.vy, 1, places=12)
        self.assertAlmostEqual(b.vy, 0, places=12)
        self.assert_conserved(engine, momentum, energy)

    def test_diagonal_contact_has_the_correct_normal_impulse(self):
        engine = self.engine([Disc("a", 2, 2, 2, 2, radius=0.5), Disc("b", 5, 5, 0, 0, radius=0.5)])
        momentum, energy = engine.momentum, engine.kinetic_energy
        a, b = engine.advance(1.3)
        self.assertAlmostEqual(engine.events[0].time, (3 * math.sqrt(2) - 1) / (2 * math.sqrt(2)), places=12)
        self.assertAlmostEqual(a.vx, 0, places=11)
        self.assertAlmostEqual(a.vy, 0, places=11)
        self.assertAlmostEqual(b.vx, 2, places=11)
        self.assertAlmostEqual(b.vy, 2, places=11)
        self.assert_conserved(engine, momentum, energy)

    def test_zero_restitution_stops_relative_normal_motion(self):
        engine = self.engine([Disc("a", 2, 3, 2, 0, radius=0.5), Disc("b", 5, 3, -1, 0, mass=3, radius=0.5)], restitution=0)
        momentum = engine.momentum
        a, b = engine.advance(2)
        self.assertAlmostEqual(a.vx, -0.25, places=12)
        self.assertAlmostEqual(b.vx, -0.25, places=12)
        self.assertAlmostEqual(b.x - a.x, 1, places=12)
        self.assertAlmostEqual(engine.momentum[0], momentum[0], places=12)
        self.assertAlmostEqual(engine.kinetic_energy, 0.125, places=12)
        self.assertAlmostEqual(engine.dissipated_energy, 3.375, places=12)

    def test_partial_restitution_matches_known_relative_speed_and_energy_loss(self):
        engine = self.engine([Disc("a", 2, 3, 2, 0, radius=0.5), Disc("b", 5, 3, -1, 0, mass=3, radius=0.5)], restitution=0.6)
        initial_momentum = engine.momentum
        a, b = engine.advance(1)
        self.assertAlmostEqual(b.vx - a.vx, 1.8, places=12)
        self.assertAlmostEqual(engine.momentum[0], initial_momentum[0], places=12)
        # Loss = 1/2 reduced_mass (1-e²) relative_speed².
        self.assertAlmostEqual(engine.dissipated_energy, 0.5 * 0.75 * (1 - 0.6 ** 2) * 9, places=12)

    def test_high_speed_collision_does_not_tunnel_in_one_large_step(self):
        engine = self.engine([Disc("a", 1, 3, 1000, 0, radius=0.1), Disc("b", 9, 3, -1000, 0, radius=0.1)])
        a, b = engine.advance(0.01)
        self.assertAlmostEqual(engine.events[0].time, 0.0039, places=12)
        self.assertAlmostEqual(a.vx, -1000, places=9)
        self.assertAlmostEqual(b.vx, 1000, places=9)
        self.assertAlmostEqual(a.x, -1.2, places=9)
        self.assertAlmostEqual(b.x, 11.2, places=9)

    def test_open_world_never_reverses_velocity_at_display_edges(self):
        engine = self.engine([Disc("a", 9, 5, 3, 2)], boundary="open")
        a, = engine.advance(5)
        self.assertEqual((a.x, a.y, a.vx, a.vy), (24, 15, 3, 2))
        self.assertEqual(engine.collision_count, 0)
        self.assertEqual(engine.events, ())

    def test_simultaneous_corner_wall_reflections_and_external_impulse(self):
        engine = self.engine([Disc("a", 2, 2, 3, 3, radius=0.5)], boundary="reflect", width=5, height=5)
        initial = engine.momentum
        energy = engine.kinetic_energy
        a, = engine.advance(1)
        self.assertAlmostEqual(a.x, 4, places=12)
        self.assertAlmostEqual(a.y, 4, places=12)
        self.assertEqual((a.vx, a.vy), (-3, -3))
        self.assertEqual(engine.collision_count, 2)
        self.assertEqual(engine.wall_impulse, (-6, -6))
        self.assertEqual(engine.momentum, (initial[0] - 6, initial[1] - 6))
        self.assertAlmostEqual(engine.kinetic_energy, energy, places=12)

    def test_inelastic_wall_loses_only_the_normal_kinetic_energy(self):
        engine = self.engine([Disc("a", 8, 2, 3, 1, radius=0.5)], boundary="reflect", restitution=0.5)
        a, = engine.advance(0.6)
        self.assertEqual(a.vx, -1.5)
        self.assertEqual(a.vy, 1)
        self.assertAlmostEqual(engine.dissipated_energy, 0.5 * 9 * 0.75, places=12)
        self.assertAlmostEqual(engine.wall_impulse[0], -4.5, places=12)

    def test_periodic_wrap_changes_position_but_never_velocity(self):
        engine = self.engine([Disc("a", 9, 5, 3, 2)], boundary="periodic")
        energy, momentum = engine.kinetic_energy, engine.momentum
        a, = engine.advance(1)
        self.assertAlmostEqual(a.x, 2, places=12)
        self.assertAlmostEqual(a.y, 1, places=12)
        self.assertEqual((a.vx, a.vy), (3, 2))
        self.assertEqual(engine.collision_count, 0)
        self.assertEqual(engine.wall_impulse, (0, 0))
        self.assertEqual(len(engine.events), 2)
        self.assert_conserved(engine, momentum, energy)

    def test_wrap_from_exact_zero_and_multiple_crossings(self):
        engine = self.engine([Disc("a", 0, 0, -17, -9)], boundary="periodic")
        a, = engine.advance(2)
        self.assertAlmostEqual(a.x, 6, places=10)
        self.assertAlmostEqual(a.y, 0, places=10)
        self.assertEqual((a.vx, a.vy), (-17, -9))
        self.assertTrue(all(event.kind == "wrap" for event in engine.events))

    def test_periodic_collision_through_horizontal_seam(self):
        engine = self.engine([Disc("a", 0.5, 3, -1, 0, radius=0.25), Disc("b", 9, 3, 1, 0, radius=0.25)], boundary="periodic")
        energy, momentum = engine.kinetic_energy, engine.momentum
        a, b = engine.advance(0.75)
        self.assertAlmostEqual(a.vx, 1, places=12)
        self.assertAlmostEqual(b.vx, -1, places=12)
        self.assertAlmostEqual(a.x, 0.25, places=12)
        self.assertAlmostEqual(b.x, 9.25, places=12)
        pair_event = next(event for event in engine.events if event.kind == "pair")
        self.assertAlmostEqual(pair_event.time, 0.5, places=12)
        self.assert_conserved(engine, momentum, energy)

    def test_periodic_collision_through_diagonal_seams(self):
        engine = self.engine([Disc("a", 0.5, 0.5, -1, -1, radius=0.25), Disc("b", 9.5, 5.5, 1, 1, radius=0.25)], boundary="periodic")
        energy, momentum = engine.kinetic_energy, engine.momentum
        a, b = engine.advance(0.5)
        expected_contact = (math.sqrt(2) - 0.5) / (2 * math.sqrt(2))
        self.assertAlmostEqual(engine.events[0].time, expected_contact, places=12)
        self.assertAlmostEqual(a.vx, 1, places=12)
        self.assertAlmostEqual(a.vy, 1, places=12)
        self.assertAlmostEqual(b.vx, -1, places=12)
        self.assertAlmostEqual(b.vy, -1, places=12)
        self.assert_conserved(engine, momentum, energy)

    def test_periodic_collision_after_a_prior_wrap(self):
        engine = self.engine([Disc("a", 9, 3, 4, 0, radius=0.25), Disc("b", 2, 3, 0, 0, radius=0.25)], boundary="periodic")
        a, b = engine.advance(1)
        self.assertAlmostEqual(a.x, 1.5, places=12)
        self.assertAlmostEqual(b.x, 3.5, places=12)
        self.assertEqual((a.vx, b.vx), (0, 4))
        self.assertEqual([event.kind for event in engine.events], ["wrap", "pair"])
        self.assertAlmostEqual(engine.events[1].time, 0.625, places=12)

    def test_symmetric_simultaneous_three_disc_contacts_conserve_energy(self):
        for restitution in (0, 0.6, 1):
            engine = self.engine([Disc("a", 2, 3, 1, 0, radius=0.5), Disc("b", 3, 3, 0, 0, mass=2, radius=0.5), Disc("c", 4, 3, -1, 0, radius=0.5)], restitution=restitution)
            a, b, c = engine.advance(0.1)
            self.assertAlmostEqual(a.vx, -restitution, places=10)
            self.assertAlmostEqual(b.vx, 0, places=10)
            self.assertAlmostEqual(c.vx, restitution, places=10)
            self.assertAlmostEqual(engine.momentum[0], 0, places=10)
            self.assertAlmostEqual(engine.kinetic_energy, restitution ** 2, places=10)
            self.assertGreaterEqual(b.x - a.x, 1 - 1e-10)
            self.assertGreaterEqual(c.x - b.x, 1 - 1e-10)

    def test_simultaneous_body_contact_against_a_wall(self):
        engine = self.engine([Disc("a", 8.5, 3, 2, 0, radius=0.5), Disc("b", 9.5, 3, 0, 0, radius=0.5)], boundary="reflect")
        initial_momentum = engine.momentum
        initial_energy = engine.kinetic_energy
        a, b = engine.advance(0.1)
        self.assertAlmostEqual(a.vx, -2, places=10)
        self.assertAlmostEqual(b.vx, 0, places=10)
        self.assertAlmostEqual(engine.kinetic_energy, initial_energy, places=10)
        self.assertAlmostEqual(engine.momentum[0], initial_momentum[0] + engine.wall_impulse[0], places=10)
        self.assertLessEqual(b.x, 9.5 + 1e-10)

    def test_light_disc_between_heavy_discs_resolves_simultaneous_contact(self):
        engine = self.engine([Disc("a", 2, 3, 1, 0, mass=100, radius=0.5), Disc("b", 3, 3, 0, 0, mass=0.05, radius=0.5), Disc("c", 4, 3, -1, 0, mass=100, radius=0.5)])
        energy = engine.kinetic_energy
        a, b, c = engine.advance(0.1)
        self.assertAlmostEqual(a.vx, -1, places=9)
        self.assertAlmostEqual(b.vx, 0, places=9)
        self.assertAlmostEqual(c.vx, 1, places=9)
        self.assert_conserved(engine, (0, 0), energy, places=8)

    def test_seeded_six_body_scenes_preserve_energy_or_dissipate_and_balance_momentum(self):
        for seed in (13, 47, 91):
            source = random.Random(seed)
            bodies = []
            while len(bodies) < 6:
                candidate = Disc(str(len(bodies)), source.uniform(1, 9), source.uniform(1, 5),
                                 source.uniform(-6, 6), source.uniform(-6, 6),
                                 mass=source.uniform(0.05, 100), radius=source.uniform(0.15, 0.4))
                if all(math.hypot(candidate.x - b.x, candidate.y - b.y) > candidate.radius + b.radius + 0.1 for b in bodies):
                    bodies.append(candidate)
            for boundary in ("reflect", "open", "periodic"):
                for restitution in (0.5, 1):
                    engine = self.engine(bodies, boundary=boundary, restitution=restitution)
                    initial_momentum, initial_energy = engine.momentum, engine.kinetic_energy
                    previous = initial_energy
                    for _ in range(100):
                        current = engine.advance(0.1)
                        self.assertLessEqual(engine.kinetic_energy, previous + max(1, initial_energy) * 1e-10)
                        previous = engine.kinetic_energy
                        if restitution == 1:
                            self.assertAlmostEqual(previous, initial_energy, delta=max(1, initial_energy) * 1e-9)
                        for component in range(2):
                            self.assertAlmostEqual(engine.momentum[component], initial_momentum[component] + engine.wall_impulse[component], delta=1e-7)
                        for i, a in enumerate(current):
                            for b in current[i + 1:]:
                                dx, dy = b.x - a.x, b.y - a.y
                                if boundary == "periodic":
                                    dx -= 10 * math.floor(dx / 10 + 0.5)
                                    dy -= 6 * math.floor(dy / 6 + 0.5)
                                self.assertGreaterEqual(math.hypot(dx, dy), a.radius + b.radius - 1e-8)

    def test_event_results_are_independent_of_rendering_step_size(self):
        bodies = [Disc("a", 2, 2, 3, 1, radius=0.25), Disc("b", 7, 3, -2, -0.4, mass=2, radius=0.4)]
        for boundary in ("reflect", "open", "periodic"):
            first = self.engine(bodies, boundary=boundary, restitution=0.8)
            second = self.engine(bodies, boundary=boundary, restitution=0.8)
            first.advance(4)
            for _ in range(960):
                second.advance(1 / 240)
            for a, b in zip(first.bodies, second.bodies):
                for name in ("x", "y", "vx", "vy"):
                    self.assertAlmostEqual(getattr(a, name), getattr(b, name), delta=1e-8)
            self.assertEqual(first.collision_count, second.collision_count)

    def test_initial_overlap_and_periodic_seam_overlap_are_rejected(self):
        for boundary, bodies in [
            ("open", [Disc("a", 2, 3, 0, 0), Disc("b", 2.2, 3, 0, 0)]),
            ("periodic", [Disc("a", 0.1, 3, 0, 0), Disc("b", 9.9, 3, 0, 0)]),
            ("periodic", [Disc("a", 0.1, 0.1, 0, 0), Disc("b", 9.9, 5.9, 0, 0)]),
        ]:
            with self.assertRaises(ValueError):
                self.engine(bodies, boundary=boundary)

    def test_nonfinite_and_invalid_inputs_are_rejected(self):
        for disc in [Disc("a", math.nan, 3, 0, 0), Disc("a", 2, 3, math.inf, 0), Disc("a", 2, 3, 0, 0, mass=0), Disc("a", 2, 3, 0, 0, radius=-1)]:
            with self.assertRaises(ValueError):
                self.engine([disc])
        for settings in [CollisionSettings(restitution=-0.1), CollisionSettings(restitution=1.1), CollisionSettings(width=math.nan), CollisionSettings(boundary="fake_bounce")]:
            with self.assertRaises(ValueError):
                CollisionEngine([Disc("a", 2, 3, 0, 0)], settings)
        with self.assertRaises(ValueError):
            self.engine([Disc("same", 2, 3, 0, 0), Disc("same", 5, 3, 0, 0)])
        with self.assertRaises(ValueError):
            self.engine([Disc("a", 0.1, 3, 0, 0)], boundary="reflect")
        engine = self.engine([Disc("a", 2, 3, 0, 0)])
        for duration in (-1, math.nan, math.inf, 61):
            with self.assertRaises(ValueError):
                engine.advance(duration)


if __name__ == "__main__":
    unittest.main()
