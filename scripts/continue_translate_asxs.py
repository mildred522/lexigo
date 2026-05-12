import argparse
import json
import sys
import time
from collections import OrderedDict
from pathlib import Path

import requests

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.asxs_streaming import (
    AsxsResponsesStreamError,
    extract_responses_stream_text,
    fix_latin1_utf8_mojibake,
    parse_indexed_translation_lines,
)
from dict_feasibility.translation import FileTranslationCache


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Continue translating JA entries with the asxs responses stream.")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", default="https://api.asxs.top/v1")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--input", type=Path, default=_REPO_ROOT / "artifacts" / "translated" / "jmdict_words.jsonl")
    parser.add_argument("--cache", type=Path, default=_REPO_ROOT / "artifacts" / "reports" / "translation-cache.json")
    parser.add_argument("--report", type=Path, default=_REPO_ROOT / "artifacts" / "reports" / "asxs-progress-report.json")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--min-batch-size", type=int, default=1)
    parser.add_argument("--max-seconds", type=int, default=1800)
    parser.add_argument("--pause-seconds", type=float, default=0.35)
    parser.add_argument("--retry-sleep-seconds", type=float, default=2.5)
    parser.add_argument("--max-retries-per-batch", type=int, default=5)
    parser.add_argument("--flush-every", type=int, default=32)
    parser.add_argument("--rewrite-output", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cache = FileTranslationCache(args.cache)
    pending = load_pending_glosses(args.input, cache)
    started_at = time.monotonic()
    deadline = started_at + max(1, args.max_seconds)

    cursor = 0
    batch_size = max(args.min_batch_size, args.batch_size)
    retries_for_cursor = 0
    translated_unique = 0
    translated_entries = 0
    succeeded_requests = 0
    failed_requests = 0
    input_tokens = 0
    output_tokens = 0
    error_samples: list[dict[str, object]] = []
    sample_translations: list[dict[str, object]] = []

    while time.monotonic() < deadline and cursor < len(pending):
        current_batch = pending[cursor:cursor + batch_size]
        texts = [item["gloss"] for item in current_batch]
        try:
            translations, usage = translate_batch_via_responses_stream(
                api_key=args.api_key,
                base_url=args.base_url,
                model=args.model,
                texts=texts,
            )
            succeeded_requests += 1
            retries_for_cursor = 0
            for item, translation in zip(current_batch, translations):
                cache.items[(item["gloss"], "en", "zh")] = translation
                translated_unique += 1
                translated_entries += int(item["entry_count"])
                if len(sample_translations) < 20:
                    sample_translations.append(
                        {
                            "gloss": item["gloss"],
                            "translation": translation,
                            "entry_count": item["entry_count"],
                            "example_lemmas": item["example_lemmas"],
                        }
                    )
            if usage:
                input_tokens += int(usage.get("input_tokens") or 0)
                output_tokens += int(usage.get("output_tokens") or 0)
            cursor += len(current_batch)
            if translated_unique % max(1, args.flush_every) == 0:
                flush_cache(cache)
            if batch_size < args.batch_size:
                batch_size += 1
            time.sleep(max(0.0, args.pause_seconds))
        except Exception as exc:
            failed_requests += 1
            retries_for_cursor += 1
            error_samples.append(
                {
                    "cursor": cursor,
                    "batch_size": batch_size,
                    "batch_preview": texts[:3],
                    "error": str(exc),
                }
            )
            if batch_size > args.min_batch_size:
                batch_size = max(args.min_batch_size, batch_size // 2)
            elif retries_for_cursor >= max(1, args.max_retries_per_batch):
                cursor += 1
                retries_for_cursor = 0
            time.sleep(max(0.0, args.retry_sleep_seconds))

    flush_cache(cache)
    if args.rewrite_output:
        rewrite_translated_file(args.input, cache)

    elapsed = time.monotonic() - started_at
    report_payload = {
        "model": args.model,
        "base_url": args.base_url,
        "elapsed_seconds": round(elapsed, 2),
        "pending_unique_glosses_at_start": len(pending),
        "requests_succeeded": succeeded_requests,
        "requests_failed": failed_requests,
        "translated_unique_glosses": translated_unique,
        "translated_entries_covered": translated_entries,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "final_cursor": cursor,
        "sample_translations": sample_translations,
        "error_samples": error_samples[:20],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.report)


def load_pending_glosses(input_path: Path, cache: FileTranslationCache) -> list[dict[str, object]]:
    pending: OrderedDict[str, dict[str, object]] = OrderedDict()
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("language") != "JA":
                continue
            if row.get("meaning_zh", "").strip():
                continue
            gloss = row.get("meaning_source_text", "").strip()
            if not gloss:
                continue
            if cache.get(gloss, "en", "zh"):
                continue
            bucket = pending.setdefault(
                gloss,
                {
                    "gloss": gloss,
                    "entry_count": 0,
                    "example_lemmas": [],
                },
            )
            bucket["entry_count"] = int(bucket["entry_count"]) + 1
            if len(bucket["example_lemmas"]) < 3:
                bucket["example_lemmas"].append(row.get("lemma", ""))
    return list(pending.values())


def translate_batch_via_responses_stream(
    *,
    api_key: str,
    base_url: str,
    model: str,
    texts: list[str],
) -> tuple[list[str], dict | None]:
    prompt = build_tab_separated_prompt(texts)
    response = requests.post(
        base_url.rstrip("/") + "/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            "store": False,
            "stream": True,
            "reasoning": {"effort": "none"},
            "text": {"verbosity": "low"},
        },
        timeout=90,
        stream=True,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"http_{response.status_code}: {response.text[:2000]}")

    raw_text, usage = extract_responses_stream_text(response.iter_lines(decode_unicode=False))
    normalized = fix_latin1_utf8_mojibake(raw_text).strip()
    if not normalized:
        raise RuntimeError("empty_stream_output")
    translations = parse_indexed_translation_lines(normalized, expected_count=len(texts))
    return translations, usage


def build_tab_separated_prompt(texts: list[str]) -> str:
    return (
        "Translate each item into concise Simplified Chinese dictionary wording.\n"
        "Return exactly one line per item in the format <index>\\t<translation>.\n"
        "Do not use JSON. Do not use code fences. Do not add commentary.\n"
        "Keep the original item order.\n\n"
        f"Items:\n{format_indexed_items(texts)}"
    )


def format_indexed_items(texts: list[str]) -> str:
    return "\n".join(f"{index}\t{text}" for index, text in enumerate(texts))


def flush_cache(cache: FileTranslationCache) -> None:
    payload = [
        {
            "text": key[0],
            "source_lang": key[1],
            "target_lang": key[2],
            "translated": value,
        }
        for key, value in sorted(cache.items.items())
    ]
    cache.path.parent.mkdir(parents=True, exist_ok=True)
    cache.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rewrite_translated_file(input_path: Path, cache: FileTranslationCache) -> None:
    temp_path = input_path.with_suffix(input_path.suffix + ".tmp")
    with input_path.open("r", encoding="utf-8") as source, temp_path.open("w", encoding="utf-8") as destination:
        for line in source:
            row = json.loads(line)
            if row.get("language") == "JA" and not row.get("meaning_zh", "").strip():
                gloss = row.get("meaning_source_text", "").strip()
                translated = cache.get(gloss, "en", "zh") if gloss else None
                if translated:
                    row["meaning_zh"] = translated
            destination.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp_path.replace(input_path)


if __name__ == "__main__":
    main()
