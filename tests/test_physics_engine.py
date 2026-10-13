"""Independent analytic/invariant checks for the enhanced physical experiments."""
import math
from dataclasses import replace
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physics_engine import FIXED_DT, PhysicsEngine, Settings


class PhysicsEngineTests(unittest.TestCase):
    def test_vacuum_trajectory(self):
        p = Settings(quadratic_drag=0)
        engine = PhysicsEngine(p)
        initial_energy = engine.reading.energy
        q = engine.advance_steps(240)
        velocity = p.launch_speed / math.sqrt(2)
        self.assertAlmostEqual(q.time, 1, places=12)
        self.assertAlmostEqual(q.x, velocity, places=10)
        self.assertAlmostEqual(q.y, velocity - p.gravity / 2, places=10)
        self.assertAlmostEqual(q.energy, initial_energy, places=9)

    def test_vacuum_landing(self):
        p = Settings(quadratic_drag=0)
        engine = PhysicsEngine(p)
        q = engine.advance_steps(2400)
        self.assertTrue(q.landed)
        self.assertEqual(q.y, 0)
        self.assertAlmostEqual(q.time, math.sqrt(2) * p.launch_speed / p.gravity, places=10)
        self.assertAlmostEqual(q.x, p.launch_speed ** 2 / p.gravity, places=9)
        self.assertEqual(engine.advance_steps(1000), q)

    def test_elevated_and_zero_speed_landing(self):
        p = Settings(quadratic_drag=0, launch_speed=0, initial_height=5)
        q = PhysicsEngine(p).advance_steps(2400)
        self.assertTrue(q.landed)
        self.assertAlmostEqual(q.time, math.sqrt(2 * p.initial_height / p.gravity), places=10)
        self.assertEqual(q.x, 0)
        zero = PhysicsEngine(Settings(launch_speed=0)).advance_steps(1)
        self.assertTrue(zero.landed)
        self.assertLess(zero.time, 1e-10)

    def test_quadratic_drag_energy_and_range(self):
        p = Settings()
        engine = PhysicsEngine(p)
        previous = engine.reading.energy
        for _ in range(7200):
            q = engine.step()
            self.assertLessEqual(q.energy, previous + 1e-8)
            previous = q.energy
            if q.landed:
                break
        vacuum = PhysicsEngine(replace(p, quadratic_drag=0)).advance_steps(7200)
        self.assertTrue(q.landed)
        self.assertLess(q.x, vacuum.x)
        self.assertLess(q.energy, vacuum.energy)

    def test_undamped_spring_analytic_solution(self):
        p = Settings(kind="spring", spring_damping=0)
        q = PhysicsEngine(p).advance_steps(2400)
        frequency = math.sqrt(p.stiffness / p.mass)
        self.assertAlmostEqual(q.x, p.amplitude * math.cos(frequency * 10), delta=2e-8)
        self.assertAlmostEqual(q.vx, -p.amplitude * frequency * math.sin(frequency * 10), delta=1e-7)
        self.assertAlmostEqual(q.energy, 0.5 * p.stiffness * p.amplitude ** 2, delta=1e-8)

    def test_damped_spring_analytic_solution(self):
        p = Settings(kind="spring")
        q = PhysicsEngine(p).advance_steps(2400)
        gamma = p.spring_damping / (2 * p.mass)
        omega = math.sqrt(p.stiffness / p.mass - gamma ** 2)
        expected = p.amplitude * math.exp(-gamma * 10) * (math.cos(omega * 10) + gamma / omega * math.sin(omega * 10))
        self.assertAlmostEqual(q.x, expected, delta=1e-8)
        self.assertLess(q.energy, 0.02)

    def test_nonlinear_pendulum_conserves_energy(self):
        p = Settings(kind="pendulum", angle_degrees=110, angular_damping=0)
        engine = PhysicsEngine(p)
        initial_energy = engine.reading.energy
        q = engine.advance_steps(24000)
        self.assertAlmostEqual(q.energy, initial_energy, delta=3e-7)
        self.assertAlmostEqual(math.hypot(q.x, q.y), p.length, places=12)

    def test_large_angle_pendulum_has_longer_period(self):
        p = Settings(kind="pendulum", angle_degrees=100, angular_damping=0)
        engine = PhysicsEngine(p)
        for _ in range(2400):
            q = engine.step()
            if q.angle <= 0:
                break
        small_angle_quarter = math.pi / 2 * math.sqrt(p.length / p.gravity)
        self.assertGreater(q.time, 1.15 * small_angle_quarter)

    def test_pendulum_damping(self):
        engine = PhysicsEngine(Settings(kind="pendulum"))
        initial = previous = engine.reading.energy
        for _ in range(2400):
            q = engine.step()
            self.assertLessEqual(q.energy, previous + 1e-9)
            previous = q.energy
        self.assertLess(previous, initial / 2)

    def test_fixed_step_batching_is_deterministic(self):
        for kind in ("projectile", "pendulum", "spring"):
            first = PhysicsEngine(Settings(kind=kind))
            second = PhysicsEngine(Settings(kind=kind))
            first.advance_steps(1920)
            for _ in range(120):
                second.advance_steps(16)
            self.assertEqual(first.reading, second.reading)
        self.assertEqual(FIXED_DT, 1 / 240)

    def test_supported_extremes_stay_finite(self):
        parameters = [
            Settings(mass=0.1, launch_speed=60, quadratic_drag=0.05, angle_degrees=80),
            Settings(kind="pendulum", length=0.2, gravity=15, angle_degrees=120, angular_damping=2),
            Settings(kind="spring", mass=0.1, stiffness=100, spring_damping=5, amplitude=2),
            Settings(kind="spring", amplitude=0),
        ]
        for p in parameters:
            engine = PhysicsEngine(p)
            for _ in range(7200):
                q = engine.step()
                self.assertTrue(math.isfinite(q.energy) and q.energy >= 0)
                self.assertTrue(math.isfinite(q.x) and math.isfinite(q.y))

    def test_invalid_configuration_and_steps_are_rejected(self):
        for p in [Settings(mass=0), Settings(gravity=math.nan), Settings(quadratic_drag=-0.1), Settings(length=math.inf), Settings(kind="unknown")]:
            with self.assertRaises(ValueError):
                PhysicsEngine(p)
        for count in (-1, 0.5, 250000):
            with self.assertRaises(ValueError):
                PhysicsEngine(Settings()).advance_steps(count)


if __name__ == "__main__":
    unittest.main()
