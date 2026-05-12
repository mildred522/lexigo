import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.translation_pipeline import iter_normalized_words, write_normalized_words


def apply_french_manual_corrections(
    *,
    input_path: Path,
    corrections_path: Path,
    output_path: Path,
    report_path: Path,
) -> dict[str, int]:
    corrections = _load_corrections(corrections_path)
    corrected_words = []
    applied_keys: set[tuple[str, str]] = set()

    for word in iter_normalized_words(input_path):
        key = (word.source_entry_id, word.meaning_source_text)
        if key in corrections:
            corrected_words.append(replace(word, meaning_zh=corrections[key]))
            applied_keys.add(key)
        else:
            corrected_words.append(word)

    write_normalized_words(output_path, corrected_words)
    report = {
        "total_words": len(corrected_words),
        "applied_corrections": len(applied_keys),
        "unused_corrections": len(set(corrections) - applied_keys),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _load_corrections(path: Path) -> dict[tuple[str, str], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        (item["source_entry_id"], item["meaning_source_text"]): item["meaning_zh"]
        for item in payload
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply reviewed French manual corrections to a JSONL batch.")
    parser.add_argument("--input", type=Path, required=True, help="Translated French JSONL input.")
    parser.add_argument("--corrections", type=Path, required=True, help="JSON correction list.")
    parser.add_argument("--output", type=Path, required=True, help="Corrected JSONL output.")
    parser.add_argument("--report", type=Path, required=True, help="Correction summary JSON output.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = apply_french_manual_corrections(
        input_path=args.input,
        corrections_path=args.corrections,
        output_path=args.output,
        report_path=args.report,
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
