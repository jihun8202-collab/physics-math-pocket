"""Deterministic, SI-unit physical models independent of Tkinter.

Runge-Kutta order 4 at 240 fixed steps/s; rendering rate never changes the model.
Sources: OpenStax College Physics 2e 5.2 and 16.4; University Physics 1 15.5.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple

FIXED_DT = 1.0 / 240.0
KINDS = ("projectile", "pendulum", "spring")


@dataclass(frozen=True)
class Settings:
    kind: str = "projectile"
    gravity: float = 9.80665
    mass: float = 1.0
    launch_speed: float = 20.0
    angle_degrees: float = 45.0
    initial_height: float = 0.0
    # D = 1/2 rho Cd A (kg/m); F_drag = -D |v| v.
    quadratic_drag: float = 0.008
    length: float = 1.5
    # Angular damping rate beta (1/s).
    angular_damping: float = 0.08
    stiffness: float = 20.0
    spring_damping: float = 0.6  # N s/m
    amplitude: float = 0.6

    def validate(self) -> None:
        if self.kind not in KINDS:
            raise ValueError("Unknown experiment kind")
        ranges = {
            "gravity": (1, 15), "mass": (0.1, 10), "launch_speed": (0, 60),
            "angle_degrees": (-120, 120), "initial_height": (0, 20),
            "quadratic_drag": (0, 0.05), "length": (0.2, 5),
            "angular_damping": (0, 2), "stiffness": (1, 100),
            "spring_damping": (0, 5), "amplitude": (0, 2),
        }
        for name, (minimum, maximum) in ranges.items():
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be finite and in [{minimum}, {maximum}]")


@dataclass(frozen=True)
class Reading:
    time: float
    x: float
    y: float
    vx: float
    vy: float
    angle: float
    angular_velocity: float
    energy: float
    landed: bool = False

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)


class PhysicsEngine:
    def __init__(self, settings: Settings) -> None:
        settings.validate()
        self.settings = settings
        angle = math.radians(settings.angle_degrees)
        if settings.kind == "projectile":
            self._state = (0.0, settings.initial_height, settings.launch_speed * math.cos(angle), settings.launch_speed * math.sin(angle))
        elif settings.kind == "pendulum":
            self._state = (angle, 0.0, 0.0, 0.0)
        else:
            self._state = (settings.amplitude, 0.0, 0.0, 0.0)
        self._steps = 0
        self._time = 0.0
        self._landed = False
        self.reading = self._read()

    def advance_steps(self, count: int) -> Reading:
        if not isinstance(count, int) or not 0 <= count <= 240000:
            raise ValueError("Step count must be an integer in [0, 240000]")
        for _ in range(count):
            if self._landed:
                break
            self.step()
        return self.reading

    def step(self) -> Reading:
        if self._landed:
            return self.reading
        next_state = self._integrate(self._state, FIXED_DT)
        if self.settings.kind == "projectile" and next_state[1] < 0:
            # Find contact inside the physical step, rather than inside the frame.
            low, high = 0.0, FIXED_DT
            for _ in range(32):
                middle = (low + high) / 2
                if self._integrate(self._state, middle)[1] >= 0:
                    low = middle
                else:
                    high = middle
            contact = (low + high) / 2
            q = self._integrate(self._state, contact)
            self._state = (q[0], 0.0, q[2], q[3])
            self._time += contact
            self._landed = True
        else:
            self._state = next_state
            self._steps += 1
            self._time = self._steps * FIXED_DT
        self.reading = self._read()
        return self.reading

    def _derivative(self, q: Tuple[float, ...]) -> Tuple[float, ...]:
        p = self.settings
        if p.kind == "projectile":
            drag = p.quadratic_drag * math.hypot(q[2], q[3]) / p.mass
            return (q[2], q[3], -drag * q[2], -p.gravity - drag * q[3])
        if p.kind == "pendulum":
            return (q[1], -p.gravity / p.length * math.sin(q[0]) - p.angular_damping * q[1], 0.0, 0.0)
        return (q[1], (-p.stiffness * q[0] - p.spring_damping * q[1]) / p.mass, 0.0, 0.0)

    def _integrate(self, q: Tuple[float, ...], dt: float) -> Tuple[float, ...]:
        def offset(k: Tuple[float, ...], factor: float) -> Tuple[float, ...]:
            return tuple(q[i] + factor * k[i] for i in range(4))
        k1 = self._derivative(q)
        k2 = self._derivative(offset(k1, dt / 2))
        k3 = self._derivative(offset(k2, dt / 2))
        k4 = self._derivative(offset(k3, dt))
        return tuple(q[i] + dt * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / 6 for i in range(4))

    def _read(self) -> Reading:
        p, q = self.settings, self._state
        if p.kind == "projectile":
            energy = 0.5 * p.mass * (q[2] ** 2 + q[3] ** 2) + p.mass * p.gravity * q[1]
            return Reading(self._time, q[0], q[1], q[2], q[3], 0, 0, energy, self._landed)
        if p.kind == "pendulum":
            theta, omega = q[:2]
            energy = 0.5 * p.mass * p.length ** 2 * omega ** 2 + p.mass * p.gravity * p.length * (1 - math.cos(theta))
            return Reading(self._time, p.length * math.sin(theta), -p.length * math.cos(theta),
                           p.length * omega * math.cos(theta), p.length * omega * math.sin(theta), theta, omega, energy)
        return Reading(self._time, q[0], 0, q[1], 0, 0, 0, 0.5 * p.mass * q[1] ** 2 + 0.5 * p.stiffness * q[0] ** 2)
