from typing import Iterable

from dict_feasibility.models import NormalizedWord


def summarize_words(words: Iterable[NormalizedWord]) -> dict[str, int | float | list[str]]:
    total_words = 0
    missing_pronunciation = 0
    missing_meaning = 0
    missing_source_meaning = 0
    sample_lemmas: list[str] = []

    for word in words:
        total_words += 1
        if not word.reading_or_ipa.strip():
            missing_pronunciation += 1
        if not word.meaning_zh.strip():
            missing_meaning += 1
        if not word.meaning_source_text.strip():
            missing_source_meaning += 1
        if word.lemma and len(sample_lemmas) < 5:
            sample_lemmas.append(word.lemma)

    if total_words == 0:
        pronunciation_coverage_ratio = 0.0
        meaning_coverage_ratio = 0.0
        source_meaning_coverage_ratio = 0.0
    else:
        pronunciation_coverage_ratio = (
            total_words - missing_pronunciation
        ) / total_words
        meaning_coverage_ratio = (total_words - missing_meaning) / total_words
        source_meaning_coverage_ratio = (total_words - missing_source_meaning) / total_words

    return {
        "total_words": total_words,
        "missing_pronunciation": missing_pronunciation,
        "missing_meaning": missing_meaning,
        "missing_source_meaning": missing_source_meaning,
        "pronunciation_coverage_ratio": pronunciation_coverage_ratio,
        "meaning_coverage_ratio": meaning_coverage_ratio,
        "source_meaning_coverage_ratio": source_meaning_coverage_ratio,
        "sample_lemmas": sample_lemmas,
    }
