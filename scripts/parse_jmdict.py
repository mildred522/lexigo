import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.jmdict_parser import parse_jmdict_file
from dict_feasibility.source_paths import (
    resolve_jmdict_source,
    resolve_tatoeba_examples_source,
    resolve_tatoeba_links_archive,
    resolve_tatoeba_sentence_archive,
)
from dict_feasibility.tatoeba_parser import (
    build_tatoeba_example_map,
    build_tatoeba_example_map_from_archives,
)


def main() -> None:
    in_path = resolve_jmdict_source(_REPO_ROOT)
    out_path = _REPO_ROOT / "artifacts/normalized/jmdict_words.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    examples_by_lemma = _build_examples_by_lemma(in_path)

    with out_path.open("w", encoding="utf-8") as handle:
        for record in parse_jmdict_file(in_path, examples_by_lemma):
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


def _build_examples_by_lemma(in_path: Path) -> dict[str, list[dict[str, str]]]:
    sentences_archive = resolve_tatoeba_sentence_archive(_REPO_ROOT)
    links_archive = resolve_tatoeba_links_archive(_REPO_ROOT)
    if sentences_archive is not None and links_archive is not None:
        target_lemmas = {
            record.lemma
            for record in parse_jmdict_file(in_path)
            if record.lemma.strip()
        }
        return build_tatoeba_example_map_from_archives(
            sentences_archive=sentences_archive,
            links_archive=links_archive,
            target_lemmas=target_lemmas,
        )

    example_path = resolve_tatoeba_examples_source(_REPO_ROOT)
    return build_tatoeba_example_map(example_path)


if __name__ == "__main__":
    main()
