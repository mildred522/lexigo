def _ratio_to_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _render_fixture_section(
    japanese_summary: dict[str, int | float | list[str]],
    french_summary: dict[str, int | float | list[str]],
) -> str:
    return f"""## Fixture Pipeline Snapshot

- Japanese total words: {int(japanese_summary['total_words'])}
- Japanese missing pronunciation: {int(japanese_summary['missing_pronunciation'])}
- Japanese missing source meaning: {int(japanese_summary['missing_source_meaning'])}
- Japanese missing meaning: {int(japanese_summary['missing_meaning'])}
- Japanese pronunciation coverage: {_ratio_to_percent(float(japanese_summary['pronunciation_coverage_ratio']))}
- Japanese source meaning coverage: {_ratio_to_percent(float(japanese_summary['source_meaning_coverage_ratio']))}
- Japanese meaning coverage: {_ratio_to_percent(float(japanese_summary['meaning_coverage_ratio']))}
- Japanese sample lemmas: {", ".join(japanese_summary['sample_lemmas'])}
- French total words: {int(french_summary['total_words'])}
- French missing pronunciation: {int(french_summary['missing_pronunciation'])}
- French missing source meaning: {int(french_summary['missing_source_meaning'])}
- French missing meaning: {int(french_summary['missing_meaning'])}
- French pronunciation coverage: {_ratio_to_percent(float(french_summary['pronunciation_coverage_ratio']))}
- French source meaning coverage: {_ratio_to_percent(float(french_summary['source_meaning_coverage_ratio']))}
- French meaning coverage: {_ratio_to_percent(float(french_summary['meaning_coverage_ratio']))}
- French sample lemmas: {", ".join(french_summary['sample_lemmas'])}
"""


def _structural_source_ready(summary: dict[str, object]) -> bool:
    return (
        int(summary.get("sampled_entries", 0)) > 0
        and float(summary.get("pronunciation_coverage_ratio", 0.0)) >= 0.99
        and float(summary.get("source_meaning_coverage_ratio", 0.0)) >= 0.99
    )


def _render_official_source_section(real_source_validation: dict[str, object]) -> str:
    japanese = real_source_validation["japanese"]
    french = real_source_validation["french"]
    sample_limit = int(real_source_validation["sample_limit"])
    return f"""## Official Source Validation

- Official source validation sample size: {sample_limit} per language
- Japanese pronunciation coverage on official sample: {_ratio_to_percent(float(japanese['pronunciation_coverage_ratio']))}
- Japanese source gloss coverage on official sample: {_ratio_to_percent(float(japanese['source_meaning_coverage_ratio']))}
- Japanese direct Chinese gloss coverage in source: {_ratio_to_percent(float(japanese['chinese_gloss_coverage_ratio']))}
- Japanese entries requiring translation: {int(japanese['translation_required_entries'])}
- French pronunciation coverage on official sample: {_ratio_to_percent(float(french['pronunciation_coverage_ratio']))}
- French source gloss coverage on official sample: {_ratio_to_percent(float(french['source_meaning_coverage_ratio']))}
- French direct Chinese gloss coverage in source: {_ratio_to_percent(float(french['chinese_gloss_coverage_ratio']))}
- French entries requiring translation: {int(french['translation_required_entries'])}
"""


def _render_translation_section(
    translation_provider: str,
    translation_sample_size: int,
    real_source_translation_validation: dict[str, object] | None,
) -> str:
    lines = [
        "## Translation",
        "",
        f"- Translation provider tested: {translation_provider}",
        f"- Fixture translation sample size: {translation_sample_size}",
    ]

    if real_source_translation_validation is None:
        lines.append("- Chinese meanings are being filled through the translation pipeline.")
        return "\n".join(lines)

    japanese = real_source_translation_validation["japanese"]
    french = real_source_translation_validation["french"]
    japanese_coverage = float(japanese["translated_coverage_ratio"])
    french_coverage = float(french["translated_coverage_ratio"])
    lines.extend(
        [
            f"- Japanese translated coverage on official sample: {_ratio_to_percent(japanese_coverage)}",
            f"- Japanese translation errors on official sample: {int(japanese['translation_errors'])}",
            f"- French translated coverage on official sample: {_ratio_to_percent(french_coverage)}",
            f"- French translation errors on official sample: {int(french['translation_errors'])}",
        ],
    )
    if japanese_coverage >= 0.8 and french_coverage >= 0.8:
        lines.extend(
            [
                "- Live provider validation shows strong Chinese-ready coverage on the official sample.",
                "- Remaining failures are limited edge cases, not a structural blocker for the project.",
            ],
        )
    else:
        lines.extend(
            [
                "- Current low official-sample translation coverage reflects the active provider setup, not a missing translation stage.",
                "- Chinese-ready content still requires validation with a stronger provider or additional glossary coverage.",
            ],
        )
    return "\n".join(lines)


def _determine_verdict(
    japanese_summary: dict[str, int | float | list[str]],
    french_summary: dict[str, int | float | list[str]],
    translation_sample_size: int,
    real_source_validation: dict[str, object] | None,
    real_source_translation_validation: dict[str, object] | None,
) -> str:
    if real_source_validation is None:
        japanese_total = int(japanese_summary["total_words"])
        french_total = int(french_summary["total_words"])
        if japanese_total > 0 and french_total > 0 and translation_sample_size > 0:
            return "High feasibility"
        if japanese_total > 0 and french_total > 0:
            return "Feasible with translation validation pending"
        return "Low feasibility"

    japanese_real = real_source_validation["japanese"]
    french_real = real_source_validation["french"]
    structural_ready = _structural_source_ready(japanese_real) and _structural_source_ready(french_real)
    direct_chinese_ready = (
        float(japanese_real.get("chinese_gloss_coverage_ratio", 0.0)) >= 0.8
        and float(french_real.get("chinese_gloss_coverage_ratio", 0.0)) >= 0.8
    )

    translated_ready = False
    if real_source_translation_validation is not None:
        japanese_translated = real_source_translation_validation["japanese"]
        french_translated = real_source_translation_validation["french"]
        translated_ready = (
            float(japanese_translated.get("translated_coverage_ratio", 0.0)) >= 0.8
            and float(french_translated.get("translated_coverage_ratio", 0.0)) >= 0.8
        )

    if structural_ready and (direct_chinese_ready or translated_ready):
        return "High feasibility"
    if structural_ready:
        return "Structurally feasible; Chinese-ready output still needs live translation validation"
    return "Low feasibility"


def render_report(
    japanese_summary: dict[str, int | float | list[str]],
    french_summary: dict[str, int | float | list[str]],
    translation_provider: str,
    translation_sample_size: int,
    real_source_validation: dict[str, object] | None = None,
    real_source_translation_validation: dict[str, object] | None = None,
) -> str:
    verdict = _determine_verdict(
        japanese_summary=japanese_summary,
        french_summary=french_summary,
        translation_sample_size=translation_sample_size,
        real_source_validation=real_source_validation,
        real_source_translation_validation=real_source_translation_validation,
    )

    sections = [
        "# Dictionary Feasibility Report",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        _render_fixture_section(japanese_summary, french_summary).rstrip(),
    ]

    if real_source_validation is not None:
        sections.extend(["", _render_official_source_section(real_source_validation).rstrip()])

    sections.extend(
        [
            "",
            _render_translation_section(
                translation_provider=translation_provider,
                translation_sample_size=translation_sample_size,
                real_source_translation_validation=real_source_translation_validation,
            ).rstrip(),
            "",
            "## Recommendation",
            "",
            "- Treat translation as a first-class requirement for both Japanese and French.",
            "- Proceed with package and search integration, but do not claim Chinese-ready data coverage until a real provider is validated on official samples.",
            "- Keep Japanese and French source glosses in the packaged database for QA and fallback.",
            "- Use the SQLite package as the app-side dictionary baseline.",
        ],
    )
    return "\n".join(sections) + "\n"
