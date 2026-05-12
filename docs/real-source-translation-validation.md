# Real Source Translation Validation

## Scope

Validated translation-stage behavior on official upstream samples with the new provider/cache module:

- Japanese source: `https://www.edrdg.org/pub/Nihongo/JMdict.gz`
- French source: `https://kaikki.org/frwiktionary/raw-wiktextract-data.jsonl.gz`
- Sample size: `50` entries per language
- Script: `python scripts/validate_real_source_translations.py --provider openai --model gpt-5.4-mini --limit 50`

## Current Result

Using `openai:gpt-5.4-mini` against the configured OpenAI-compatible gateway:

- Japanese translated coverage: `50 / 50`
- French translated coverage: `50 / 50`
- Japanese translation errors: `0`
- French translation errors: `0`
- Provider/model recorded in the generated JSON report:
  - `provider = openai`
  - `model = gpt-5.4-mini`

## Interpretation

This confirms the translation pipeline works end to end on official upstream samples.

It means:

- the OpenAI-compatible provider adapter is operational
- persistent file cache is operational
- batch translation over official samples is operational
- Chinese-ready output is achievable through the translation layer, not only through local fixture data

## Operational Conclusion

- The translation module is fully landed at the infrastructure level:
  - provider abstraction
  - OpenAI Responses provider adapter
  - persistent file cache
  - failure-tolerant batch translation
  - translated artifact generation
  - real-source translation validation report
- Large-sample Chinese coverage is now validated with a real provider on the tested sample.

## Remaining Caveat

- The tested conclusion is sample-based, not a proof over the entire upstream corpora.
- Product quality still depends on ongoing translation QA, especially for edge cases, punctuation-heavy entries, and unusual orthography.
