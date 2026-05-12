from __future__ import annotations

import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import BinaryIO, Iterable

import requests

from dict_feasibility.models import NormalizedWord
from dict_feasibility.real_source_validation import JMdict_URL, KAIKKI_FR_URL
from dict_feasibility.translation import TranslationCache, TranslationProvider
from dict_feasibility.translation_pipeline import run_translation_pipeline

_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"
_ZH_LANGS = {"zho", "chi", "cmn"}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def sample_jmdict_words_from_gz_file(path: Path, limit: int) -> list[NormalizedWord]:
    with gzip.open(path, "rb") as handle:
        return sample_jmdict_words_from_gz_stream(handle, limit=limit)


def sample_jmdict_words_from_gz_stream(handle: BinaryIO, limit: int) -> list[NormalizedWord]:
    results: list[NormalizedWord] = []
    for _, elem in ET.iterparse(handle, events=("end",)):
        if elem.tag != "entry":
            continue

        lemma = elem.findtext("./k_ele/keb") or elem.findtext("./r_ele/reb") or ""
        reading = elem.findtext("./r_ele/reb") or ""
        source_text = ""
        source_lang = ""
        zh_text = ""
        for gloss in elem.findall("./sense/gloss"):
            lang = gloss.attrib.get(_XML_LANG_ATTR, "eng")
            text = (gloss.text or "").strip()
            if not text:
                continue
            if not source_text and lang == "eng":
                source_text = text
                source_lang = "en"
            if lang in _ZH_LANGS and not zh_text:
                zh_text = text
        if zh_text:
            source_text = zh_text
            source_lang = "zh"

        results.append(
            NormalizedWord(
                language="JA",
                lemma=lemma,
                surface=lemma,
                reading_or_ipa=reading,
                pos="",
                meaning_source="jmdict",
                meaning_zh=zh_text,
                source_name="JMdict",
                source_entry_id=elem.findtext("./ent_seq") or lemma,
                meaning_source_text=source_text,
                meaning_source_lang=source_lang,
            )
        )
        elem.clear()
        if len(results) >= limit:
            break
    return results


def sample_kaikki_words_from_gz_file(path: Path, limit: int) -> list[NormalizedWord]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return sample_kaikki_words_from_lines(handle, limit=limit)


def sample_kaikki_words_from_lines(lines: Iterable[str], limit: int) -> list[NormalizedWord]:
    results: list[NormalizedWord] = []
    for line in lines:
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("lang_code") != "fr":
            continue

        ipa = ""
        for sound in payload.get("sounds", []):
            ipa = sound.get("ipa", "")
            if ipa:
                break
        gloss = ""
        for sense in payload.get("senses", []):
            for item in sense.get("glosses", []):
                text = item.strip()
                if text:
                    gloss = text
                    break
            if gloss:
                break

        results.append(
            NormalizedWord(
                language="FR",
                lemma=payload.get("word", ""),
                surface=payload.get("word", ""),
                reading_or_ipa=ipa,
                pos=payload.get("pos", ""),
                meaning_source="kaikki",
                meaning_zh="",
                source_name="Kaikki French Wiktionary",
                source_entry_id=payload.get("word", ""),
                meaning_source_text=gloss,
                meaning_source_lang="fr" if gloss else "",
            )
        )
        if len(results) >= limit:
            break
    return results


def summarize_translation_validation(
    *,
    language: str,
    requested_limit: int,
    translated_words: list[NormalizedWord],
    pipeline_summary: dict[str, int | list[str]],
) -> dict[str, object]:
    sampled_entries = int(pipeline_summary["total_words"])
    translated_entries = int(pipeline_summary["already_translated"]) + int(
        pipeline_summary["translated_now"]
    )
    return {
        "language": language,
        "requested_limit": requested_limit,
        "sampled_entries": sampled_entries,
        "translated_entries": translated_entries,
        "translated_coverage_ratio": _ratio(translated_entries, sampled_entries),
        "already_translated": int(pipeline_summary["already_translated"]),
        "translated_now": int(pipeline_summary["translated_now"]),
        "cache_hits": int(pipeline_summary["cache_hits"]),
        "translation_errors": int(pipeline_summary["translation_errors"]),
        "failed_terms": list(pipeline_summary["failed_terms"]),
        "sample_pairs": [
            {
                "lemma": word.lemma,
                "source_text": word.meaning_source_text,
                "meaning_zh": word.meaning_zh,
            }
            for word in translated_words[:5]
        ],
    }


def fetch_remote_translation_validation_report(
    *,
    limit: int,
    provider: TranslationProvider,
    cache: TranslationCache,
) -> dict[str, object]:
    with requests.get(JMdict_URL, stream=True, timeout=120) as jmdict_response:
        jmdict_response.raise_for_status()
        jmdict_response.raw.decode_content = False
        with gzip.GzipFile(fileobj=jmdict_response.raw) as jmdict_stream:
            japanese_words = sample_jmdict_words_from_gz_stream(jmdict_stream, limit=limit)

    with requests.get(KAIKKI_FR_URL, stream=True, timeout=120) as kaikki_response:
        kaikki_response.raise_for_status()
        kaikki_response.raw.decode_content = False
        with gzip.GzipFile(fileobj=kaikki_response.raw, mode="rb") as kaikki_bytes:
            french_lines = (line.decode("utf-8") for line in kaikki_bytes)
            french_words = sample_kaikki_words_from_lines(french_lines, limit=limit)

    translated_japanese, japanese_summary = run_translation_pipeline(
        japanese_words,
        provider=provider,
        cache=cache,
    )
    translated_french, french_summary = run_translation_pipeline(
        french_words,
        provider=provider,
        cache=cache,
    )

    return {
        "sample_limit": limit,
        "japanese": summarize_translation_validation(
            language="JA",
            requested_limit=limit,
            translated_words=translated_japanese,
            pipeline_summary=japanese_summary,
        ),
        "french": summarize_translation_validation(
            language="FR",
            requested_limit=limit,
            translated_words=translated_french,
            pipeline_summary=french_summary,
        ),
    }
