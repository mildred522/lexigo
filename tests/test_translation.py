import json
import subprocess
import sys
from pathlib import Path

import pytest

from dict_feasibility.translation import (
    LlamaCppChatTranslationProvider,
    MemoryTranslationCache,
    OpenAIResponsesTranslationProvider,
    build_translation_provider,
    translate_with_cache,
)


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        self.calls += 1
        return f"{text}-zh"


class FakeBatchProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
        self.batch_calls = 0

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        self.batch_calls += 1
        return [f"{text}-zh" for text in texts]


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def post(self, url: str, *, headers: dict, json: dict, timeout: int) -> FakeResponse:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        return FakeResponse(self.payload)


def test_translate_with_cache_calls_provider_once() -> None:
    provider = FakeProvider()
    cache = MemoryTranslationCache()

    first = translate_with_cache(cache, provider, "hello", "fr", "zh")
    second = translate_with_cache(cache, provider, "hello", "fr", "zh")

    assert first == "hello-zh"
    assert second == "hello-zh"
    assert provider.calls == 1


_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_translate_with_cache_distinct_language_keys() -> None:
    provider = FakeProvider()
    cache = MemoryTranslationCache()

    translate_with_cache(cache, provider, "hello", "fr", "zh")
    translate_with_cache(cache, provider, "hello", "fr", "ja")
    translate_with_cache(cache, provider, "hello", "en", "zh")

    assert provider.calls == 3


def test_openai_provider_posts_responses_request() -> None:
    session = FakeSession(
        {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "你好",
                        }
                    ],
                }
            ]
        }
    )
    provider = OpenAIResponsesTranslationProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="gpt-test",
        session=session,
    )

    translated = provider.translate("salutation de bienvenue", "fr", "zh")

    assert translated == "你好"
    assert session.calls
    call = session.calls[0]
    assert call["url"] == "https://example.test/v1/responses"
    assert call["headers"]["Authorization"] == "Bearer test-key"
    assert call["json"]["model"] == "gpt-test"
    assert call["json"]["input"].startswith("Translate the following text")
    assert call["json"]["reasoning"] == {"effort": "none"}
    assert call["json"]["text"] == {"verbosity": "low"}


def test_openai_provider_raises_when_output_text_missing() -> None:
    provider = OpenAIResponsesTranslationProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="gpt-test",
        session=FakeSession({"output": []}),
    )

    with pytest.raises(ValueError, match="No translated text returned"):
        provider.translate("to drink", "en", "zh")


def test_translate_batch_uses_single_request_and_preserves_order() -> None:
    session = FakeSession(
        {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "items": [
                                        {"index": 0, "translation": "你好"},
                                        {"index": 1, "translation": "谢谢"},
                                    ]
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                }
            ]
        }
    )
    provider = OpenAIResponsesTranslationProvider(
        api_key="test-key",
        base_url="https://example.test/v1",
        model="gpt-5-mini",
        session=session,
    )

    translated = provider.translate_batch(
        ["salutation de bienvenue", "remerciement"],
        "fr",
        "zh",
    )

    assert translated == ["你好", "谢谢"]
    assert len(session.calls) == 1
    assert "Return a JSON object" in session.calls[0]["json"]["input"]
    assert session.calls[0]["json"]["reasoning"] == {"effort": "none"}
    assert session.calls[0]["json"]["text"] == {"verbosity": "low"}


def test_llama_cpp_provider_posts_chat_completions_request() -> None:
    session = FakeSession(
        {
            "choices": [
                {
                    "message": {
                        "content": "立体几何",
                    }
                }
            ]
        }
    )
    provider = LlamaCppChatTranslationProvider(
        api_key="unused",
        base_url="http://127.0.0.1:8080/v1",
        model="qwen2.5:3b",
        session=session,
    )

    translated = provider.translate("solid geometry", "en", "zh")

    assert translated == "立体几何"
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == "http://127.0.0.1:8080/v1/chat/completions"
    assert call["json"]["model"] == "qwen2.5:3b"
    assert call["json"]["temperature"] == 0
    assert call["json"]["messages"][0]["role"] == "system"
    assert "Return only the translation" in call["json"]["messages"][0]["content"]
    assert call["json"]["messages"][1]["role"] == "user"
    assert "solid geometry" in call["json"]["messages"][1]["content"]


def test_llama_cpp_provider_raises_when_message_missing() -> None:
    provider = LlamaCppChatTranslationProvider(
        api_key="unused",
        base_url="http://127.0.0.1:8080/v1",
        model="qwen2.5:3b",
        session=FakeSession({"choices": []}),
    )

    with pytest.raises(ValueError, match="No translated text returned"):
        provider.translate("solid geometry", "en", "zh")


def test_build_translation_provider_supports_llama_cpp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:8080/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "unused")
    provider = build_translation_provider(
        provider_name="llama_cpp",
        glossary_path=None,
        model="qwen2.5:3b",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
    )

    assert isinstance(provider, LlamaCppChatTranslationProvider)


def test_translate_meanings_script_runs() -> None:
    script = _REPO_ROOT / "scripts" / "translate_meanings.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "translation cache ready" in result.stdout
