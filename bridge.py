#!/usr/bin/env python3
"""
bridge.py

Сценарий сборки Android APK-обёртки для APKLife.

Идея: приложение запускает локальный webview-контейнер (Capacitor Android shell),
а веб-часть берётся из текущей версии репозитория.

Требования:
- Node.js + npm
- Java JDK 17+
- Android SDK + ANDROID_HOME/ANDROID_SDK_ROOT
- Git (для --pull)

Пример:
    python bridge.py --pull --release
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANDROID_BRIDGE_DIR = ROOT / "android_bridge"
TOOLS: dict[str, str] = {}


class BridgeBuildError(RuntimeError):
    """Ошибка сборки bridge APK."""


def _resolve_tool(name: str) -> str:
    """Resolve executable path in a cross-platform-safe way.

    На Windows npm/npx часто доступны как .cmd/.bat файлы,
    поэтому проверяем расширения явно и сохраняем абсолютный путь.
    """
    candidates = [name]
    if os.name == "nt":
        candidates.extend([f"{name}.cmd", f"{name}.bat", f"{name}.exe"])

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    raise BridgeBuildError(
        f"Не найден инструмент '{name}' в PATH. "
        "Проверьте PATH для Node.js/npm/npx, Git и Android SDK."
    )


def run(command: list[str], cwd: Path | None = None) -> None:
    """Run command and raise BridgeBuildError on non-zero exit code."""
    print("$", " ".join(command))
    result = subprocess.run(command, cwd=cwd, text=True)
    if result.returncode != 0:
        raise BridgeBuildError(f"Команда завершилась с ошибкой: {' '.join(command)}")


def ensure_environment() -> None:
    """Validate required CLI tools and environment variables."""
    TOOLS["npm"] = _resolve_tool("npm")
    TOOLS["npx"] = _resolve_tool("npx")
    TOOLS["git"] = _resolve_tool("git")

    if not os.environ.get("ANDROID_HOME") and not os.environ.get("ANDROID_SDK_ROOT"):
        raise BridgeBuildError("Не задан ANDROID_HOME/ANDROID_SDK_ROOT. Нужен Android SDK.")


def maybe_pull_latest(should_pull: bool) -> None:
    """Optionally update repository before build."""
    if not should_pull:
        return
    run([TOOLS["git"], "pull", "--rebase"], cwd=ROOT)


def ensure_bridge_project(app_id: str, app_name: str) -> None:
    """Initialize capacitor project once for android bridge wrapper."""
    if ANDROID_BRIDGE_DIR.exists():
        return

    ANDROID_BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    run([TOOLS["npm"], "init", "-y"], cwd=ANDROID_BRIDGE_DIR)
    run([TOOLS["npm"], "install", "@capacitor/core", "@capacitor/android"], cwd=ANDROID_BRIDGE_DIR)
    run([TOOLS["npx"], "cap", "init", app_name, app_id], cwd=ANDROID_BRIDGE_DIR)


def write_web_assets(base_url: str) -> None:
    """Create minimal www entry point that redirects into local web app."""
    web_dir = ANDROID_BRIDGE_DIR / "www"
    web_dir.mkdir(parents=True, exist_ok=True)

    index_html = f"""<!doctype html>
<html lang=\"ru\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>APKLife Android</title>
    <style>
      body {{ font-family: sans-serif; margin: 0; padding: 16px; background: #f5f6fa; }}
      .card {{ background: white; border-radius: 12px; padding: 16px; box-shadow: 0 4px 16px rgba(0,0,0,.08); }}
      a {{ color: #0d6efd; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h2>APKLife Android bridge</h2>
      <p>Открываем приложение по адресу:</p>
      <p><a href=\"{base_url}\">{base_url}</a></p>
      <p>Если сервер не запущен локально, откройте его и перезапустите приложение.</p>
    </div>
    <script>
      window.location.replace('{base_url}');
    </script>
  </body>
</html>
"""
    (web_dir / "index.html").write_text(index_html, encoding="utf-8")


def _resolve_gradle() -> Path:
    """Resolve platform-specific gradle wrapper path."""
    android_dir = ANDROID_BRIDGE_DIR / "android"
    if os.name == "nt":
        gradle = android_dir / "gradlew.bat"
    else:
        gradle = android_dir / "gradlew"

    if not gradle.exists():
        raise BridgeBuildError(f"Не найден gradle wrapper: {gradle}")
    return gradle


def build_apk(release: bool) -> Path:
    """Sync capacitor Android project and build APK."""
    run([TOOLS["npx"], "cap", "add", "android"], cwd=ANDROID_BRIDGE_DIR)
    run([TOOLS["npx"], "cap", "sync", "android"], cwd=ANDROID_BRIDGE_DIR)

    gradle = _resolve_gradle()
    task = "assembleRelease" if release else "assembleDebug"
    run([str(gradle), task], cwd=ANDROID_BRIDGE_DIR / "android")

    apk_name = "app-release.apk" if release else "app-debug.apk"
    apk_path = (
        ANDROID_BRIDGE_DIR
        / "android"
        / "app"
        / "build"
        / "outputs"
        / "apk"
        / ("release" if release else "debug")
        / apk_name
    )

    if not apk_path.exists():
        raise BridgeBuildError(f"APK не найден: {apk_path}")

    return apk_path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Сборка Android APK bridge для APKLife")
    parser.add_argument("--pull", action="store_true", help="Перед сборкой обновить репозиторий через git pull --rebase")
    parser.add_argument("--release", action="store_true", help="Собрать release APK (по умолчанию debug)")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="URL локального web-приложения")
    parser.add_argument("--app-id", default="ru.apklife.mobile", help="Android application id")
    parser.add_argument("--app-name", default="APKLife", help="Название Android приложения")
    return parser.parse_args()


def main() -> None:
    """Bridge build flow."""
    args = parse_args()

    ensure_environment()
    maybe_pull_latest(args.pull)
    ensure_bridge_project(args.app_id, args.app_name)
    write_web_assets(args.base_url)
    apk_path = build_apk(args.release)

    print("\n✅ APK успешно собран:")
    print(apk_path)


if __name__ == "__main__":
    try:
        main()
    except BridgeBuildError as error:
        print(f"❌ Ошибка bridge-сборки: {error}")
        raise SystemExit(1)
