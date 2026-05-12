import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.reporting import summarize_words
from dict_feasibility.translation_pipeline import iter_normalized_words


def _artifact_path(filename: str) -> Path:
    translated = _REPO_ROOT / "artifacts" / "translated" / filename
    if translated.exists():
        return translated
    return _REPO_ROOT / "artifacts" / "normalized" / filename


def main() -> None:
    reports_dir = _REPO_ROOT / "artifacts" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    (reports_dir / "jmdict-summary.json").write_text(
        json.dumps(
            summarize_words(iter_normalized_words(_artifact_path("jmdict_words.jsonl"))),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (reports_dir / "kaikki-fr-summary.json").write_text(
        json.dumps(
            summarize_words(iter_normalized_words(_artifact_path("kaikki_fr_words.jsonl"))),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
