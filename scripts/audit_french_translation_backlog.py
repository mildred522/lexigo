import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.translation_pipeline import iter_normalized_words


def audit_french_translation_backlog(path: Path) -> dict[str, object]:
    source_lang_counts: Counter[str] = Counter()
    unique_nonempty_source_texts: set[tuple[str, str]] = set()
    total_words = 0
    translated_words = 0
    missing_source_text_words = 0

    for word in iter_normalized_words(path):
        total_words += 1
        source_text = word.meaning_source_text.strip()
        source_lang = word.meaning_source_lang.strip() or "unknown"
        source_lang_counts[source_lang] += 1

        if word.meaning_zh.strip():
            translated_words += 1

        if not source_text:
            missing_source_text_words += 1
            continue

        unique_nonempty_source_texts.add((source_lang, source_text))

    return {
        "generated_at": "2026-04-20",
        "input_path": str(path).replace("\\", "/"),
        "total_words": total_words,
        "translated_words": translated_words,
        "untranslated_words": total_words - translated_words,
        "missing_source_text_words": missing_source_text_words,
        "unique_nonempty_source_texts": len(unique_nonempty_source_texts),
        "source_lang_counts": dict(source_lang_counts),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the current French translation backlog.")
    parser.add_argument(
        "--input",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "translated" / "kaikki_fr_words.jsonl",
        help="Path to the translated French artifact to audit.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "reports" / "french-translation-baseline.json",
        help="Where to write the backlog audit JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = audit_french_translation_backlog(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
