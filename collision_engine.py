"""Continuous, deterministic two-dimensional collisions of frictionless discs.

Units are metres, kilograms and seconds. Between instantaneous impacts velocities
are constant: no gravity, friction, rotation or external driving is applied.
Pair impulses conserve momentum; elastic impacts conserve kinetic energy.
Physical wall impulses are reported separately. Periodic boundaries describe a
torus, including disc collisions through either seam and through diagonal seams.

Model reference: OpenStax University Physics 1, section 9.4 Types of Collisions.
https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Disc:
    id: str
    x: float
    y: float
    vx: float
    vy: float
    mass: float = 1.0
    radius: float = 0.3


@dataclass(frozen=True)
class CollisionSettings:
    width: float = 10.0
    height: float = 6.0
    boundary: str = "reflect"
    restitution: float = 1.0


@dataclass(frozen=True)
class CollisionEvent:
    time: float
    kind: str  # pair, wall, wrap
    body_ids: Tuple[str, ...]
    normal: Tuple[float, float] = (0.0, 0.0)
    impulse: float = 0.0


@dataclass
class _Body:
    id: str
    x: float
    y: float
    vx: float
    vy: float
    mass: float
    radius: float


@dataclass(frozen=True)
class _Contact:
    # Positive impulse increases the separating normal velocity.
    terms: Tuple[Tuple[int, float, float], ...]
    kind: str
    body_ids: Tuple[str, ...]
    normal: Tuple[float, float]


class CollisionEngine:
    """1–6 rigid discs with continuous time-of-impact collision detection.

    Simultaneous contacts use a mass-weighted contact projection followed by
    restitution. This is one explicit rigid-body simultaneous-impact model;
    it does not model material deformation or claim an exact real-world contact
    duration. No random values or rendering-frame-dependent physical forces exist.
    """
    def __init__(self, bodies: Iterable[Disc], settings: Optional[CollisionSettings] = None):
        self.settings = settings or CollisionSettings()
        self._validate_settings()
        original = tuple(bodies)
        if not 1 <= len(original) <= 6:
            raise ValueError("Provide between 1 and 6 discs")
        self._bodies: List[_Body] = []
        identifiers = set()
        for disc in original:
            if not isinstance(disc, Disc) or not isinstance(disc.id, str) or not disc.id.strip() or disc.id in identifiers:
                raise ValueError("Each disc needs a unique nonempty string id")
            identifiers.add(disc.id)
            for name in ("x", "y", "vx", "vy", "mass", "radius"):
                if not _finite(getattr(disc, name)):
                    raise ValueError(f"{disc.id}: {name} must be finite")
            if not 0.0001 <= disc.mass <= 1_000_000:
                raise ValueError("Disc mass must be in [0.0001, 1000000] kg")
            if disc.radius <= 0 or 2 * disc.radius >= min(self.settings.width, self.settings.height):
                raise ValueError("Positive radius must fit inside the world")
            if max(abs(disc.vx), abs(disc.vy)) > 10000:
                raise ValueError("Velocity components must be in [-10000, 10000] m/s")
            if self.settings.boundary == "reflect":
                if not disc.radius <= disc.x <= self.settings.width - disc.radius or not disc.radius <= disc.y <= self.settings.height - disc.radius:
                    raise ValueError(f"{disc.id}: centre must keep the whole disc inside physical walls")
            elif not 0 <= disc.x <= self.settings.width or not 0 <= disc.y <= self.settings.height:
                raise ValueError(f"{disc.id}: initial centre must be inside the world")
            self._bodies.append(_Body(disc.id, disc.x, disc.y, disc.vx, disc.vy, disc.mass, disc.radius))
        self._position_epsilon = 1e-10 * max(1.0, self.settings.width, self.settings.height)
        # Small discs make the nearest periodic image unambiguous at contact.
        for i, a in enumerate(self._bodies):
            for b in self._bodies[i + 1:]:
                radius = a.radius + b.radius
                if self.settings.boundary == "periodic" and radius >= min(self.settings.width, self.settings.height) / 2:
                    raise ValueError("Periodic pairs need summed radii smaller than half the shortest world side")
                dx, dy = self._delta(a, b)
                if math.hypot(dx, dy) < radius - self._position_epsilon:
                    raise ValueError(f"Initial discs {a.id} and {b.id} overlap")
        self.time = 0.0
        self.events: Tuple[CollisionEvent, ...] = ()
        self.collision_count = 0
        self.wall_impulse = (0.0, 0.0)
        self._initial_energy = self.kinetic_energy

    def _validate_settings(self):
        p = self.settings
        if p.boundary not in ("reflect", "open", "periodic"):
            raise ValueError("Boundary must be reflect, open or periodic")
        if not _finite(p.width) or not _finite(p.height) or not 0.001 <= p.width <= 1_000_000 or not 0.001 <= p.height <= 1_000_000:
            raise ValueError("World sides must be finite and in [0.001, 1000000] metres")
        if not _finite(p.restitution) or not 0 <= p.restitution <= 1:
            raise ValueError("Restitution must be in [0, 1]")

    @property
    def bodies(self) -> Tuple[Disc, ...]:
        p = self.settings
        return tuple(Disc(b.id, b.x % p.width if p.boundary == "periodic" else b.x,
                          b.y % p.height if p.boundary == "periodic" else b.y,
                          b.vx, b.vy, b.mass, b.radius) for b in self._bodies)

    @property
    def kinetic_energy(self) -> float:
        return math.fsum(0.5 * b.mass * (b.vx * b.vx + b.vy * b.vy) for b in self._bodies)

    @property
    def momentum(self) -> Tuple[float, float]:
        return (math.fsum(b.mass * b.vx for b in self._bodies), math.fsum(b.mass * b.vy for b in self._bodies))

    @property
    def dissipated_energy(self) -> float:
        return max(0.0, self._initial_energy - self.kinetic_energy)

    def step(self, dt: float) -> Tuple[Disc, ...]:
        return self.advance(dt)

    def advance(self, seconds: float) -> Tuple[Disc, ...]:
        if not _finite(seconds) or not 0 <= seconds <= 60:
            raise ValueError("Advance duration must be finite and in [0, 60] seconds")
        remaining = float(seconds)
        end_time = self.time + remaining
        occurred = []
        iterations = 0
        while remaining > 0:
            event_time = self._next_event(remaining)
            if event_time is None:
                self._move(remaining)
                self.time = end_time
                remaining = 0.0
                break
            event_time = max(0.0, min(remaining, event_time))
            self._move(event_time)
            self.time += event_time
            remaining = max(0.0, end_time - self.time)
            wrapped = self._wrap(occurred)
            contacts = self._contacts()
            applied = self._resolve_contacts(contacts, occurred)
            iterations += 1
            if iterations > 100000:
                raise RuntimeError("Too many collision events in one advance; use a shorter duration")
            if event_time == 0 and not wrapped and not applied:
                # A grazing contact has no impulse. Move by a tiny positive time
                # to avoid detecting the same floating-point tangency forever.
                tiny = min(remaining, 1e-12)
                if tiny == 0:
                    break
                self._move(tiny)
                self.time += tiny
                remaining = max(0.0, end_time - self.time)
            if remaining <= 1e-14 * max(1.0, abs(end_time)):
                self._move(remaining)
                self.time = end_time
                break
        self.events = tuple(occurred)
        return self.bodies

    def _move(self, seconds):
        for b in self._bodies:
            b.x += b.vx * seconds
            b.y += b.vy * seconds

    def _delta(self, a, b):
        dx, dy = b.x - a.x, b.y - a.y
        if self.settings.boundary == "periodic":
            dx -= self.settings.width * math.floor(dx / self.settings.width + 0.5)
            dy -= self.settings.height * math.floor(dy / self.settings.height + 0.5)
        return dx, dy

    def _next_event(self, remaining):
        p = self.settings
        best = None
        def consider(t):
            nonlocal best
            if t >= -1e-12 and t <= remaining + 1e-12 and (best is None or t < best):
                best = max(0.0, t)
        for b in self._bodies:
            if p.boundary == "reflect":
                if b.vx < -1e-12: consider((b.radius - b.x) / b.vx)
                if b.vx > 1e-12: consider((p.width - b.radius - b.x) / b.vx)
                if b.vy < -1e-12: consider((b.radius - b.y) / b.vy)
                if b.vy > 1e-12: consider((p.height - b.radius - b.y) / b.vy)
            elif p.boundary == "periodic":
                if b.vx < -1e-12: consider(-b.x / b.vx)
                if b.vx > 1e-12: consider((p.width - b.x) / b.vx)
                if b.vy < -1e-12: consider(-b.y / b.vy)
                if b.vy > 1e-12: consider((p.height - b.y) / b.vy)
        images = [(0.0, 0.0)] if p.boundary != "periodic" else [(x * p.width, y * p.height) for x in (-1, 0, 1) for y in (-1, 0, 1)]
        for i, a in enumerate(self._bodies):
            for b in self._bodies[i + 1:]:
                vx, vy = b.vx - a.vx, b.vy - a.vy
                speed_sq = vx * vx + vy * vy
                if speed_sq <= 1e-24:
                    continue
                radius = a.radius + b.radius
                for ox, oy in images:
                    dx, dy = b.x + ox - a.x, b.y + oy - a.y
                    inward = dx * vx + dy * vy
                    if inward >= -1e-11 * radius:
                        continue
                    gap = dx * dx + dy * dy - radius * radius
                    if gap <= self._position_epsilon * radius:
                        consider(0.0)
                        continue
                    discriminant = inward * inward - speed_sq * gap
                    if discriminant <= 0:
                        continue
                    root = math.sqrt(discriminant)
                    # Stable early root of a t² + 2 b t + c = 0.
                    consider(gap / (-inward + root))
        return best

    def _wrap(self, occurred):
        if self.settings.boundary != "periodic":
            return False
        wrapped = False
        p = self.settings
        for b in self._bodies:
            sides = []
            if b.x <= self._position_epsilon and b.vx < 0:
                b.x = p.width; sides.append("x")
            elif b.x >= p.width - self._position_epsilon and b.vx > 0:
                b.x = 0.0; sides.append("x")
            if b.y <= self._position_epsilon and b.vy < 0:
                b.y = p.height; sides.append("y")
            elif b.y >= p.height - self._position_epsilon and b.vy > 0:
                b.y = 0.0; sides.append("y")
            if sides:
                occurred.append(CollisionEvent(self.time, "wrap", (b.id,)))
                wrapped = True
        return wrapped

    def _contacts(self):
        contacts = []
        eps, p = self._position_epsilon, self.settings
        for i, a in enumerate(self._bodies):
            if p.boundary == "reflect":
                walls = [
                    (a.x <= a.radius + eps, 1.0, 0.0),
                    (a.x >= p.width - a.radius - eps, -1.0, 0.0),
                    (a.y <= a.radius + eps, 0.0, 1.0),
                    (a.y >= p.height - a.radius - eps, 0.0, -1.0),
                ]
                for touching, nx, ny in walls:
                    if touching:
                        contacts.append(_Contact(((i, nx, ny),), "wall", (a.id,), (nx, ny)))
            for j in range(i + 1, len(self._bodies)):
                b = self._bodies[j]
                dx, dy = self._delta(a, b)
                distance = math.hypot(dx, dy)
                if distance <= a.radius + b.radius + eps:
                    if distance < eps:
                        raise RuntimeError("Disc centres coincide")
                    nx, ny = dx / distance, dy / distance
                    contacts.append(_Contact(((i, -nx, -ny), (j, nx, ny)), "pair", (a.id, b.id), (nx, ny)))
        return sorted(contacts, key=lambda c: (c.kind, tuple(sorted(c.body_ids)), c.normal))

    def _resolve_contacts(self, contacts, occurred):
        if not contacts:
            return False
        # Project pre-impact velocities onto all nonpenetrating contact velocities.
        # The compression impulse is multiplied by (1+e) for restitution. At a
        # single contact this is precisely the standard mass-weighted impulse law.
        matrix = []
        for a in contacts:
            row = []
            for b in contacts:
                entry = math.fsum((ax * bx + ay * by) / self._bodies[i].mass
                                  for i, ax, ay in a.terms for j, bx, by in b.terms if i == j)
                row.append(entry)
            matrix.append(row)
        before = [math.fsum(self._bodies[i].vx * nx + self._bodies[i].vy * ny for i, nx, ny in c.terms) for c in contacts]
        if min(before) >= -1e-11:
            return False
        tolerance = 1e-12 * max(1.0, max(abs(value) for value in before))
        impulses = _contact_projection(matrix, before, tolerance)
        applied = False
        factor = 1 + self.settings.restitution
        for contact, compressed_impulse in zip(contacts, impulses):
            impulse = factor * compressed_impulse
            if impulse <= 0:
                continue
            for i, nx, ny in contact.terms:
                b = self._bodies[i]
                b.vx += impulse * nx / b.mass
                b.vy += impulse * ny / b.mass
            if contact.kind == "wall":
                wx, wy = self.wall_impulse
                nx, ny = contact.normal
                self.wall_impulse = (wx + impulse * nx, wy + impulse * ny)
            self.collision_count += 1
            occurred.append(CollisionEvent(self.time, contact.kind, contact.body_ids, contact.normal, impulse))
            applied = True
        return applied


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _solve_linear(matrix, rhs):
    """Small pivoted dense solve; redundant constraints use the bounded fallback."""
    count = len(rhs)
    rows = [list(row) + [rhs[i]] for i, row in enumerate(matrix)]
    scale = max(abs(value) for row in matrix for value in row)
    for column in range(count):
        pivot = max(range(column, count), key=lambda i: abs(rows[i][column]))
        if abs(rows[pivot][column]) <= scale * 1e-15:
            return None
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        for j in range(column, count + 1):
            rows[column][j] /= divisor
        for i in range(column + 1, count):
            multiplier = rows[i][column]
            for j in range(column, count + 1):
                rows[i][j] -= multiplier * rows[column][j]
    result = [0.0] * count
    for i in range(count - 1, -1, -1):
        result[i] = rows[i][count] - math.fsum(rows[i][j] * result[j] for j in range(i + 1, count))
    return result


def _contact_projection(matrix, before, tolerance):
    """Nonnegative convex contact projection with a deterministic active set.

    Exact solves keep light discs between heavy discs from requiring thousands
    of rendering-blocking iterations. A projected iteration fallback handles
    linearly redundant contacts whose impulse distribution is nonunique.
    """
    count = len(before)
    impulses = [0.0] * count
    active = set()
    for _ in range(count * 4 + 64):
        residual = [before[i] + math.fsum(matrix[i][j] * impulses[j] for j in range(count)) for i in range(count)]
        candidates = [i for i in range(count) if i not in active and residual[i] < -tolerance]
        if not candidates:
            return impulses
        active.add(min(candidates, key=lambda i: (residual[i], i)))
        for _ in range(count * 4 + 64):
            selected = sorted(active)
            solution = _solve_linear([[matrix[i][j] for j in selected] for i in selected], [-before[i] for i in selected])
            if solution is None:
                return _iterative_projection(matrix, before, tolerance, impulses)
            proposed = [0.0] * count
            for i, value in zip(selected, solution):
                proposed[i] = value
            invalid = [i for i in selected if proposed[i] <= 0]
            if not invalid:
                impulses = proposed
                break
            alpha = min(impulses[i] / (impulses[i] - proposed[i])
                        if impulses[i] > 0 else 0.0 for i in invalid)
            impulses = [impulses[i] + alpha * (proposed[i] - impulses[i]) for i in range(count)]
            for i in selected:
                if impulses[i] <= 0:
                    impulses[i] = 0.0
                    active.remove(i)
            if not active:
                break
        else:
            return _iterative_projection(matrix, before, tolerance, impulses)
    return _iterative_projection(matrix, before, tolerance, impulses)


def _iterative_projection(matrix, before, tolerance, impulses):
    for _ in range(8192):
        largest_change = 0.0
        for i in range(len(before)):
            normal_speed = before[i] + math.fsum(matrix[i][j] * impulses[j] for j in range(len(before)))
            updated = max(0.0, impulses[i] - normal_speed / matrix[i][i])
            largest_change = max(largest_change, abs(updated - impulses[i]) * matrix[i][i])
            impulses[i] = updated
        if largest_change <= tolerance:
            return impulses
    raise RuntimeError("Simultaneous contact solver did not converge")
