import argparse
import shutil
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = ("dictionary.db", "manifest.json")


def sync_android_assets(*, package_dir: Path, assets_dir: Path) -> None:
    missing_files = [name for name in _REQUIRED_FILES if not (package_dir / name).is_file()]
    if missing_files:
        missing_list = ", ".join(missing_files)
        raise FileNotFoundError(f"Missing required packaged dictionary file(s) in {package_dir}: {missing_list}")

    assets_dir.mkdir(parents=True, exist_ok=True)
    for filename in _REQUIRED_FILES:
        shutil.copy2(package_dir / filename, assets_dir / filename)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync packaged dictionary files into Android assets.")
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "package",
        help="Directory containing dictionary.db and manifest.json.",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=_REPO_ROOT / "android-app" / "app" / "build" / "generated" / "assets" / "dictionary",
        help="Destination assets directory for Android packaging.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    sync_android_assets(
        package_dir=args.package_dir,
        assets_dir=args.assets_dir,
    )


if __name__ == "__main__":
    main()
