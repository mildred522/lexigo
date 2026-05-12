from dict_feasibility.ja_learning_levels import (
    AcceptedLearningLevel,
    JapaneseDbRow,
    JlptItem,
    apply_learning_levels_to_sqlite,
    classify_jlpt_items,
    parse_n5_html_table,
    parse_ts_vocabulary,
)
import sqlite3
from pathlib import Path


def test_parse_ts_vocabulary_extracts_written_and_reading() -> None:
    source = """
    export const vocabulary = [
      {
        id: 1,
        kanji: "\u5b66\u6821",
        japanese: "\u5b66\u6821[\u304c\u3063\u3053\u3046]",
        english: "school"
      }
    ];
    """

    items = parse_ts_vocabulary(source, level="N5", limit=10)

    assert items == [
        JlptItem(level="N5", written="\u5b66\u6821", reading="\u304c\u3063\u3053\u3046", gloss="school", source="ts"),
    ]


def test_parse_ts_vocabulary_merges_split_ruby_markup() -> None:
    source = """
    export const vocabulary = [
      {
        id: 1,
        kanji: "\u5fc3\u914d",
        japanese: "\u5fc3[\u3057\u3093] \u914d[\u3071\u3044]",
        english: "\u3059\u308b\uff1ato worry"
      }
    ];
    """

    items = parse_ts_vocabulary(source, level="N4", limit=10)

    assert items == [
        JlptItem(level="N4", written="\u5fc3\u914d", reading="\u3057\u3093\u3071\u3044", gloss="\u3059\u308b\uff1ato worry", source="ts"),
    ]


def test_parse_ts_vocabulary_strips_optional_honorific_prefix() -> None:
    source = """
    export const vocabulary = [
      {
        id: 1,
        kanji: "\u4e3b\u4eba",
        japanese: "\uff08\u3054\uff09 \u4e3b[\u3057\u3085] \u4eba[\u3058\u3093]",
        english: "husband"
      }
    ];
    """

    items = parse_ts_vocabulary(source, level="N4", limit=10)

    assert items[0].written == "\u4e3b\u4eba"
    assert items[0].reading == "\u3057\u3085\u3058\u3093"


def test_parse_n5_html_uses_kana_word_as_reading() -> None:
    source = """
    <table>
      <tr><th>Kanji</th><th>Kana</th><th>POS</th><th>Definition</th></tr>
      <tr><td>\u3042\u306a\u305f</td><td></td><td>pron</td><td>you</td></tr>
    </table>
    """

    items = parse_n5_html_table(source, limit=10)

    assert items == [
        JlptItem(level="N5", written="\u3042\u306a\u305f", reading="\u3042\u306a\u305f", gloss="you", source="html"),
    ]


def test_classify_prefers_exact_written_reading_match() -> None:
    items = [JlptItem(level="N5", written="\u6c34", reading="\u307f\u305a", gloss="water", source="test")]
    rows = [
        JapaneseDbRow(1, "\u6c34", "\u6c34", "\u307f\u305a", "noun", "\u6c34", "water"),
        JapaneseDbRow(2, "\u6c34", "\u6c34", "\u3059\u3044", "noun", "\u5468\u4e09", "Wednesday"),
    ]

    result = classify_jlpt_items(items, rows)

    assert [entry.word_id for entry in result.accepted] == [1]
    assert result.needs_review == []


def test_classify_sends_ambiguous_fallback_to_review() -> None:
    items = [JlptItem(level="N5", written="\u30d1\u30f3", reading="", gloss="bread", source="test")]
    rows = [
        JapaneseDbRow(1, "\u30d1\u30f3", "\u30d1\u30f3", "\u30d1\u30f3", "noun", "\u9762\u5305", "bread"),
        JapaneseDbRow(2, "\u30d1\u30f3", "\u30d1\u30f3", "\u30d1\u30f3", "prefix", "\u5168\u7403\u7684", "pan-"),
    ]

    result = classify_jlpt_items(items, rows)

    assert result.accepted == []
    assert len(result.needs_review) == 1
    assert result.needs_review[0].written == "\u30d1\u30f3"
    assert result.needs_review[0].candidate_word_ids == [1, 2]


def test_classify_uses_unique_reading_fallback_for_kana_written_items() -> None:
    items = [JlptItem(level="N5", written="\u3042\u306a\u305f", reading="\u3042\u306a\u305f", gloss="you", source="test")]
    rows = [
        JapaneseDbRow(1, "\u8cb4\u65b9", "\u8cb4\u65b9", "\u3042\u306a\u305f", "pronoun", "\u4f60", "you"),
    ]

    result = classify_jlpt_items(items, rows)

    assert [entry.word_id for entry in result.accepted] == [1]
    assert result.accepted[0].source == "jlpt_reading_unique_fallback"


def test_classify_splits_multiple_jlpt_readings_for_exact_match() -> None:
    items = [JlptItem(level="N5", written="\u4e5d", reading="\u304f\u3001\u304d\u3085\u3046", gloss="nine", source="test")]
    rows = [
        JapaneseDbRow(1, "\u4e5d", "\u4e5d", "\u304d\u3085\u3046", "noun", "\u4e5d", "nine"),
    ]

    result = classify_jlpt_items(items, rows)

    assert [entry.word_id for entry in result.accepted] == [1]


def test_apply_learning_levels_to_sqlite_writes_best_level_per_word(tmp_path: Path) -> None:
    db_path = tmp_path / "dictionary.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("create table words (id integer primary key, language text not null)")
        connection.execute("insert into words (id, language) values (1, 'JA')")
        connection.commit()
    finally:
        connection.close()

    summary = apply_learning_levels_to_sqlite(
        db_path,
        [
            AcceptedLearningLevel(
                language="JA",
                word_id=1,
                lemma="\u8a66\u9a13",
                surface="\u8a66\u9a13",
                reading_or_ipa="\u3057\u3051\u3093",
                level="N2",
                level_rank=4,
                learnable=True,
                confidence=0.98,
                source="jlpt_word_reading_exact",
                reason="Matched JLPT N2 using jlpt_word_reading_exact.",
            ),
            AcceptedLearningLevel(
                language="JA",
                word_id=1,
                lemma="\u8a66\u9a13",
                surface="\u8a66\u9a13",
                reading_or_ipa="\u3057\u3051\u3093",
                level="N4",
                level_rank=2,
                learnable=True,
                confidence=0.82,
                source="jlpt_word_unique_fallback",
                reason="Matched JLPT N4 using jlpt_word_unique_fallback.",
            ),
        ],
    )

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            """
            select word_id, language, level, level_rank, learnable, source, review_status
            from word_learning_levels
            """
        ).fetchone()
    finally:
        connection.close()

    assert summary == {"input_rows": 2, "written_rows": 1}
    assert row == (1, "JA", "N4", 2, 1, "jlpt_word_unique_fallback", "accepted")
