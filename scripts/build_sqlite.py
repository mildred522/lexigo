import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.sqlite_builder import build_sqlite
from dict_feasibility.translation_pipeline import iter_normalized_words


def iter_words(path: Path):
    yield from iter_normalized_words(path)


def _artifact_path(filename: str) -> Path:
    translated = _REPO_ROOT / "artifacts" / "translated" / filename
    if translated.exists():
        return translated
    return _REPO_ROOT / "artifacts" / "normalized" / filename


def main() -> None:
    def iter_all_words():
        yield from iter_words(_artifact_path("jmdict_words.jsonl"))
        yield from iter_words(_artifact_path("kaikki_fr_words.jsonl"))

    build_sqlite(_REPO_ROOT / "artifacts" / "prototype.db", iter_all_words())


if __name__ == "__main__":
    main()
