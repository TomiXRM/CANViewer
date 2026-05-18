import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


APP_NAME = "CANViewer"
BUNDLE_ID = "com.tomixrm.CANViewer"
ROOT_DIR = Path(__file__).resolve().parents[1]
APPIMAGE_TOOL_URLS = {
    "x86_64": "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage",
    "aarch64": "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-aarch64.AppImage",
}


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT_DIR, check=True)


def remove_previous_output(output_dir: Path) -> None:
    for path in [
        output_dir / APP_NAME,
        output_dir / f"{APP_NAME}.exe",
        output_dir / f"{APP_NAME}.app",
        output_dir / f"{APP_NAME}.dmg",
        output_dir / f"{APP_NAME}.AppDir",
        output_dir / f"{APP_NAME}-{platform.machine()}.AppImage",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    for pattern in ["*.AppImage", "*.build", "*.dist", "*.onefile-build", "*.app"]:
        for path in output_dir.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()


def nuitka_base_command(output_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "nuitka",
        "main.py",
        f"--output-dir={output_dir}",
        "--output-filename=CANViewer",
        "--standalone",
        "--follow-imports",
        "--enable-plugin=pyside6",
        "--include-module=can.interfaces.slcan",
        "--include-module=can.interfaces.gs_usb",
        "--include-package=gs_usb",
        "--include-package=usb",
        "--assume-yes-for-downloads",
        "--remove-output",
    ]


def build_macos(output_dir: Path, create_dmg: bool) -> None:
    command = nuitka_base_command(output_dir)
    command.extend(
        [
            "--macos-create-app-bundle",
            "--macos-app-icon=asset/icon.icns",
            f"--macos-app-name={APP_NAME}",
            f"--macos-signed-app-name={BUNDLE_ID}",
        ]
    )

    sign_identity = os.environ.get("MACOS_SIGN_IDENTITY")
    if sign_identity:
        command.extend(
            [
                f"--macos-sign-identity={sign_identity}",
                "--macos-sign-notarization",
            ]
        )

    run(command)

    app_bundles = sorted(output_dir.glob("*.app"))
    if not app_bundles:
        raise RuntimeError(f"No .app bundle was created in {output_dir}")

    app_path = app_bundles[0]
    expected_app_path = output_dir / f"{APP_NAME}.app"
    if app_path != expected_app_path:
        if expected_app_path.exists():
            shutil.rmtree(expected_app_path)
        app_path.rename(expected_app_path)

    for dist_dir in output_dir.glob("*.dist"):
        if dist_dir.is_dir() and not any(dist_dir.iterdir()):
            dist_dir.rmdir()

    if create_dmg:
        dmg_path = output_dir / f"{APP_NAME}.dmg"
        if dmg_path.exists():
            dmg_path.unlink()
        run(
            [
                "hdiutil",
                "create",
                "-volname",
                APP_NAME,
                "-srcfolder",
                str(expected_app_path),
                "-ov",
                "-format",
                "UDZO",
                str(dmg_path),
            ]
        )
        if sign_identity and sign_identity != "auto":
            run(["codesign", "--force", "--sign", sign_identity, str(dmg_path)])


def build_windows(output_dir: Path) -> None:
    command = nuitka_base_command(output_dir)
    command.extend(
        [
            "--onefile",
            "--windows-icon-from-ico=asset/icon.ico",
            "--windows-disable-console",
        ]
    )
    run(command)


def build_linux(output_dir: Path, create_appimage: bool) -> None:
    command = nuitka_base_command(output_dir)
    command.append("--linux-icon=asset/icon.png")
    if not create_appimage:
        command.append("--onefile")
    run(command)

    if create_appimage:
        create_linux_appimage(output_dir)


def create_linux_appimage(output_dir: Path) -> None:
    dist_dirs = sorted(output_dir.glob("*.dist"))
    if not dist_dirs:
        raise RuntimeError(
            f"No Nuitka standalone directory was created in {output_dir}"
        )

    app_dir = output_dir / f"{APP_NAME}.AppDir"
    if app_dir.exists():
        shutil.rmtree(app_dir)

    bin_dir = app_dir / "usr" / "bin"
    icon_dir = app_dir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    applications_dir = app_dir / "usr" / "share" / "applications"
    bin_dir.mkdir(parents=True)
    icon_dir.mkdir(parents=True)
    applications_dir.mkdir(parents=True)

    shutil.copytree(dist_dirs[0], bin_dir, dirs_exist_ok=True)
    shutil.copy2(ROOT_DIR / "asset" / "icon.png", app_dir / f"{APP_NAME}.png")
    shutil.copy2(ROOT_DIR / "asset" / "icon.png", icon_dir / f"{APP_NAME}.png")

    desktop_entry = linux_desktop_entry(exec_command=APP_NAME)
    (app_dir / f"{APP_NAME}.desktop").write_text(desktop_entry, encoding="utf-8")
    (applications_dir / f"{BUNDLE_ID}.desktop").write_text(
        desktop_entry,
        encoding="utf-8",
    )

    app_run = app_dir / "AppRun"
    app_run.write_text(
        f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/{APP_NAME}" "$@"
""",
        encoding="utf-8",
    )
    app_run.chmod(0o755)

    tool = get_appimagetool()
    arch = appimage_arch()
    env = os.environ.copy()
    env["ARCH"] = arch
    appimage_path = output_dir / f"{APP_NAME}-{arch}.AppImage"
    run_with_env([str(tool), str(app_dir), str(appimage_path)], env=env)

    installer_path = output_dir / "install_linux_desktop.sh"
    shutil.copy2(ROOT_DIR / "scripts" / "install_linux_desktop.sh", installer_path)
    installer_path.chmod(0o755)
    shutil.copy2(ROOT_DIR / "asset" / "icon.png", output_dir / f"{APP_NAME}.png")


def linux_desktop_entry(exec_command: str) -> str:
    return f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment=CAN bus monitor
Exec={exec_command} %F
Icon={APP_NAME}
Terminal=false
Categories=Development;Utility;
StartupWMClass={APP_NAME}
"""


def appimage_arch() -> str:
    machine = platform.machine()
    if machine in {"amd64", "x86_64"}:
        return "x86_64"
    if machine in {"aarch64", "arm64"}:
        return "aarch64"
    raise RuntimeError(f"Unsupported AppImage architecture: {machine}")


def get_appimagetool() -> Path:
    configured_tool = os.environ.get("APPIMAGETOOL")
    if configured_tool:
        return Path(configured_tool)

    path_tool = shutil.which("appimagetool")
    if path_tool:
        return Path(path_tool)

    arch = appimage_arch()
    url = APPIMAGE_TOOL_URLS[arch]
    cache_dir = ROOT_DIR / ".cache" / "appimagetool"
    cache_dir.mkdir(parents=True, exist_ok=True)
    tool = cache_dir / f"appimagetool-{arch}.AppImage"
    if not tool.exists():
        print(f"Downloading appimagetool from {url}")
        urllib.request.urlretrieve(url, tool)
    tool.chmod(0o755)
    return extract_appimage_tool(tool)


def extract_appimage_tool(tool: Path) -> Path:
    extract_dir = tool.parent / f"{tool.stem}.squashfs-root"
    app_run = extract_dir / "AppRun"
    if app_run.exists():
        return app_run

    run([str(tool), "--appimage-extract"])
    extracted = ROOT_DIR / "squashfs-root"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    shutil.move(str(extracted), extract_dir)
    return app_run


def run_with_env(command: list[str], env: dict[str, str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT_DIR, check=True, env=env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CANViewer with Nuitka")
    parser.add_argument(
        "--output-dir",
        default="dist",
        help="Directory for Nuitka build output",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous Nuitka output before building",
    )
    parser.add_argument(
        "--dmg",
        action="store_true",
        help="Create a DMG after building the macOS .app",
    )
    parser.add_argument(
        "--appimage",
        action="store_true",
        help="Create an AppImage after building the Linux standalone app",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = (ROOT_DIR / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.clean:
        remove_previous_output(output_dir)

    system = platform.system()
    if system == "Darwin":
        build_macos(output_dir, args.dmg)
    elif system == "Windows":
        build_windows(output_dir)
    elif system == "Linux":
        build_linux(output_dir, args.appimage)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


if __name__ == "__main__":
    os.chdir(ROOT_DIR)
    main()
