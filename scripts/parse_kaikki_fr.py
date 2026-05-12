import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.kaikki_parser import parse_kaikki_french_file
from dict_feasibility.source_paths import resolve_kaikki_fr_source


def main() -> None:
    in_path = resolve_kaikki_fr_source(_REPO_ROOT)
    out_path = _REPO_ROOT / "artifacts/normalized/kaikki_fr_words.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        for record in parse_kaikki_french_file(in_path):
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
