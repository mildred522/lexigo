# Real Source Validation

## Scope

Validated official upstream sources with a real sample size of 50 entries per language:

- Japanese: `https://www.edrdg.org/pub/Nihongo/JMdict.gz`
- French: `https://kaikki.org/frwiktionary/raw-wiktextract-data.jsonl.gz`

## Results

### Japanese

- Sampled entries: 50
- Pronunciation present: 50 / 50
- Source gloss present: 50 / 50
- Chinese gloss present directly in source: 0 / 50
- English gloss present: 50 / 50
- Immediate implication: Japanese source structure is strong, but Chinese meanings are not directly available in this sample and need translation or a Chinese-aligned source.

### French

- Sampled entries: 50
- Pronunciation present: 50 / 50
- Source gloss present: 50 / 50
- Chinese gloss present directly in source: 0 / 50
- Immediate implication: French source structure is strong, but Chinese meanings require a translation layer.

## Conclusion

- Structural feasibility is high: both official sources provide stable lemma, pronunciation, and source-language gloss data across the tested sample.
- Chinese-ready feasibility is not high without an explicit translation pipeline.
- The previous fixture-only conclusion was too optimistic for a Chinese-targeted app.
- Current defensible conclusion: the project is feasible if translation is treated as a first-class part of the data pipeline for both Japanese and French.
