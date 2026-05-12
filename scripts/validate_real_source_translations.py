import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.real_source_translation_validation import (
    fetch_remote_translation_validation_report,
)
from dict_feasibility.translation import (
    FileTranslationCache,
    build_translation_provider,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--provider", choices=["mapping", "openai", "llama_cpp"], default="mapping")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--glossary", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--base-url-env", default="OPENAI_BASE_URL")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def _default_glossary_path() -> Path:
    source_path = _REPO_ROOT / "sources" / "translations" / "glossary.json"
    if source_path.exists():
        return source_path
    return _REPO_ROOT / "tests" / "fixtures" / "translation_glossary.json"


def main() -> None:
    args = parse_args()
    provider = build_translation_provider(
        provider_name=args.provider,
        glossary_path=args.glossary or _default_glossary_path(),
        model=args.model,
        api_key_env=args.api_key_env,
        base_url_env=args.base_url_env,
    )
    cache = FileTranslationCache(
        args.cache
        or (_REPO_ROOT / "artifacts" / "reports" / "translation-cache.json")
    )
    report = fetch_remote_translation_validation_report(
        limit=args.limit,
        provider=provider,
        cache=cache,
    )
    report["provider"] = args.provider
    report["model"] = args.model
    report_path = args.report or (
        _REPO_ROOT / "artifacts" / "reports" / "real-source-translation-validation.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(report_path)


if __name__ == "__main__":
    main()
