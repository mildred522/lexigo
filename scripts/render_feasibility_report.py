import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.feasibility_report import render_report


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _translation_provider_label(real_source_translation_validation: dict[str, object] | None) -> str:
    if real_source_translation_validation is None:
        return "mapping-glossary"
    provider = str(real_source_translation_validation.get("provider", "")).strip()
    model = str(real_source_translation_validation.get("model", "")).strip()
    if provider and model:
        return f"{provider}:{model}"
    if provider:
        return provider
    return "mapping-glossary"


def main() -> None:
    reports_dir = _REPO_ROOT / "artifacts" / "reports"
    docs_dir = _REPO_ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    japanese_summary = json.loads((reports_dir / "jmdict-summary.json").read_text(encoding="utf-8"))
    french_summary = json.loads((reports_dir / "kaikki-fr-summary.json").read_text(encoding="utf-8"))
    translation_summary = json.loads((reports_dir / "translation-summary.json").read_text(encoding="utf-8"))
    real_source_validation = _load_optional_json(reports_dir / "real-source-validation.json")
    real_source_translation_validation = _load_optional_json(
        reports_dir / "real-source-translation-validation.json",
    )
    translation_sample_size = sum(
        int(item["translated_now"]) + int(item["already_translated"])
        for item in translation_summary.values()
    )
    report = render_report(
        japanese_summary=japanese_summary,
        french_summary=french_summary,
        translation_provider=_translation_provider_label(real_source_translation_validation),
        translation_sample_size=translation_sample_size,
        real_source_validation=real_source_validation,
        real_source_translation_validation=real_source_translation_validation,
    )
    (docs_dir / "feasibility-report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
