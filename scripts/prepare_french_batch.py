import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from dict_feasibility.translation_pipeline import iter_normalized_words, write_normalized_words
from french_classifier import classify_french_entry
from french_rule_translator import apply_french_rule_translation


def prepare_french_batch(
    *,
    input_path: Path,
    blocked_output_path: Path,
    rule_output_path: Path,
    local_output_path: Path,
    summary_output_path: Path,
) -> dict[str, int]:
    blocked_words = []
    rule_words = []
    local_words = []
    total_words = 0

    for word in iter_normalized_words(input_path):
        total_words += 1
        bucket = classify_french_entry(word)
        if bucket == "blocked":
            blocked_words.append(word)
            continue
        if bucket == "rule_based":
            rule_words.append(apply_french_rule_translation(word))
            continue
        local_words.append(word)

    write_normalized_words(blocked_output_path, blocked_words)
    write_normalized_words(rule_output_path, rule_words)
    write_normalized_words(local_output_path, local_words)

    summary = {
        "total_words": total_words,
        "blocked": len(blocked_words),
        "rule_based": len(rule_words),
        "local_candidate": len(local_words),
    }
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a French JSONL batch into blocked, rule, and local subsets.")
    parser.add_argument("--input", type=Path, required=True, help="Input French JSONL batch.")
    parser.add_argument("--blocked-output", type=Path, required=True, help="Output JSONL for blocked entries.")
    parser.add_argument("--rule-output", type=Path, required=True, help="Output JSONL for deterministic rule translations.")
    parser.add_argument("--local-output", type=Path, required=True, help="Output JSONL for local model candidates.")
    parser.add_argument("--summary-output", type=Path, required=True, help="Output JSON summary path.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = prepare_french_batch(
        input_path=args.input,
        blocked_output_path=args.blocked_output,
        rule_output_path=args.rule_output,
        local_output_path=args.local_output,
        summary_output_path=args.summary_output,
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
