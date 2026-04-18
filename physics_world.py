import pymunk
import random
import math
import numpy as np

BALL_COLORS_BGR = [
    (60,  60,  255),   # red
    (30,  160, 255),   # orange
    (0,   230, 230),   # yellow
    (30,  220, 30),    # green
    (230, 230, 0),     # cyan
    (255, 80,  30),    # blue
    (255, 30,  160),   # violet
    (200, 30,  255),   # purple
    (30,  255, 150),   # lime
    (255, 180, 30),    # sky blue
]

JITTER_THRESHOLD = 8
ELASTICITY = 0.85
FRICTION = 0.3
BALL_MASS = 1.0
MAX_BALLS = 20
SPAWN_INTERVAL = 1.2   # seconds between new balls


class PhysicsWorld:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.space = pymunk.Space()
        self.space.gravity = (0, 900)

        self._add_screen_borders()

        self.obstacle_shapes = []
        self.obstacle_body = None
        self._prev_centroids = []

        self.balls = []       # list of (body, shape, color)
        self._color_idx = 0
        self._spawn_timer = 0.0

    # ── screen border walls (left + right only — balls fall in from top, out at bottom) ──
    def _add_screen_borders(self):
        w, h = self.width, self.height
        sb = self.space.static_body
        walls = [
            pymunk.Segment(sb, (0, 0), (0, h), 4),   # left
            pymunk.Segment(sb, (w, 0), (w, h), 4),   # right
        ]
        for seg in walls:
            seg.elasticity = ELASTICITY
            seg.friction = FRICTION
        self.space.add(*walls)

    # ── ball spawning ──────────────────────────────────────────────────────
    def _next_color(self):
        color = BALL_COLORS_BGR[self._color_idx % len(BALL_COLORS_BGR)]
        self._color_idx += 1
        return color

    def _spawn_one(self):
        radius = random.randint(12, 20)
        cx = self.width // 2
        x = cx + random.randint(-60, 60)
        y = radius + 2   # just inside top edge
        vx = random.uniform(-120, 120)

        moment = pymunk.moment_for_circle(BALL_MASS, 0, radius)
        body = pymunk.Body(BALL_MASS, moment)
        body.position = (x, y)
        body.velocity = (vx, 0)

        shape = pymunk.Circle(body, radius)
        shape.elasticity = ELASTICITY
        shape.friction = FRICTION

        self.space.add(body, shape)
        self.balls.append((body, shape, self._next_color()))

    def spawn_initial(self, n=10):
        """Drop n balls staggered from the top so they cascade in."""
        for i in range(n):
            radius = random.randint(12, 20)
            cx = self.width // 2
            x = cx + random.randint(-80, 80)
            y = radius + 2 + i * 55   # stack them downward from top so they don't overlap
            vx = random.uniform(-100, 100)

            moment = pymunk.moment_for_circle(BALL_MASS, 0, radius)
            body = pymunk.Body(BALL_MASS, moment)
            body.position = (x, y)
            body.velocity = (vx, 0)

            shape = pymunk.Circle(body, radius)
            shape.elasticity = ELASTICITY
            shape.friction = FRICTION

            self.space.add(body, shape)
            self.balls.append((body, shape, self._next_color()))

    # ── obstacle management ────────────────────────────────────────────────
    def _centroid(self, pts):
        return pts.mean(axis=0)

    def _should_update(self, new_contours):
        if len(new_contours) != len(self._prev_centroids):
            return True
        for hull, prev_c in zip(new_contours, self._prev_centroids):
            c = self._centroid(hull.astype(float))
            dist = math.hypot(c[0] - prev_c[0], c[1] - prev_c[1])
            if dist >= JITTER_THRESHOLD:
                return True
        return False

    def update_obstacles(self, contours):
        if not self._should_update(contours):
            return

        if self.obstacle_shapes:
            self.space.remove(*self.obstacle_shapes)
            self.obstacle_shapes = []
        if self.obstacle_body and self.obstacle_body in self.space.bodies:
            self.space.remove(self.obstacle_body)

        if not contours:
            self._prev_centroids = []
            self.obstacle_body = None
            return

        static_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.space.add(static_body)
        self.obstacle_body = static_body

        new_centroids = []
        for hull in contours:
            pts = hull.astype(float)
            new_centroids.append(self._centroid(pts))
            n = len(pts)
            for j in range(n):
                a = tuple(pts[j].astype(int))
                b = tuple(pts[(j + 1) % n].astype(int))
                seg = pymunk.Segment(static_body, a, b, 3)
                seg.elasticity = ELASTICITY
                seg.friction = FRICTION
                self.obstacle_shapes.append(seg)

        self.space.add(*self.obstacle_shapes)
        self._prev_centroids = new_centroids

    # ── simulation step ────────────────────────────────────────────────────
    def step(self, dt):
        self.space.step(min(dt, 1 / 30))

        # remove balls that have fallen off the bottom
        fallen = [b for b in self.balls if b[0].position.y > self.height + 80]
        for ball in fallen:
            self.space.remove(ball[0], ball[1])
            self.balls.remove(ball)

        # timed fountain spawn
        self._spawn_timer += dt
        if self._spawn_timer >= SPAWN_INTERVAL and len(self.balls) < MAX_BALLS:
            self._spawn_one()
            self._spawn_timer = 0.0

    # ── query for rendering ────────────────────────────────────────────────
    def get_ball_draw_data(self):
        return [
            (int(body.position.x), int(body.position.y), int(shape.radius), color)
            for body, shape, color in self.balls
        ]
