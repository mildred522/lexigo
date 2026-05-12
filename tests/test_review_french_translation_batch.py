import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from review_french_translation_batch import review_french_translation_batch


def _make_word(
    *,
    lemma: str,
    meaning_source_text: str,
    meaning_zh: str,
    source_entry_id: str | None = None,
) -> dict[str, str]:
    return {
        "language": "FR",
        "lemma": lemma,
        "surface": lemma,
        "reading_or_ipa": "",
        "pos": "noun",
        "meaning_source": "kaikki",
        "meaning_zh": meaning_zh,
        "source_name": "Kaikki French Wiktionary",
        "source_entry_id": source_entry_id or lemma,
        "meaning_source_text": meaning_source_text,
        "meaning_source_lang": "fr",
        "example_sentences_json": "[]",
    }


def test_review_french_translation_batch_flags_high_risk_entries(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    rows = [
        _make_word(
            lemma="siège",
            meaning_source_text="Première personne du singulier du présent de l’indicatif de siéger.",
            meaning_zh="我 present indicative of to sit",
        ),
        _make_word(
            lemma="mardi",
            meaning_source_text="Le jour du mardi.",
            meaning_zh="星期二。",
        ),
        _make_word(
            lemma="ouvrage",
            meaning_source_text="Première personne du singulier du présent de l’indicatif du verbe ouvrager.",
            meaning_zh="第一人称单数的现在时动词“ouvrager”",
        ),
        _make_word(
            lemma="computer",
            meaning_source_text="Supputer.",
            meaning_zh="",
        ),
    ]
    input_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = review_french_translation_batch(input_path)

    assert report["total_words"] == 4
    assert report["flagged_words"] == 3
    assert report["reason_counts"] == {
        "contains_ascii_letters": 2,
        "empty_translation": 1,
        "grammar_gloss_leftover_latin": 1,
        "template_not_in_chinese_form": 1,
    }
    assert [item["lemma"] for item in report["flagged_entries"]] == ["siège", "ouvrage", "computer"]
    assert report["flagged_entries"][0]["reasons"] == [
        "contains_ascii_letters",
        "grammar_gloss_leftover_latin",
        "template_not_in_chinese_form",
    ]


def test_review_french_translation_batch_flags_template_not_in_chinese_form(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    row = _make_word(
        lemma="siege",
        meaning_source_text="Premiere personne du singulier du present de l'indicatif de sieger.",
        meaning_zh="\u6211 present indicative of to sit",
    )
    input_path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")

    report = review_french_translation_batch(input_path)

    assert report["flagged_words"] == 1
    assert report["reason_counts"]["template_not_in_chinese_form"] == 1


def test_review_french_translation_batch_does_not_require_template_for_ordinary_grammar_definition(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "batch.jsonl"
    row = _make_word(
        lemma="les",
        meaning_source_text="Pronom personnel de la troisieme personne du pluriel accusatif.",
        meaning_zh="\u7b2c\u4e09\u4eba\u79f0\u590d\u6570\u5bbe\u683c\u4eba\u79f0\u4ee3\u8bcd\u3002",
    )
    input_path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")

    report = review_french_translation_batch(input_path)

    assert report["flagged_words"] == 0


def test_review_french_translation_batch_allows_known_latin_notation(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    rows = [
        _make_word(
            lemma="au",
            meaning_source_text="Langue torricelli parlee en Papouasie-Nouvelle-Guinee (code ISO 639-3 : avt).",
            meaning_zh="\u963f\u97e6\u7279\u8bed\uff08ISO 639-3\u7f16\u7801\uff1aavt\uff09\u5728\u5df4\u5e03\u4e9a\u65b0\u51e0\u5185\u4e9a\u4f7f\u7528",
        ),
        _make_word(
            lemma="B",
            meaning_source_text="Bleu du RVB.",
            meaning_zh="RGB\u7684\u84dd\u8272",
        ),
        _make_word(
            lemma="B",
            meaning_source_text="Dans la musique de jazz, element d'une grille d'accords AABA.",
            meaning_zh="B\u6bb5\uff0c\u7235\u58eb\u4e50\u4e2d\u548c\u5f26\u6846\u67b6\u7684\u4e00\u90e8\u5206\uff0c\u901a\u5e38\u5448AABA\u5f62\u5f0f\u3002",
        ),
        _make_word(
            lemma="de",
            meaning_source_text="Utilise dans certaines locutions d'origine latine, comme de facto.",
            meaning_zh="\u7528\u4e8e\u67d0\u4e9b\u6e90\u81ea\u62c9\u4e01\u8bed\u7684\u8bcd\u7ec4\u4e2d\uff0c\u5982de facto\u3002",
        ),
        _make_word(
            lemma="lieu",
            meaning_source_text="Nom donne a deux genres de poissons osseux de mer.",
            meaning_zh=(
                "\u5bf9\u4e24\u7c7b\u6d77\u751f\u786c\u9aa8\u9c7c\u7684\u79f0\u547c"
                "\uff08Theragra spp. \u548c Pollachius spp.\uff09\u3002"
            ),
        ),
    ]
    input_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = review_french_translation_batch(input_path)

    assert report["flagged_words"] == 0


def test_review_french_translation_batch_still_flags_english_residue(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    row = _make_word(
        lemma="texte",
        meaning_source_text="Suite ordonnee de mots ecrits.",
        meaning_zh="\u5e8f\u5217 written words",
    )
    input_path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")

    report = review_french_translation_batch(input_path)

    assert report["flagged_words"] == 1
    assert report["reason_counts"]["contains_ascii_letters"] == 1


def test_review_french_translation_batch_allows_translated_uncertainty_terms(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    row = _make_word(
        lemma="indefini",
        meaning_source_text="Dont la fin ne peut pas etre determinee.",
        meaning_zh="\u7ec8\u70b9\u6216\u8fb9\u754c\u4e0d\u786e\u5b9a\u3001\u65e0\u6cd5\u786e\u5b9a\u7684\u3002",
    )
    input_path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")

    report = review_french_translation_batch(input_path)

    assert report["flagged_words"] == 0
