import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.translation import (
    FallbackTranslationProvider,
    FileTranslationCache,
    build_translation_provider,
    load_supplemental_translation_overrides,
)
from dict_feasibility.translation_pipeline import (
    load_normalized_words,
    run_translation_job,
    write_normalized_words,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["mapping", "openai", "llama_cpp"], default="mapping")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--fallback-provider", choices=["openai", "llama_cpp"])
    parser.add_argument("--fallback-model")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--base-url-env", default="OPENAI_BASE_URL")
    parser.add_argument("--fallback-api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--fallback-base-url-env", default="OPENAI_BASE_URL")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--glossary", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--checkpoint-every", type=int, default=0)
    parser.add_argument("--checkpoint-output", type=Path)
    parser.add_argument("--checkpoint-report", type=Path)
    return parser.parse_args()


def _default_glossary_path() -> Path:
    source_path = _REPO_ROOT / "sources" / "translations" / "glossary.json"
    if source_path.exists():
        return source_path
    return _REPO_ROOT / "tests" / "fixtures" / "translation_glossary.json"


def _default_cache_path() -> Path:
    return _REPO_ROOT / "artifacts" / "reports" / "translation-cache.json"


def _default_overrides_path() -> Path | None:
    source_path = _REPO_ROOT / "sources" / "translations" / "supplemental_overrides.json"
    if source_path.exists():
        return source_path
    return None


def main() -> None:
    args = parse_args()

    if args.input is None:
        normalized_dir = _REPO_ROOT / "artifacts" / "normalized"
        translated_dir = _REPO_ROOT / "artifacts" / "translated"
        translated_dir.mkdir(parents=True, exist_ok=True)

        all_summaries: dict[str, dict[str, int | list[str]]] = {}
        cache = FileTranslationCache(args.cache or _default_cache_path())
        supplemental_overrides = _load_supplemental_overrides(args)
        for filename in ("jmdict_words.jsonl", "kaikki_fr_words.jsonl"):
            words = load_normalized_words(normalized_dir / filename)
            provider = _build_provider(args)
            translated_words, summary = run_translation_job(
                words,
                provider=provider,
                cache=cache,
                supplemental_overrides=supplemental_overrides,
                batch_size=args.batch_size,
            )
            write_normalized_words(translated_dir / filename, translated_words)
            all_summaries[filename] = summary
        report_path = _REPO_ROOT / "artifacts" / "reports" / "translation-summary.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(all_summaries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(report_path)
        return

    assert args.output is not None
    assert args.report is not None

    words = load_normalized_words(args.input)
    provider = _build_provider(args)
    checkpoint_output = None
    checkpoint_report = None
    if args.checkpoint_every > 0:
        checkpoint_output = args.checkpoint_output or args.output
        checkpoint_report = args.checkpoint_report or args.report
    translated_words, summary = run_translation_job(
        words,
        provider=provider,
        cache=FileTranslationCache(args.cache or _default_cache_path()),
        supplemental_overrides=_load_supplemental_overrides(args),
        batch_size=args.batch_size,
        checkpoint_every=args.checkpoint_every,
        checkpoint_output_path=checkpoint_output,
        checkpoint_report_path=checkpoint_report,
    )
    write_normalized_words(args.output, translated_words)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_provider(args: argparse.Namespace):
    primary = build_translation_provider(
        provider_name=args.provider,
        glossary_path=args.glossary or _default_glossary_path(),
        model=args.model,
        api_key_env=args.api_key_env,
        base_url_env=args.base_url_env,
    )
    if not args.fallback_provider:
        return primary

    fallback = build_translation_provider(
        provider_name=args.fallback_provider,
        glossary_path=args.glossary or _default_glossary_path(),
        model=args.fallback_model or args.model,
        api_key_env=args.fallback_api_key_env,
        base_url_env=args.fallback_base_url_env,
    )
    return FallbackTranslationProvider(primary=primary, secondary=fallback)


def _load_supplemental_overrides(args: argparse.Namespace):
    path = args.overrides or _default_overrides_path()
    if path is None:
        return []
    return load_supplemental_translation_overrides(path)


if __name__ == "__main__":
    main()
