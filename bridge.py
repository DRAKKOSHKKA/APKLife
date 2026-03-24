#!/usr/bin/env python3
"""Android bridge builder (Variant A: Capacitor wrapper).

Builds APK/AAB shell which opens project UI in WebView by redirecting to base URL.
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
    """Bridge build error."""


def _resolve_tool(name: str) -> str:
    """Resolve executable path in a cross-platform-safe way."""
    candidates = [name]
    if os.name == "nt":
        candidates.extend([f"{name}.cmd", f"{name}.bat", f"{name}.exe"])

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    raise BridgeBuildError(
        f"Не найден инструмент '{name}' в PATH. " "Установите инструмент и перезапустите терминал."
    )


def run(command: list[str], cwd: Path | None = None) -> None:
    """Run command and fail with actionable output."""
    print("$", " ".join(command))
    result = subprocess.run(command, cwd=cwd, text=True)
    if result.returncode != 0:
        raise BridgeBuildError(
            "Команда завершилась с ошибкой:\n"
            f"  {' '.join(command)}\n"
            "Проверьте Java/Android SDK/Node и попробуйте снова."
        )


def ensure_environment() -> None:
    """Validate required tools and Android environment."""
    TOOLS["npm"] = _resolve_tool("npm")
    TOOLS["npx"] = _resolve_tool("npx")
    TOOLS["git"] = _resolve_tool("git")
    TOOLS["java"] = _resolve_tool("java")

    if not os.environ.get("ANDROID_HOME") and not os.environ.get("ANDROID_SDK_ROOT"):
        raise BridgeBuildError(
            "Не задан ANDROID_HOME/ANDROID_SDK_ROOT. " "Добавьте Android SDK в переменные среды."
        )

    run([TOOLS["java"], "-version"])


def maybe_pull_latest(should_pull: bool) -> None:
    """Optionally run git pull --rebase before build."""
    if should_pull:
        run([TOOLS["git"], "pull", "--rebase"], cwd=ROOT)


def _has_capacitor_config() -> bool:
    return (ANDROID_BRIDGE_DIR / "capacitor.config.json").exists() or (
        ANDROID_BRIDGE_DIR / "capacitor.config.ts"
    ).exists()


def ensure_bridge_project(app_id: str, app_name: str) -> None:
    """Idempotent project init.

    - Initializes npm project if missing.
    - Installs capacitor packages if missing.
    - Runs `cap init` only when capacitor config does not exist.
    """
    ANDROID_BRIDGE_DIR.mkdir(parents=True, exist_ok=True)

    package_json = ANDROID_BRIDGE_DIR / "package.json"
    if not package_json.exists():
        run([TOOLS["npm"], "init", "-y"], cwd=ANDROID_BRIDGE_DIR)

    node_modules = ANDROID_BRIDGE_DIR / "node_modules"
    if not node_modules.exists():
        run(
            [TOOLS["npm"], "install", "@capacitor/core", "@capacitor/android"],
            cwd=ANDROID_BRIDGE_DIR,
        )

    if not _has_capacitor_config():
        run([TOOLS["npx"], "cap", "init", app_name, app_id], cwd=ANDROID_BRIDGE_DIR)


def write_web_assets(base_url: str) -> None:
    """Create static bridge page that redirects to target URL."""
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
    .card {{ background: white; border-radius: 12px; padding: 16px;
      box-shadow: 0 4px 16px rgba(0,0,0,.08); }}
    a {{ color: #0d6efd; }}
  </style>
</head>
<body>
  <div class=\"card\">
    <h2>APKLife Android bridge</h2>
    <p>Открываем приложение по адресу:</p>
    <p><a href=\"{base_url}\">{base_url}</a></p>
  </div>
  <script>window.location.replace('{base_url}');</script>
</body>
</html>
"""
    (web_dir / "index.html").write_text(index_html, encoding="utf-8")


def ensure_android_platform() -> None:
    """Add Android platform only once; otherwise sync only."""
    android_dir = ANDROID_BRIDGE_DIR / "android"
    if android_dir.exists():
        run([TOOLS["npx"], "cap", "sync", "android"], cwd=ANDROID_BRIDGE_DIR)
    else:
        run([TOOLS["npx"], "cap", "add", "android"], cwd=ANDROID_BRIDGE_DIR)
        run([TOOLS["npx"], "cap", "sync", "android"], cwd=ANDROID_BRIDGE_DIR)


def _resolve_gradle() -> Path:
    android_dir = ANDROID_BRIDGE_DIR / "android"
    gradle = android_dir / ("gradlew.bat" if os.name == "nt" else "gradlew")
    if not gradle.exists():
        raise BridgeBuildError(
            f"Не найден gradle wrapper: {gradle}. " "Проверьте корректность `npx cap add android`."
        )
    return gradle


def clean_gradle_build() -> None:
    """Remove app build outputs before building artifacts."""
    build_dir = ANDROID_BRIDGE_DIR / "android" / "app" / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"🧹 Cleaned: {build_dir}")


def build_artifacts(release: bool, build_aab: bool) -> list[Path]:
    """Build APK/AAB and return produced artifact paths."""
    gradle = _resolve_gradle()
    android_dir = ANDROID_BRIDGE_DIR / "android"

    tasks = ["assembleRelease"] if release else ["assembleDebug"]
    if build_aab:
        tasks.append("bundleRelease")

    for task in tasks:
        run([str(gradle), task], cwd=android_dir)

    artifacts: list[Path] = []
    if release:
        artifacts.append(
            android_dir / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
        )
    else:
        artifacts.append(
            android_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
        )

    if build_aab:
        artifacts.append(
            android_dir / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab"
        )

    missing = [path for path in artifacts if not path.exists()]
    if missing:
        raise BridgeBuildError(
            "Артефакты не найдены:\n" + "\n".join(f"  - {path}" for path in missing)
        )

    return [path.resolve() for path in artifacts]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Сборка Android APK bridge для APKLife (Variant A)"
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Перед сборкой обновить репозиторий через git pull --rebase",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--debug", action="store_true", help="Собрать debug APK (по умолчанию)")
    mode_group.add_argument("--release", action="store_true", help="Собрать release APK")

    parser.add_argument(
        "--aab", action="store_true", help="Дополнительно собрать release AAB (bundleRelease)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Удалить android_bridge/android/app/build перед сборкой",
    )

    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5000",
        help="URL локального/удалённого web-приложения",
    )
    parser.add_argument("--app-id", default="ru.apklife.mobile", help="Android application id")
    parser.add_argument("--app-name", default="APKLife", help="Название Android приложения")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    release = bool(args.release)

    if args.aab and not release:
        raise BridgeBuildError("Флаг --aab доступен только вместе с --release.")

    ensure_environment()
    maybe_pull_latest(args.pull)
    ensure_bridge_project(args.app_id, args.app_name)
    write_web_assets(args.base_url)
    ensure_android_platform()

    if args.clean:
        clean_gradle_build()

    artifacts = build_artifacts(release=release, build_aab=args.aab)

    print("\n✅ Build completed. Artifacts:")
    for artifact in artifacts:
        print(f" - {artifact}")


if __name__ == "__main__":
    try:
        main()
    except BridgeBuildError as error:
        print(f"❌ Ошибка bridge-сборки: {error}")
        raise SystemExit(1) from error
