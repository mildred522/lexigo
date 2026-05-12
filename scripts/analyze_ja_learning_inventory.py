from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dict_feasibility.ja_learning_levels import BAD_POS_MARKERS


LOW_VALUE_MEANING_MARKERS = BAD_POS_MARKERS + (
    "surname",
    "given name",
    "place name",
    "company",
    "organization",
    "archaic",
    "obsolete",
    "rare",
    "vulgar",
    "fuck",
)
LOW_VALUE_POS_MARKERS = BAD_POS_MARKERS + (
    "archaic",
    "suffix",
    "prefix",
    "counter",
    "auxiliary",
)
BAD_LEMMA_RE = re.compile(r"[\s;,/]|^[-～]|[-～]$")


@dataclass(frozen=True, slots=True)
class CandidateRow:
    word_id: int
    lemma: str
    reading_or_ipa: str
    pos: str
    meaning_zh: str
    meaning_source_text: str
    score: int
    reasons: list[str]


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze full Japanese learning-level inventory after JLPT matching.")
    parser.add_argument("--db", type=Path, default=Path("artifacts/package/dictionary.db"))
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts/learning_levels/ja"))
    parser.add_argument("--candidate-limit", type=int, default=20_000)
    args = parser.parse_args()

    started = time.perf_counter()
    rows = _load_rows(args.db)
    accepted_ids = _load_accepted_ids(args.db)

    low_value_reasons: Counter[str] = Counter()
    unknown_clean = 0
    candidates: list[CandidateRow] = []

    for row in rows:
        word_id = int(row["id"])
        if word_id in accepted_ids:
            continue
        low_reason = _low_value_reason(row)
        if low_reason:
            low_value_reasons[low_reason] += 1
            continue
        unknown_clean += 1
        candidate = _score_candidate(row)
        if candidate.score >= 95:
            candidates.append(candidate)

    candidates.sort(key=lambda item: (-item.score, item.word_id))
    selected_candidates = candidates[: args.candidate_limit]

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out_dir / "ja_unknown_high_value_candidates.jsonl", selected_candidates)
    summary = {
        "total_ja_words": len(rows),
        "jlpt_leveled_unique_words": len(accepted_ids),
        "remaining_after_jlpt": len(rows) - len(accepted_ids),
        "low_value_filtered_count": sum(low_value_reasons.values()),
        "low_value_reasons": dict(low_value_reasons.most_common()),
        "unknown_clean_count": unknown_clean,
        "high_value_candidate_count": len(candidates),
        "selected_high_value_candidates": len(selected_candidates),
        "candidate_score_buckets": _score_buckets(candidates),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "sample_candidates": [asdict(item) for item in selected_candidates[:30]],
    }
    (out_dir / "ja_learning_inventory.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _load_rows(db_path: Path) -> list[sqlite3.Row]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            """
            SELECT id, lemma, surface, reading_or_ipa, pos, meaning_zh, meaning_source_text
            FROM words
            WHERE language = 'JA'
            """
        ).fetchall()
    finally:
        connection.close()


def _load_accepted_ids(db_path: Path) -> set[int]:
    connection = sqlite3.connect(db_path)
    try:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'word_learning_levels'
            LIMIT 1
            """
        ).fetchone()
        if not exists:
            return set()
        return {
            int(row[0])
            for row in connection.execute(
                """
                SELECT word_id
                FROM word_learning_levels
                WHERE language = 'JA'
                  AND learnable = 1
                  AND review_status = 'accepted'
                """
            )
        }
    finally:
        connection.close()


def _low_value_reason(row: sqlite3.Row) -> str | None:
    lemma = str(row["lemma"] or "").strip()
    pos = str(row["pos"] or "").lower()
    meaning_source_text = str(row["meaning_source_text"] or "").lower()
    meaning_zh = str(row["meaning_zh"] or "").strip()
    if not lemma:
        return "blank_lemma"
    if not meaning_zh and not meaning_source_text.strip():
        return "blank_meaning"
    for marker in LOW_VALUE_POS_MARKERS:
        if marker in pos:
            return f"pos:{marker}"
    for marker in LOW_VALUE_MEANING_MARKERS:
        if marker in meaning_source_text:
            return f"meaning:{marker}"
    if BAD_LEMMA_RE.search(lemma):
        return "lemma:punc_or_phrase_marker"
    if len(lemma) > 12:
        return "lemma:too_long"
    return None


def _score_candidate(row: sqlite3.Row) -> CandidateRow:
    lemma = str(row["lemma"] or "").strip()
    reading = str(row["reading_or_ipa"] or "").strip()
    pos = str(row["pos"] or "").lower()
    meaning_zh = str(row["meaning_zh"] or "").strip()
    meaning_source_text = str(row["meaning_source_text"] or "").strip()
    score = 0
    reasons: list[str] = []

    if "pronoun" in pos or "conjunction" in pos or "interjection" in pos:
        score += 45
        reasons.append("function_word")
    if _is_actual_verb_pos(pos):
        score += 40
        reasons.append("verb")
    if "adjective" in pos or "adjectival nouns" in pos:
        score += 36
        reasons.append("adjective")
    if "adverb" in pos:
        score += 34
        reasons.append("adverb")
    if "noun (common)" in pos:
        score += 28
        reasons.append("common_noun")
    if "expressions" in pos:
        score -= 18
        reasons.append("expression_penalty")
    if 2 <= len(lemma) <= 4:
        score += 24
        reasons.append("short_lemma")
    elif 5 <= len(lemma) <= 7:
        score += 12
        reasons.append("medium_lemma")
    if reading:
        score += 10
        reasons.append("has_reading")
    if meaning_zh:
        score += 12
        reasons.append("has_zh")
    if meaning_source_text and len(meaning_source_text) <= 90:
        score += 10
        reasons.append("compact_gloss")
    if any(char in lemma for char in "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをん"):
        score += 4
        reasons.append("kana_visible")

    return CandidateRow(
        word_id=int(row["id"]),
        lemma=lemma,
        reading_or_ipa=reading,
        pos=str(row["pos"] or ""),
        meaning_zh=meaning_zh,
        meaning_source_text=meaning_source_text,
        score=score,
        reasons=reasons,
    )


def _score_buckets(candidates: list[CandidateRow]) -> dict[str, int]:
    buckets = Counter()
    for candidate in candidates:
        if candidate.score >= 110:
            buckets["110+"] += 1
        elif candidate.score >= 95:
            buckets["95-109"] += 1
        elif candidate.score >= 80:
            buckets["80-94"] += 1
        elif candidate.score >= 60:
            buckets["60-79"] += 1
    return dict(buckets)


def _is_actual_verb_pos(pos: str) -> bool:
    return any(
        marker in pos
        for marker in (
            "ichidan verb",
            "godan verb",
            "suru verb",
            "kuru verb",
            "irregular verb",
            "transitive verb",
            "intransitive verb",
        )
    )


def _write_jsonl(path: Path, rows: list[CandidateRow]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
