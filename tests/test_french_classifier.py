import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from french_classifier import classify_french_entry


def test_classify_french_entry_returns_blocked_for_missing_source() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="cinquante",
        surface="cinquante",
        reading_or_ipa="",
        pos="num",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="cinquante",
        meaning_source_text="",
        meaning_source_lang="",
    )

    assert classify_french_entry(word) == "blocked"


def test_classify_french_entry_returns_rule_based_for_morphology_template() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="si\u00e8ge",
        surface="si\u00e8ge",
        reading_or_ipa="",
        pos="verb",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="si\u00e8ge",
        meaning_source_text=(
            "Premi\u00e8re personne du singulier du pr\u00e9sent de "
            "l\u2019indicatif de si\u00e9ger."
        ),
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "rule_based"


def test_classify_french_entry_returns_rule_based_for_simple_feminine_template() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="une",
        surface="une",
        reading_or_ipa="",
        pos="determiner",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="une",
        meaning_source_text="F\u00e9minin de un.",
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "rule_based"


def test_classify_french_entry_returns_local_candidate_for_other_glosses() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="mardi",
        surface="mardi",
        reading_or_ipa="",
        pos="noun",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="mardi",
        meaning_source_text="Le jour du mardi.",
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "local_candidate"


def test_classify_french_entry_does_not_treat_lexical_contraction_as_rule_based() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="rictus",
        surface="rictus",
        reading_or_ipa="",
        pos="noun",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="rictus",
        meaning_source_text="Contraction de la bouche, grimace des levres et des joues.",
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "local_candidate"


def test_classify_french_entry_does_not_treat_embedded_alphabet_phrase_as_rule_based() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="acrophonie",
        surface="acrophonie",
        reading_or_ipa="",
        pos="noun",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="acrophonie",
        meaning_source_text="Principe selon lequel un signe represente la lettre de l'alphabet.",
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "local_candidate"


def test_classify_french_entry_returns_rule_based_for_alphabet_letter_template() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="an",
        surface="an",
        reading_or_ipa="",
        pos="letter",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="an",
        meaning_source_text="Premi\u00e8re lettre de l\u2019alphabet g\u00e9orgien, ka.",
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "rule_based"
