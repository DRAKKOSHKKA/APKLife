#!/usr/bin/env python3
"""
bridge.py

Сценарий сборки Android APK-обёртки для APKLife.

Идея: приложение запускает локальный webview-контейнер (Capacitor Android shell),
а веб-часть берётся из текущей версии репозитория.

Требования:
- Node.js + npm
- Java JDK 17+
- Android SDK + ANDROID_HOME
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


class BridgeBuildError(RuntimeError):
    pass


def run(command: list[str], cwd: Path | None = None) -> None:
    print("$", " ".join(command))
    result = subprocess.run(command, cwd=cwd, text=True)
    if result.returncode != 0:
        raise BridgeBuildError(f"Команда завершилась с ошибкой: {' '.join(command)}")


def ensure_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise BridgeBuildError(f"Не найден инструмент '{name}'. Установите его и повторите.")


def ensure_environment() -> None:
    ensure_tool("npm")
    ensure_tool("npx")
    ensure_tool("git")

    if not os.environ.get("ANDROID_HOME") and not os.environ.get("ANDROID_SDK_ROOT"):
        raise BridgeBuildError("Не задан ANDROID_HOME/ANDROID_SDK_ROOT. Нужен Android SDK.")


def maybe_pull_latest(should_pull: bool) -> None:
    if not should_pull:
        return
    run(["git", "pull", "--rebase"], cwd=ROOT)


def ensure_bridge_project(app_id: str, app_name: str) -> None:
    if not ANDROID_BRIDGE_DIR.exists():
        ANDROID_BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        run(["npm", "init", "-y"], cwd=ANDROID_BRIDGE_DIR)
        run(["npm", "install", "@capacitor/core", "@capacitor/android"], cwd=ANDROID_BRIDGE_DIR)
        run(["npx", "cap", "init", app_name, app_id], cwd=ANDROID_BRIDGE_DIR)


def write_web_assets(base_url: str) -> None:
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


def build_apk(release: bool) -> Path:
    run(["npx", "cap", "add", "android"], cwd=ANDROID_BRIDGE_DIR)
    run(["npx", "cap", "sync", "android"], cwd=ANDROID_BRIDGE_DIR)

    gradle = ANDROID_BRIDGE_DIR / "android" / "gradlew"
    if not gradle.exists():
        raise BridgeBuildError("Не найден gradlew в android_bridge/android")

    task = "assembleRelease" if release else "assembleDebug"
    run([str(gradle), task], cwd=ANDROID_BRIDGE_DIR / "android")

    apk_name = "app-release.apk" if release else "app-debug.apk"
    apk_path = ANDROID_BRIDGE_DIR / "android" / "app" / "build" / "outputs" / "apk" / (
        "release" if release else "debug"
    ) / apk_name

    if not apk_path.exists():
        raise BridgeBuildError(f"APK не найден: {apk_path}")

    return apk_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Сборка Android APK bridge для APKLife")
    parser.add_argument("--pull", action="store_true", help="Перед сборкой обновить репозиторий через git pull --rebase")
    parser.add_argument("--release", action="store_true", help="Собрать release APK (по умолчанию debug)")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="URL локального web-приложения")
    parser.add_argument("--app-id", default="ru.apklife.mobile", help="Android application id")
    parser.add_argument("--app-name", default="APKLife", help="Название Android приложения")
    return parser.parse_args()


def main() -> None:
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
