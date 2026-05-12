# Japanese Study Card Layout Design

## Goal

Improve the memorization experience by redesigning the learning and review screens around a focused, immersive study card. The first version targets Japanese only for grammar-aware presentation, because the current JMdict data has complete translations, readings, and detailed part-of-speech metadata.

This design intentionally focuses on visual layout first. Interaction refinements such as auto-advance, keyboard submit behavior, and answer animation should follow after the layout is stable.

## Scope

In scope:

- Redesign the visual layout of `LearningScreen` and `ReviewScreen`.
- Remove daily cover and personalized background treatment from study/review flows.
- Add Japanese grammar chips derived from existing `pos` strings.
- Keep learning/review logic unchanged.
- Share layout components between learning and review where practical.

Out of scope:

- French grammar-aware cards.
- New learning algorithms or spaced repetition changes.
- Full Japanese grammar analysis beyond deterministic `pos` mapping.
- New dictionary data fields.
- Audio engine changes.

## Experience Principles

- The study card is the visual center.
- Progress is visible but quiet.
- The layout should not jump between question, input, feedback, and summary states.
- Primary actions stay in the thumb-friendly lower area.
- Grammar chips must be accurate; if a feature cannot be confidently derived from `pos`, do not show it.
- Study and review should feel like the same flow with different data.

## Page Structure

The learning and review screens should use a shared three-part layout:

```text
Top Bar
  Title
  Language and progress metadata

Study Card
  Prompt content
  Reading
  Japanese grammar chips
  Meaning or feedback content

Action Zone
  Choice options or spelling input
  Speak / hint / submit / continue controls
```

### Top Bar

The top bar should show only session state:

- `学习` or `复习`
- language label
- current progress such as `3 / 20`
- review queue count when relevant

It should not show daily cover, achievement summaries, or background controls.

### Study Card

The card should have a stable minimum height so the page does not feel jumpy across stages.

Choice stage:

- Large Japanese lemma.
- Reading below the lemma.
- Grammar chips below reading.
- Optional lightweight prompt hint if needed.

Spelling stage:

- Large Chinese meaning as the prompt.
- Grammar chips and language context remain visible.
- Reading may stay hidden until feedback if the prompt would give away the answer.

Feedback stage:

- Correct/incorrect state.
- Full word information:
  - lemma
  - reading
  - grammar chips
  - Chinese meaning
  - source meaning if useful
  - examples if available

Summary stage:

- Compact session summary in the same visual system.
- Restart action stays in the action zone.

## Japanese Grammar Chips

The first version derives chips from `StudyWordItem.pos`.

Supported chips:

- `名词` from `noun`
- `一段动词` from `Ichidan verb`
- `五段动词` from `Godan verb`
- `する动词` from `suru verb`
- `自动词` from `intransitive verb`
- `他动词` from `transitive verb`
- `い形容词` from `adjective (keiyoushi)`
- `な形容词` from `adjectival nouns or quasi-adjectives`
- `副词` from `adverb`
- `表达` from `expressions`
- `代词` from `pronoun`
- `接头词` from `prefix`
- `接尾词` from `suffix`
- `感叹词` from `interjection`

Rules:

- Preserve order by learning value: main part of speech first, then conjugation/type, then transitivity.
- Deduplicate chips.
- Cap visible chips to avoid crowding. If more chips exist, show the most useful ones first.
- Only show chips for Japanese in the first implementation.

## Component Boundaries

Recommended components:

- `StudySessionScaffold`
  - Shared top/card/action layout for learning and review.
- `JapaneseGrammarChipRow`
  - Maps `StudyWordItem.pos` to deterministic Japanese chips.
- `StudyPromptCard`
  - Displays prompt, reading, chips, and feedback content.
- `ChoiceAnswerGrid`
  - Large stable choice buttons.
- `SpellingAnswerPanel`
  - Stable spelling input and secondary actions.

These components should live near the existing study UI code unless the implementation naturally reveals a better local boundary.

## Data Flow

Existing state should remain the source of truth:

- `LearningUiState`
- `ReviewUiState`
- `LearningSession`
- `StudyWordItem`

The UI should derive chips locally from `StudyWordItem.language` and `StudyWordItem.pos`. No repository, database, or translation pipeline change is required.

## Error Handling

- If `pos` is blank or unknown, show no grammar chips.
- If reading is blank, omit the reading row.
- If examples are absent, omit examples.
- Long meanings should wrap inside the card without pushing primary actions off screen on typical phone sizes.

## Testing

Unit tests:

- Japanese `pos` strings map to expected chips.
- Unknown or French words do not show Japanese grammar chips.
- Mixed `pos` strings deduplicate and prioritize chips.

Compose/UI tests:

- Learning screen shows Japanese grammar chips for a Japanese word.
- Review screen uses the same visual card path.
- Daily cover does not appear in the study/review flow after the redesign.

Manual checks:

- Choice stage fits on a phone viewport.
- Spelling stage works with keyboard visible.
- Feedback stage remains readable with long meaning text.

## Rollout

1. Add deterministic Japanese grammar chip mapper and tests.
2. Introduce shared study layout components.
3. Apply the layout to `LearningScreen`.
4. Apply the layout to `ReviewScreen`.
5. Run focused unit and Compose tests.

The first implementation should avoid modifying learning behavior. Once the visual structure is stable, interaction handfeel work can follow as a separate design.
