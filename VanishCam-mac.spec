"""Build VanishCam.app for macOS: the full edition, run locally without the online licence."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs


root = Path(SPECPATH).resolve()
icon_file = root / "build" / "icon" / "VanishCam.icns"
resources = (
    (root / "models" / "selfie_segmenter_landscape.tflite", "models"),
    (root / "models" / "gesture_recognizer.task", "models"),
    (root / "models" / "blaze_face_short_range.tflite", "models"),
    (root / "hand_landmarker.task", "."),
    (root / "assets" / "substitution_log.png", "assets"),
    (root / "assets" / "vanish.MP3", "assets"),
    (root / "assets" / "teleport.MP3", "assets"),
    (root / "assets" / "itachi_crow_sheet.png", "assets"),
    (root / "assets" / "sharingan.png", "assets"),
    (root / "editions" / "full" / "edition.txt", "."),
)

missing = [str(path) for path in (icon_file, *(path for path, _ in resources)) if not path.is_file()]
if missing:
    raise SystemExit("Files needed for the build are missing (run build_mac.sh):\n" + "\n".join(missing))

analysis = Analysis(
    [str(root / "vanish_cam_mac.py")],
    pathex=[str(root)],
    binaries=collect_dynamic_libs("mediapipe"),
    datas=[(str(path), destination) for path, destination in resources],
    hiddenimports=["pygame.mixer", "mediapipe.tasks.c"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],  # Only the licence dialogs use it.
    noarchive=False,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="VanishCam",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
collected = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="VanishCam",
)
app = BUNDLE(
    collected,
    name="VanishCam.app",
    icon=str(icon_file),
    bundle_identifier="local.vanishcam",
    version="0.1.0",
    info_plist={
        "NSCameraUsageDescription": "VanishCam applies its effects to your webcam video. The video stays on this Mac.",
        "NSHighResolutionCapable": True,
    },
)
