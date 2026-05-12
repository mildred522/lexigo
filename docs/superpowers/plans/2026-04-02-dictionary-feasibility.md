# Dictionary Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python-based feasibility pipeline that validates Japanese and French dictionary sources, samples data quality, runs a small real translation experiment, and produces a queryable SQLite prototype plus a written feasibility conclusion.

**Architecture:** Use a small Python package with source-specific parsers, a provider-based translation layer, and a SQLite builder. Keep raw downloads in `sources/`, normalized JSONL in `artifacts/normalized/`, and generated outputs in `artifacts/`. Drive everything through tested library functions first, then thin CLI scripts.

**Tech Stack:** Python 3.12, pytest, requests, SQLite, JSONL, gzip, standard library dataclasses

---

### Task 1: Bootstrap Repository And Test Harness

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.gitignore`
- Create: `C:\Users\10379\安卓单词软件\pyproject.toml`
- Create: `C:\Users\10379\安卓单词软件\README.md`
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\__init__.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_smoke.py`

- [ ] **Step 1: Write the failing smoke test**

```python
# C:\Users\10379\安卓单词软件\tests\test_smoke.py
from dict_feasibility import __version__


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dict_feasibility'`

- [ ] **Step 3: Write minimal implementation and project metadata**

```toml
# C:\Users\10379\安卓单词软件\pyproject.toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "dict-feasibility"
version = "0.1.0"
description = "Dictionary feasibility validation pipeline"
requires-python = ">=3.12"
dependencies = [
  "requests>=2.32.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\__init__.py
__version__ = "0.1.0"
```

```gitignore
# C:\Users\10379\安卓单词软件\.gitignore
__pycache__/
.pytest_cache/
.venv/
sources/
artifacts/
*.sqlite
*.db
```

```md
# C:\Users\10379\安卓单词软件\README.md
# Dictionary Feasibility

Validate JMdict, Tatoeba, and Kaikki data for a future Android vocabulary app.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Initialize git and commit**

```bash
git init
git add .gitignore pyproject.toml README.md src/dict_feasibility/__init__.py tests/test_smoke.py
git commit -m "chore: bootstrap dictionary feasibility project"
```

### Task 2: Add Shared Models And Filesystem Layout Helpers

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\models.py`
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\paths.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_paths.py`

- [ ] **Step 1: Write the failing tests**

```python
# C:\Users\10379\安卓单词软件\tests\test_paths.py
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.paths import ensure_project_dirs


def test_ensure_project_dirs_creates_expected_structure(tmp_path: Path) -> None:
    result = ensure_project_dirs(tmp_path)

    assert result.sources_dir.exists()
    assert result.artifacts_dir.exists()
    assert result.normalized_dir.exists()
    assert result.reports_dir.exists()


def test_normalized_word_to_record() -> None:
    word = NormalizedWord(
        language="JA",
        lemma="食べる",
        surface="食べる",
        reading_or_ipa="たべる",
        pos="verb",
        meaning_source="jmdict",
        meaning_zh="吃",
        source_name="JMdict",
        source_entry_id="1001",
    )

    assert word.to_record()["meaning_zh"] == "吃"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_paths.py -v`
Expected: FAIL with missing modules `dict_feasibility.models` and `dict_feasibility.paths`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\models.py
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

    def to_record(self) -> dict[str, str]:
        return asdict(self)
```

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\paths.py
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProjectDirs:
    root: Path
    sources_dir: Path
    artifacts_dir: Path
    normalized_dir: Path
    reports_dir: Path


def ensure_project_dirs(root: Path) -> ProjectDirs:
    sources_dir = root / "sources"
    artifacts_dir = root / "artifacts"
    normalized_dir = artifacts_dir / "normalized"
    reports_dir = artifacts_dir / "reports"
    for path in (sources_dir, artifacts_dir, normalized_dir, reports_dir):
        path.mkdir(parents=True, exist_ok=True)
    return ProjectDirs(
        root=root,
        sources_dir=sources_dir,
        artifacts_dir=artifacts_dir,
        normalized_dir=normalized_dir,
        reports_dir=reports_dir,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_paths.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/models.py src/dict_feasibility/paths.py tests/test_paths.py
git commit -m "feat: add shared models and project path helpers"
```

### Task 3: Track Source Metadata And Licenses

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\source_registry.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\write_source_registry.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_source_registry.py`

- [ ] **Step 1: Write the failing tests**

```python
# C:\Users\10379\安卓单词软件\tests\test_source_registry.py
import json
from pathlib import Path

from dict_feasibility.source_registry import SourceRegistry, SourceSpec


def test_registry_writes_json_manifest(tmp_path: Path) -> None:
    registry = SourceRegistry(
        specs=[
            SourceSpec(
                key="jmdict",
                source_name="JMdict",
                download_url="https://example.test/jmdict",
                version="2026-04-01",
                license_name="EDRDG",
                notes="Requires attribution",
            )
        ]
    )

    out_path = tmp_path / "sources.json"
    registry.write(out_path)
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    assert payload[0]["key"] == "jmdict"
    assert payload[0]["license_name"] == "EDRDG"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_source_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dict_feasibility.source_registry'`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\source_registry.py
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class SourceSpec:
    key: str
    source_name: str
    download_url: str
    version: str
    license_name: str
    notes: str


@dataclass(slots=True)
class SourceRegistry:
    specs: list[SourceSpec]

    def write(self, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(spec) for spec in self.specs]
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

```python
# C:\Users\10379\安卓单词软件\scripts\write_source_registry.py
from pathlib import Path

from dict_feasibility.source_registry import SourceRegistry, SourceSpec


def main() -> None:
    registry = SourceRegistry(
        specs=[
            SourceSpec(
                key="jmdict",
                source_name="JMdict",
                download_url="https://www.edrdg.org/jmdict/j_jmdict.html",
                version="manual",
                license_name="EDRDG",
                notes="Confirm attribution before redistribution.",
            ),
            SourceSpec(
                key="tatoeba",
                source_name="Tatoeba",
                download_url="https://tatoeba.org/en/downloads",
                version="weekly",
                license_name="CC BY 2.0 FR",
                notes="Sentence and translation licensing must be preserved.",
            ),
            SourceSpec(
                key="kaikki_fr",
                source_name="Kaikki French Wiktionary",
                download_url="https://kaikki.org/frwiktionary/rawdata.html",
                version="manual",
                license_name="Wiktionary derived",
                notes="Verify downstream attribution language before product use.",
            ),
        ]
    )
    registry.write(Path("artifacts/reports/source_registry.json"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_source_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/source_registry.py scripts/write_source_registry.py tests/test_source_registry.py
git commit -m "feat: add source registry manifest generation"
```

### Task 4: Parse JMdict Into Normalized Japanese Records

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\jmdict_parser.py`
- Create: `C:\Users\10379\安卓单词软件\tests\fixtures\jmdict_sample.json`
- Create: `C:\Users\10379\安卓单词软件\tests\test_jmdict_parser.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\parse_jmdict.py`

- [ ] **Step 1: Write the failing test**

```python
# C:\Users\10379\安卓单词软件\tests\test_jmdict_parser.py
from pathlib import Path

from dict_feasibility.jmdict_parser import parse_jmdict_file


def test_parse_jmdict_file_extracts_core_fields() -> None:
    fixture = Path("tests/fixtures/jmdict_sample.json")
    records = list(parse_jmdict_file(fixture))

    assert records[0].language == "JA"
    assert records[0].lemma == "食べる"
    assert records[0].reading_or_ipa == "たべる"
    assert records[0].meaning_zh == "吃"
```

```json
// C:\Users\10379\安卓单词软件\tests\fixtures\jmdict_sample.json
[
  {
    "id": "1001",
    "kanji": [{"text": "食べる"}],
    "kana": [{"text": "たべる", "common": true}],
    "sense": [
      {
        "gloss": [
          {"lang": "eng", "text": "to eat"},
          {"lang": "zho", "text": "吃"}
        ],
        "partOfSpeech": ["verb"]
      }
    ]
  }
]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jmdict_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dict_feasibility.jmdict_parser'`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\jmdict_parser.py
import json
from pathlib import Path
from typing import Iterator

from dict_feasibility.models import NormalizedWord


def _pick_zh_gloss(sense: dict) -> str:
    for gloss in sense.get("gloss", []):
        if gloss.get("lang") in {"zho", "chi", "cmn"}:
            return gloss.get("text", "")
    for gloss in sense.get("gloss", []):
        if gloss.get("lang") == "eng":
            return gloss.get("text", "")
    return ""


def parse_jmdict_file(path: Path) -> Iterator[NormalizedWord]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    for entry in entries:
        sense = entry.get("sense", [{}])[0]
        lemma = entry.get("kanji", [{}])[0].get("text") or entry.get("kana", [{}])[0].get("text", "")
        reading = entry.get("kana", [{}])[0].get("text", "")
        yield NormalizedWord(
            language="JA",
            lemma=lemma,
            surface=lemma,
            reading_or_ipa=reading,
            pos=", ".join(sense.get("partOfSpeech", [])),
            meaning_source="jmdict",
            meaning_zh=_pick_zh_gloss(sense),
            source_name="JMdict",
            source_entry_id=str(entry.get("id", "")),
        )
```

```python
# C:\Users\10379\安卓单词软件\scripts\parse_jmdict.py
import json
from pathlib import Path

from dict_feasibility.jmdict_parser import parse_jmdict_file


def main() -> None:
    in_path = Path("sources/jmdict/jmdict-sample.json")
    out_path = Path("artifacts/normalized/jmdict_words.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        for record in parse_jmdict_file(in_path):
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jmdict_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/jmdict_parser.py scripts/parse_jmdict.py tests/fixtures/jmdict_sample.json tests/test_jmdict_parser.py
git commit -m "feat: parse jmdict sample into normalized records"
```

### Task 5: Parse Kaikki French Data Into Normalized Records

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\kaikki_parser.py`
- Create: `C:\Users\10379\安卓单词软件\tests\fixtures\kaikki_fr_sample.jsonl`
- Create: `C:\Users\10379\安卓单词软件\tests\test_kaikki_parser.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\parse_kaikki_fr.py`

- [ ] **Step 1: Write the failing test**

```python
# C:\Users\10379\安卓单词软件\tests\test_kaikki_parser.py
from pathlib import Path

from dict_feasibility.kaikki_parser import parse_kaikki_french_file


def test_parse_kaikki_french_file_extracts_core_fields() -> None:
    fixture = Path("tests/fixtures/kaikki_fr_sample.jsonl")
    records = list(parse_kaikki_french_file(fixture))

    assert records[0].language == "FR"
    assert records[0].lemma == "bonjour"
    assert records[0].reading_or_ipa == "bɔ̃.ʒuʁ"
    assert records[0].meaning_zh == ""
```

```json
{"word":"bonjour","sounds":[{"ipa":"bɔ̃.ʒuʁ"}],"pos":"intj","senses":[{"glosses":["hello"],"examples":[{"text":"Bonjour, Marie !"}]}]}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_kaikki_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dict_feasibility.kaikki_parser'`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\kaikki_parser.py
import json
from pathlib import Path
from typing import Iterator

from dict_feasibility.models import NormalizedWord


def parse_kaikki_french_file(path: Path) -> Iterator[NormalizedWord]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entry = json.loads(line)
            ipa = ""
            for sound in entry.get("sounds", []):
                ipa = sound.get("ipa", "")
                if ipa:
                    break
            yield NormalizedWord(
                language="FR",
                lemma=entry.get("word", ""),
                surface=entry.get("word", ""),
                reading_or_ipa=ipa,
                pos=entry.get("pos", ""),
                meaning_source="kaikki",
                meaning_zh="",
                source_name="Kaikki French Wiktionary",
                source_entry_id=entry.get("word", ""),
            )
```

```python
# C:\Users\10379\安卓单词软件\scripts\parse_kaikki_fr.py
import json
from pathlib import Path

from dict_feasibility.kaikki_parser import parse_kaikki_french_file


def main() -> None:
    in_path = Path("sources/kaikki_fr/kaikki-fr-sample.jsonl")
    out_path = Path("artifacts/normalized/kaikki_fr_words.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        for record in parse_kaikki_french_file(in_path):
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_kaikki_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/kaikki_parser.py scripts/parse_kaikki_fr.py tests/fixtures/kaikki_fr_sample.jsonl tests/test_kaikki_parser.py
git commit -m "feat: parse kaikki french sample into normalized records"
```

### Task 6: Normalize Example Sentences For Japanese And French

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\examples.py`
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\tatoeba_parser.py`
- Create: `C:\Users\10379\安卓单词软件\tests\fixtures\tatoeba_sample.tsv`
- Create: `C:\Users\10379\安卓单词软件\tests\test_examples.py`

- [ ] **Step 1: Write the failing tests**

```python
# C:\Users\10379\安卓单词软件\tests\test_examples.py
from pathlib import Path

from dict_feasibility.examples import collect_french_examples, score_example
from dict_feasibility.tatoeba_parser import parse_tatoeba_pairs


def test_collect_french_examples_reads_first_sentence() -> None:
    entry = {
        "senses": [
            {"examples": [{"text": "Bonjour, Marie !"}]},
        ]
    }

    examples = collect_french_examples(entry)
    assert examples == ["Bonjour, Marie !"]


def test_score_example_prefers_mid_length_sentences() -> None:
    assert score_example("Bonjour, Marie !") > score_example("Salut")


def test_parse_tatoeba_pairs_reads_japanese_chinese_rows() -> None:
    pairs = list(parse_tatoeba_pairs(Path("tests/fixtures/tatoeba_sample.tsv")))
    assert pairs[0]["sentence_foreign"] == "食べます。"
    assert pairs[0]["sentence_zh"] == "我吃。"
```

```tsv
# C:\Users\10379\安卓单词软件\tests\fixtures\tatoeba_sample.tsv
食べる	食べます。	我吃。
行く	学校へ行きます。	我去学校。
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_examples.py -v`
Expected: FAIL with missing module `dict_feasibility.examples`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\examples.py
def collect_french_examples(entry: dict) -> list[str]:
    results: list[str] = []
    for sense in entry.get("senses", []):
        for example in sense.get("examples", []):
            text = example.get("text", "").strip()
            if text:
                results.append(text)
    return results


def score_example(text: str) -> int:
    length = len(text.strip())
    if 12 <= length <= 60:
        return 100
    if 6 <= length < 12 or 61 <= length <= 90:
        return 60
    return 20
```

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\tatoeba_parser.py
import csv
from pathlib import Path
from typing import Iterator


def parse_tatoeba_pairs(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for lemma, sentence_foreign, sentence_zh in reader:
            yield {
                "lemma": lemma.strip(),
                "sentence_foreign": sentence_foreign.strip(),
                "sentence_zh": sentence_zh.strip(),
            }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_examples.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/examples.py src/dict_feasibility/tatoeba_parser.py tests/fixtures/tatoeba_sample.tsv tests/test_examples.py
git commit -m "feat: add example extraction and tatoeba sample parsing"
```

### Task 7: Add Translation Provider Interface And Cache

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\translation.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_translation.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\translate_meanings.py`

- [ ] **Step 1: Write the failing tests**

```python
# C:\Users\10379\安卓单词软件\tests\test_translation.py
from pathlib import Path

from dict_feasibility.translation import MemoryTranslationCache, translate_with_cache


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        self.calls += 1
        return f"{text}-zh"


def test_translate_with_cache_calls_provider_once() -> None:
    provider = FakeProvider()
    cache = MemoryTranslationCache()

    first = translate_with_cache(cache, provider, "hello", "fr", "zh")
    second = translate_with_cache(cache, provider, "hello", "fr", "zh")

    assert first == "hello-zh"
    assert second == "hello-zh"
    assert provider.calls == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_translation.py -v`
Expected: FAIL with missing module `dict_feasibility.translation`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\translation.py
from dataclasses import dataclass, field


@dataclass
class MemoryTranslationCache:
    items: dict[tuple[str, str, str], str] = field(default_factory=dict)

    def get(self, text: str, source_lang: str, target_lang: str) -> str | None:
        return self.items.get((text, source_lang, target_lang))

    def set(self, text: str, source_lang: str, target_lang: str, translated: str) -> None:
        self.items[(text, source_lang, target_lang)] = translated


def translate_with_cache(
    cache: MemoryTranslationCache,
    provider: object,
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    cached = cache.get(text, source_lang, target_lang)
    if cached is not None:
        return cached
    translated = provider.translate(text, source_lang, target_lang)
    cache.set(text, source_lang, target_lang, translated)
    return translated
```

```python
# C:\Users\10379\安卓单词软件\scripts\translate_meanings.py
from dict_feasibility.translation import MemoryTranslationCache


def main() -> None:
    cache = MemoryTranslationCache()
    print(f"translation cache ready: {len(cache.items)} entries")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_translation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/translation.py scripts/translate_meanings.py tests/test_translation.py
git commit -m "feat: add translation provider cache abstraction"
```

### Task 8: Build The SQLite Prototype Database

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\sqlite_builder.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_sqlite_builder.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\build_sqlite.py`

- [ ] **Step 1: Write the failing tests**

```python
# C:\Users\10379\安卓单词软件\tests\test_sqlite_builder.py
import sqlite3
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.sqlite_builder import build_sqlite


def test_build_sqlite_creates_queryable_words_table(tmp_path: Path) -> None:
    db_path = tmp_path / "prototype.db"
    build_sqlite(
        db_path,
        [
            NormalizedWord(
                language="JA",
                lemma="食べる",
                surface="食べる",
                reading_or_ipa="たべる",
                pos="verb",
                meaning_source="jmdict",
                meaning_zh="吃",
                source_name="JMdict",
                source_entry_id="1001",
            )
        ],
    )

    conn = sqlite3.connect(db_path)
    row = conn.execute("select lemma, meaning_zh from words where lemma = '食べる'").fetchone()
    conn.close()

    assert row == ("食べる", "吃")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sqlite_builder.py -v`
Expected: FAIL with missing module `dict_feasibility.sqlite_builder`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\sqlite_builder.py
import sqlite3
from pathlib import Path

from dict_feasibility.models import NormalizedWord


SCHEMA = """
create table if not exists words (
  id integer primary key autoincrement,
  language text not null,
  lemma text not null,
  surface text not null,
  reading_or_ipa text not null,
  pos text not null,
  meaning_source text not null,
  meaning_zh text not null,
  source_name text not null,
  source_entry_id text not null
);
create index if not exists idx_words_language on words(language);
create index if not exists idx_words_lemma on words(lemma);
create index if not exists idx_words_surface on words(surface);
"""


def build_sqlite(db_path: Path, words: list[NormalizedWord]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            """
            insert into words (
              language, lemma, surface, reading_or_ipa, pos,
              meaning_source, meaning_zh, source_name, source_entry_id
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    word.language,
                    word.lemma,
                    word.surface,
                    word.reading_or_ipa,
                    word.pos,
                    word.meaning_source,
                    word.meaning_zh,
                    word.source_name,
                    word.source_entry_id,
                )
                for word in words
            ],
        )
        conn.commit()
    finally:
        conn.close()
```

```python
# C:\Users\10379\安卓单词软件\scripts\build_sqlite.py
import json
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.sqlite_builder import build_sqlite


def _load_words(path: Path) -> list[NormalizedWord]:
    words: list[NormalizedWord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            words.append(NormalizedWord(**json.loads(line)))
    return words


def main() -> None:
    words = _load_words(Path("artifacts/normalized/jmdict_words.jsonl"))
    words.extend(_load_words(Path("artifacts/normalized/kaikki_fr_words.jsonl")))
    build_sqlite(Path("artifacts/prototype.db"), words)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sqlite_builder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/sqlite_builder.py scripts/build_sqlite.py tests/test_sqlite_builder.py
git commit -m "feat: build prototype sqlite dictionary database"
```

### Task 9: Generate Quality Sample Reports

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\reporting.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_reporting.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\sample_report.py`

- [ ] **Step 1: Write the failing tests**

```python
# C:\Users\10379\安卓单词软件\tests\test_reporting.py
from dict_feasibility.models import NormalizedWord
from dict_feasibility.reporting import summarize_words


def test_summarize_words_counts_missing_fields() -> None:
    summary = summarize_words(
        [
            NormalizedWord(
                language="FR",
                lemma="bonjour",
                surface="bonjour",
                reading_or_ipa="",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="你好",
                source_name="Kaikki",
                source_entry_id="bonjour",
            )
        ]
    )

    assert summary["total_words"] == 1
    assert summary["missing_pronunciation"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reporting.py -v`
Expected: FAIL with missing module `dict_feasibility.reporting`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\reporting.py
from dict_feasibility.models import NormalizedWord


def summarize_words(words: list[NormalizedWord]) -> dict[str, int]:
    total_words = len(words)
    missing_pronunciation = sum(1 for word in words if not word.reading_or_ipa.strip())
    missing_meaning = sum(1 for word in words if not word.meaning_zh.strip())
    return {
        "total_words": total_words,
        "missing_pronunciation": missing_pronunciation,
        "missing_meaning": missing_meaning,
    }
```

```python
# C:\Users\10379\安卓单词软件\scripts\sample_report.py
import json
from pathlib import Path

from dict_feasibility.jmdict_parser import parse_jmdict_file
from dict_feasibility.kaikki_parser import parse_kaikki_french_file
from dict_feasibility.reporting import summarize_words


def main() -> None:
    reports_dir = Path("artifacts/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    japanese_words = list(parse_jmdict_file(Path("sources/jmdict/jmdict-sample.json")))
    french_words = list(parse_kaikki_french_file(Path("sources/kaikki_fr/kaikki-fr-sample.jsonl")))

    (reports_dir / "jmdict-summary.json").write_text(
        json.dumps(summarize_words(japanese_words), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "kaikki-fr-summary.json").write_text(
        json.dumps(summarize_words(french_words), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reporting.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dict_feasibility/reporting.py scripts/sample_report.py tests/test_reporting.py
git commit -m "feat: add normalized data quality summary reporting"
```

### Task 10: Render The Feasibility Conclusion Document

**Files:**
- Create: `C:\Users\10379\安卓单词软件\src\dict_feasibility\feasibility_report.py`
- Create: `C:\Users\10379\安卓单词软件\tests\test_feasibility_report.py`
- Create: `C:\Users\10379\安卓单词软件\scripts\render_feasibility_report.py`
- Modify: `C:\Users\10379\安卓单词软件\README.md`
- Create: `C:\Users\10379\安卓单词软件\docs\feasibility-report.md`

- [ ] **Step 1: Write the failing test**

```python
# C:\Users\10379\安卓单词软件\tests\test_feasibility_report.py
from dict_feasibility.feasibility_report import render_report


def test_render_report_includes_verdict_and_counts() -> None:
    report = render_report(
        japanese_summary={"total_words": 1200, "missing_pronunciation": 10, "missing_meaning": 20},
        french_summary={"total_words": 900, "missing_pronunciation": 50, "missing_meaning": 900},
        translation_provider="openai",
        translation_sample_size=25,
    )

    assert "Feasible with scope limits" in report
    assert "Japanese total words: 1200" in report
    assert "French total words: 900" in report
    assert "Translation provider tested: openai" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_feasibility_report.py -v`
Expected: FAIL with missing module `dict_feasibility.feasibility_report`

- [ ] **Step 3: Write the report renderer and CLI**

```python
# C:\Users\10379\安卓单词软件\src\dict_feasibility\feasibility_report.py
def render_report(
    japanese_summary: dict[str, int],
    french_summary: dict[str, int],
    translation_provider: str,
    translation_sample_size: int,
) -> str:
    verdict = "Feasible"
    if french_summary["missing_meaning"] > 0:
        verdict = "Feasible with scope limits"
    return f"""# Dictionary Feasibility Report

## Verdict

{verdict}

## Japanese

- Japanese total words: {japanese_summary['total_words']}
- Japanese missing pronunciation: {japanese_summary['missing_pronunciation']}
- Japanese missing meaning: {japanese_summary['missing_meaning']}

## French

- French total words: {french_summary['total_words']}
- French missing pronunciation: {french_summary['missing_pronunciation']}
- French missing meaning: {french_summary['missing_meaning']}

## Translation

- Translation provider tested: {translation_provider}
- Translation sample size: {translation_sample_size}

## Recommendation

- Next stage: proceed to production-scale data cleaning if verdict is feasible.
"""
```

```python
# C:\Users\10379\安卓单词软件\scripts\render_feasibility_report.py
import json
from pathlib import Path

from dict_feasibility.feasibility_report import render_report


def main() -> None:
    japanese_summary = json.loads(Path("artifacts/reports/jmdict-summary.json").read_text(encoding="utf-8"))
    french_summary = json.loads(Path("artifacts/reports/kaikki-fr-summary.json").read_text(encoding="utf-8"))
    report = render_report(
        japanese_summary=japanese_summary,
        french_summary=french_summary,
        translation_provider="openai",
        translation_sample_size=25,
    )
    Path("docs/feasibility-report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_feasibility_report.py -v`
Expected: PASS

- [ ] **Step 5: Run the pipeline and render the report**

Run:

```bash
python scripts/write_source_registry.py
python scripts/parse_jmdict.py
python scripts/parse_kaikki_fr.py
python scripts/build_sqlite.py
python scripts/sample_report.py
python scripts/render_feasibility_report.py
```

Expected:
- `artifacts/reports/source_registry.json` exists
- `artifacts/reports/jmdict-summary.json` exists
- `artifacts/reports/kaikki-fr-summary.json` exists
- `docs/feasibility-report.md` exists

- [ ] **Step 6: Update README runbook**

```md
# C:\Users\10379\安卓单词软件\README.md
# Dictionary Feasibility

## Setup

1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `python -m pip install -e .[dev]`

## Commands

1. `python scripts/write_source_registry.py`
2. `python scripts/parse_jmdict.py`
3. `python scripts/parse_kaikki_fr.py`
4. `python scripts/build_sqlite.py`
5. `python scripts/sample_report.py`
6. `python scripts/render_feasibility_report.py`
```

- [ ] **Step 7: Verify full test suite**

Run: `python -m pytest -v`
Expected: PASS

Run: `python -m compileall src scripts`
Expected: PASS with no syntax errors

- [ ] **Step 8: Commit**

```bash
git add README.md docs/feasibility-report.md src/dict_feasibility/feasibility_report.py scripts/render_feasibility_report.py tests/test_feasibility_report.py artifacts/reports/source_registry.json artifacts/reports/jmdict-summary.json artifacts/reports/kaikki-fr-summary.json
git commit -m "docs: render feasibility report from pipeline outputs"
```
