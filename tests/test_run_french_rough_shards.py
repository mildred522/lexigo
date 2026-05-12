import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from run_french_rough_shards import discover_shards, make_shard_paths


def test_discover_shards_filters_original_numbered_shards(tmp_path: Path) -> None:
    (tmp_path / "kaikki_fr_part_0001.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "kaikki_fr_part_0002.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "kaikki_fr_part_0002.local.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "kaikki_fr_batch_0001_1000.jsonl").write_text("", encoding="utf-8")

    shards = discover_shards(tmp_path, start_index=2, end_index=2)

    assert [shard.name for shard in shards] == ["kaikki_fr_part_0002.jsonl"]


def test_make_shard_paths_uses_rough_output_conventions() -> None:
    paths = make_shard_paths(Path("artifacts/normalized/fr_shards/kaikki_fr_part_0002.jsonl"))

    assert paths.blocked_output == Path("artifacts/normalized/fr_shards/kaikki_fr_part_0002.blocked.jsonl")
    assert paths.rule_output == Path("artifacts/translated/fr_shards/kaikki_fr_part_0002.rule.jsonl")
    assert paths.local_output == Path("artifacts/normalized/fr_shards/kaikki_fr_part_0002.local.jsonl")
    assert paths.translated_output == Path("artifacts/translated/fr_shards/kaikki_fr_part_0002.qwen25.out.jsonl")
    assert paths.review_report == Path("artifacts/reports/french-rough/kaikki_fr_part_0002.qwen25.review.json")
