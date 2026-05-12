import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHARD_RE = re.compile(r"^kaikki_fr_part_(?P<index>\d{4})\.jsonl$")


@dataclass(frozen=True)
class ShardPaths:
    input_path: Path
    blocked_output: Path
    rule_output: Path
    local_output: Path
    prep_summary: Path
    translated_output: Path
    translation_summary: Path
    checkpoint_output: Path
    checkpoint_report: Path
    review_report: Path


def discover_shards(input_dir: Path, *, start_index: int, end_index: int | None) -> list[Path]:
    shards: list[tuple[int, Path]] = []
    for path in input_dir.glob("kaikki_fr_part_*.jsonl"):
        match = _SHARD_RE.match(path.name)
        if not match:
            continue
        index = int(match.group("index"))
        if index < start_index:
            continue
        if end_index is not None and index > end_index:
            continue
        shards.append((index, path))
    return [path for _, path in sorted(shards)]


def make_shard_paths(input_path: Path) -> ShardPaths:
    stem = input_path.stem
    normalized_dir = input_path.parent
    translated_dir = Path("artifacts/translated/fr_shards")
    reports_dir = Path("artifacts/reports/french-rough")
    return ShardPaths(
        input_path=input_path,
        blocked_output=normalized_dir / f"{stem}.blocked.jsonl",
        rule_output=translated_dir / f"{stem}.rule.jsonl",
        local_output=normalized_dir / f"{stem}.local.jsonl",
        prep_summary=reports_dir / f"{stem}.prep.summary.json",
        translated_output=translated_dir / f"{stem}.qwen25.out.jsonl",
        translation_summary=reports_dir / f"{stem}.qwen25.summary.json",
        checkpoint_output=translated_dir / f"{stem}.qwen25.checkpoint.jsonl",
        checkpoint_report=reports_dir / f"{stem}.qwen25.progress.json",
        review_report=reports_dir / f"{stem}.qwen25.review.json",
    )


def run_shards(args: argparse.Namespace) -> None:
    shards = discover_shards(args.input_dir, start_index=args.start_index, end_index=args.end_index)
    progress_path = args.progress_report
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    completed = 0
    skipped = 0

    for shard in shards:
        paths = make_shard_paths(shard)
        if paths.review_report.exists() and not args.force:
            skipped += 1
            _write_progress(progress_path, shard=shard, completed=completed, skipped=skipped, status="skipped")
            continue

        _run_prepare(paths)
        _run_translate(paths, args)
        _run_review(paths)
        completed += 1
        _write_progress(progress_path, shard=shard, completed=completed, skipped=skipped, status="completed")


def _run_prepare(paths: ShardPaths) -> None:
    _run(
        [
            sys.executable,
            "scripts/prepare_french_batch.py",
            "--input",
            str(paths.input_path),
            "--blocked-output",
            str(paths.blocked_output),
            "--rule-output",
            str(paths.rule_output),
            "--local-output",
            str(paths.local_output),
            "--summary-output",
            str(paths.prep_summary),
        ]
    )


def _run_translate(paths: ShardPaths, args: argparse.Namespace) -> None:
    env = os.environ.copy()
    env.setdefault("OPENAI_API_KEY", args.api_key)
    env.setdefault("OPENAI_BASE_URL", args.base_url)
    _run(
        [
            sys.executable,
            "scripts/translate_normalized_words.py",
            "--provider",
            args.provider,
            "--model",
            args.model,
            "--batch-size",
            str(args.batch_size),
            "--checkpoint-every",
            str(args.checkpoint_every),
            "--input",
            str(paths.local_output),
            "--output",
            str(paths.translated_output),
            "--report",
            str(paths.translation_summary),
            "--checkpoint-output",
            str(paths.checkpoint_output),
            "--checkpoint-report",
            str(paths.checkpoint_report),
            "--cache",
            str(args.cache),
        ],
        env=env,
    )


def _run_review(paths: ShardPaths) -> None:
    _run(
        [
            sys.executable,
            "scripts/review_french_translation_batch.py",
            "--input",
            str(paths.translated_output),
            "--output",
            str(paths.review_report),
        ]
    )


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=_REPO_ROOT, env=env, check=True)


def _write_progress(progress_path: Path, *, shard: Path, completed: int, skipped: int, status: str) -> None:
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "last_shard": shard.name,
        "last_status": status,
        "completed_shards": completed,
        "skipped_shards": skipped,
    }
    progress_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rough French translation across numbered shard files.")
    parser.add_argument("--input-dir", type=Path, default=Path("artifacts/normalized/fr_shards"))
    parser.add_argument("--start-index", type=int, default=2)
    parser.add_argument("--end-index", type=int, default=None)
    parser.add_argument("--provider", default="llama_cpp")
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--api-key", default="local")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--checkpoint-every", type=int, default=500)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/reports/translation-cache-qwen2.5-fr-rough.json"))
    parser.add_argument("--progress-report", type=Path, default=Path("artifacts/reports/french-rough/run-progress.json"))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    run_shards(_parse_args())


if __name__ == "__main__":
    main()
