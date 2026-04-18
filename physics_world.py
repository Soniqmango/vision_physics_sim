import pymunk
import random
import math
import numpy as np

BALL_COLORS_BGR = [
    (60,  60,  255),
    (30,  160, 255),
    (0,   230, 230),
    (30,  220, 30),
    (230, 230, 0),
    (255, 80,  30),
    (255, 30,  160),
    (200, 30,  255),
    (30,  255, 150),
    (255, 180, 30),
]

JITTER_THRESHOLD = 8
FRICTION = 0.3
BALL_MASS = 1.0

DEFAULT_PARAMS = {
    "size":       16,    # ball radius px
    "h_speed":   120,    # max horizontal velocity at spawn
    "rate":        8,    # balls spawned per 10 s  → interval = 10/rate
    "gravity":   900,    # px/s²
    "bounce":     85,    # elasticity × 100
    "max_balls":  20,
}


class PhysicsWorld:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.space = pymunk.Space()
        self.space.gravity = (0, DEFAULT_PARAMS["gravity"])

        self._wall_shapes = self._add_screen_borders()

        self.obstacle_shapes = []
        self.obstacle_body = None
        self._prev_centroids = []

        self.balls = []
        self._color_idx = 0
        self._spawn_timer = 0.0

    # ── screen border walls ────────────────────────────────────────────────
    def _add_screen_borders(self):
        w, h = self.width, self.height
        sb = self.space.static_body
        walls = [
            pymunk.Segment(sb, (0, 0), (0, h), 4),   # left
            pymunk.Segment(sb, (w, 0), (w, h), 4),   # right
        ]
        for seg in walls:
            seg.elasticity = DEFAULT_PARAMS["bounce"] / 100
            seg.friction = FRICTION
        self.space.add(*walls)
        return walls

    # ── ball spawning ──────────────────────────────────────────────────────
    def _next_color(self):
        color = BALL_COLORS_BGR[self._color_idx % len(BALL_COLORS_BGR)]
        self._color_idx += 1
        return color

    def _make_ball(self, x, y, radius, h_speed, elasticity):
        vx = random.uniform(-h_speed, h_speed)
        moment = pymunk.moment_for_circle(BALL_MASS, 0, radius)
        body = pymunk.Body(BALL_MASS, moment)
        body.position = (x, y)
        body.velocity = (vx, 0)
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = FRICTION
        self.space.add(body, shape)
        self.balls.append((body, shape, self._next_color()))

    def _spawn_one(self, params):
        radius = params["size"] + random.randint(-4, 4)
        radius = max(5, radius)
        cx = self.width // 2
        x = cx + random.randint(-60, 60)
        y = radius + 2
        self._make_ball(x, y, radius, params["h_speed"], params["bounce"] / 100)

    def spawn_initial(self, n, params):
        for i in range(n):
            radius = params["size"] + random.randint(-4, 4)
            radius = max(5, radius)
            cx = self.width // 2
            x = cx + random.randint(-80, 80)
            y = radius + 2 + i * (radius * 2 + 10)
            self._make_ball(x, y, radius, params["h_speed"], params["bounce"] / 100)

    # ── obstacle management ────────────────────────────────────────────────
    def _centroid(self, pts):
        return pts.mean(axis=0)

    def _should_update(self, new_contours):
        if len(new_contours) != len(self._prev_centroids):
            return True
        for hull, prev_c in zip(new_contours, self._prev_centroids):
            c = self._centroid(hull.astype(float))
            if math.hypot(c[0] - prev_c[0], c[1] - prev_c[1]) >= JITTER_THRESHOLD:
                return True
        return False

    def update_obstacles(self, contours, elasticity):
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
                seg.elasticity = elasticity
                seg.friction = FRICTION
                self.obstacle_shapes.append(seg)

        self.space.add(*self.obstacle_shapes)
        self._prev_centroids = new_centroids

    # ── simulation step ────────────────────────────────────────────────────
    def step(self, dt, params):
        self.space.gravity = (0, params["gravity"])
        self.space.step(min(dt, 1 / 30))

        fallen = [b for b in self.balls if b[0].position.y > self.height + 80]
        for ball in fallen:
            self.space.remove(ball[0], ball[1])
            self.balls.remove(ball)

        interval = 10.0 / max(params["rate"], 1)
        self._spawn_timer += dt
        if self._spawn_timer >= interval and len(self.balls) < params["max_balls"]:
            self._spawn_one(params)
            self._spawn_timer = 0.0

    # ── query for rendering ────────────────────────────────────────────────
    def get_ball_draw_data(self):
        return [
            (int(body.position.x), int(body.position.y), int(shape.radius), color)
            for body, shape, color in self.balls
        ]
