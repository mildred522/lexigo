from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


LEVEL_RANK = {
    "N5": 1,
    "N4": 2,
    "N3": 3,
    "N2": 4,
    "N1": 5,
    "advanced": 6,
    "exclude": 99,
    "needs_review": 98,
}
LEARNABLE_LEVELS = {"N5", "N4", "N3", "N2", "N1"}
VALID_LEVELS = LEARNABLE_LEVELS | {"advanced", "exclude", "needs_review"}


@dataclass(frozen=True, slots=True)
class AiLevelDecision:
    word_id: int
    lemma: str
    reading_or_ipa: str
    meaning_zh: str
    meaning_source_text: str
    level: str
    confidence: float
    decision: str
    reason: str
    source: str


@dataclass(frozen=True, slots=True)
class BatchClassification:
    decisions: list[AiLevelDecision]
    usage: dict[str, int]


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify high-value Japanese unknown candidates with an AI model.")
    parser.add_argument("--input", type=Path, default=Path("artifacts/learning_levels/ja/ja_unknown_high_value_candidates.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/learning_levels/ja/ja_ai_level_decisions.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("artifacts/learning_levels/ja/ja_ai_level_decisions.summary.json"))
    parser.add_argument("--db", type=Path, default=Path("artifacts/package/dictionary.db"))
    parser.add_argument("--limit", type=int, default=8_000)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-batches", type=int)
    parser.add_argument("--apply-db", action="store_true")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--base-url", default="https://api.deepseek.com/v1")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--auth-header", choices=["bearer", "api-key"], default="bearer")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        raise SystemExit(f"Missing API key env: {args.api_key_env}")

    started = time.perf_counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    candidates = _load_candidates(args.input, limit=args.limit)
    completed_ids = _load_completed_ids(args.output)
    pending = [row for row in candidates if int(row["word_id"]) not in completed_ids]
    batches = [pending[index : index + args.batch_size] for index in range(0, len(pending), args.batch_size)]
    if args.max_batches is not None:
        batches = batches[: args.max_batches]

    accepted = 0
    failed = 0
    written = 0
    usage_totals: dict[str, int] = {}
    with args.output.open("a", encoding="utf-8", newline="\n") as handle:
        for index, batch in enumerate(batches, start=1):
            try:
                classified = classify_batch(
                    batch,
                    api_key=api_key,
                    base_url=args.base_url,
                    model=args.model,
                    auth_header=args.auth_header,
                    timeout=args.timeout,
                )
            except Exception as error:
                failed += 1
                print(f"batch {index}/{len(batches)} failed: {error}", file=sys.stderr)
                continue
            decisions = classified.decisions
            for key, value in classified.usage.items():
                usage_totals[key] = usage_totals.get(key, 0) + value
            by_id = {decision.word_id: decision for decision in decisions}
            for row in batch:
                word_id = int(row["word_id"])
                decision = by_id.get(word_id)
                if decision is None:
                    decision = _fallback_review(row, source=f"ai:{args.model}:missing_output")
                handle.write(json.dumps(asdict(decision), ensure_ascii=False, sort_keys=True) + "\n")
                written += 1
            handle.flush()
            accepted += 1
            print(f"batch {index}/{len(batches)} ok, decisions={len(decisions)}, written={written}, usage={classified.usage}")

    all_decisions = list(_iter_decisions(args.output))
    db_summary = apply_ai_decisions_to_sqlite(args.db, all_decisions) if args.apply_db else None
    summary = summarize_decisions(
        all_decisions,
        extra={
            "input_limit": args.limit,
            "batch_size": args.batch_size,
            "attempted_batches": len(batches),
            "succeeded_batches": accepted,
            "failed_batches": failed,
            "written_this_run": written,
            "usage_this_run": usage_totals,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "db_write": db_summary,
        },
    )
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def classify_batch(
    batch: list[dict],
    *,
    api_key: str,
    base_url: str,
    model: str,
    auth_header: str,
    timeout: int,
) -> BatchClassification:
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps([_prompt_row(row) for row in batch], ensure_ascii=False)},
        ],
    }
    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers=_build_headers(api_key, auth_header),
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    raw_decisions = _extract_json_array(content)
    usage = {
        key: int(value)
        for key, value in payload.get("usage", {}).items()
        if isinstance(value, int)
    }
    return BatchClassification(
        decisions=[_normalize_decision(row, batch, source=f"ai:{model}") for row in raw_decisions],
        usage=usage,
    )


def apply_ai_decisions_to_sqlite(db_path: Path, decisions: Iterable[AiLevelDecision]) -> dict[str, int]:
    rows = list(decisions)
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
        existing_ids = {
            int(row[0])
            for row in connection.execute(
                """
                SELECT word_id
                FROM word_learning_levels
                WHERE language = 'JA'
                  AND source LIKE 'jlpt_%'
                """
            )
        }
        insert_rows = [
            row for row in rows
            if row.word_id not in existing_ids
        ]
        connection.executemany(
            """
            insert or replace into word_learning_levels (
              word_id,
              language,
              level,
              level_rank,
              learnable,
              confidence,
              source,
              review_status,
              reason
            ) values (?, 'JA', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    row.word_id,
                    row.level,
                    LEVEL_RANK[row.level],
                    int(row.level in LEARNABLE_LEVELS and row.confidence >= 0.68 and row.decision == "learnable"),
                    row.confidence,
                    row.source,
                    _review_status(row),
                    row.reason,
                )
                for row in insert_rows
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return {"input_rows": len(rows), "written_rows": len(insert_rows), "jlpt_skipped_rows": len(rows) - len(insert_rows)}


def summarize_decisions(decisions: list[AiLevelDecision], extra: dict) -> dict:
    by_level: dict[str, int] = {}
    by_status: dict[str, int] = {}
    learnable = 0
    for row in decisions:
        by_level[row.level] = by_level.get(row.level, 0) + 1
        status = _review_status(row)
        by_status[status] = by_status.get(status, 0) + 1
        if row.level in LEARNABLE_LEVELS and row.confidence >= 0.68 and row.decision == "learnable":
            learnable += 1
    return {
        "total_decisions": len(decisions),
        "learnable_decisions": learnable,
        "by_level": dict(sorted(by_level.items(), key=lambda item: LEVEL_RANK.get(item[0], 999))),
        "by_review_status": dict(sorted(by_status.items())),
        **extra,
    }


def _load_candidates(path: Path, limit: int) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
            if len(rows) >= limit:
                break
    return rows


def _build_headers(api_key: str, auth_header: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if auth_header == "api-key":
        headers["api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _load_completed_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    return {decision.word_id for decision in _iter_decisions(path)}


def _iter_decisions(path: Path) -> Iterable[AiLevelDecision]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if not isinstance(row.get("source"), str):
                    row["source"] = "ai:deepseek-chat"
                yield AiLevelDecision(**row)


def _prompt_row(row: dict) -> dict:
    return {
        "word_id": row["word_id"],
        "lemma": row["lemma"],
        "reading": row["reading_or_ipa"],
        "pos": row["pos"],
        "meaning_zh": row["meaning_zh"],
        "meaning_en": row["meaning_source_text"],
    }


def _extract_json_array(content: str) -> list[dict]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", content)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, list):
        raise ValueError("AI output must be a JSON array")
    return value


def _normalize_decision(raw: dict, batch: list[dict], source: str) -> AiLevelDecision:
    source_rows = {int(row["word_id"]): row for row in batch}
    word_id = int(raw["word_id"])
    source_row = source_rows[word_id]
    level = str(raw.get("level", "needs_review")).strip()
    if level not in VALID_LEVELS:
        level = "needs_review"
    confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
    decision = str(raw.get("decision", "")).strip() or ("learnable" if level in LEARNABLE_LEVELS else level)
    if level in LEARNABLE_LEVELS and confidence < 0.68:
        decision = "needs_review"
    return AiLevelDecision(
        word_id=word_id,
        lemma=str(source_row["lemma"]),
        reading_or_ipa=str(source_row["reading_or_ipa"]),
        meaning_zh=str(source_row["meaning_zh"]),
        meaning_source_text=str(source_row["meaning_source_text"]),
        level=level,
        confidence=confidence,
        decision=decision,
        reason=str(raw.get("reason", "")).strip()[:240],
        source=source,
    )


def _fallback_review(row: dict, source: str) -> AiLevelDecision:
    return AiLevelDecision(
        word_id=int(row["word_id"]),
        lemma=str(row["lemma"]),
        reading_or_ipa=str(row["reading_or_ipa"]),
        meaning_zh=str(row["meaning_zh"]),
        meaning_source_text=str(row["meaning_source_text"]),
        level="needs_review",
        confidence=0.0,
        decision="needs_review",
        reason="AI response omitted this row.",
        source=source,
    )


def _review_status(row: AiLevelDecision) -> str:
    if row.level in LEARNABLE_LEVELS and row.confidence >= 0.68 and row.decision == "learnable":
        return "accepted"
    if row.level == "exclude" or row.decision == "exclude":
        return "excluded"
    if row.level == "advanced" or row.decision == "advanced":
        return "advanced"
    return "needs_review"


SYSTEM_PROMPT = """You classify Japanese vocabulary for a beginner-to-advanced learning app.

Return ONLY a valid JSON array. One output object per input object.

Allowed level values:
- N5: very basic survival vocabulary, everyday beginner words.
- N4: common daily words after basic foundation.
- N3: common but more abstract, intermediate daily/work/school words.
- N2: advanced common words for essays, news, formal language, abstract concepts.
- N1: very advanced, literary, idiomatic, specialized but still useful.
- advanced: valid Japanese word but unsuitable for the main beginner/intermediate learning path.
- exclude: vulgar, proper name, brand/company, narrow technical term, archaic/obsolete, typo-like, or very low learning value.
- needs_review: ambiguous or not enough information.

Rules:
- Be conservative. Do not put formal, literary, idiomatic, or obscure words into N5/N4.
- If unsure between a JLPT level and advanced, choose advanced or needs_review.
- Function words and very common everyday words can be N5/N4.
- Useful verbs/adjectives/nouns can be N4/N3 when common; abstract/formal words usually N2/N1/advanced.
- Output fields exactly: word_id, level, confidence, decision, reason.
- decision must be one of: learnable, advanced, exclude, needs_review.
- confidence is 0.0 to 1.0.
- reason must be concise English, max 20 words.
"""


if __name__ == "__main__":
    main()
