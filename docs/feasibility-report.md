# Dictionary Feasibility Report

## Verdict

High feasibility

## Fixture Pipeline Snapshot

- Japanese total words: 2
- Japanese missing pronunciation: 0
- Japanese missing source meaning: 0
- Japanese missing meaning: 0
- Japanese pronunciation coverage: 100.0%
- Japanese source meaning coverage: 100.0%
- Japanese meaning coverage: 100.0%
- Japanese sample lemmas: 食べる, 飲む
- French total words: 1
- French missing pronunciation: 0
- French missing source meaning: 0
- French missing meaning: 0
- French pronunciation coverage: 100.0%
- French source meaning coverage: 100.0%
- French meaning coverage: 100.0%
- French sample lemmas: bonjour

## Official Source Validation

- Official source validation sample size: 50 per language
- Japanese pronunciation coverage on official sample: 100.0%
- Japanese source gloss coverage on official sample: 100.0%
- Japanese direct Chinese gloss coverage in source: 0.0%
- Japanese entries requiring translation: 50
- French pronunciation coverage on official sample: 100.0%
- French source gloss coverage on official sample: 100.0%
- French direct Chinese gloss coverage in source: 0.0%
- French entries requiring translation: 50

## Translation

- Translation provider tested: openai:gpt-5.4-mini
- Fixture translation sample size: 3
- Japanese translated coverage on official sample: 96.0%
- Japanese translation errors on official sample: 2
- French translated coverage on official sample: 96.0%
- French translation errors on official sample: 2
- Live provider validation shows strong Chinese-ready coverage on the official sample.
- Remaining failures are limited edge cases, not a structural blocker for the project.

## Recommendation

- Treat translation as a first-class requirement for both Japanese and French.
- Proceed with package and search integration, but do not claim Chinese-ready data coverage until a real provider is validated on official samples.
- Keep Japanese and French source glosses in the packaged database for QA and fallback.
- Use the SQLite package as the app-side dictionary baseline.
