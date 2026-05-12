import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.models import NormalizedWord
from dict_feasibility.translation_pipeline import iter_normalized_words, write_normalized_words


def should_translate(word: NormalizedWord) -> bool:
    return (not word.meaning_zh.strip()) and bool(word.meaning_source_text.strip())


def shard_french_translation_input(input_path: Path, output_dir: Path, shard_size: int) -> list[Path]:
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in output_dir.glob("kaikki_fr_part_*.jsonl"):
        existing.unlink()

    shard_paths: list[Path] = []
    bucket: list[NormalizedWord] = []
    index = 1

    for word in iter_normalized_words(input_path):
        if not should_translate(word):
            continue

        bucket.append(word)
        if len(bucket) == shard_size:
            shard_path = output_dir / f"kaikki_fr_part_{index:04d}.jsonl"
            write_normalized_words(shard_path, bucket)
            shard_paths.append(shard_path)
            bucket = []
            index += 1

    if bucket:
        shard_path = output_dir / f"kaikki_fr_part_{index:04d}.jsonl"
        write_normalized_words(shard_path, bucket)
        shard_paths.append(shard_path)

    return shard_paths


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shard untranslated French rows into deterministic JSONL chunks.")
    parser.add_argument(
        "--input",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "translated" / "kaikki_fr_words.jsonl",
        help="Path to the translated French artifact to shard.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "normalized" / "fr_shards",
        help="Directory that will receive shard JSONL files.",
    )
    parser.add_argument(
        "--shard-size",
        type=int,
        default=10000,
        help="Number of rows per shard.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    shard_paths = shard_french_translation_input(
        input_path=args.input,
        output_dir=args.output_dir,
        shard_size=args.shard_size,
    )
    for path in shard_paths:
        print(path)


if __name__ == "__main__":
    main()
