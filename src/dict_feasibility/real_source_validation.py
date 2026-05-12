from __future__ import annotations

import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import BinaryIO, Iterable

import requests

JMdict_URL = "https://www.edrdg.org/pub/Nihongo/JMdict.gz"
KAIKKI_FR_URL = "https://kaikki.org/frwiktionary/raw-wiktextract-data.jsonl.gz"
_ZH_LANGS = {"zho", "chi", "cmn"}
_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _summarize_counts(
    *,
    source_key: str,
    requested_limit: int,
    sampled_entries: int,
    pronunciation_present: int,
    source_meaning_present: int,
    chinese_gloss_present: int,
    english_gloss_present: int,
    sample_terms: list[str],
) -> dict[str, object]:
    return {
        "source_key": source_key,
        "requested_limit": requested_limit,
        "sampled_entries": sampled_entries,
        "pronunciation_present": pronunciation_present,
        "source_meaning_present": source_meaning_present,
        "chinese_gloss_present": chinese_gloss_present,
        "english_gloss_present": english_gloss_present,
        "pronunciation_coverage_ratio": _ratio(pronunciation_present, sampled_entries),
        "source_meaning_coverage_ratio": _ratio(source_meaning_present, sampled_entries),
        "chinese_gloss_coverage_ratio": _ratio(chinese_gloss_present, sampled_entries),
        "english_gloss_coverage_ratio": _ratio(english_gloss_present, sampled_entries),
        "translation_required_entries": sampled_entries - chinese_gloss_present,
        "sample_terms": sample_terms,
    }


def summarize_jmdict_gz_file(path: Path, limit: int) -> dict[str, object]:
    with gzip.open(path, "rb") as handle:
        return summarize_jmdict_gz_stream(handle, limit=limit)


def summarize_jmdict_gz_stream(handle: BinaryIO, limit: int) -> dict[str, object]:
    sampled_entries = 0
    pronunciation_present = 0
    source_meaning_present = 0
    chinese_gloss_present = 0
    english_gloss_present = 0
    sample_terms: list[str] = []

    for _, elem in ET.iterparse(handle, events=("end",)):
        if elem.tag != "entry":
            continue

        lemma = elem.findtext("./k_ele/keb") or elem.findtext("./r_ele/reb") or ""
        if len(sample_terms) < 5 and lemma:
            sample_terms.append(lemma)

        if elem.findtext("./r_ele/reb"):
            pronunciation_present += 1

        glosses = list(elem.findall("./sense/gloss"))
        if glosses:
            source_meaning_present += 1

        has_zh = False
        has_eng = False
        for gloss in glosses:
            lang = gloss.attrib.get(_XML_LANG_ATTR, "eng")
            if lang in _ZH_LANGS:
                has_zh = True
            if lang == "eng":
                has_eng = True
        if has_zh:
            chinese_gloss_present += 1
        if has_eng:
            english_gloss_present += 1

        sampled_entries += 1
        elem.clear()
        if sampled_entries >= limit:
            break

    return _summarize_counts(
        source_key="jmdict",
        requested_limit=limit,
        sampled_entries=sampled_entries,
        pronunciation_present=pronunciation_present,
        source_meaning_present=source_meaning_present,
        chinese_gloss_present=chinese_gloss_present,
        english_gloss_present=english_gloss_present,
        sample_terms=sample_terms,
    )


def summarize_kaikki_gz_file(path: Path, limit: int) -> dict[str, object]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return summarize_kaikki_jsonl_lines(handle, limit=limit)


def summarize_kaikki_jsonl_lines(lines: Iterable[str], limit: int) -> dict[str, object]:
    sampled_entries = 0
    pronunciation_present = 0
    source_meaning_present = 0
    chinese_gloss_present = 0
    english_gloss_present = 0
    sample_terms: list[str] = []

    for line in lines:
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("lang_code") != "fr":
            continue

        lemma = payload.get("word", "")
        if len(sample_terms) < 5 and lemma:
            sample_terms.append(lemma)

        sounds = payload.get("sounds", [])
        if any(sound.get("ipa", "").strip() for sound in sounds):
            pronunciation_present += 1

        senses = payload.get("senses", [])
        glosses: list[str] = []
        for sense in senses:
            glosses.extend([gloss for gloss in sense.get("glosses", []) if gloss.strip()])
        if glosses:
            source_meaning_present += 1

        sampled_entries += 1
        if sampled_entries >= limit:
            break

    return _summarize_counts(
        source_key="kaikki_fr",
        requested_limit=limit,
        sampled_entries=sampled_entries,
        pronunciation_present=pronunciation_present,
        source_meaning_present=source_meaning_present,
        chinese_gloss_present=chinese_gloss_present,
        english_gloss_present=english_gloss_present,
        sample_terms=sample_terms,
    )


def fetch_remote_sample_report(limit: int) -> dict[str, object]:
    with requests.get(JMdict_URL, stream=True, timeout=120) as jmdict_response:
        jmdict_response.raise_for_status()
        jmdict_response.raw.decode_content = False
        with gzip.GzipFile(fileobj=jmdict_response.raw) as jmdict_stream:
            japanese_summary = summarize_jmdict_gz_stream(jmdict_stream, limit=limit)

    with requests.get(KAIKKI_FR_URL, stream=True, timeout=120) as kaikki_response:
        kaikki_response.raise_for_status()
        kaikki_response.raw.decode_content = False
        with gzip.GzipFile(
            fileobj=kaikki_response.raw,
            mode="rb",
        ) as kaikkI_bytes:
            french_lines = (
                raw_line.decode("utf-8")
                for raw_line in kaikkI_bytes
            )
            french_summary = summarize_kaikki_jsonl_lines(french_lines, limit=limit)

    return {
        "sample_limit": limit,
        "japanese": japanese_summary,
        "french": french_summary,
    }
