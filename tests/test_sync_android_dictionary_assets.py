import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.sync_android_dictionary_assets import sync_android_assets


def test_sync_android_assets_copies_dictionary_files(tmp_path: Path) -> None:
    package_dir = tmp_path / "artifacts" / "package"
    assets_dir = tmp_path / "android-app" / "app" / "src" / "main" / "assets" / "dictionary"
    package_dir.mkdir(parents=True, exist_ok=True)

    db_bytes = b"sqlite-db-content"
    manifest_payload = {"db_filename": "dictionary.db", "schema_version": 1}
    (package_dir / "dictionary.db").write_bytes(db_bytes)
    (package_dir / "manifest.json").write_text(json.dumps(manifest_payload), encoding="utf-8")

    sync_android_assets(package_dir=package_dir, assets_dir=assets_dir)

    assert (assets_dir / "dictionary.db").read_bytes() == db_bytes
    assert json.loads((assets_dir / "manifest.json").read_text(encoding="utf-8")) == manifest_payload


def test_sync_android_assets_fails_when_required_source_is_missing(tmp_path: Path) -> None:
    package_dir = tmp_path / "artifacts" / "package"
    assets_dir = tmp_path / "android-app" / "app" / "src" / "main" / "assets" / "dictionary"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "manifest.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="dictionary.db"):
        sync_android_assets(package_dir=package_dir, assets_dir=assets_dir)


def test_sync_android_assets_script_runs_with_cli_paths(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    package_dir = tmp_path / "package"
    assets_dir = tmp_path / "assets"
    package_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    db_bytes = b"db-from-hermetic-script-test"
    manifest_payload = {"source": "hermetic-test", "schema_version": 2}
    (package_dir / "dictionary.db").write_bytes(db_bytes)
    (package_dir / "manifest.json").write_text(json.dumps(manifest_payload), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "sync_android_dictionary_assets.py"),
            "--package-dir",
            str(package_dir),
            "--assets-dir",
            str(assets_dir),
        ],
        cwd=repo_root,
        check=True,
    )

    assert (assets_dir / "dictionary.db").read_bytes() == db_bytes
    assert json.loads((assets_dir / "manifest.json").read_text(encoding="utf-8")) == manifest_payload
