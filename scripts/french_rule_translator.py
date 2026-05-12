import re
import sys
from dataclasses import replace
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.models import NormalizedWord

_LEMMA_RE = r"(?P<lemma>.+?)"
_ARTICLE_RE = r"(?:du|de la|de l['\u2019]|d['\u2019]|de)"

_FIRST_PERSON_PRESENT_RE = re.compile(
    rf"^Premi(?:\u00e8|e)re personne du singulier du pr(?:\u00e9|e)sent de "
    rf"l['\u2019]indicatif {_ARTICLE_RE} {_LEMMA_RE}\.$",
    re.IGNORECASE,
)
_PLURAL_OF_RE = re.compile(rf"^Pluriel de {_LEMMA_RE}\.$", re.IGNORECASE)
_GENDER_NUMBER_OF_RE = re.compile(
    rf"^(?P<gender>F(?:\u00e9|e)minin|Masculin) (?P<number>singulier|pluriel) de {_LEMMA_RE}\.$",
    re.IGNORECASE,
)
_GENDER_OF_RE = re.compile(
    rf"^(?P<gender>F(?:\u00e9|e)minin|Masculin) de {_LEMMA_RE}\.$",
    re.IGNORECASE,
)
_PARTICIPLE_RE = re.compile(
    rf"^Participe (?P<kind>pr(?:\u00e9|e)sent|pass(?:\u00e9|e)) {_ARTICLE_RE} {_LEMMA_RE}\.$",
    re.IGNORECASE,
)
_ALPHABET_LETTER_RE = re.compile(
    r"^(?P<letter_ordinal>Premi(?:\u00e8|e)re|\w+(?:\u00e8|e)me) lettre de l['\u2019]alphabet "
    r"(?P<alphabet>g[\u00e9e]orgien), (?P<name>.+?)\.$",
    re.IGNORECASE,
)
_ALPHABET_LETTER_AND_VOWEL_RE = re.compile(
    r"^(?P<letter_ordinal>\w+(?:\u00e8|e)me) lettre et (?P<vowel_ordinal>\w+(?:\u00e8|e)me) "
    r"voyelle de l['\u2019]alphabet(?: \((?P<case>majuscule|minuscule)\))?\.$",
    re.IGNORECASE,
)
_ORDINAL_ZH = {
    "premiere": "\u7b2c\u4e00",
    "premi\u00e8re": "\u7b2c\u4e00",
    "quatrieme": "\u7b2c\u56db",
    "quatri\u00e8me": "\u7b2c\u56db",
    "quatorzieme": "\u7b2c\u5341\u56db",
    "quatorzi\u00e8me": "\u7b2c\u5341\u56db",
    "quinzieme": "\u7b2c\u5341\u4e94",
    "quinzi\u00e8me": "\u7b2c\u5341\u4e94",
    "vingtieme": "\u7b2c\u4e8c\u5341",
    "vingti\u00e8me": "\u7b2c\u4e8c\u5341",
}
_ALPHABET_ZH = {
    "georgien": "\u683c\u9c81\u5409\u4e9a",
    "g\u00e9orgien": "\u683c\u9c81\u5409\u4e9a",
}
_CASE_ZH = {
    "majuscule": "\u5927\u5199",
    "minuscule": "\u5c0f\u5199",
}


def translate_french_rule_gloss(text: str) -> str | None:
    source = " ".join(text.strip().split())

    match = _FIRST_PERSON_PRESENT_RE.match(source)
    if match:
        return f"\u52a8\u8bcd\u201c{match.group('lemma')}\u201d\u7684\u76f4\u9648\u5f0f\u73b0\u5728\u65f6\u7b2c\u4e00\u4eba\u79f0\u5355\u6570\u5f62\u5f0f"

    match = _PLURAL_OF_RE.match(source)
    if match:
        return f"{match.group('lemma')} \u7684\u590d\u6570\u5f62\u5f0f"

    match = _GENDER_NUMBER_OF_RE.match(source)
    if match:
        gender = "\u9634\u6027" if match.group("gender").lower().startswith(("f", "fé")) else "\u9633\u6027"
        number = "\u5355\u6570" if match.group("number").lower() == "singulier" else "\u590d\u6570"
        return f"{match.group('lemma')} \u7684{gender}{number}\u5f62\u5f0f"

    match = _GENDER_OF_RE.match(source)
    if match:
        gender = "\u9634\u6027" if match.group("gender").lower().startswith(("f", "fé")) else "\u9633\u6027"
        return f"{match.group('lemma')} \u7684{gender}\u5f62\u5f0f"

    match = _PARTICIPLE_RE.match(source)
    if match:
        kind = "\u73b0\u5728\u5206\u8bcd" if match.group("kind").lower().startswith(("pr", "pré")) else "\u8fc7\u53bb\u5206\u8bcd"
        return f"\u52a8\u8bcd\u201c{match.group('lemma')}\u201d\u7684{kind}"

    match = _ALPHABET_LETTER_RE.match(source)
    if match:
        ordinal = _translate_ordinal(match.group("letter_ordinal"))
        alphabet = _ALPHABET_ZH.get(match.group("alphabet").lower(), match.group("alphabet"))
        return f"{alphabet}\u5b57\u6bcd\u8868\u7684{ordinal}\u4e2a\u5b57\u6bcd {match.group('name')}"

    match = _ALPHABET_LETTER_AND_VOWEL_RE.match(source)
    if match:
        letter_ordinal = _translate_ordinal(match.group("letter_ordinal"))
        vowel_ordinal = _translate_ordinal(match.group("vowel_ordinal"))
        suffix = ""
        if match.group("case"):
            suffix = f"\uff08{_CASE_ZH.get(match.group('case').lower(), match.group('case'))}\uff09"
        return f"\u5b57\u6bcd\u8868\u7684{letter_ordinal}\u4e2a\u5b57\u6bcd\u3001{vowel_ordinal}\u4e2a\u5143\u97f3{suffix}"

    return None


def _translate_ordinal(value: str) -> str:
    return _ORDINAL_ZH.get(value.lower(), value)


def apply_french_rule_translation(word: NormalizedWord) -> NormalizedWord:
    translated = translate_french_rule_gloss(word.meaning_source_text)
    if translated is None:
        return word
    return replace(word, meaning_zh=translated)
