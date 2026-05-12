from dict_feasibility.translation import FallbackTranslationProvider


class StubProvider:
    def __init__(self, *, error_texts: set[str] | None = None, overrides: dict[str, str] | None = None) -> None:
        self.error_texts = error_texts or set()
        self.overrides = overrides or {}
        self.calls: list[str] = []

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        self.calls.append(text)
        if text in self.error_texts:
            raise RuntimeError(f"cannot translate {text}")
        return self.overrides.get(text, f"{text}-{target_lang}")

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        return [self.translate(text, source_lang, target_lang) for text in texts]


def test_fallback_provider_uses_secondary_after_primary_failure() -> None:
    primary = StubProvider(error_texts={"Bande dessinee japonaise."})
    secondary = StubProvider(overrides={"Bande dessinee japonaise.": "Japanese comics."})
    provider = FallbackTranslationProvider(primary=primary, secondary=secondary)

    assert provider.translate("Bande dessinee japonaise.", "fr", "zh") == "Japanese comics."
    assert primary.calls == ["Bande dessinee japonaise."]
    assert secondary.calls == ["Bande dessinee japonaise."]
