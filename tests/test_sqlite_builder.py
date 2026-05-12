import sqlite3
import subprocess
import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.sqlite_builder import build_sqlite


def test_build_sqlite_creates_queryable_words_table(tmp_path: Path) -> None:
    db_path = tmp_path / "prototype.db"
    build_sqlite(
        db_path,
        [
            NormalizedWord(
                language="JA",
                lemma="食べる",
                surface="食べる",
                reading_or_ipa="たべる",
                pos="verb",
                meaning_source="jmdict",
                meaning_zh="吃",
                source_name="JMdict",
                source_entry_id="1001",
                meaning_source_text="eat",
                meaning_source_lang="en",
            )
        ],
    )

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            select lemma, meaning_source_text, meaning_source_lang, meaning_zh, example_sentences_json
            from words
            where lemma = ?
            """,
            ("食べる",),
        ).fetchone()
    finally:
        conn.close()

    assert row == ("食べる", "eat", "en", "吃", "[]")


def test_build_sqlite_creates_fts_table(tmp_path: Path) -> None:
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

    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "select lemma, meaning_zh from words_fts where words_fts match '你好'",
        ).fetchone()
    finally:
        conn.close()

    assert row == ("bonjour", "你好")


def test_build_sqlite_replaces_existing_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "prototype.db"
    initial_word = NormalizedWord(
        language="JA",
        lemma="食べる",
        surface="食べる",
        reading_or_ipa="たべる",
        pos="verb",
        meaning_source="jmdict",
        meaning_zh="吃",
        source_name="JMdict",
        source_entry_id="1001",
        meaning_source_text="eat",
        meaning_source_lang="en",
    )
    replacement_word = NormalizedWord(
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

    build_sqlite(db_path, [initial_word])
    build_sqlite(db_path, [replacement_word])

    conn = sqlite3.connect(db_path)
    try:
        row_count = conn.execute("select count(*) from words").fetchone()
        row = conn.execute(
            "select lemma, language, meaning_zh from words order by id",
        ).fetchone()
    finally:
        conn.close()

    assert row_count == (1,)
    assert row == ("bonjour", "FR", "你好")


def test_build_sqlite_script_prefers_translated_artifacts() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    db_path = repo_root / "artifacts" / "prototype.db"

    db_path.unlink(missing_ok=True)
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "parse_jmdict.py")],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "parse_kaikki_fr.py")],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "translate_normalized_words.py")],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "build_sqlite.py")],
        cwd=repo_root,
        check=True,
    )

    conn = sqlite3.connect(db_path)
    try:
        french_row = conn.execute(
            """
            select meaning_source_text, meaning_source_lang, meaning_zh
            from words
            where language = 'FR'
            """,
        ).fetchone()
    finally:
        conn.close()

    assert db_path.exists()
    assert french_row == ("salutation de bienvenue", "fr", "你好")
