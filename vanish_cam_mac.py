"""macOS app entry point: the local run of vanish_cam, without the online licence."""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path


LOG_PATH = Path.home() / "Library" / "Logs" / "VanishCam" / "vanishcam.log"
MATPLOTLIB_DIR = Path.home() / "Library" / "Caches" / "VanishCam" / "matplotlib"

# How to vanish and how to come back, per mode.
GESTURES = {
    "normal": ("Step back in and raise a V sign (index and middle finger).", "Press R to reappear."),
    "particles": ("Step back in and raise a V sign (index and middle finger).", "Press R to reappear."),
    "naruto": ("Step back in and press your palms together, fingers flat.", "Press R to reappear."),
    "goku": ("Step back in and hold two fingers against your forehead.", "Repeat the gesture to reappear."),
    "itachi": ("Step back in and touch both hands in front of your chest.", "Release, then touch again to reappear."),
}
START_BUTTON = (445, 384, 710, 447)  # left, top, right, bottom


def launched_without_terminal() -> bool:
    """Finder starts an app with stdout on /dev/null; a shell gives a TTY or a pipe."""
    try:
        return os.path.samestat(os.fstat(1), os.stat(os.devnull))
    except OSError:
        return True


def redirect_output_to_log() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = LOG_PATH.open("w", buffering=1, encoding="utf-8")
    # Replace the real descriptors too, so MediaPipe's and OpenCV's native output is kept.
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    sys.stdout = sys.stderr = log


def show_error(message: str) -> None:
    subprocess.run(
        ["osascript", "-e", "on run argv",
         "-e", 'display alert "VanishCam" message (item 1 of argv) as critical',
         "-e", "end run", message],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def instructions_canvas(mode: str):
    import cv2
    import numpy as np

    canvas = np.full((470, 780, 3), (26, 29, 34), dtype=np.uint8)

    def text(value: str, origin: tuple[int, int], scale: float, color: tuple[int, int, int], thickness: int = 1):
        cv2.putText(canvas, value, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

    text("BEFORE THE VIDEO STARTS", (70, 59), 0.86, (236, 239, 242), 2)
    cards = (
        ("1  CAPTURE THE BACKGROUND", "Press START, then step out of the frame.",
         "The empty room is captured during the first 4 seconds."),
        ("2  VANISH", *GESTURES[mode]),
    )
    for index, (heading, first, second) in enumerate(cards):
        top = 88 + index * 118
        cv2.rectangle(canvas, (70, top), (710, top + 104), (48, 54, 62), -1, cv2.LINE_AA)
        cv2.rectangle(canvas, (70, top), (710, top + 104), (111, 142, 153), 2, cv2.LINE_AA)
        text(heading, (88, top + 33), 0.62, (240, 245, 247), 2)
        text(first, (88, top + 62), 0.53, (179, 195, 201))
        text(second, (88, top + 87), 0.53, (179, 195, 201))
    # Goku has no manual keys: the gesture is the only way to vanish and reappear.
    manual_keys = "" if mode == "goku" else "V vanish  |  R reappear  |  "
    text(f"SPACE new background  |  {manual_keys}F fullscreen  |  Q quit", (70, 352), 0.43, (179, 195, 201))
    left, top, right, bottom = START_BUTTON
    cv2.rectangle(canvas, (left, top), (right, bottom), (78, 132, 124), -1)
    text("START", (left + 88, top + 41), 0.72, (240, 245, 247), 2)
    text("ENTER starts  |  Q quits", (70, top + 38), 0.43, (179, 195, 201))
    return canvas


def confirm_start(mode: str) -> bool:
    """Show the steps vanish_cam only prints to a terminal. False means the user quit."""
    import cv2

    title = "Before you start"
    canvas = instructions_canvas(mode)
    started = [False]
    left, top, right, bottom = START_BUTTON

    def on_mouse(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONUP and left <= x <= right and top <= y <= bottom:
            started[0] = True

    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(title, on_mouse)
    try:
        while not started[0]:
            cv2.imshow(title, canvas)
            key = cv2.waitKey(30) & 0xFF
            if key in (10, 13):
                return True
            if key in (ord("q"), 27):
                return False
            if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                return False
        return True
    finally:
        cv2.destroyWindow(title)


def main() -> int:
    detached = launched_without_terminal()
    if detached:
        redirect_output_to_log()
    if getattr(sys, "frozen", False):
        # PyInstaller gives matplotlib (imported by MediaPipe) a config folder it deletes on
        # exit, so the font cache would be rebuilt, slowly, on every launch.
        os.environ["MPLCONFIGDIR"] = str(MATPLOTLIB_DIR)
    try:
        import vanish_cam

        if "--self-test" in sys.argv[1:]:
            # self_test() reads the licence config, which this build does not ship.
            vanish_cam.load_config = lambda: None

        run_camera = vanish_cam.run_camera

        def run_camera_after_instructions(args, resources, mode, *rest):
            if not confirm_start(mode):
                return 0
            return run_camera(args, resources, mode, *rest)

        vanish_cam.run_camera = run_camera_after_instructions
        return vanish_cam.run()
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        traceback.print_exc()
        if detached:
            show_error(f"{error}\n\nLog: {LOG_PATH}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
