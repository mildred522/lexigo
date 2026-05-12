import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
import shutil

from dict_feasibility.models import NormalizedWord
from dict_feasibility.package_export import export_dictionary_package
from dict_feasibility.sqlite_builder import build_sqlite


def test_export_dictionary_package_writes_manifest_and_database(tmp_path: Path) -> None:
    root = tmp_path
    artifacts_dir = root / "artifacts"
    reports_dir = artifacts_dir / "reports"
    package_dir = artifacts_dir / "package"
    db_path = artifacts_dir / "prototype.db"
    reports_dir.mkdir(parents=True, exist_ok=True)

    build_sqlite(
        db_path,
        [
            NormalizedWord(
                language="FR",
                lemma="bonjour",
                surface="bonjour",
                reading_or_ipa="bOn.zur",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="hello",
                source_name="Kaikki French Wiktionary",
                source_entry_id="bonjour",
                meaning_source_text="salutation de bienvenue",
                meaning_source_lang="fr",
            ),
            NormalizedWord(
                language="JA",
                lemma="nomu",
                surface="nomu",
                reading_or_ipa="no-mu",
                pos="verb",
                meaning_source="jmdict",
                meaning_zh="drink",
                source_name="JMdict",
                source_entry_id="1002",
                meaning_source_text="to drink",
                meaning_source_lang="en",
            ),
        ],
    )

    (reports_dir / "translation-summary.json").write_text(
        json.dumps({"jmdict_words.jsonl": {"translated_now": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (reports_dir / "source_registry.json").write_text("[]", encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "feasibility-report.md").write_text("# report", encoding="utf-8")

    export_dictionary_package(
        db_path=db_path,
        reports_dir=reports_dir,
        docs_dir=root / "docs",
        out_dir=package_dir,
    )

    manifest_path = package_dir / "manifest.json"
    exported_db = package_dir / "dictionary.db"

    assert exported_db.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["db_filename"] == "dictionary.db"
    assert manifest["entry_count"] == 2
    assert manifest["language_counts"] == {"FR": 1, "JA": 1}
    assert manifest["search_capabilities"]["fts"] is True


def test_export_dictionary_package_copies_referenced_metadata_into_package(tmp_path: Path) -> None:
    root = tmp_path
    artifacts_dir = root / "artifacts"
    reports_dir = artifacts_dir / "reports"
    package_dir = artifacts_dir / "package"
    docs_dir = root / "docs"
    db_path = artifacts_dir / "prototype.db"

    reports_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    build_sqlite(
        db_path,
        [
            NormalizedWord(
                language="FR",
                lemma="bonjour",
                surface="bonjour",
                reading_or_ipa="bOn.zur",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="hello",
                source_name="Kaikki French Wiktionary",
                source_entry_id="bonjour",
                meaning_source_text="salutation de bienvenue",
                meaning_source_lang="fr",
            )
        ],
    )

    (reports_dir / "translation-summary.json").write_text("{}", encoding="utf-8")
    (reports_dir / "source_registry.json").write_text('[{"key":"jmdict"}]', encoding="utf-8")
    (docs_dir / "feasibility-report.md").write_text("# feasibility", encoding="utf-8")

    export_dictionary_package(
        db_path=db_path,
        reports_dir=reports_dir,
        docs_dir=docs_dir,
        out_dir=package_dir,
    )

    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    source_registry_path = Path(manifest["source_registry_path"])
    feasibility_report_path = Path(manifest["feasibility_report_path"])

    assert not source_registry_path.is_absolute()
    assert not feasibility_report_path.is_absolute()
    assert (package_dir / source_registry_path).read_text(encoding="utf-8") == '[{"key":"jmdict"}]'
    assert (package_dir / feasibility_report_path).read_text(encoding="utf-8") == "# feasibility"


def test_export_dictionary_package_script_runs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with prepared_repo_export_inputs(repo_root):
        subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "export_dictionary_package.py")],
            cwd=repo_root,
            check=True,
        )

        package_dir = repo_root / "artifacts" / "package"
        manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))

        assert (package_dir / "dictionary.db").exists()
        assert manifest["entry_count"] >= 1
        assert manifest["search_capabilities"]["exact_lookup"] is True


@contextmanager
def prepared_repo_export_inputs(repo_root: Path):
    artifacts_dir = repo_root / "artifacts"
    reports_dir = artifacts_dir / "reports"
    package_dir = artifacts_dir / "package"
    db_path = artifacts_dir / "prototype.db"
    translation_summary_path = reports_dir / "translation-summary.json"
    source_registry_path = reports_dir / "source_registry.json"

    backup_root = repo_root / "pytest_temp_root" / "package_export_backups"
    backup_root.mkdir(parents=True, exist_ok=True)

    managed_paths = [
        db_path,
        translation_summary_path,
        source_registry_path,
        package_dir,
    ]

    backups: list[tuple[Path, Path]] = []
    for path in managed_paths:
        if not path.exists():
            continue
        relative = path.relative_to(repo_root)
        backup_path = backup_root / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, backup_path, dirs_exist_ok=True)
        else:
            shutil.copy2(path, backup_path)
        backups.append((path, backup_path))

    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        build_sqlite(
            db_path,
            [
                NormalizedWord(
                    language="FR",
                    lemma="bonjour",
                    surface="bonjour",
                    reading_or_ipa="bOn.zur",
                    pos="intj",
                    meaning_source="kaikki",
                    meaning_zh="hello",
                    source_name="Kaikki French Wiktionary",
                    source_entry_id="bonjour",
                    meaning_source_text="salutation de bienvenue",
                    meaning_source_lang="fr",
                )
            ],
        )
        translation_summary_path.write_text("{}", encoding="utf-8")
        source_registry_path.write_text('[{"key":"kaikki_fr"}]', encoding="utf-8")
        yield
    finally:
        for path in managed_paths:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        for original, backup in backups:
            original.parent.mkdir(parents=True, exist_ok=True)
            if backup.is_dir():
                shutil.copytree(backup, original, dirs_exist_ok=True)
            else:
                shutil.copy2(backup, original)
        shutil.rmtree(backup_root, ignore_errors=True)
