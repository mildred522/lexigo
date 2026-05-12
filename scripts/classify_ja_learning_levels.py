from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dict_feasibility.ja_learning_levels import (
    apply_learning_levels_to_sqlite,
    classify_jlpt_items,
    load_japanese_rows,
    parse_n5_html_table,
    parse_ts_vocabulary,
    summarize,
    write_jsonl,
)

N5_URL = "https://passjapanesetest.com/jlpt-n5-vocabulary-list/"
TS_URLS = {
    "N4": "https://raw.githubusercontent.com/chadmuro/jlpt-vocab/main/data/n4/vocabulary.ts",
    "N3": "https://raw.githubusercontent.com/chadmuro/jlpt-vocab/main/data/n3/vocabulary.ts",
    "N2": "https://raw.githubusercontent.com/chadmuro/jlpt-vocab/main/data/n2/vocabulary.ts",
    "N1": "https://raw.githubusercontent.com/chadmuro/jlpt-vocab/main/data/n1/vocabulary.ts",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Japanese dictionary rows into JLPT learning levels.")
    parser.add_argument("--db", type=Path, default=Path("artifacts/package/dictionary.db"))
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts/learning_levels/ja"))
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--write-db", action="store_true", help="Write accepted levels into the SQLite package.")
    parser.add_argument("--refresh-sources", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    out_dir = args.out_dir
    source_dir = out_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    per_level = max(args.limit // 5, 1)
    source_started = time.perf_counter()
    items = _load_jlpt_items(source_dir, per_level, refresh=args.refresh_sources)
    source_elapsed = time.perf_counter() - source_started
    items = items[: args.limit]

    db_started = time.perf_counter()
    rows = load_japanese_rows(args.db)
    db_elapsed = time.perf_counter() - db_started

    classify_started = time.perf_counter()
    result = classify_jlpt_items(items, rows)
    classify_elapsed = time.perf_counter() - classify_started

    write_started = time.perf_counter()
    write_jsonl(out_dir / "ja_learning_levels.accepted.jsonl", result.accepted)
    write_jsonl(out_dir / "ja_learning_levels.needs_review.jsonl", result.needs_review)
    write_jsonl(out_dir / "ja_learning_levels.missing.jsonl", result.missing)
    summary = summarize(
        result,
        elapsed={
            "source_load": round(source_elapsed, 4),
            "db_load_and_index_input": round(db_elapsed, 4),
            "classification": round(classify_elapsed, 4),
            "write_outputs": 0.0,
            "total": 0.0,
        },
        total_items=len(items),
    )
    write_elapsed = time.perf_counter() - write_started
    summary["elapsed_seconds"]["write_outputs"] = round(write_elapsed, 4)

    if args.write_db:
        db_write_started = time.perf_counter()
        db_write_summary = apply_learning_levels_to_sqlite(args.db, result.accepted)
        summary["db_write"] = db_write_summary
        summary["elapsed_seconds"]["db_write"] = round(time.perf_counter() - db_write_started, 4)

    summary["elapsed_seconds"]["total"] = round(time.perf_counter() - started, 4)
    (out_dir / "ja_learning_levels.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _load_jlpt_items(source_dir: Path, per_level: int, refresh: bool) -> list:
    n5_html = _cached_get(N5_URL, source_dir / "n5_passjapanesetest.html", refresh=refresh)
    items = parse_n5_html_table(n5_html, limit=per_level)
    for level, url in TS_URLS.items():
        source = _cached_get(url, source_dir / f"{level.lower()}_vocabulary.ts", refresh=refresh)
        items.extend(parse_ts_vocabulary(source, level=level, limit=per_level))
    return items


def _cached_get(url: str, path: Path, refresh: bool) -> str:
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    path.write_text(response.text, encoding="utf-8", newline="\n")
    return response.text


if __name__ == "__main__":
    main()
