import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from french_rule_translator import apply_french_rule_translation, translate_french_rule_gloss


def test_translate_french_rule_gloss_handles_first_person_present() -> None:
    assert (
        translate_french_rule_gloss(
            "Premi\u00e8re personne du singulier du pr\u00e9sent de l\u2019indicatif de si\u00e9ger."
        )
        == "\u52a8\u8bcd\u201csi\u00e9ger\u201d\u7684\u76f4\u9648\u5f0f\u73b0\u5728\u65f6\u7b2c\u4e00\u4eba\u79f0\u5355\u6570\u5f62\u5f0f"
    )


def test_translate_french_rule_gloss_handles_plural_of() -> None:
    assert translate_french_rule_gloss("Pluriel de anglaise.") == "anglaise \u7684\u590d\u6570\u5f62\u5f0f"


def test_translate_french_rule_gloss_handles_simple_feminine_of() -> None:
    assert translate_french_rule_gloss("F\u00e9minin de un.") == "un \u7684\u9634\u6027\u5f62\u5f0f"


def test_translate_french_rule_gloss_handles_georgian_alphabet_letter() -> None:
    assert (
        translate_french_rule_gloss("Premi\u00e8re lettre de l\u2019alphabet g\u00e9orgien, ka.")
        == "\u683c\u9c81\u5409\u4e9a\u5b57\u6bcd\u8868\u7684\u7b2c\u4e00\u4e2a\u5b57\u6bcd ka"
    )


def test_translate_french_rule_gloss_handles_alphabet_letter_and_vowel() -> None:
    assert (
        translate_french_rule_gloss("Quinzi\u00e8me lettre et quatri\u00e8me voyelle de l\u2019alphabet (majuscule).")
        == "\u5b57\u6bcd\u8868\u7684\u7b2c\u5341\u4e94\u4e2a\u5b57\u6bcd\u3001\u7b2c\u56db\u4e2a\u5143\u97f3\uff08\u5927\u5199\uff09"
    )


def test_translate_french_rule_gloss_returns_none_for_ordinary_definition() -> None:
    assert translate_french_rule_gloss("Contraction de la bouche, grimace des levres.") is None


def test_apply_french_rule_translation_sets_meaning_zh() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="anglaises",
        surface="anglaises",
        reading_or_ipa="",
        pos="adj",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="anglaises",
        meaning_source_text="Pluriel de anglaise.",
        meaning_source_lang="fr",
    )

    translated = apply_french_rule_translation(word)

    assert translated.meaning_zh == "anglaise \u7684\u590d\u6570\u5f62\u5f0f"
    assert word.meaning_zh == ""
