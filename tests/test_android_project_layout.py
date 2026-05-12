from pathlib import Path


def test_android_project_layout_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "android-app" / "settings.gradle.kts").exists()
    assert (root / "android-app" / "app" / "build.gradle.kts").exists()
    assert (root / "android-app" / "app" / "src" / "main" / "AndroidManifest.xml").exists()
    assert (
        root
        / "android-app"
        / "app"
        / "src"
        / "main"
        / "java"
        / "com"
        / "aiproduct"
        / "vocab"
        / "MainActivity.kt"
    ).exists()


def test_android_app_keeps_dictionary_db_uncompressed() -> None:
    root = Path(__file__).resolve().parents[1]
    build_gradle = (root / "android-app" / "app" / "build.gradle.kts").read_text(encoding="utf-8")

    assert "noCompress" in build_gradle
    assert "\"db\"" in build_gradle or "\"dictionary.db\"" in build_gradle
