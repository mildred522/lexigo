import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from dict_feasibility.models import NormalizedWord
from dict_feasibility.translation import (
    SupplementalTranslationOverride,
    TranslationCache,
    TranslationProvider,
    find_supplemental_translation_override,
)


def iter_normalized_words(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield NormalizedWord(**json.loads(line))


def load_normalized_words(path: Path) -> list[NormalizedWord]:
    return list(iter_normalized_words(path))


def write_normalized_words(path: Path, words: Iterable[NormalizedWord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for word in words:
            handle.write(json.dumps(word.to_record(), ensure_ascii=False) + "\n")


def append_normalized_words(path: Path, words: Iterable[NormalizedWord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for word in words:
            handle.write(json.dumps(word.to_record(), ensure_ascii=False) + "\n")


def write_summary(path: Path, summary: dict[str, int | float | list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def run_translation_job(
    words: Iterable[NormalizedWord],
    *,
    provider: TranslationProvider,
    cache: TranslationCache,
    target_lang: str = "zh",
    supplemental_overrides: list[SupplementalTranslationOverride] | None = None,
    batch_size: int = 1,
    checkpoint_every: int = 0,
    checkpoint_output_path: Path | None = None,
    checkpoint_report_path: Path | None = None,
) -> tuple[list[NormalizedWord], dict[str, int | list[str]]]:
    words_list = list(words)
    total_words = len(words_list)
    if checkpoint_every <= 0:
        return run_translation_pipeline(
            words_list,
            provider=provider,
            cache=cache,
            target_lang=target_lang,
            supplemental_overrides=supplemental_overrides,
            batch_size=batch_size,
        )

    if checkpoint_output_path is not None:
        checkpoint_output_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_output_path.write_text("", encoding="utf-8")

    translated_words: list[NormalizedWord] = []
    summary: dict[str, int | list[str]] = {
        "total_words": total_words,
        "already_translated": 0,
        "translated_now": 0,
        "missing_source_text": 0,
        "copied_directly": 0,
        "cache_hits": 0,
        "translation_errors": 0,
        "failed_terms": [],
    }

    for start in range(0, total_words, checkpoint_every):
        chunk = words_list[start : start + checkpoint_every]
        translated_chunk, chunk_summary = run_translation_pipeline(
            chunk,
            provider=provider,
            cache=cache,
            target_lang=target_lang,
            supplemental_overrides=supplemental_overrides,
            batch_size=batch_size,
        )
        translated_words.extend(translated_chunk)
        _merge_summary(summary, chunk_summary)

        if checkpoint_output_path is not None:
            append_normalized_words(checkpoint_output_path, translated_chunk)
        if checkpoint_report_path is not None:
            write_summary(
                checkpoint_report_path,
                build_progress_summary(
                    summary,
                    processed_words=min(start + len(chunk), total_words),
                    total_words=total_words,
                ),
            )

    return translated_words, summary


def run_translation_pipeline(
    words: Iterable[NormalizedWord],
    *,
    provider: TranslationProvider,
    cache: TranslationCache,
    target_lang: str = "zh",
    supplemental_overrides: list[SupplementalTranslationOverride] | None = None,
    batch_size: int = 1,
) -> tuple[list[NormalizedWord], dict[str, int | list[str]]]:
    translated_words: list[NormalizedWord | None] = []
    total_words = 0
    already_translated = 0
    translated_now = 0
    missing_source_text = 0
    copied_directly = 0
    cache_hits = 0
    translation_errors = 0
    failed_terms: list[str] = []
    overrides = supplemental_overrides or []
    pending_by_source_lang: dict[str, list[dict[str, object]]] = {}
    pending_lookup: dict[tuple[str, str, str], dict[str, object]] = {}

    def flush_pending(source_lang: str) -> None:
        nonlocal translation_errors, translated_now
        pending = pending_by_source_lang.get(source_lang)
        if not pending:
            return
        texts = [str(item["text"]) for item in pending]
        try:
            if hasattr(provider, "translate_batch") and len(texts) > 1:
                translations = provider.translate_batch(texts, source_lang, target_lang)
            else:
                translations = [provider.translate(text, source_lang, target_lang) for text in texts]
        except Exception:
            translations = []
            for item in pending:
                try:
                    translated_text = provider.translate(item["text"], source_lang, target_lang)
                except Exception:
                    translation_errors += len(item["waiters"])
                    failed_terms.extend(word.lemma for _, word in item["waiters"])
                    for index, word in item["waiters"]:
                        translated_words[index] = word
                    pending_lookup.pop(item["cache_key"], None)
                    continue
                translations.append((item, translated_text))
            for item, translated_text in translations:
                translated_text = translated_text.strip()
                cache_key = item["cache_key"]
                cache.set(item["text"], source_lang, target_lang, translated_text)
                for index, word in item["waiters"]:
                    translated_words[index] = replace(word, meaning_zh=translated_text)
                    translated_now += 1
                pending_lookup.pop(cache_key, None)
            pending_by_source_lang[source_lang] = []
            return

        for item, translated_text in zip(pending, translations):
            translated_text = translated_text.strip()
            cache_key = item["cache_key"]
            cache.set(item["text"], source_lang, target_lang, translated_text)
            for index, word in item["waiters"]:
                translated_words[index] = replace(word, meaning_zh=translated_text)
                translated_now += 1
            pending_lookup.pop(cache_key, None)
        pending_by_source_lang[source_lang] = []

    for word in words:
        total_words += 1
        translated_words.append(None)
        current_index = len(translated_words) - 1
        if word.meaning_zh.strip():
            already_translated += 1
            translated_words[current_index] = word
            continue

        override_meaning = find_supplemental_translation_override(
            word.language,
            word.lemma,
            word.reading_or_ipa,
            word.source_entry_id,
            overrides,
        )
        if override_meaning is not None:
            translated_now += 1
            translated_words[current_index] = replace(word, meaning_zh=override_meaning)
            continue

        if not word.meaning_source_text.strip():
            missing_source_text += 1
            translated_words[current_index] = word
            continue

        if word.meaning_source_lang == target_lang:
            copied_directly += 1
            translated_now += 1
            translated_words[current_index] = replace(word, meaning_zh=word.meaning_source_text)
            continue

        cache_key = (word.meaning_source_text, word.meaning_source_lang, target_lang)
        cached = cache.get(*cache_key)
        if cached is not None:
            cache_hits += 1
            translated_now += 1
            translated_words[current_index] = replace(word, meaning_zh=cached)
            continue

        if cache_key in pending_lookup:
            cache_hits += 1
            pending_lookup[cache_key]["waiters"].append((current_index, word))
            continue

        source_lang = word.meaning_source_lang
        pending_item = {
            "text": word.meaning_source_text,
            "cache_key": cache_key,
            "waiters": [(current_index, word)],
        }
        pending_lookup[cache_key] = pending_item
        pending_by_source_lang.setdefault(source_lang, []).append(pending_item)
        if len(pending_by_source_lang[source_lang]) >= max(1, batch_size):
            flush_pending(source_lang)

    for source_lang in list(pending_by_source_lang):
        flush_pending(source_lang)

    summary = {
        "total_words": total_words,
        "already_translated": already_translated,
        "translated_now": translated_now,
        "missing_source_text": missing_source_text,
        "copied_directly": copied_directly,
        "cache_hits": cache_hits,
        "translation_errors": translation_errors,
        "failed_terms": failed_terms,
    }
    return [word for word in translated_words if word is not None], summary


def build_progress_summary(
    summary: dict[str, int | list[str]],
    *,
    processed_words: int,
    total_words: int,
) -> dict[str, int | float | list[str]]:
    percent_complete = 100.0 if total_words == 0 else round((processed_words / total_words) * 100, 2)
    progress = dict(summary)
    progress["processed_words"] = processed_words
    progress["total_words"] = total_words
    progress["remaining_words"] = max(total_words - processed_words, 0)
    progress["percent_complete"] = percent_complete
    return progress


def _merge_summary(
    target: dict[str, int | list[str]],
    chunk: dict[str, int | list[str]],
) -> None:
    for key in (
        "already_translated",
        "translated_now",
        "missing_source_text",
        "copied_directly",
        "cache_hits",
        "translation_errors",
    ):
        target[key] = int(target[key]) + int(chunk[key])
    target["failed_terms"] = list(target["failed_terms"]) + list(chunk["failed_terms"])
