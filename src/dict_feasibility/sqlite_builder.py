import sqlite3
from pathlib import Path
from typing import Iterable

from dict_feasibility.models import NormalizedWord


SCHEMA = """
drop table if exists words;
drop table if exists words_fts;

create table words (
  id integer primary key autoincrement,
  language text not null,
  lemma text not null,
  surface text not null,
  reading_or_ipa text not null,
  pos text not null,
  meaning_source text not null,
  meaning_source_text text not null,
  meaning_source_lang text not null,
  meaning_zh text not null,
  example_sentences_json text not null,
  source_name text not null,
  source_entry_id text not null
);

create index idx_words_language on words(language);
create index idx_words_lemma on words(lemma);
create index idx_words_surface on words(surface);

create virtual table words_fts using fts5(
  language,
  lemma,
  surface,
  reading_or_ipa,
  pos,
  meaning_source,
  meaning_source_text,
  meaning_source_lang,
  meaning_zh,
  source_name,
  source_entry_id
);
"""


def build_sqlite(db_path: Path, words: Iterable[NormalizedWord]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            """
            insert into words (
              language,
              lemma,
              surface,
              reading_or_ipa,
              pos,
              meaning_source,
              meaning_source_text,
              meaning_source_lang,
              meaning_zh,
              example_sentences_json,
              source_name,
              source_entry_id
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    word.language,
                    word.lemma,
                    word.surface,
                    word.reading_or_ipa,
                    word.pos,
                    word.meaning_source,
                    word.meaning_source_text,
                    word.meaning_source_lang,
                    word.meaning_zh,
                    word.example_sentences_json,
                    word.source_name,
                    word.source_entry_id,
                )
                for word in words
            ),
        )
        conn.execute(
            """
            insert into words_fts (
              language,
              lemma,
              surface,
              reading_or_ipa,
              pos,
              meaning_source,
              meaning_source_text,
              meaning_source_lang,
              meaning_zh,
              source_name,
              source_entry_id
            )
            select
              language,
              lemma,
              surface,
              reading_or_ipa,
              pos,
              meaning_source,
              meaning_source_text,
              meaning_source_lang,
              meaning_zh,
              source_name,
              source_entry_id
            from words
            """
        )
        conn.commit()
    finally:
        conn.close()
