import cv2
import numpy as np
import time

from vision import Capture, get_contours
from physics_world import PhysicsWorld, DEFAULT_PARAMS

WINDOW_MAIN   = "Vision Physics Sim"
WINDOW_TUNER  = "Sensitivity Tuner"
WINDOW_BALLS  = "Ball Controls"


def setup_tuner():
    cv2.namedWindow(WINDOW_TUNER, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_TUNER, 420, 80)
    cv2.createTrackbar("Sensitivity", WINDOW_TUNER, 30, 100, lambda _: None)


def setup_ball_controls():
    cv2.namedWindow(WINDOW_BALLS, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_BALLS, 420, 280)
    noop = lambda _: None
    cv2.createTrackbar("Size      (px)",      WINDOW_BALLS, DEFAULT_PARAMS["size"],     50,   noop)
    cv2.createTrackbar("H. Speed  (px/s)",    WINDOW_BALLS, DEFAULT_PARAMS["h_speed"],  400,  noop)
    cv2.createTrackbar("Rate      (per 10s)", WINDOW_BALLS, DEFAULT_PARAMS["rate"],     30,   noop)
    cv2.createTrackbar("Gravity   (px/s²)",   WINDOW_BALLS, DEFAULT_PARAMS["gravity"],  3000, noop)
    cv2.createTrackbar("Bounce    (0-100)",   WINDOW_BALLS, DEFAULT_PARAMS["bounce"],   100,  noop)
    cv2.createTrackbar("Max balls",           WINDOW_BALLS, DEFAULT_PARAMS["max_balls"],50,   noop)


def get_ball_params():
    return {
        "size":      max(5, cv2.getTrackbarPos("Size      (px)",      WINDOW_BALLS)),
        "h_speed":   cv2.getTrackbarPos("H. Speed  (px/s)",    WINDOW_BALLS),
        "rate":      max(1, cv2.getTrackbarPos("Rate      (per 10s)", WINDOW_BALLS)),
        "gravity":   cv2.getTrackbarPos("Gravity   (px/s²)",   WINDOW_BALLS),
        "bounce":    cv2.getTrackbarPos("Bounce    (0-100)",   WINDOW_BALLS),
        "max_balls": max(1, cv2.getTrackbarPos("Max balls",           WINDOW_BALLS)),
    }


def get_sensitivity():
    return cv2.getTrackbarPos("Sensitivity", WINDOW_TUNER)


def draw_overlay(frame, ball_data, contours, show_debug, fps, has_bg):
    out = frame.copy()

    if show_debug and contours:
        for hull in contours:
            pts = hull.reshape(-1, 1, 2).astype(np.int32)
            cv2.polylines(out, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

    for (x, y, r, color) in ball_data:
        cv2.circle(out, (x, y), r, color, -1)
        cv2.circle(out, (x, y), r, (0, 0, 0), 1)

    cv2.putText(out, f"FPS: {fps:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

    if not has_bg:
        msg = "Press B to sample background"
        (tw, th), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cx = (out.shape[1] - tw) // 2
        cy = out.shape[0] // 2
        cv2.rectangle(out, (cx - 12, cy - th - 8), (cx + tw + 12, cy + 8), (0, 0, 0), -1)
        cv2.putText(out, msg, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 255), 2, cv2.LINE_AA)
    else:
        hints = "B: re-sample  |  D: debug outlines  |  ESC/Q: quit"
        cv2.putText(out, hints, (10, out.shape[0] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)

    return out


def main():
    capture = Capture(width=1280, height=720)

    setup_tuner()
    setup_ball_controls()
    params = get_ball_params()

    world = PhysicsWorld(capture.width, capture.height)
    world.spawn_initial(10, params)

    cv2.namedWindow(WINDOW_MAIN, cv2.WINDOW_NORMAL)

    background = None
    show_debug = True
    prev_time = time.perf_counter()

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q'), ord('Q')):
            break
        if key in (ord('d'), ord('D')):
            show_debug = not show_debug
        if key in (ord('b'), ord('B')):
            frame = capture.read()
            if frame is not None:
                background = frame.copy()

        frame = capture.read()
        if frame is None:
            continue

        params = get_ball_params()

        contours = []
        if background is not None:
            sensitivity = get_sensitivity()
            contours, _ = get_contours(frame, background, sensitivity)
            world.update_obstacles(contours, params["bounce"] / 100)

        now = time.perf_counter()
        dt = now - prev_time
        prev_time = now
        world.step(dt, params)

        fps = 1.0 / dt if dt > 0 else 0
        ball_data = world.get_ball_draw_data()
        out = draw_overlay(frame, ball_data, contours, show_debug, fps, background is not None)

        cv2.imshow(WINDOW_MAIN, out)

    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
