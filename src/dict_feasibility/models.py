from dataclasses import asdict, dataclass


@dataclass(slots=True)
class NormalizedWord:
    language: str
    lemma: str
    surface: str
    reading_or_ipa: str
    pos: str
    meaning_source: str
    meaning_zh: str
    source_name: str
    source_entry_id: str
    meaning_source_text: str = ""
    meaning_source_lang: str = ""
    example_sentences_json: str = "[]"

    def to_record(self) -> dict[str, str]:
        return asdict(self)
