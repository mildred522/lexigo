from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import html
import json
import re
import sqlite3
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class JlptItem:
    level: str
    written: str
    reading: str
    gloss: str
    source: str


@dataclass(frozen=True, slots=True)
class JapaneseDbRow:
    id: int
    lemma: str
    surface: str
    reading_or_ipa: str
    pos: str
    meaning_zh: str
    meaning_source_text: str


@dataclass(frozen=True, slots=True)
class AcceptedLearningLevel:
    language: str
    word_id: int
    lemma: str
    surface: str
    reading_or_ipa: str
    level: str
    level_rank: int
    learnable: bool
    confidence: float
    source: str
    reason: str


@dataclass(frozen=True, slots=True)
class ReviewCandidate:
    language: str
    jlpt_level: str
    written: str
    reading: str
    gloss: str
    candidate_word_ids: list[int]
    candidate_summaries: list[dict[str, str | int]]
    review_reason: str


@dataclass(frozen=True, slots=True)
class MissingJlptItem:
    language: str
    jlpt_level: str
    written: str
    reading: str
    gloss: str
    reason: str


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    accepted: list[AcceptedLearningLevel]
    needs_review: list[ReviewCandidate]
    missing: list[MissingJlptItem]


LEVEL_RANK = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
BAD_POS_MARKERS = (
    "surname",
    "person",
    "given name",
    "place",
    "company",
    "organization",
    "product name",
    "unclassified",
    "archaism",
    "obsolete",
    "rare",
    "derogatory",
    "vulgar",
)
KANA_RE = re.compile(r"^[\u3041-\u3096\u30a1-\u30fa\u30fc]+$")
READING_SPLIT_RE = re.compile(r"[、,/;；，\s]+")
OPTIONAL_JA_PREFIX_RE = re.compile(r"^（[^）]+）\s*")


def parse_ts_vocabulary(source: str, level: str, limit: int | None = None) -> list[JlptItem]:
    blocks = re.findall(
        r"""\{\s*id:\s*\d+,\s*kanji:\s*"(.*?)",\s*japanese:\s*"(.*?)",\s*english:\s*"(.*?)"\s*\}""",
        source,
        flags=re.S,
    )
    items: list[JlptItem] = []
    for kanji, japanese, english in blocks:
        written, reading = _parse_japanese_source_fields(kanji, japanese)
        if written:
            items.append(
                JlptItem(
                    level=level,
                    written=written,
                    reading=reading.strip(),
                    gloss=english.strip(),
                    source="ts",
                ),
            )
        if limit is not None and len(items) >= limit:
            break
    return items


def parse_n5_html_table(source: str, limit: int | None = None) -> list[JlptItem]:
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", source, flags=re.S | re.I)
    items: list[JlptItem] = []
    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S | re.I)
        if len(cells) < 4:
            continue
        kanji = _strip_html(cells[0])
        kana = _strip_html(cells[1])
        definition = _strip_html(cells[3])
        if kanji.lower() == "kanji":
            continue
        written = kanji or kana
        if written.startswith("～") or kana.startswith("～"):
            continue
        written = _normalize_written(written)
        reading = kana or (written if KANA_RE.fullmatch(written) else "")
        if written:
            items.append(JlptItem(level="N5", written=written, reading=reading, gloss=definition, source="html"))
        if limit is not None and len(items) >= limit:
            break
    return items


def load_japanese_rows(db_path: Path) -> list[JapaneseDbRow]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT id, lemma, surface, reading_or_ipa, pos, meaning_zh, meaning_source_text
            FROM words
            WHERE language = 'JA'
            """,
        ).fetchall()
    finally:
        connection.close()
    return [JapaneseDbRow(*row) for row in rows]


def classify_jlpt_items(items: Iterable[JlptItem], rows: Iterable[JapaneseDbRow]) -> ClassificationResult:
    by_surface: dict[str, list[JapaneseDbRow]] = defaultdict(list)
    by_surface_reading: dict[tuple[str, str], list[JapaneseDbRow]] = defaultdict(list)
    by_reading: dict[str, list[JapaneseDbRow]] = defaultdict(list)
    for row in rows:
        if row.reading_or_ipa:
            by_reading[row.reading_or_ipa].append(row)
        for written in {row.lemma, row.surface}:
            if not written:
                continue
            by_surface[written].append(row)
            by_surface_reading[(written, row.reading_or_ipa)].append(row)

    accepted: list[AcceptedLearningLevel] = []
    needs_review: list[ReviewCandidate] = []
    missing: list[MissingJlptItem] = []

    for item in items:
        readings = _split_readings(item.reading)
        exact_rows = _dedupe_rows(
            row
            for reading in readings
            for row in by_surface_reading.get((item.written, reading), [])
        )
        if exact_rows:
            good_rows = [row for row in exact_rows if is_learning_clean(row)]
            if good_rows:
                accepted.extend(
                    _accepted(row, item, confidence=0.98, source="jlpt_word_reading_exact")
                    for row in good_rows
                )
                continue
            needs_review.append(_review(item, exact_rows, "Exact written+reading matches are not learning-clean."))
            continue

        fallback_rows = by_surface.get(item.written, [])
        good_rows = [row for row in fallback_rows if is_learning_clean(row)]
        if len(good_rows) == 1:
            accepted.append(_accepted(good_rows[0], item, confidence=0.82, source="jlpt_word_unique_fallback"))
        elif fallback_rows:
            needs_review.append(
                _review(
                    item,
                    fallback_rows,
                    "Written form matched multiple or zero clean dictionary entries.",
                ),
            )
        elif readings:
            reading_rows = _dedupe_rows(row for reading in readings for row in by_reading.get(reading, []))
            good_rows = [row for row in reading_rows if is_learning_clean(row)]
            if len(good_rows) == 1:
                accepted.append(_accepted(good_rows[0], item, confidence=0.78, source="jlpt_reading_unique_fallback"))
            elif reading_rows:
                needs_review.append(
                    _review(
                        item,
                        reading_rows,
                        "Reading-only form matched multiple or zero clean dictionary entries.",
                    ),
                )
        else:
            missing.append(
                MissingJlptItem(
                    language="JA",
                    jlpt_level=item.level,
                    written=item.written,
                    reading=item.reading,
                    gloss=item.gloss,
                    reason="No matching JMdict row in current SQLite package.",
                ),
            )

    return ClassificationResult(accepted=accepted, needs_review=needs_review, missing=missing)


def is_learning_clean(row: JapaneseDbRow) -> bool:
    if not row.meaning_zh.strip():
        return False
    pos = row.pos.lower()
    return not any(marker in pos for marker in BAD_POS_MARKERS)


def write_jsonl(path: Path, rows: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")


def apply_learning_levels_to_sqlite(db_path: Path, rows: Iterable[AcceptedLearningLevel]) -> dict[str, int]:
    input_rows = list(rows)
    selected = _select_best_level_per_word(input_rows)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            create table if not exists word_learning_levels (
              word_id integer primary key,
              language text not null,
              level text not null,
              level_rank integer not null,
              learnable integer not null,
              confidence real not null,
              source text not null,
              review_status text not null,
              reason text not null,
              foreign key(word_id) references words(id) on delete cascade
            );
            create index if not exists idx_word_learning_levels_language_rank
              on word_learning_levels(language, level_rank);
            create index if not exists idx_word_learning_levels_level
              on word_learning_levels(level);
            """
        )
        connection.execute("delete from word_learning_levels")
        connection.executemany(
            """
            insert into word_learning_levels (
              word_id,
              language,
              level,
              level_rank,
              learnable,
              confidence,
              source,
              review_status,
              reason
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    row.word_id,
                    row.language,
                    row.level,
                    row.level_rank,
                    int(row.learnable),
                    row.confidence,
                    row.source,
                    "accepted",
                    row.reason,
                )
                for row in selected
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return {"input_rows": len(input_rows), "written_rows": len(selected)}


def summarize(result: ClassificationResult, elapsed: dict[str, float], total_items: int) -> dict:
    accepted_by_level: dict[str, int] = defaultdict(int)
    accepted_by_source: dict[str, int] = defaultdict(int)
    for row in result.accepted:
        accepted_by_level[row.level] += 1
        accepted_by_source[row.source] += 1
    review_by_level: dict[str, int] = defaultdict(int)
    for row in result.needs_review:
        review_by_level[row.jlpt_level] += 1
    missing_by_level: dict[str, int] = defaultdict(int)
    for row in result.missing:
        missing_by_level[row.jlpt_level] += 1
    return {
        "total_items": total_items,
        "accepted_count": len(result.accepted),
        "needs_review_count": len(result.needs_review),
        "missing_count": len(result.missing),
        "accepted_by_level": dict(sorted(accepted_by_level.items())),
        "accepted_by_source": dict(sorted(accepted_by_source.items())),
        "needs_review_by_level": dict(sorted(review_by_level.items())),
        "missing_by_level": dict(sorted(missing_by_level.items())),
        "elapsed_seconds": elapsed,
    }


def _accepted(
    row: JapaneseDbRow,
    item: JlptItem,
    confidence: float,
    source: str,
) -> AcceptedLearningLevel:
    return AcceptedLearningLevel(
        language="JA",
        word_id=row.id,
        lemma=row.lemma,
        surface=row.surface,
        reading_or_ipa=row.reading_or_ipa,
        level=item.level,
        level_rank=LEVEL_RANK[item.level],
        learnable=True,
        confidence=confidence,
        source=source,
        reason=f"Matched JLPT {item.level} using {source}.",
    )


def _review(item: JlptItem, rows: list[JapaneseDbRow], reason: str) -> ReviewCandidate:
    return ReviewCandidate(
        language="JA",
        jlpt_level=item.level,
        written=item.written,
        reading=item.reading,
        gloss=item.gloss,
        candidate_word_ids=[row.id for row in rows],
        candidate_summaries=[
            {
                "word_id": row.id,
                "lemma": row.lemma,
                "reading_or_ipa": row.reading_or_ipa,
                "pos": row.pos,
                "meaning_zh": row.meaning_zh,
                "meaning_source_text": row.meaning_source_text,
            }
            for row in rows[:8]
        ],
        review_reason=reason,
    )


def _strip_html(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", "", value)
    return html.unescape(no_tags).strip()


def _select_best_level_per_word(rows: Iterable[AcceptedLearningLevel]) -> list[AcceptedLearningLevel]:
    selected: dict[int, AcceptedLearningLevel] = {}
    for row in rows:
        current = selected.get(row.word_id)
        if current is None or (row.level_rank, -row.confidence) < (current.level_rank, -current.confidence):
            selected[row.word_id] = row
    return sorted(selected.values(), key=lambda row: (row.level_rank, row.word_id))


def _parse_japanese_source_fields(kanji: str, japanese: str) -> tuple[str, str]:
    japanese = japanese.strip()
    ruby_parts = re.findall(r"([^\[\]\s]+?)\[(.*?)\]", japanese)
    if ruby_parts:
        written = "".join(part for part, _ in ruby_parts)
        reading = "".join(reading for _, reading in ruby_parts)
    else:
        written = kanji or japanese
        reading = japanese if KANA_RE.fullmatch(japanese) else ""
    return _normalize_written(written), reading.strip()


def _normalize_written(value: str) -> str:
    value = OPTIONAL_JA_PREFIX_RE.sub("", value.strip())
    return re.sub(r"\s+", "", value)


def _split_readings(value: str) -> list[str]:
    return [reading for reading in (part.strip() for part in READING_SPLIT_RE.split(value)) if reading]


def _dedupe_rows(rows: Iterable[JapaneseDbRow]) -> list[JapaneseDbRow]:
    seen: set[int] = set()
    deduped: list[JapaneseDbRow] = []
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        deduped.append(row)
    return deduped
