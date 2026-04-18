import cv2
import numpy as np
import time

from vision import Capture, get_contours
from physics_world import PhysicsWorld

WINDOW_MAIN = "Vision Physics Sim"
WINDOW_TUNER = "Sensitivity Tuner"


def setup_tuner():
    cv2.namedWindow(WINDOW_TUNER, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_TUNER, 400, 80)
    cv2.createTrackbar("Sensitivity", WINDOW_TUNER, 30, 100, lambda _: None)


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

    # HUD
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
    world = PhysicsWorld(capture.width, capture.height)
    world.spawn_initial(10)

    setup_tuner()
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

        contours = []
        if background is not None:
            sensitivity = get_sensitivity()
            contours, _ = get_contours(frame, background, sensitivity)
            world.update_obstacles(contours)

        now = time.perf_counter()
        dt = now - prev_time
        prev_time = now
        world.step(dt)

        fps = 1.0 / dt if dt > 0 else 0
        ball_data = world.get_ball_draw_data()
        out = draw_overlay(frame, ball_data, contours, show_debug, fps, background is not None)

        cv2.imshow(WINDOW_MAIN, out)

    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
