# Vision Physics Sim

A real-time augmented reality physics sandbox. Your webcam feed becomes the background; physical objects placed in front of it turn into rigid collision walls — and colourful balls fall from the top and bounce off them live.

The detection is background-subtraction based: sample your empty background once, and anything that appears in front of it is automatically treated as an obstacle, regardless of colour.

---

## How it works

```
Webcam frame
     │
     ▼
absdiff(frame, background) → threshold mask
     │
     ▼
Find contours → convex hulls → Pymunk static segment bodies
     │
     ▼
Pymunk 2D physics step  (gravity + elasticity)
     │
     ▼
Draw balls onto frame → cv2.imshow()
```

A spatial jitter guard compares contour centroids frame-to-frame and only rebuilds collision bodies when an object actually moves, keeping the simulation stable when objects are still.

---

## Requirements

- Python 3.9+
- A webcam

## Installation

```bash
git clone https://github.com/Soniqmango/vision-physics-sim.git
cd vision-physics-sim
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Two windows open alongside the main view:

| Window | Purpose |
|---|---|
| **Sensitivity Tuner** | Controls how different a pixel must be from the background to count as an obstacle |
| **Ball Controls** | Live sliders for ball size, speed, spawn rate, gravity, bounce, and max count |

### First-time setup

1. Point your camera at the plain background (wall, desk, etc.) with **no objects** in frame.
2. Press **`B`** to sample the background — detection activates immediately.
3. Place or hold objects in front of the camera and watch the balls react.
4. Press **`B`** again any time the lighting changes to re-sample.

### Controls

| Key | Action |
|---|---|
| `B` | Sample / re-sample background |
| `D` | Toggle green contour outlines (debug view) |
| `ESC` / `Q` | Quit |

### Ball Controls sliders

| Slider | Effect |
|---|---|
| **Size** | Ball radius (px) |
| **H. Speed** | Horizontal velocity spread at spawn |
| **Rate** | Balls spawned per 10 seconds |
| **Gravity** | Downward acceleration (px/s²) |
| **Bounce** | Elasticity — energy kept on collision (0–100%) |
| **Max balls** | Maximum balls in the scene at once |

---

## Tech stack

| Library | Role |
|---|---|
| [OpenCV](https://opencv.org/) | Webcam capture, background subtraction, drawing, display |
| [Pymunk](http://www.pymunk.org/) | 2D rigid-body physics engine |
| [NumPy](https://numpy.org/) | Frame arithmetic |

---

## Project structure

```
vision_physics_sim/
├── main.py           # Game loop, tuner windows, rendering
├── vision.py         # Webcam capture + background-subtraction contour detection
├── physics_world.py  # Pymunk space, obstacle bodies, ball fountain
└── requirements.txt
```

---

## Tips

- **Sensitivity too low** → small or lightly coloured objects won't be detected. Raise the slider.
- **Sensitivity too high** → shadows and noise create phantom obstacles. Lower the slider or re-sample the background.
- Works best with a **plain, evenly lit background** (solid-colour wall or large sheet of paper).
- For the most dramatic effect, use objects with clearly defined edges — books, hands, cardboard shapes.

---

## Adding the demo GIF

> **To record and add your own demo:**
>
> **Mac:** Open QuickTime → File → New Screen Recording, record a 5–10 second clip of the sim in action, then convert with:
> ```bash
> ffmpeg -i demo.mov -vf "fps=20,scale=800:-1:flags=lanczos" -loop 0 assets/demo.gif
> ```
> **Windows:** Use Xbox Game Bar (`Win+G`) or [ScreenToGif](https://www.screentogif.com/) to record directly to GIF.
>
> Place the file at `assets/demo.gif` and it will appear at the top of this README automatically.
