import json
import shutil
import sqlite3
from pathlib import Path


def _language_counts(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "select language, count(*) from words group by language order by language",
        ).fetchall()
    finally:
        conn.close()
    return {language: count for language, count in rows}


def _entry_count(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("select count(*) from words").fetchone()
    finally:
        conn.close()
    return 0 if row is None else int(row[0])


def _copy_optional_file(*, source_path: Path, out_dir: Path, relative_path: str) -> str | None:
    if not source_path.exists():
        return None
    destination = out_dir / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    return relative_path


def export_dictionary_package(
    *,
    db_path: Path,
    reports_dir: Path,
    docs_dir: Path,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    exported_db = out_dir / "dictionary.db"
    shutil.copy2(db_path, exported_db)

    translation_summary_path = reports_dir / "translation-summary.json"
    translation_summary = {}
    if translation_summary_path.exists():
        translation_summary = json.loads(translation_summary_path.read_text(encoding="utf-8"))

    source_registry_relative_path = _copy_optional_file(
        source_path=reports_dir / "source_registry.json",
        out_dir=out_dir,
        relative_path="reports/source_registry.json",
    )
    feasibility_report_relative_path = _copy_optional_file(
        source_path=docs_dir / "feasibility-report.md",
        out_dir=out_dir,
        relative_path="docs/feasibility-report.md",
    )

    manifest = {
        "schema_version": 1,
        "db_filename": exported_db.name,
        "entry_count": _entry_count(db_path),
        "language_counts": _language_counts(db_path),
        "translation_summary": translation_summary,
        "search_capabilities": {
            "exact_lookup": True,
            "fts": True,
        },
        "source_registry_path": source_registry_relative_path,
        "feasibility_report_path": feasibility_report_relative_path,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
