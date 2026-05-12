import json

import pytest

from dict_feasibility.asxs_streaming import (
    AsxsResponsesStreamError,
    extract_responses_stream_text,
    fix_latin1_utf8_mojibake,
    parse_indexed_translation_lines,
)


def test_extract_responses_stream_text_collects_deltas_and_usage() -> None:
    lines = [
        'event: response.created',
        'data: {"type":"response.created","response":{"id":"resp_1"}}',
        'data: {"type":"response.output_text.delta","delta":"0\\t名匠\\n"}',
        'data: {"type":"response.output_text.delta","delta":"1\\t自我介绍"}',
        'data: {"type":"response.completed","response":{"usage":{"input_tokens":12,"output_tokens":8}}}',
    ]

    text, usage = extract_responses_stream_text(lines)

    assert text == "0\t名匠\n1\t自我介绍"
    assert usage == {"input_tokens": 12, "output_tokens": 8}


def test_extract_responses_stream_text_accepts_raw_bytes_without_unicode_line_splitting() -> None:
    lines = [
        b'event: response.created',
        b'data: {"type":"response.output_text.delta","delta":"0\\t\xe8\x8d\xa3\xe8\xaa\x89\xe5\xb8\x82\xe6\xb0\x91"}',
        b'data: {"type":"response.completed","response":{"usage":{"input_tokens":7,"output_tokens":4}}}',
    ]

    text, usage = extract_responses_stream_text(lines)

    assert text == "0\t荣誉市民"
    assert usage == {"input_tokens": 7, "output_tokens": 4}


def test_extract_responses_stream_text_raises_on_error_event() -> None:
    lines = [
        "event: error",
        'data: {"error":{"type":"rate_limit_error","message":"Concurrency limit exceeded"}}',
    ]

    with pytest.raises(AsxsResponsesStreamError, match="Concurrency limit exceeded"):
        extract_responses_stream_text(lines)


def test_parse_indexed_translation_lines_reads_tab_separated_rows() -> None:
    parsed = parse_indexed_translation_lines(
        "0\t名匠\n1\t自我介绍\n2\t扬名",
        expected_count=3,
    )

    assert parsed == ["名匠", "自我介绍", "扬名"]


def test_parse_indexed_translation_lines_raises_when_rows_missing() -> None:
    with pytest.raises(ValueError, match="Missing translations for indices: 1"):
        parse_indexed_translation_lines(
            "0\t名匠\n2\t扬名",
            expected_count=3,
        )


def test_fix_latin1_utf8_mojibake_repairs_proxy_text() -> None:
    broken = "".join(chr(value) for value in [229, 150, 157])

    repaired = fix_latin1_utf8_mojibake(broken)

    assert repaired == "喝"
