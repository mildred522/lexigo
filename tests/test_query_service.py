import subprocess
import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.query_service import search_words, search_words_exact
from dict_feasibility.sqlite_builder import build_sqlite


def test_search_words_exact_matches_language_and_lemma(tmp_path: Path) -> None:
    db_path = tmp_path / "prototype.db"
    build_sqlite(
        db_path,
        [
            NormalizedWord(
                language="FR",
                lemma="bonjour",
                surface="bonjour",
                reading_or_ipa="bɔ̃.ʒuʁ",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="你好",
                source_name="Kaikki French Wiktionary",
                source_entry_id="bonjour",
                meaning_source_text="salutation de bienvenue",
                meaning_source_lang="fr",
            )
        ],
    )

    results = search_words_exact(db_path, lemma="bonjour", language="FR")

    assert len(results) == 1
    assert results[0]["meaning_zh"] == "你好"
    assert results[0]["meaning_source_text"] == "salutation de bienvenue"


def test_search_words_fts_matches_translated_meaning(tmp_path: Path) -> None:
    db_path = tmp_path / "prototype.db"
    build_sqlite(
        db_path,
        [
            NormalizedWord(
                language="JA",
                lemma="飲む",
                surface="飲む",
                reading_or_ipa="のむ",
                pos="verb",
                meaning_source="jmdict",
                meaning_zh="喝",
                source_name="JMdict",
                source_entry_id="1002",
                meaning_source_text="to drink",
                meaning_source_lang="en",
            ),
            NormalizedWord(
                language="FR",
                lemma="bonjour",
                surface="bonjour",
                reading_or_ipa="bɔ̃.ʒuʁ",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="你好",
                source_name="Kaikki French Wiktionary",
                source_entry_id="bonjour",
                meaning_source_text="salutation de bienvenue",
                meaning_source_lang="fr",
            ),
        ],
    )

    results = search_words(db_path, query="你好")

    assert len(results) == 1
    assert results[0]["lemma"] == "bonjour"


def test_search_words_script_queries_database() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "build_sqlite.py")],
        cwd=repo_root,
        check=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "search_words.py"),
            "--query",
            "你好",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "bonjour" in result.stdout
