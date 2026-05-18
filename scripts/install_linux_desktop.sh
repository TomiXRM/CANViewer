#!/usr/bin/env bash
set -euo pipefail

APP_NAME="CANViewer"
APP_ID="com.tomixrm.CANViewer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

APPIMAGE_PATH="${1:-}"
if [[ -z "${APPIMAGE_PATH}" ]]; then
  APPIMAGE_PATH="$(find "${SCRIPT_DIR}" "${ROOT_DIR}/dist" -maxdepth 1 -name "${APP_NAME}-*.AppImage" -print -quit 2>/dev/null || true)"
fi

if [[ -z "${APPIMAGE_PATH}" || ! -f "${APPIMAGE_PATH}" ]]; then
  echo "Usage: $0 /path/to/${APP_NAME}.AppImage" >&2
  exit 1
fi

ICON_SOURCE=""
if [[ -f "${SCRIPT_DIR}/${APP_NAME}.png" ]]; then
  ICON_SOURCE="${SCRIPT_DIR}/${APP_NAME}.png"
elif [[ -f "${ROOT_DIR}/asset/icon.png" ]]; then
  ICON_SOURCE="${ROOT_DIR}/asset/icon.png"
else
  echo "Could not find ${APP_NAME} icon." >&2
  exit 1
fi

INSTALL_DIR="${HOME}/.local/bin"
APPLICATIONS_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

mkdir -p "${INSTALL_DIR}" "${APPLICATIONS_DIR}" "${ICON_DIR}"

INSTALLED_APPIMAGE="${INSTALL_DIR}/${APP_NAME}.AppImage"
cp "${APPIMAGE_PATH}" "${INSTALLED_APPIMAGE}"
chmod +x "${INSTALLED_APPIMAGE}"

cp "${ICON_SOURCE}" "${ICON_DIR}/${APP_NAME}.png"

cat > "${APPLICATIONS_DIR}/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=CAN bus monitor
Exec=${INSTALLED_APPIMAGE} %F
Icon=${APP_NAME}
Terminal=false
Categories=Development;Utility;
StartupWMClass=${APP_NAME}
EOF

chmod 644 "${APPLICATIONS_DIR}/${APP_ID}.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APPLICATIONS_DIR}" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "${HOME}/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed ${APP_NAME}"
echo "AppImage: ${INSTALLED_APPIMAGE}"
echo "Desktop entry: ${APPLICATIONS_DIR}/${APP_ID}.desktop"
