import sqlite3
from pathlib import Path


def _row_to_record(cursor: sqlite3.Cursor, row: tuple) -> dict[str, str]:
    columns = [description[0] for description in cursor.description]
    return {column: value for column, value in zip(columns, row)}


def search_words_exact(db_path: Path, *, lemma: str, language: str | None = None) -> list[dict[str, str]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if language:
            cursor = conn.execute(
                """
                select language, lemma, surface, reading_or_ipa, pos,
                       meaning_source, meaning_source_text, meaning_source_lang,
                       meaning_zh, source_name, source_entry_id
                from words
                where lemma = ? and language = ?
                order by lemma
                """,
                (lemma, language),
            )
        else:
            cursor = conn.execute(
                """
                select language, lemma, surface, reading_or_ipa, pos,
                       meaning_source, meaning_source_text, meaning_source_lang,
                       meaning_zh, source_name, source_entry_id
                from words
                where lemma = ?
                order by language, lemma
                """,
                (lemma,),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def search_words(db_path: Path, *, query: str, language: str | None = None, limit: int = 20) -> list[dict[str, str]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if language:
            cursor = conn.execute(
                """
                select language, lemma, surface, reading_or_ipa, pos,
                       meaning_source, meaning_source_text, meaning_source_lang,
                       meaning_zh, source_name, source_entry_id
                from words_fts
                where words_fts match ? and language = ?
                limit ?
                """,
                (query, language, limit),
            )
        else:
            cursor = conn.execute(
                """
                select language, lemma, surface, reading_or_ipa, pos,
                       meaning_source, meaning_source_text, meaning_source_lang,
                       meaning_zh, source_name, source_entry_id
                from words_fts
                where words_fts match ?
                limit ?
                """,
                (query, limit),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
