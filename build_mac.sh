#!/bin/bash
# Build dist/VanishCam.app. Set PYTHON to choose the interpreter that creates .venv.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV_PY=".venv/bin/python"
LOGO="marketing/vanishcam_minimal_logo.png"

if [ ! -x "$VENV_PY" ]; then
    "$PYTHON" -m venv .venv
fi
# requirements.txt pins mediapipe 1.0.1, which aborts on Apple Silicon
# (google-ai-edge/mediapipe#6356), so install a fixed release in its place.
grep -v '^mediapipe' requirements.txt \
    | "$VENV_PY" -m pip install --quiet -r /dev/stdin "mediapipe==1.2.3" "pyinstaller>=6,<7"

# A python.org Python has no CA certificates until its installer script is run; use the system's.
SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/ssl/cert.pem}" \
    "$VENV_PY" -c "from vanish_cam import download_models; download_models('normal'); download_models('goku')"

iconset="build/icon/VanishCam.iconset"
rm -rf build/icon
mkdir -p "$iconset"
for size in 16 32 128 256 512; do
    double=$((size * 2))
    sips -z "$size" "$size" "$LOGO" --out "$iconset/icon_${size}x${size}.png" >/dev/null
    sips -z "$double" "$double" "$LOGO" --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$iconset" -o build/icon/VanishCam.icns

"$VENV_PY" -m PyInstaller --noconfirm --distpath dist --workpath build/pyinstaller VanishCam-mac.spec
rm -rf dist/VanishCam  # PyInstaller's intermediate folder; the app bundle holds its own copy.

dist/VanishCam.app/Contents/MacOS/VanishCam --self-test
echo "Built dist/VanishCam.app"
