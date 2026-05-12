import json
from pathlib import Path
from typing import Iterator, Mapping, Sequence
import xml.etree.ElementTree as ET

from dict_feasibility.examples import serialize_example_pairs
from dict_feasibility.models import NormalizedWord
from dict_feasibility.source_paths import open_binary_maybe_gzip


def _pick_zh_gloss(sense: dict) -> str:
    for gloss in sense.get("gloss", []):
        if gloss.get("lang") in {"zho", "chi", "cmn"}:
            return gloss.get("text", "")
    return ""


def _pick_english_gloss(sense: dict) -> str:
    for gloss in sense.get("gloss", []):
        if gloss.get("lang") == "eng":
            return gloss.get("text", "")
    return ""


def _first_text(entries: Sequence[dict] | None) -> str:
    if not entries:
        return ""
    for entry in entries:
        text = entry.get("text")
        if text:
            return text
    return ""


def parse_jmdict_file(
    path: Path,
    examples_by_lemma: Mapping[str, list[dict[str, str]]] | None = None,
) -> Iterator[NormalizedWord]:
    if path.suffix == ".json":
        entries = json.loads(path.read_text(encoding="utf-8"))
        yield from _iter_json_entries(entries, examples_by_lemma)
        return

    with open_binary_maybe_gzip(path) as handle:
        context = ET.iterparse(handle, events=("end",))
        for _, entry in context:
            if entry.tag != "entry":
                continue
            normalized = _normalized_word_from_xml_entry(entry, examples_by_lemma)
            if normalized is not None:
                yield normalized
            entry.clear()


def _iter_json_entries(
    entries: Sequence[dict],
    examples_by_lemma: Mapping[str, list[dict[str, str]]] | None,
) -> Iterator[NormalizedWord]:
    for entry in entries:
        sense_entry = next(iter(entry.get("sense") or []), {})
        lemma = _first_text(entry.get("kanji")) or _first_text(entry.get("kana"))
        reading = _first_text(entry.get("kana"))
        zh_gloss = _pick_zh_gloss(sense_entry)
        english_gloss = _pick_english_gloss(sense_entry)
        example_pairs = (examples_by_lemma or {}).get(lemma, [])
        yield NormalizedWord(
            language="JA",
            lemma=lemma,
            surface=lemma,
            reading_or_ipa=reading,
            pos=", ".join(sense_entry.get("partOfSpeech", [])),
            meaning_source="jmdict",
            meaning_zh=zh_gloss,
            source_name="JMdict",
            source_entry_id=str(entry.get("id", "")),
            meaning_source_text=zh_gloss or english_gloss,
            meaning_source_lang="zh" if zh_gloss else ("en" if english_gloss else ""),
            example_sentences_json=serialize_example_pairs(example_pairs),
        )


def _normalized_word_from_xml_entry(
    entry: ET.Element,
    examples_by_lemma: Mapping[str, list[dict[str, str]]] | None,
) -> NormalizedWord | None:
    sense_entries = entry.findall("sense")
    sense_entry = sense_entries[0] if sense_entries else None
    lemma = entry.findtext("k_ele/keb") or entry.findtext("r_ele/reb") or ""
    reading = entry.findtext("r_ele/reb") or ""
    zh_gloss = _pick_zh_gloss_xml(sense_entry)
    english_gloss = _pick_english_gloss_xml(sense_entry)
    pos = ", ".join(text for text in _collect_texts(sense_entry, "pos") if text)
    example_pairs = (examples_by_lemma or {}).get(lemma, [])
    return NormalizedWord(
        language="JA",
        lemma=lemma,
        surface=lemma,
        reading_or_ipa=reading,
        pos=pos,
        meaning_source="jmdict",
        meaning_zh=zh_gloss,
        source_name="JMdict",
        source_entry_id=entry.findtext("ent_seq", default=""),
        meaning_source_text=zh_gloss or english_gloss,
        meaning_source_lang="zh" if zh_gloss else ("en" if english_gloss else ""),
        example_sentences_json=serialize_example_pairs(example_pairs),
    )


def _pick_zh_gloss_xml(sense_entry: ET.Element | None) -> str:
    return _pick_gloss_xml(sense_entry, {"zho", "chi", "cmn", "zh"})


def _pick_english_gloss_xml(sense_entry: ET.Element | None) -> str:
    return _pick_gloss_xml(sense_entry, {"eng"})


def _pick_gloss_xml(sense_entry: ET.Element | None, accepted_langs: set[str]) -> str:
    if sense_entry is None:
        return ""
    for gloss in sense_entry.findall("gloss"):
        lang = gloss.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "eng")
        text = (gloss.text or "").strip()
        if lang in accepted_langs and text:
            return text
    return ""


def _collect_texts(sense_entry: ET.Element | None, tag: str) -> list[str]:
    if sense_entry is None:
        return []
    return [(item.text or "").strip() for item in sense_entry.findall(tag)]
